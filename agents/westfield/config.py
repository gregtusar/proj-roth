"""
Configuration for the Westfield agent.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration settings for Westfield agent."""
    
    # Reddit API settings
    REDDIT_CLIENT_ID: Optional[str] = os.getenv("REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET: Optional[str] = os.getenv("REDDIT_CLIENT_SECRET")
    REDDIT_USER_AGENT: str = os.getenv("REDDIT_USER_AGENT", "westfield-agent/1.0")
    
    # Default subreddit
    DEFAULT_SUBREDDIT: str = "newjersey"
    
    # Data storage
    DATA_DIR: Path = Path(os.getenv("WESTFIELD_DATA_DIR", "data"))
    REDDIT_DATA_DIR: Path = DATA_DIR / "reddit"
    VECTOR_STORE_DIR: Path = DATA_DIR / "chroma"
    
    # Download settings
    DEFAULT_DAYS_BACK: int = 30
    DEFAULT_COMMENT_LIMIT: int = 50
    MAX_POSTS_PER_BATCH: int = 100
    
    # Monitoring settings
    UPDATE_INTERVAL_SECONDS: int = 300  # 5 minutes
    STREAM_PAUSE_AFTER: int = 10
    
    # Vector store settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    COLLECTION_NAME: str = "westfield_politics"
    MAX_SEARCH_RESULTS: int = 20
    RELEVANCE_THRESHOLD: float = 0.5
    
    # Analysis settings
    HIGH_ENGAGEMENT_THRESHOLD: int = 100
    MEDIUM_ENGAGEMENT_THRESHOLD: int = 20
    
    # NJ-specific locations to track
    NJ_LOCATIONS = [
        # Counties
        "Union County", "Somerset County", "Hunterdon County", 
        "Morris County", "Warren County", "Essex County", "Sussex County",
        
        # Major cities/towns in District 7
        "Westfield", "Summit", "Cranford", "Berkeley Heights", "New Providence",
        "Springfield", "Mountainside", "Garwood", "Scotch Plains", "Fanwood",
        "Clark", "Kenilworth", "Roselle Park", "Millburn", "Short Hills",
        "Madison", "Chatham", "Florham Park", "Morristown", "Parsippany",
        
        # Other NJ locations
        "Newark", "Jersey City", "Trenton", "Princeton", "New Brunswick",
        "Edison", "Woodbridge", "Elizabeth", "Paterson", "Camden"
    ]
    
    # NJ politicians to track
    NJ_POLITICIANS = [
        # Federal
        "Tom Kean Jr", "Tom Malinowski", "Cory Booker", "Bob Menendez",
        
        # State
        "Phil Murphy", "Governor Murphy",
        
        # Local officials (add as discovered)
    ]
    
    # Keywords for local politics
    POLITICAL_KEYWORDS = [
        # Elections
        "election", "candidate", "campaign", "vote", "ballot", "primary",
        
        # Issues
        "property tax", "school board", "zoning", "development", "traffic",
        "public safety", "police", "fire department", "infrastructure",
        "affordable housing", "transit", "NJ Transit", "commute",
        
        # Government
        "mayor", "council", "township", "borough", "freeholder", "commissioner",
        "superintendent", "board of education"
    ]
    
    @classmethod
    def validate(cls):
        """Validate configuration settings."""
        if not cls.REDDIT_CLIENT_ID or not cls.REDDIT_CLIENT_SECRET:
            raise ValueError(
                "Reddit API credentials not found. Please set REDDIT_CLIENT_ID and "
                "REDDIT_CLIENT_SECRET environment variables."
            )
        
        # Create directories if they don't exist
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.REDDIT_DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_reddit_credentials(cls) -> dict:
        """Get Reddit API credentials."""
        return {
            "client_id": cls.REDDIT_CLIENT_ID,
            "client_secret": cls.REDDIT_CLIENT_SECRET,
            "user_agent": cls.REDDIT_USER_AGENT
        }