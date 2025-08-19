"""
Westfield Agent - Local Politics Intelligence using Google ADK
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import asyncio

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from google import genai
from google.genai import types

from agents.westfield.reddit.client import RedditClient
from agents.westfield.reddit.downloader import RedditDownloader
from agents.westfield.storage.vector_store import VectorStore
from agents.westfield.models.reddit_data import PoliticalTopic, ContentRelevance
from agents.westfield.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini client
client = genai.Client()

# Agent configuration
MODEL_ID = "gemini-2.0-flash-exp"

AGENT_PROMPT = """You are the Westfield Agent, an AI assistant specializing in New Jersey local politics and social media intelligence.

Your primary data source is Reddit (r/newjersey and related subreddits), which you monitor for discussions about:
- Local elections and candidates
- Property taxes and budgets
- School board issues
- Infrastructure and development
- Public safety concerns
- Transportation (NJ Transit, traffic)
- Environmental issues
- Local government decisions

You have access to:
1. A vector database of Reddit posts and comments about NJ politics
2. Real-time Reddit search capabilities
3. The ability to download and analyze new posts

Focus areas include:
- NJ Congressional District 07 (Union, Somerset, Hunterdon, Morris, Warren, Essex, Sussex counties)
- Cities like Westfield, Summit, Cranford, Berkeley Heights, Springfield
- State-level politics affecting these communities

When answering questions:
- Cite specific Reddit posts when relevant (include scores and comment counts)
- Identify trending topics and sentiment
- Highlight different perspectives from the community
- Note any emerging issues or concerns

Be objective and present multiple viewpoints when they exist in the data."""


def reddit_search_tool(query: str, subreddit: str = "newjersey", limit: int = 10) -> Dict[str, Any]:
    """
    Search Reddit for posts matching a query.
    
    Args:
        query: Search query
        subreddit: Subreddit to search (default: newjersey)
        limit: Maximum number of results (default: 10)
    
    Returns:
        Dictionary with search results
    """
    try:
        # Run async function in sync context
        async def search():
            client = RedditClient()
            posts = await client.search_posts(
                subreddit_name=subreddit,
                query=query,
                limit=limit,
                time_filter="month",
                sort="relevance"
            )
            return posts
        
        # Get event loop or create new one
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        posts = loop.run_until_complete(search())
        
        # Format results
        results = []
        for post in posts:
            results.append({
                "title": post["title"],
                "author": post["author"],
                "score": post["score"],
                "num_comments": post["num_comments"],
                "created": post["created_utc"].isoformat(),
                "url": post["permalink"],
                "selftext": post["selftext"][:500] if post["selftext"] else None,
                "subreddit": post["subreddit"]
            })
        
        return {
            "query": query,
            "subreddit": subreddit,
            "count": len(results),
            "posts": results
        }
        
    except Exception as e:
        logger.error(f"Error searching Reddit: {e}")
        return {
            "error": str(e),
            "query": query,
            "posts": []
        }


def vector_search_tool(query: str, limit: int = 10, filter_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Search the vector database for relevant Reddit content.
    
    Args:
        query: Search query
        limit: Maximum number of results (default: 10)
        filter_type: Filter by type - "post" or "comment" (optional)
    
    Returns:
        Dictionary with search results and context
    """
    try:
        store = VectorStore()
        
        # Build filter
        filter_metadata = None
        if filter_type:
            filter_metadata = {"type": filter_type}
        
        # Search
        results = store.search(
            query=query,
            n_results=limit,
            filter_metadata=filter_metadata
        )
        
        # Format results
        formatted_results = []
        for metadata, score in results:
            result = {
                "type": metadata["type"],
                "score": metadata.get("score", 0),
                "author": metadata["author"],
                "created": metadata["created_utc"],
                "similarity": round(score, 3),
                "url": metadata["url"]
            }
            
            # Add type-specific fields
            if metadata["type"] == "post":
                result["post_id"] = metadata["post_id"]
                result["num_comments"] = metadata.get("num_comments", 0)
            else:
                result["comment_id"] = metadata["comment_id"]
                result["post_id"] = metadata["post_id"]
            
            # Add analysis fields if present
            if metadata.get("topics"):
                result["topics"] = metadata["topics"].split(",")
            if metadata.get("locations"):
                result["locations"] = metadata["locations"].split(",")
            if metadata.get("sentiment"):
                result["sentiment"] = metadata["sentiment"]
            
            formatted_results.append(result)
        
        # Get context for LLM
        context = store.get_context_for_query(query, max_tokens=1500)
        
        return {
            "query": query,
            "count": len(formatted_results),
            "results": formatted_results,
            "context": context
        }
        
    except Exception as e:
        logger.error(f"Error searching vector store: {e}")
        return {
            "error": str(e),
            "query": query,
            "results": [],
            "context": ""
        }


def get_trending_topics_tool(days_back: int = 7, limit: int = 10) -> Dict[str, Any]:
    """
    Get trending political topics from recent Reddit activity.
    
    Args:
        days_back: Number of days to look back (default: 7)
        limit: Maximum number of topics (default: 10)
    
    Returns:
        Dictionary with trending topics and example posts
    """
    try:
        store = VectorStore()
        stats = store.get_statistics()
        
        # Get topic counts
        topics = stats.get("topics", {})
        
        # Sort by frequency
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        # Get example posts for each topic
        trending = []
        for topic_name, count in sorted_topics:
            if topic_name and topic_name != "other":
                try:
                    # Get sample posts for this topic
                    topic_enum = PoliticalTopic(topic_name)
                    sample_posts = store.search_by_topic(topic_enum, n_results=3)
                    
                    trending.append({
                        "topic": topic_name.replace("_", " ").title(),
                        "count": count,
                        "examples": [
                            {
                                "url": post["url"],
                                "score": post.get("score", 0)
                            }
                            for post in sample_posts[:3]
                        ]
                    })
                except:
                    continue
        
        return {
            "period": f"Last {days_back} days",
            "trending_topics": trending,
            "total_documents": stats["total_documents"]
        }
        
    except Exception as e:
        logger.error(f"Error getting trending topics: {e}")
        return {
            "error": str(e),
            "trending_topics": []
        }


def download_new_posts_tool(subreddit: str = "newjersey", fetch_comments: bool = True) -> Dict[str, Any]:
    """
    Download new posts from Reddit since last update.
    
    Args:
        subreddit: Subreddit to update (default: newjersey)
        fetch_comments: Whether to fetch comments (default: True)
    
    Returns:
        Dictionary with update summary
    """
    try:
        # Run async function
        async def update():
            client = RedditClient()
            downloader = RedditDownloader(client)
            return await downloader.update_data(
                subreddit=subreddit,
                fetch_comments=fetch_comments
            )
        
        # Get event loop or create new one
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(update())
        
        # Update vector index if we got new posts
        if result["new_posts"] > 0:
            store = VectorStore()
            client = RedditClient()
            downloader = RedditDownloader(client)
            
            # Load and index new posts
            posts = downloader.load_posts(limit=result["new_posts"])
            for post in posts:
                store.add_post(post)
                
                # Add comments
                comments = downloader.load_comments(post.id)
                for comment in comments:
                    store.add_comment(comment, post.id)
            
            store.update_relevance_scores()
        
        return {
            "subreddit": subreddit,
            "new_posts": result["new_posts"],
            "new_comments": result["new_comments"],
            "update_time": result["update_time"],
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error downloading new posts: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }


# Create the agent
westfield_agent = client.agents.create(
    model=MODEL_ID,
    instructions=AGENT_PROMPT,
    tools=[
        types.Tool(
            code_execution=types.CodeExecutionTool()
        ),
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="reddit_search",
                    description="Search Reddit for posts about a topic",
                    parameters={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "subreddit": {
                                "type": "string",
                                "description": "Subreddit to search (default: newjersey)",
                                "default": "newjersey"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                ),
                types.FunctionDeclaration(
                    name="vector_search",
                    description="Search the vector database for relevant Reddit content using semantic similarity",
                    parameters={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 10
                            },
                            "filter_type": {
                                "type": "string",
                                "description": "Filter by type: 'post' or 'comment'",
                                "enum": ["post", "comment"]
                            }
                        },
                        "required": ["query"]
                    }
                ),
                types.FunctionDeclaration(
                    name="get_trending_topics",
                    description="Get trending political topics from recent Reddit activity",
                    parameters={
                        "type": "object",
                        "properties": {
                            "days_back": {
                                "type": "integer",
                                "description": "Number of days to look back",
                                "default": 7
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of topics",
                                "default": 10
                            }
                        }
                    }
                ),
                types.FunctionDeclaration(
                    name="download_new_posts",
                    description="Download new Reddit posts since last update",
                    parameters={
                        "type": "object",
                        "properties": {
                            "subreddit": {
                                "type": "string",
                                "description": "Subreddit to update",
                                "default": "newjersey"
                            },
                            "fetch_comments": {
                                "type": "boolean",
                                "description": "Whether to fetch comments",
                                "default": True
                            }
                        }
                    }
                )
            ]
        )
    ]
)

# Tool mapping
TOOL_FUNCTIONS = {
    "reddit_search": reddit_search_tool,
    "vector_search": vector_search_tool,
    "get_trending_topics": get_trending_topics_tool,
    "download_new_posts": download_new_posts_tool
}


def process_tool_calls(response):
    """Process tool calls from the agent response."""
    for part in response.candidates[0].content.parts:
        if part.function_call:
            function_name = part.function_call.name
            args = part.function_call.args
            
            if function_name in TOOL_FUNCTIONS:
                logger.info(f"Calling tool: {function_name}")
                result = TOOL_FUNCTIONS[function_name](**args)
                return result
    return None


def chat_with_agent(query: str, session_id: Optional[str] = None) -> str:
    """
    Chat with the Westfield agent.
    
    Args:
        query: User query
        session_id: Optional session ID for conversation continuity
    
    Returns:
        Agent response
    """
    try:
        # Create or resume session
        if session_id:
            session = client.agents.sessions.get(session_id)
        else:
            session = client.agents.sessions.create(agent_id=westfield_agent.name)
        
        # Send message
        response = session.send_message(query)
        
        # Process any tool calls
        tool_result = process_tool_calls(response)
        
        # Return the text response
        return response.candidates[0].content.parts[0].text
        
    except Exception as e:
        logger.error(f"Error in chat_with_agent: {e}")
        return f"Error: {str(e)}"


# Export the agent and functions
__all__ = [
    "westfield_agent",
    "chat_with_agent",
    "reddit_search_tool",
    "vector_search_tool",
    "get_trending_topics_tool",
    "download_new_posts_tool"
]