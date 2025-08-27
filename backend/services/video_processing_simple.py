"""
Simplified video processing service that works without ffmpeg
This version updates status but skips actual video processing
"""
import logging
import asyncio
from datetime import datetime

from services.video_asset_service import get_video_asset_service
from models.video_asset import VideoStatus, VideoMetadata

logger = logging.getLogger(__name__)

async def process_video_async(video_id: str, gcs_path: str):
    """Simplified video processing - just update status"""
    service = get_video_asset_service()
    
    try:
        # Update status to processing
        await service.update_video_status(video_id, VideoStatus.PROCESSING)
        
        # Simulate processing delay
        await asyncio.sleep(2)
        
        # Create mock metadata (in production, this would be extracted from the video)
        metadata = VideoMetadata(
            duration=60.0,
            resolution="1920x1080",
            aspect_ratio="16:9",
            file_size=10485760  # 10MB
        )
        
        # Generate thumbnail URL (using a placeholder for now)
        thumb_url = f"https://storage.googleapis.com/{service.bucket_name}/videos/thumbnails/placeholder.jpg"
        
        # Update metadata
        await service.update_video_metadata(
            video_id, 
            metadata, 
            thumb_url, 
            f"videos/thumbnails/{video_id}.jpg"
        )
        
        # Update status to ready
        await service.update_video_status(video_id, VideoStatus.READY)
        
        logger.info(f"Video {video_id} processing complete (simplified)")
        
    except Exception as e:
        logger.error(f"Error processing video {video_id}: {e}")
        await service.update_video_status(
            video_id, 
            VideoStatus.ERROR,
            error=str(e)
        )

def process_video_background(video_id: str, gcs_path: str):
    """Synchronous wrapper for FastAPI BackgroundTasks"""
    # Create a new event loop for the background task
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(process_video_async(video_id, gcs_path))
    finally:
        loop.close()