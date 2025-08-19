"""
Reddit data downloader for initial data collection and updates.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from .client import RedditClient
from ..models.reddit_data import RedditPost, RedditComment

logger = logging.getLogger(__name__)


class RedditDownloader:
    """Downloads and manages Reddit data for local politics analysis."""
    
    def __init__(
        self,
        client: RedditClient,
        data_dir: str = "data/reddit"
    ):
        """
        Initialize the downloader.
        
        Args:
            client: RedditClient instance
            data_dir: Directory to store downloaded data
        """
        self.client = client
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.posts_dir = self.data_dir / "posts"
        self.comments_dir = self.data_dir / "comments"
        self.metadata_dir = self.data_dir / "metadata"
        
        for dir_path in [self.posts_dir, self.comments_dir, self.metadata_dir]:
            dir_path.mkdir(exist_ok=True)
    
    async def download_initial_data(
        self,
        subreddit: str = "newjersey",
        days_back: int = 30,
        fetch_comments: bool = True,
        comment_limit: int = 50
    ) -> Dict[str, Any]:
        """
        Download initial dataset from subreddit.
        
        Args:
            subreddit: Subreddit name to download from
            days_back: Number of days of history to fetch
            fetch_comments: Whether to fetch comments for posts
            comment_limit: Max comments per post
        
        Returns:
            Summary of downloaded data
        """
        logger.info(f"Starting initial download from r/{subreddit}")
        
        # Fetch historical posts
        posts = await self.client.fetch_historical_posts(
            subreddit,
            days_back=days_back
        )
        
        logger.info(f"Fetched {len(posts)} posts from last {days_back} days")
        
        # Convert to data models and save
        saved_posts = []
        for post_data in posts:
            post = RedditPost(
                id=post_data["id"],
                title=post_data["title"],
                author=post_data["author"],
                created_utc=post_data["created_utc"],
                score=post_data["score"],
                upvote_ratio=post_data["upvote_ratio"],
                num_comments=post_data["num_comments"],
                permalink=post_data["permalink"],
                url=post_data["url"],
                selftext=post_data["selftext"],
                subreddit=post_data["subreddit"],
                is_self=post_data["is_self"],
                link_flair_text=post_data.get("link_flair_text"),
                distinguished=post_data.get("distinguished"),
                stickied=post_data["stickied"],
                locked=post_data["locked"],
                over_18=post_data["over_18"],
                spoiler=post_data["spoiler"]
            )
            
            # Save post
            self._save_post(post)
            saved_posts.append(post)
        
        # Fetch comments if requested
        total_comments = 0
        if fetch_comments:
            logger.info("Fetching comments for posts...")
            
            # Prioritize posts with more engagement
            sorted_posts = sorted(
                saved_posts,
                key=lambda p: p.score + p.num_comments,
                reverse=True
            )
            
            for post in sorted_posts[:100]:  # Limit to top 100 posts
                if post.num_comments > 0:
                    try:
                        comments_data = await self.client.fetch_comments(
                            post.id,
                            limit=comment_limit
                        )
                        
                        for comment_data in comments_data:
                            comment = RedditComment(
                                id=comment_data["id"],
                                author=comment_data["author"],
                                body=comment_data["body"],
                                created_utc=comment_data["created_utc"],
                                score=comment_data["score"],
                                parent_id=comment_data["parent_id"],
                                permalink=comment_data["permalink"],
                                is_submitter=comment_data.get("is_submitter", False),
                                distinguished=comment_data.get("distinguished"),
                                edited=comment_data.get("edited", False),
                                depth=comment_data.get("depth", 0),
                                locked=comment_data.get("locked", False),
                                collapsed=comment_data.get("collapsed", False)
                            )
                            
                            self._save_comment(comment, post.id)
                            total_comments += 1
                        
                        # Rate limiting
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error fetching comments for post {post.id}: {e}")
        
        # Save metadata
        metadata = {
            "subreddit": subreddit,
            "download_date": datetime.now().isoformat(),
            "days_back": days_back,
            "total_posts": len(saved_posts),
            "total_comments": total_comments,
            "date_range": {
                "start": min(p.created_utc for p in saved_posts).isoformat(),
                "end": max(p.created_utc for p in saved_posts).isoformat()
            }
        }
        
        self._save_metadata(metadata)
        
        logger.info(f"Download complete: {len(saved_posts)} posts, {total_comments} comments")
        
        return metadata
    
    async def update_data(
        self,
        subreddit: str = "newjersey",
        fetch_comments: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch new posts since last update.
        
        Args:
            subreddit: Subreddit to update
            fetch_comments: Whether to fetch comments
        
        Returns:
            Summary of new data
        """
        # Get last update time
        last_update = self._get_last_update_time()
        
        logger.info(f"Updating data since {last_update}")
        
        # Fetch new posts
        new_posts = []
        posts = await self.client.fetch_posts(
            subreddit,
            limit=100,
            sort="new"
        )
        
        for post_data in posts:
            if post_data["created_utc"] > last_update:
                post = RedditPost(
                    id=post_data["id"],
                    title=post_data["title"],
                    author=post_data["author"],
                    created_utc=post_data["created_utc"],
                    score=post_data["score"],
                    upvote_ratio=post_data["upvote_ratio"],
                    num_comments=post_data["num_comments"],
                    permalink=post_data["permalink"],
                    url=post_data["url"],
                    selftext=post_data["selftext"],
                    subreddit=post_data["subreddit"],
                    is_self=post_data["is_self"],
                    link_flair_text=post_data.get("link_flair_text"),
                    distinguished=post_data.get("distinguished"),
                    stickied=post_data["stickied"],
                    locked=post_data["locked"],
                    over_18=post_data["over_18"],
                    spoiler=post_data["spoiler"]
                )
                
                self._save_post(post)
                new_posts.append(post)
        
        # Fetch comments for new posts
        new_comments = 0
        if fetch_comments:
            for post in new_posts:
                if post.num_comments > 0:
                    try:
                        comments_data = await self.client.fetch_comments(
                            post.id,
                            limit=50
                        )
                        
                        for comment_data in comments_data:
                            comment = RedditComment(
                                id=comment_data["id"],
                                author=comment_data["author"],
                                body=comment_data["body"],
                                created_utc=comment_data["created_utc"],
                                score=comment_data["score"],
                                parent_id=comment_data["parent_id"],
                                permalink=comment_data["permalink"],
                                is_submitter=comment_data.get("is_submitter", False),
                                distinguished=comment_data.get("distinguished"),
                                edited=comment_data.get("edited", False),
                                depth=comment_data.get("depth", 0),
                                locked=comment_data.get("locked", False),
                                collapsed=comment_data.get("collapsed", False)
                            )
                            
                            self._save_comment(comment, post.id)
                            new_comments += 1
                        
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error fetching comments for post {post.id}: {e}")
        
        logger.info(f"Update complete: {len(new_posts)} new posts, {new_comments} new comments")
        
        return {
            "new_posts": len(new_posts),
            "new_comments": new_comments,
            "update_time": datetime.now().isoformat()
        }
    
    async def continuous_monitoring(
        self,
        subreddit: str = "newjersey",
        update_interval: int = 300  # 5 minutes
    ):
        """
        Continuously monitor subreddit for new posts.
        
        Args:
            subreddit: Subreddit to monitor
            update_interval: Seconds between update checks
        """
        logger.info(f"Starting continuous monitoring of r/{subreddit}")
        
        while True:
            try:
                # Perform update
                result = await self.update_data(subreddit)
                
                if result["new_posts"] > 0:
                    logger.info(f"Found {result['new_posts']} new posts")
                
                # Wait before next update
                await asyncio.sleep(update_interval)
                
            except Exception as e:
                logger.error(f"Error during monitoring: {e}")
                await asyncio.sleep(update_interval * 2)  # Back off on error
    
    def _save_post(self, post: RedditPost):
        """Save post to disk."""
        filename = self.posts_dir / f"{post.id}.json"
        with open(filename, "w") as f:
            json.dump(post.to_dict(), f, indent=2)
    
    def _save_comment(self, comment: RedditComment, post_id: str):
        """Save comment to disk."""
        # Organize comments by post
        post_comments_dir = self.comments_dir / post_id
        post_comments_dir.mkdir(exist_ok=True)
        
        filename = post_comments_dir / f"{comment.id}.json"
        with open(filename, "w") as f:
            json.dump(comment.to_dict(), f, indent=2)
    
    def _save_metadata(self, metadata: Dict[str, Any]):
        """Save metadata about the download."""
        filename = self.metadata_dir / f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(metadata, f, indent=2)
    
    def _get_last_update_time(self) -> datetime:
        """Get the time of the last update."""
        # Look for most recent post
        posts = list(self.posts_dir.glob("*.json"))
        
        if not posts:
            # No posts, return 30 days ago
            return datetime.now() - timedelta(days=30)
        
        # Find most recent post
        latest_time = datetime.min
        for post_file in posts:
            with open(post_file) as f:
                post_data = json.load(f)
                created = datetime.fromisoformat(post_data["created_utc"])
                if created > latest_time:
                    latest_time = created
        
        return latest_time
    
    def load_posts(self, limit: Optional[int] = None) -> List[RedditPost]:
        """Load saved posts from disk."""
        posts = []
        post_files = list(self.posts_dir.glob("*.json"))
        
        if limit:
            post_files = post_files[:limit]
        
        for post_file in post_files:
            with open(post_file) as f:
                post_data = json.load(f)
                posts.append(RedditPost.from_dict(post_data))
        
        return posts
    
    def load_comments(self, post_id: str) -> List[RedditComment]:
        """Load comments for a specific post."""
        comments = []
        comments_dir = self.comments_dir / post_id
        
        if comments_dir.exists():
            for comment_file in comments_dir.glob("*.json"):
                with open(comment_file) as f:
                    comment_data = json.load(f)
                    comments.append(RedditComment.from_dict(comment_data))
        
        return comments