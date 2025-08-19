"""
Westfield Agent - Local Politics Intelligence from Social Media
"""

from .reddit.client import RedditClient
from .reddit.downloader import RedditDownloader
from .storage.vector_store import VectorStore
from .models.reddit_data import RedditPost, RedditComment, LocalIssue
from .config import Config

__version__ = "1.0.0"
__all__ = [
    "RedditClient",
    "RedditDownloader", 
    "VectorStore",
    "RedditPost",
    "RedditComment",
    "LocalIssue",
    "Config"
]