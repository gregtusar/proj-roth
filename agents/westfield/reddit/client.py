"""
Reddit API client for fetching posts and comments from subreddits.
Uses PRAW (Python Reddit API Wrapper) for authentication and data access.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime, timedelta
import praw
import prawcore
from praw.models import Submission, Comment, Subreddit
import logging

logger = logging.getLogger(__name__)


class RedditClient:
    """Async-compatible Reddit client for fetching and monitoring subreddit data."""
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_agent: str = "westfield-agent/1.0"
    ):
        """Initialize Reddit client with authentication credentials."""
        self.client_id = client_id or os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = user_agent
        
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Reddit API credentials required. Set REDDIT_CLIENT_ID and "
                "REDDIT_CLIENT_SECRET environment variables or pass them as arguments."
            )
        
        self.reddit = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent
        )
        
        # Verify authentication
        try:
            self.reddit.user.me()
        except prawcore.exceptions.ResponseException:
            # Read-only mode is fine for our use case
            logger.info("Using Reddit API in read-only mode")
    
    def get_subreddit(self, name: str) -> Subreddit:
        """Get a subreddit by name."""
        return self.reddit.subreddit(name)
    
    async def fetch_posts(
        self,
        subreddit_name: str,
        limit: int = 100,
        time_filter: str = "week",
        sort: str = "hot"
    ) -> List[Dict[str, Any]]:
        """
        Fetch posts from a subreddit.
        
        Args:
            subreddit_name: Name of the subreddit (e.g., "newjersey")
            limit: Maximum number of posts to fetch
            time_filter: Time filter for top posts ("hour", "day", "week", "month", "year", "all")
            sort: Sort method ("hot", "new", "top", "rising")
        
        Returns:
            List of post dictionaries with metadata and content
        """
        subreddit = self.get_subreddit(subreddit_name)
        
        # Select appropriate listing based on sort method
        if sort == "hot":
            posts = subreddit.hot(limit=limit)
        elif sort == "new":
            posts = subreddit.new(limit=limit)
        elif sort == "top":
            posts = subreddit.top(time_filter=time_filter, limit=limit)
        elif sort == "rising":
            posts = subreddit.rising(limit=limit)
        else:
            raise ValueError(f"Invalid sort method: {sort}")
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._extract_posts,
            posts
        )
    
    def _extract_posts(self, posts) -> List[Dict[str, Any]]:
        """Extract post data from PRAW submission objects."""
        extracted = []
        for post in posts:
            extracted.append({
                "id": post.id,
                "title": post.title,
                "author": str(post.author) if post.author else "[deleted]",
                "created_utc": datetime.fromtimestamp(post.created_utc),
                "score": post.score,
                "upvote_ratio": post.upvote_ratio,
                "num_comments": post.num_comments,
                "permalink": f"https://reddit.com{post.permalink}",
                "url": post.url,
                "selftext": post.selftext,
                "subreddit": str(post.subreddit),
                "is_self": post.is_self,
                "link_flair_text": post.link_flair_text,
                "distinguished": post.distinguished,
                "stickied": post.stickied,
                "locked": post.locked,
                "over_18": post.over_18,
                "spoiler": post.spoiler,
            })
        return extracted
    
    async def fetch_comments(
        self,
        post_id: str,
        limit: int = 100,
        depth: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch comments from a post.
        
        Args:
            post_id: Reddit post ID
            limit: Maximum number of comments to fetch
            depth: Maximum depth of comment tree to traverse
        
        Returns:
            List of comment dictionaries
        """
        submission = self.reddit.submission(id=post_id)
        
        # Expand comment forest
        submission.comments.replace_more(limit=0)
        
        # Run in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._extract_comments,
            submission.comments,
            limit,
            depth
        )
    
    def _extract_comments(
        self,
        comments,
        limit: int,
        depth: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Extract comment data from PRAW comment objects."""
        extracted = []
        count = 0
        
        def process_comment(comment, current_depth=0):
            nonlocal count
            if count >= limit:
                return
            if depth is not None and current_depth > depth:
                return
            
            if isinstance(comment, Comment):
                extracted.append({
                    "id": comment.id,
                    "author": str(comment.author) if comment.author else "[deleted]",
                    "body": comment.body,
                    "created_utc": datetime.fromtimestamp(comment.created_utc),
                    "score": comment.score,
                    "is_submitter": comment.is_submitter,
                    "distinguished": comment.distinguished,
                    "edited": comment.edited,
                    "parent_id": comment.parent_id,
                    "permalink": f"https://reddit.com{comment.permalink}",
                    "depth": current_depth,
                    "locked": comment.locked,
                    "collapsed": comment.collapsed,
                })
                count += 1
                
                # Process replies
                for reply in comment.replies:
                    process_comment(reply, current_depth + 1)
        
        for comment in comments:
            process_comment(comment)
        
        return extracted
    
    async def stream_new_posts(
        self,
        subreddit_name: str,
        pause_after: int = 10,
        skip_existing: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream new posts from a subreddit as they appear.
        
        Args:
            subreddit_name: Name of the subreddit
            pause_after: Number of items to yield before pausing
            skip_existing: Whether to skip existing posts on first run
        
        Yields:
            Post dictionaries as they appear
        """
        subreddit = self.get_subreddit(subreddit_name)
        
        # Track seen posts to avoid duplicates
        seen_ids = set()
        
        # Skip existing posts if requested
        if skip_existing:
            for post in subreddit.new(limit=100):
                seen_ids.add(post.id)
        
        while True:
            try:
                # Check for new posts
                for post in subreddit.new(limit=pause_after):
                    if post.id not in seen_ids:
                        seen_ids.add(post.id)
                        post_data = self._extract_posts([post])[0]
                        yield post_data
                
                # Rate limit - Reddit API allows 60 requests per minute
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error streaming posts: {e}")
                await asyncio.sleep(60)  # Back off on error
    
    async def search_posts(
        self,
        subreddit_name: str,
        query: str,
        limit: int = 100,
        time_filter: str = "all",
        sort: str = "relevance"
    ) -> List[Dict[str, Any]]:
        """
        Search for posts in a subreddit.
        
        Args:
            subreddit_name: Name of the subreddit
            query: Search query
            limit: Maximum number of results
            time_filter: Time filter for search
            sort: Sort method for results
        
        Returns:
            List of matching posts
        """
        subreddit = self.get_subreddit(subreddit_name)
        
        # Run search in executor
        loop = asyncio.get_event_loop()
        posts = await loop.run_in_executor(
            None,
            lambda: list(subreddit.search(
                query,
                limit=limit,
                time_filter=time_filter,
                sort=sort
            ))
        )
        
        return self._extract_posts(posts)
    
    async def fetch_historical_posts(
        self,
        subreddit_name: str,
        days_back: int = 30,
        batch_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical posts from a subreddit going back specified days.
        
        Args:
            subreddit_name: Name of the subreddit
            days_back: Number of days to go back
            batch_size: Number of posts to fetch per batch
        
        Returns:
            List of historical posts
        """
        all_posts = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Fetch posts in batches
        for sort_method in ["hot", "top", "new"]:
            posts = await self.fetch_posts(
                subreddit_name,
                limit=batch_size,
                time_filter="month" if days_back > 7 else "week",
                sort=sort_method
            )
            
            # Filter by date and deduplicate
            existing_ids = {p["id"] for p in all_posts}
            for post in posts:
                if post["id"] not in existing_ids and post["created_utc"] >= cutoff_date:
                    all_posts.append(post)
        
        # Sort by creation time
        all_posts.sort(key=lambda x: x["created_utc"], reverse=True)
        
        return all_posts