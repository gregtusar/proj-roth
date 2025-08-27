from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

class VideoStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"

class VideoPlatform(str, Enum):
    ORIGINAL = "original"
    TIKTOK = "tiktok"
    INSTAGRAM_FEED = "instagram_feed"
    INSTAGRAM_REEL = "instagram_reel"
    INSTAGRAM_STORY = "instagram_story"
    EMAIL = "email"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    YOUTUBE_SHORT = "youtube_short"

class VideoVersion(BaseModel):
    url: str
    gcs_path: str
    size: int
    duration: Optional[float] = None
    resolution: Optional[str] = None
    format: str = "mp4"
    created_at: datetime

class VideoMetadata(BaseModel):
    duration: float  # in seconds
    resolution: str  # e.g., "1920x1080"
    aspect_ratio: str  # e.g., "16:9"
    file_size: int  # in bytes
    fps: Optional[float] = None
    codec: Optional[str] = None
    bitrate: Optional[int] = None

class VideoAsset(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    tags: List[str] = []
    campaign: Optional[str] = None
    status: VideoStatus = VideoStatus.UPLOADING
    original_filename: str
    original_url: str
    gcs_path: str
    versions: Dict[str, VideoVersion] = {}
    thumbnail_url: Optional[str] = None
    thumbnail_gcs_path: Optional[str] = None
    metadata: Optional[VideoMetadata] = None
    uploaded_by: str
    uploaded_by_email: str
    uploaded_at: datetime
    updated_at: datetime
    processing_error: Optional[str] = None
    usage_count: int = 0
    is_active: bool = True

class CreateVideoRequest(BaseModel):
    title: str
    description: Optional[str] = None
    tags: List[str] = []
    campaign: Optional[str] = None

class UpdateVideoRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    campaign: Optional[str] = None
    is_active: Optional[bool] = None

class VideoListResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    tags: List[str]
    campaign: Optional[str]
    status: VideoStatus
    thumbnail_url: Optional[str]
    duration: Optional[float]
    uploaded_at: str
    uploaded_by_email: str
    versions_count: int
    usage_count: int

class VideoDetailResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    tags: List[str]
    campaign: Optional[str]
    status: VideoStatus
    original_url: str
    versions: Dict[str, VideoVersion]
    thumbnail_url: Optional[str]
    metadata: Optional[VideoMetadata]
    uploaded_by_email: str
    uploaded_at: str
    updated_at: str
    usage_count: int

class VideoProcessingConfig(BaseModel):
    platform: VideoPlatform
    max_duration: Optional[int] = None  # seconds
    resolution: Optional[str] = None
    aspect_ratio: Optional[str] = None
    max_file_size: Optional[int] = None  # MB
    format: str = "mp4"
    quality: str = "high"  # low, medium, high

# Platform-specific processing configurations
PLATFORM_CONFIGS = {
    VideoPlatform.TIKTOK: VideoProcessingConfig(
        platform=VideoPlatform.TIKTOK,
        max_duration=60,
        resolution="1080x1920",
        aspect_ratio="9:16",
        max_file_size=287,
        format="mp4",
        quality="high"
    ),
    VideoPlatform.INSTAGRAM_REEL: VideoProcessingConfig(
        platform=VideoPlatform.INSTAGRAM_REEL,
        max_duration=90,
        resolution="1080x1920",
        aspect_ratio="9:16",
        max_file_size=4000,
        format="mp4",
        quality="high"
    ),
    VideoPlatform.INSTAGRAM_FEED: VideoProcessingConfig(
        platform=VideoPlatform.INSTAGRAM_FEED,
        max_duration=60,
        resolution="1080x1080",
        aspect_ratio="1:1",
        max_file_size=4000,
        format="mp4",
        quality="high"
    ),
    VideoPlatform.INSTAGRAM_STORY: VideoProcessingConfig(
        platform=VideoPlatform.INSTAGRAM_STORY,
        max_duration=15,
        resolution="1080x1920",
        aspect_ratio="9:16",
        max_file_size=4000,
        format="mp4",
        quality="high"
    ),
    VideoPlatform.EMAIL: VideoProcessingConfig(
        platform=VideoPlatform.EMAIL,
        max_duration=30,
        resolution="640x360",
        aspect_ratio="16:9",
        max_file_size=5,
        format="mp4",
        quality="low"
    ),
    VideoPlatform.YOUTUBE_SHORT: VideoProcessingConfig(
        platform=VideoPlatform.YOUTUBE_SHORT,
        max_duration=60,
        resolution="1080x1920",
        aspect_ratio="9:16",
        max_file_size=128,
        format="mp4",
        quality="high"
    ),
}