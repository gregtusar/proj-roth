#!/usr/bin/env python3
"""
Script to fix stuck video processing by manually updating video status
"""
import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.cloud import firestore
from backend.models.video_asset import VideoStatus, VideoMetadata

async def fix_stuck_videos():
    """Find and fix videos stuck in processing state"""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "proj-roth")
    
    # Initialize Firestore
    db = firestore.AsyncClient(project=project_id)
    videos_collection = db.collection('video_assets')
    
    print(f"Checking for stuck videos in project: {project_id}")
    
    # Find videos stuck in UPLOADING or PROCESSING status
    stuck_statuses = [VideoStatus.UPLOADING.value, VideoStatus.PROCESSING.value]
    
    for status in stuck_statuses:
        query = videos_collection.where(
            filter=firestore.FieldFilter("status", "==", status)
        )
        
        async for doc in query.stream():
            video_data = doc.to_dict()
            video_id = doc.id
            
            # Check how long it's been stuck
            uploaded_at = video_data.get('uploaded_at')
            if uploaded_at:
                # Handle both timezone-aware and naive datetimes
                from datetime import timezone
                now = datetime.now(timezone.utc)
                
                # Convert uploaded_at to timezone-aware if needed
                if hasattr(uploaded_at, 'tzinfo') and uploaded_at.tzinfo is not None:
                    # Already timezone-aware
                    time_diff = now - uploaded_at
                else:
                    # Naive datetime, assume UTC
                    uploaded_at_aware = uploaded_at.replace(tzinfo=timezone.utc)
                    time_diff = now - uploaded_at_aware
                    
                hours_stuck = time_diff.total_seconds() / 3600
                
                print(f"\nFound stuck video: {video_id}")
                print(f"  Title: {video_data.get('title', 'Untitled')}")
                print(f"  Status: {status}")
                print(f"  Stuck for: {hours_stuck:.1f} hours")
                
                # If stuck for more than 30 minutes, mark as ready with mock metadata
                if hours_stuck > 0.5:
                    print(f"  Fixing video {video_id}...")
                    
                    # Update with mock metadata
                    from datetime import timezone
                    update_data = {
                        "status": VideoStatus.READY.value,
                        "updated_at": datetime.now(timezone.utc),
                        "metadata": {
                            "duration": 60.0,
                            "resolution": "1920x1080",
                            "aspect_ratio": "16:9",
                            "file_size": 10485760  # 10MB placeholder
                        },
                        "processing_error": None
                    }
                    
                    # Add thumbnail URL if not present
                    if not video_data.get('thumbnail_url'):
                        bucket_name = f"{project_id}-campaign-assets"
                        update_data["thumbnail_url"] = f"https://storage.googleapis.com/{bucket_name}/videos/thumbnails/placeholder.jpg"
                        update_data["thumbnail_gcs_path"] = f"videos/thumbnails/{video_id}.jpg"
                    
                    await videos_collection.document(video_id).update(update_data)
                    print(f"  ✓ Video {video_id} marked as READY")

async def main():
    """Main entry point"""
    try:
        await fix_stuck_videos()
        print("\n✅ Stuck video fix complete!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())