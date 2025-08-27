"""
Firestore-based video asset management service
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from google.cloud import firestore, storage
from google.api_core import exceptions
import os
import logging

from models.video_asset import (
    VideoAsset, VideoStatus, VideoVersion, VideoMetadata,
    CreateVideoRequest, UpdateVideoRequest
)

logger = logging.getLogger(__name__)

class VideoAssetService:
    def __init__(self, project_id: Optional[str] = None):
        """Initialize Firestore and GCS connections for video asset management"""
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "proj-roth")
        
        try:
            # Initialize Firestore client
            self.firestore_client = firestore.AsyncClient(project=self.project_id)
            self.videos_collection = self.firestore_client.collection('video_assets')
            
            # Initialize Storage client (but don't create bucket yet)
            self.storage_client = storage.Client(project=self.project_id)
            self.bucket_name = f"{self.project_id}-campaign-assets"
            
            # Just reference the bucket, don't try to create it
            self.bucket = self.storage_client.bucket(self.bucket_name)
            
            self.connected = True
            logger.info(f"[Video Assets] Service initialized for project: {self.project_id}")
            
        except Exception as e:
            logger.error(f"Warning: Could not initialize Video Asset Service: {e}")
            self.connected = False
            self.firestore_client = None
            self.storage_client = None
    
    async def create_video_asset(
        self,
        user_id: str,
        user_email: str,
        title: str,
        original_filename: str,
        gcs_path: str,
        description: Optional[str] = None,
        tags: List[str] = [],
        campaign: Optional[str] = None
    ) -> VideoAsset:
        """Create a new video asset record"""
        if not self.connected:
            raise RuntimeError("Video Asset Service is not connected")
        
        video_id = str(uuid.uuid4())
        
        # Generate GCS URLs
        original_url = f"https://storage.googleapis.com/{self.bucket_name}/{gcs_path}"
        
        video_data = {
            "id": video_id,
            "title": title,
            "description": description or "",
            "tags": tags,
            "campaign": campaign,
            "status": VideoStatus.UPLOADING.value,
            "original_filename": original_filename,
            "original_url": original_url,
            "gcs_path": gcs_path,
            "versions": {},
            "thumbnail_url": None,
            "thumbnail_gcs_path": None,
            "metadata": None,
            "uploaded_by": user_id,
            "uploaded_by_email": user_email,
            "uploaded_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "processing_error": None,
            "usage_count": 0,
            "is_active": True
        }
        
        # Create document with video_id as document ID
        await self.videos_collection.document(video_id).set(video_data)
        
        return VideoAsset(**video_data)
    
    async def get_user_videos(
        self,
        user_id: Optional[str] = None,
        campaign: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[VideoStatus] = None,
        limit: int = 100
    ) -> List[VideoAsset]:
        """Get videos with optional filters"""
        if not self.connected:
            logger.warning("[Video Assets] Not connected, returning empty list")
            return []
        
        try:
            query = self.videos_collection
            
            # Apply filters
            if user_id:
                query = query.where(
                    filter=firestore.FieldFilter("uploaded_by", "==", user_id)
                )
            
            if campaign:
                query = query.where(
                    filter=firestore.FieldFilter("campaign", "==", campaign)
                )
            
            if status:
                query = query.where(
                    filter=firestore.FieldFilter("status", "==", status.value)
                )
            
            # Apply active filter
            query = query.where(
                filter=firestore.FieldFilter("is_active", "==", True)
            ).limit(limit)
            
            videos = []
            async for doc in query.stream():
                video_data = doc.to_dict()
                
                # Filter by tags in memory if specified
                if tags and not any(tag in video_data.get("tags", []) for tag in tags):
                    continue
                
                try:
                    video = VideoAsset(**video_data)
                    videos.append(video)
                except Exception as e:
                    logger.error(f"[Video Assets] Error creating VideoAsset: {e}")
                    logger.error(f"  Data: {video_data}")
            
            # Sort by uploaded_at in memory (newest first)
            videos.sort(key=lambda x: x.uploaded_at, reverse=True)
            
            logger.info(f"[Video Assets] Found {len(videos)} videos")
            return videos
            
        except Exception as e:
            logger.error(f"[Video Assets] Error fetching videos: {e}")
            return []
    
    async def get_video(self, video_id: str) -> Optional[VideoAsset]:
        """Get a specific video asset"""
        if not self.connected:
            return None
        
        doc = await self.videos_collection.document(video_id).get()
        
        if doc.exists:
            video_data = doc.to_dict()
            return VideoAsset(**video_data)
        
        return None
    
    async def update_video(
        self,
        video_id: str,
        user_id: str,
        update_data: UpdateVideoRequest
    ) -> bool:
        """Update video asset metadata"""
        if not self.connected:
            return False
        
        doc_ref = self.videos_collection.document(video_id)
        
        # First verify ownership
        doc = await doc_ref.get()
        if not doc.exists:
            return False
        
        video_data = doc.to_dict()
        if video_data.get("uploaded_by") != user_id:
            logger.warning(f"User {user_id} attempted to update video {video_id} they don't own")
            return False
        
        # Build update dict
        updates = {"updated_at": datetime.utcnow()}
        
        if update_data.title is not None:
            updates["title"] = update_data.title
        if update_data.description is not None:
            updates["description"] = update_data.description
        if update_data.tags is not None:
            updates["tags"] = update_data.tags
        if update_data.campaign is not None:
            updates["campaign"] = update_data.campaign
        if update_data.is_active is not None:
            updates["is_active"] = update_data.is_active
        
        # Update the video
        await doc_ref.update(updates)
        
        return True
    
    async def update_video_status(
        self,
        video_id: str,
        status: VideoStatus,
        error: Optional[str] = None
    ) -> bool:
        """Update video processing status"""
        if not self.connected:
            return False
        
        doc_ref = self.videos_collection.document(video_id)
        
        updates = {
            "status": status.value,
            "updated_at": datetime.utcnow()
        }
        
        if error:
            updates["processing_error"] = error
        
        await doc_ref.update(updates)
        return True
    
    async def add_video_version(
        self,
        video_id: str,
        platform: str,
        version: VideoVersion
    ) -> bool:
        """Add a processed version of the video"""
        if not self.connected:
            return False
        
        doc_ref = self.videos_collection.document(video_id)
        
        # Convert version to dict
        version_dict = version.dict()
        version_dict["created_at"] = version.created_at
        
        updates = {
            f"versions.{platform}": version_dict,
            "updated_at": datetime.utcnow()
        }
        
        await doc_ref.update(updates)
        return True
    
    async def update_video_metadata(
        self,
        video_id: str,
        metadata: VideoMetadata,
        thumbnail_url: Optional[str] = None,
        thumbnail_gcs_path: Optional[str] = None
    ) -> bool:
        """Update video metadata after processing"""
        if not self.connected:
            return False
        
        doc_ref = self.videos_collection.document(video_id)
        
        updates = {
            "metadata": metadata.dict(),
            "status": VideoStatus.READY.value,
            "updated_at": datetime.utcnow()
        }
        
        if thumbnail_url:
            updates["thumbnail_url"] = thumbnail_url
        if thumbnail_gcs_path:
            updates["thumbnail_gcs_path"] = thumbnail_gcs_path
        
        await doc_ref.update(updates)
        return True
    
    async def increment_usage_count(self, video_id: str) -> bool:
        """Increment the usage count for a video"""
        if not self.connected:
            return False
        
        doc_ref = self.videos_collection.document(video_id)
        
        await doc_ref.update({
            "usage_count": firestore.Increment(1),
            "updated_at": datetime.utcnow()
        })
        
        return True
    
    async def delete_video(self, video_id: str, user_id: str) -> bool:
        """Soft delete a video (set is_active to False)"""
        if not self.connected:
            return False
        
        doc_ref = self.videos_collection.document(video_id)
        
        # Verify ownership
        doc = await doc_ref.get()
        if not doc.exists:
            return False
        
        video_data = doc.to_dict()
        if video_data.get("uploaded_by") != user_id:
            logger.warning(f"User {user_id} attempted to delete video {video_id} they don't own")
            return False
        
        # Soft delete
        await doc_ref.update({
            "is_active": False,
            "updated_at": datetime.utcnow()
        })
        
        return True
    
    async def search_videos(
        self,
        query: str,
        limit: int = 50
    ) -> List[VideoAsset]:
        """Search videos by title, description, or tags"""
        if not self.connected:
            return []
        
        # This is a simple implementation - for production, consider using
        # Algolia, Elasticsearch, or Firebase Extensions for full-text search
        
        all_videos = await self.get_user_videos(limit=limit * 2)
        
        query_lower = query.lower()
        matching_videos = []
        
        for video in all_videos:
            # Check title
            if query_lower in video.title.lower():
                matching_videos.append(video)
                continue
            
            # Check description
            if video.description and query_lower in video.description.lower():
                matching_videos.append(video)
                continue
            
            # Check tags
            if any(query_lower in tag.lower() for tag in video.tags):
                matching_videos.append(video)
        
        return matching_videos[:limit]
    
    def get_signed_upload_url(
        self,
        filename: str,
        content_type: str = "video/mp4",
        expiration: int = 3600
    ) -> tuple[str, str]:
        """Generate a signed URL for direct browser upload to GCS"""
        if not self.connected:
            raise RuntimeError("Video Asset Service is not connected")
        
        # Generate unique path
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = filename.replace(" ", "_").replace("/", "_")
        gcs_path = f"videos/raw/{timestamp}_{safe_filename}"
        
        blob = self.bucket.blob(gcs_path)
        
        # Generate signed URL for upload
        url = blob.generate_signed_url(
            version="v4",
            expiration=expiration,
            method="PUT",
            content_type=content_type
        )
        
        return url, gcs_path
    
    def get_public_url(self, gcs_path: str) -> str:
        """Get public URL for a GCS object"""
        return f"https://storage.googleapis.com/{self.bucket_name}/{gcs_path}"

# Singleton instance
_video_service = None

def get_video_asset_service() -> VideoAssetService:
    """Get or create singleton VideoAssetService instance"""
    global _video_service
    if _video_service is None:
        _video_service = VideoAssetService()
    return _video_service