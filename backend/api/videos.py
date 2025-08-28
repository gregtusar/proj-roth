from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Body
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
from datetime import datetime
import mimetypes
import os

from api.auth import get_current_user
from services.video_asset_service import get_video_asset_service
from services.video_processing_simple import process_video_background
from models.video_asset import (
    UpdateVideoRequest,
    VideoListResponse,
    VideoDetailResponse,
    VideoStatus
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Maximum file size (500MB)
MAX_FILE_SIZE = 500 * 1024 * 1024

@router.get("/", response_model=List[VideoListResponse])
async def get_videos(
    campaign: Optional[str] = None,
    tags: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get all videos with optional filters"""
    service = get_video_asset_service()
    
    if not service.connected:
        return []
    
    # Parse tags if provided
    tag_list = tags.split(",") if tags else None
    
    # Parse status if provided
    status_enum = VideoStatus(status) if status else None
    
    videos = await service.get_user_videos(
        campaign=campaign,
        tags=tag_list,
        status=status_enum,
        limit=limit
    )
    
    # Convert to response format
    return [
        VideoListResponse(
            id=v.id,
            title=v.title,
            description=v.description,
            tags=v.tags,
            campaign=v.campaign,
            status=v.status,
            thumbnail_url=v.thumbnail_url,
            duration=v.metadata.duration if v.metadata else None,
            uploaded_at=v.uploaded_at.isoformat(),
            uploaded_by_email=v.uploaded_by_email,
            versions_count=len(v.versions),
            usage_count=v.usage_count
        )
        for v in videos
    ]

@router.get("/search")
async def search_videos(
    q: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Search videos by title, description, or tags"""
    service = get_video_asset_service()
    
    if not service.connected:
        return []
    
    videos = await service.search_videos(q, limit)
    
    return [
        VideoListResponse(
            id=v.id,
            title=v.title,
            description=v.description,
            tags=v.tags,
            campaign=v.campaign,
            status=v.status,
            thumbnail_url=v.thumbnail_url,
            duration=v.metadata.duration if v.metadata else None,
            uploaded_at=v.uploaded_at.isoformat(),
            uploaded_by_email=v.uploaded_by_email,
            versions_count=len(v.versions),
            usage_count=v.usage_count
        )
        for v in videos
    ]

@router.get("/{video_id}", response_model=VideoDetailResponse)
async def get_video(
    video_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed information about a specific video"""
    service = get_video_asset_service()
    
    if not service.connected:
        raise HTTPException(status_code=503, detail="Service not available")
    
    video = await service.get_video(video_id)
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return VideoDetailResponse(
        id=video.id,
        title=video.title,
        description=video.description,
        tags=video.tags,
        campaign=video.campaign,
        status=video.status,
        original_url=video.original_url,
        versions=video.versions,
        thumbnail_url=video.thumbnail_url,
        metadata=video.metadata,
        uploaded_by_email=video.uploaded_by_email,
        uploaded_at=video.uploaded_at.isoformat(),
        updated_at=video.updated_at.isoformat(),
        usage_count=video.usage_count
    )

@router.post("/upload-url")
async def get_upload_url(
    request: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Get a signed URL for direct browser upload to GCS"""
    filename = request.get("filename")
    content_type = request.get("content_type", "video/mp4")
    
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    service = get_video_asset_service()
    
    if not service.connected:
        raise HTTPException(status_code=503, detail="Service not available")
    
    try:
        # Validate content type
        if not content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="Invalid content type - must be a video")
        
        upload_url, gcs_path = service.get_signed_upload_url(
            filename=filename,
            content_type=content_type
        )
        
        # Check if we should use proxy upload instead
        if upload_url == "USE_PROXY_UPLOAD":
            return {
                "upload_url": "USE_PROXY_UPLOAD",
                "gcs_path": gcs_path,
                "expires_in": 3600,
                "proxy_endpoint": "/api/videos/upload-file"
            }
        
        return {
            "upload_url": upload_url,
            "gcs_path": gcs_path,
            "expires_in": 3600
        }
        
    except Exception as e:
        logger.error(f"Error generating upload URL: {str(e)}")
        # Instead of failing completely, fall back to proxy upload
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = filename.replace(" ", "_").replace("/", "_")
        gcs_path = f"videos/raw/{timestamp}_{safe_filename}"
        
        return {
            "upload_url": "USE_PROXY_UPLOAD",
            "gcs_path": gcs_path,
            "expires_in": 3600,
            "proxy_endpoint": "/api/videos/upload-file",
            "error_fallback": True
        }

@router.post("/")
async def create_video(
    request: dict = Body(...),
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user)
):
    """Create a new video asset after successful upload"""
    service = get_video_asset_service()
    
    if not service.connected:
        raise HTTPException(status_code=503, detail="Service not available")
    
    # Extract parameters from request body
    gcs_path = request.get("gcs_path")
    original_filename = request.get("original_filename")
    
    if not gcs_path or not original_filename:
        raise HTTPException(status_code=400, detail="Missing required fields: gcs_path and original_filename")
    
    try:
        # Create video asset record
        video = await service.create_video_asset(
            user_id=current_user["id"],
            user_email=current_user["email"],
            title=request.get("title", ""),
            original_filename=original_filename,
            gcs_path=gcs_path,
            description=request.get("description"),
            tags=request.get("tags", []),
            campaign=request.get("campaign")
        )
        
        # Queue background processing if background_tasks is available
        if background_tasks:
            background_tasks.add_task(
                process_video_background,
                video_id=video.id,
                gcs_path=gcs_path
            )
        
        return {
            "id": video.id,
            "status": video.status,
            "message": "Video uploaded successfully. Processing will begin shortly."
        }
        
    except Exception as e:
        logger.error(f"Error creating video asset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create video asset: {str(e)}")

@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    title: str = None,
    description: str = None,
    tags: str = None,
    campaign: str = None,
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user)
):
    """Direct file upload endpoint (for smaller videos)"""
    service = get_video_asset_service()
    
    if not service.connected:
        raise HTTPException(status_code=503, detail="Service not available")
    
    # Validate file type
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Check file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB")
    
    try:
        # Generate GCS path
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = file.filename.replace(" ", "_").replace("/", "_")
        gcs_path = f"videos/raw/{timestamp}_{safe_filename}"
        
        # Upload to GCS
        blob = service.bucket.blob(gcs_path)
        blob.upload_from_string(contents, content_type=file.content_type)
        
        # Parse tags
        tag_list = tags.split(",") if tags else []
        
        # Create video asset record
        video = await service.create_video_asset(
            user_id=current_user["id"],
            user_email=current_user["email"],
            title=title or file.filename,
            original_filename=file.filename,
            gcs_path=gcs_path,
            description=description,
            tags=tag_list,
            campaign=campaign
        )
        
        # Queue background processing
        if background_tasks:
            background_tasks.add_task(
                process_video_background,
                video_id=video.id,
                gcs_path=gcs_path
            )
        
        return {
            "id": video.id,
            "status": video.status,
            "message": "Video uploaded successfully. Processing will begin shortly."
        }
        
    except Exception as e:
        logger.error(f"Error uploading video file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload video: {str(e)}")

@router.put("/{video_id}")
async def update_video(
    video_id: str,
    request: UpdateVideoRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update video metadata"""
    service = get_video_asset_service()
    
    if not service.connected:
        raise HTTPException(status_code=503, detail="Service not available")
    
    success = await service.update_video(
        video_id=video_id,
        user_id=current_user["id"],
        update_data=request
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Video not found or access denied")
    
    return {"message": "Video updated successfully"}

@router.delete("/{video_id}")
async def delete_video(
    video_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a video (soft delete)"""
    service = get_video_asset_service()
    
    if not service.connected:
        raise HTTPException(status_code=503, detail="Service not available")
    
    success = await service.delete_video(video_id, current_user["id"])
    
    if not success:
        raise HTTPException(status_code=404, detail="Video not found or access denied")
    
    return {"message": "Video deleted successfully"}

@router.post("/{video_id}/track-usage")
async def track_usage(
    video_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Track usage of a video asset"""
    service = get_video_asset_service()
    
    if not service.connected:
        raise HTTPException(status_code=503, detail="Service not available")
    
    await service.increment_usage_count(video_id)
    
    return {"message": "Usage tracked"}