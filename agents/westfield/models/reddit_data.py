"""
Data models for Reddit posts and comments with local politics analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class ContentRelevance(Enum):
    """Relevance categories for local politics content."""
    HIGH = "high"  # Directly about local politics/issues
    MEDIUM = "medium"  # Tangentially related or mentions local areas
    LOW = "low"  # Not related to local politics
    UNKNOWN = "unknown"  # Not yet analyzed


class PoliticalTopic(Enum):
    """Categories of political topics."""
    ELECTIONS = "elections"
    TAXES = "taxes"
    EDUCATION = "education"
    INFRASTRUCTURE = "infrastructure"
    HOUSING = "housing"
    ENVIRONMENT = "environment"
    CRIME_SAFETY = "crime_safety"
    HEALTHCARE = "healthcare"
    TRANSPORTATION = "transportation"
    ECONOMY = "economy"
    SOCIAL_ISSUES = "social_issues"
    LOCAL_GOVERNMENT = "local_government"
    STATE_POLITICS = "state_politics"
    OTHER = "other"


@dataclass
class RedditPost:
    """Reddit post with metadata and analysis fields."""
    
    # Reddit metadata
    id: str
    title: str
    author: str
    created_utc: datetime
    score: int
    upvote_ratio: float
    num_comments: int
    permalink: str
    url: str
    selftext: str
    subreddit: str
    
    # Additional metadata
    is_self: bool = False
    link_flair_text: Optional[str] = None
    distinguished: Optional[str] = None
    stickied: bool = False
    locked: bool = False
    over_18: bool = False
    spoiler: bool = False
    
    # Analysis fields
    relevance: ContentRelevance = ContentRelevance.UNKNOWN
    topics: List[PoliticalTopic] = field(default_factory=list)
    locations_mentioned: List[str] = field(default_factory=list)
    politicians_mentioned: List[str] = field(default_factory=list)
    issues_mentioned: List[str] = field(default_factory=list)
    sentiment_score: Optional[float] = None  # -1 to 1
    embedding: Optional[List[float]] = None  # For RAG
    summary: Optional[str] = None
    
    # Processing metadata
    fetched_at: datetime = field(default_factory=datetime.now)
    analyzed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "created_utc": self.created_utc.isoformat(),
            "score": self.score,
            "upvote_ratio": self.upvote_ratio,
            "num_comments": self.num_comments,
            "permalink": self.permalink,
            "url": self.url,
            "selftext": self.selftext,
            "subreddit": self.subreddit,
            "is_self": self.is_self,
            "link_flair_text": self.link_flair_text,
            "distinguished": self.distinguished,
            "stickied": self.stickied,
            "locked": self.locked,
            "over_18": self.over_18,
            "spoiler": self.spoiler,
            "relevance": self.relevance.value,
            "topics": [t.value for t in self.topics],
            "locations_mentioned": self.locations_mentioned,
            "politicians_mentioned": self.politicians_mentioned,
            "issues_mentioned": self.issues_mentioned,
            "sentiment_score": self.sentiment_score,
            "embedding": self.embedding,
            "summary": self.summary,
            "fetched_at": self.fetched_at.isoformat(),
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RedditPost":
        """Create from dictionary."""
        # Convert string dates to datetime
        data["created_utc"] = datetime.fromisoformat(data["created_utc"])
        data["fetched_at"] = datetime.fromisoformat(data.get("fetched_at", datetime.now().isoformat()))
        if data.get("analyzed_at"):
            data["analyzed_at"] = datetime.fromisoformat(data["analyzed_at"])
        
        # Convert string enums
        data["relevance"] = ContentRelevance(data.get("relevance", "unknown"))
        data["topics"] = [PoliticalTopic(t) for t in data.get("topics", [])]
        
        return cls(**data)


@dataclass
class RedditComment:
    """Reddit comment with metadata and analysis."""
    
    # Reddit metadata
    id: str
    author: str
    body: str
    created_utc: datetime
    score: int
    parent_id: str
    permalink: str
    
    # Additional metadata
    is_submitter: bool = False
    distinguished: Optional[str] = None
    edited: bool = False
    depth: int = 0
    locked: bool = False
    collapsed: bool = False
    
    # Analysis fields
    relevance: ContentRelevance = ContentRelevance.UNKNOWN
    topics: List[PoliticalTopic] = field(default_factory=list)
    sentiment_score: Optional[float] = None
    embedding: Optional[List[float]] = None
    
    # Processing metadata
    fetched_at: datetime = field(default_factory=datetime.now)
    analyzed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "author": self.author,
            "body": self.body,
            "created_utc": self.created_utc.isoformat(),
            "score": self.score,
            "parent_id": self.parent_id,
            "permalink": self.permalink,
            "is_submitter": self.is_submitter,
            "distinguished": self.distinguished,
            "edited": self.edited,
            "depth": self.depth,
            "locked": self.locked,
            "collapsed": self.collapsed,
            "relevance": self.relevance.value,
            "topics": [t.value for t in self.topics],
            "sentiment_score": self.sentiment_score,
            "embedding": self.embedding,
            "fetched_at": self.fetched_at.isoformat(),
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RedditComment":
        """Create from dictionary."""
        # Convert string dates to datetime
        data["created_utc"] = datetime.fromisoformat(data["created_utc"])
        data["fetched_at"] = datetime.fromisoformat(data.get("fetched_at", datetime.now().isoformat()))
        if data.get("analyzed_at"):
            data["analyzed_at"] = datetime.fromisoformat(data["analyzed_at"])
        
        # Convert string enums
        data["relevance"] = ContentRelevance(data.get("relevance", "unknown"))
        data["topics"] = [PoliticalTopic(t) for t in data.get("topics", [])]
        
        return cls(**data)


@dataclass
class LocalIssue:
    """Represents a local political issue extracted from social media."""
    
    title: str
    description: str
    topics: List[PoliticalTopic]
    locations: List[str]
    
    # Source tracking
    source_posts: List[str] = field(default_factory=list)  # Post IDs
    source_comments: List[str] = field(default_factory=list)  # Comment IDs
    
    # Metrics
    total_mentions: int = 0
    average_sentiment: float = 0.0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    
    # Analysis
    summary: Optional[str] = None
    key_arguments_pro: List[str] = field(default_factory=list)
    key_arguments_con: List[str] = field(default_factory=list)
    related_politicians: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "title": self.title,
            "description": self.description,
            "topics": [t.value for t in self.topics],
            "locations": self.locations,
            "source_posts": self.source_posts,
            "source_comments": self.source_comments,
            "total_mentions": self.total_mentions,
            "average_sentiment": self.average_sentiment,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "summary": self.summary,
            "key_arguments_pro": self.key_arguments_pro,
            "key_arguments_con": self.key_arguments_con,
            "related_politicians": self.related_politicians,
        }