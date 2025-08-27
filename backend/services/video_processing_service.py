"""
Video processing service for extracting metadata and creating platform-specific versions
"""
import os
import logging
import subprocess
import tempfile
import json
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from google.cloud import storage
import asyncio
from concurrent.futures import ThreadPoolExecutor

from services.video_asset_service import get_video_asset_service
from models.video_asset import (
    VideoStatus, VideoVersion, VideoMetadata, VideoPlatform,
    PLATFORM_CONFIGS
)

logger = logging.getLogger(__name__)

# Thread pool for CPU-intensive tasks
executor = ThreadPoolExecutor(max_workers=4)

class VideoProcessingService:
    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "proj-roth")
        self.bucket_name = f"{self.project_id}-campaign-assets"
        
        try:
            self.storage_client = storage.Client(project=self.project_id)
            self.bucket = self.storage_client.bucket(self.bucket_name)
        except Exception as e:
            logger.error(f"Failed to initialize storage client: {e}")
            self.storage_client = None
            self.bucket = None
    
    def extract_metadata(self, video_path: str) -> VideoMetadata:
        """Extract metadata from video file using ffprobe"""
        try:
            # Run ffprobe to get video information
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"ffprobe failed: {result.stderr}")
                # Return basic metadata if ffprobe fails
                file_size = os.path.getsize(video_path)
                return VideoMetadata(
                    duration=0.0,
                    resolution="unknown",
                    aspect_ratio="unknown",
                    file_size=file_size
                )
            
            data = json.loads(result.stdout)
            
            # Extract video stream information
            video_stream = next((s for s in data.get('streams', []) if s['codec_type'] == 'video'), None)
            
            if not video_stream:
                raise ValueError("No video stream found")
            
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            resolution = f"{width}x{height}"
            
            # Calculate aspect ratio
            if width and height:
                gcd = self._gcd(width, height)
                aspect_ratio = f"{width//gcd}:{height//gcd}"
            else:
                aspect_ratio = "unknown"
            
            # Get format information
            format_info = data.get('format', {})
            duration = float(format_info.get('duration', 0))
            file_size = int(format_info.get('size', 0))
            bitrate = int(format_info.get('bit_rate', 0))
            
            # Get additional stream info
            fps = None
            if 'r_frame_rate' in video_stream:
                fps_str = video_stream['r_frame_rate']
                if '/' in fps_str:
                    num, den = map(int, fps_str.split('/'))
                    if den > 0:
                        fps = num / den
            
            codec = video_stream.get('codec_name')
            
            return VideoMetadata(
                duration=duration,
                resolution=resolution,
                aspect_ratio=aspect_ratio,
                file_size=file_size,
                fps=fps,
                codec=codec,
                bitrate=bitrate
            )
            
        except subprocess.TimeoutExpired:
            logger.error("ffprobe timed out")
            raise
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            raise
    
    def _gcd(self, a: int, b: int) -> int:
        """Calculate greatest common divisor"""
        while b:
            a, b = b, a % b
        return a
    
    def generate_thumbnail(self, video_path: str, output_path: str, timestamp: float = 1.0) -> bool:
        """Generate thumbnail from video at specified timestamp"""
        try:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', str(timestamp),
                '-vframes', '1',
                '-vf', 'scale=320:-1',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"ffmpeg thumbnail generation failed: {result.stderr}")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("ffmpeg thumbnail generation timed out")
            return False
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return False
    
    def process_for_platform(
        self,
        input_path: str,
        output_path: str,
        platform: VideoPlatform
    ) -> Tuple[bool, Optional[VideoMetadata]]:
        """Process video for specific platform requirements"""
        try:
            config = PLATFORM_CONFIGS.get(platform)
            if not config:
                logger.error(f"No configuration found for platform: {platform}")
                return False, None
            
            # Build ffmpeg command
            cmd = ['ffmpeg', '-i', input_path]
            
            # Add video filters
            filters = []
            
            # Resolution and aspect ratio
            if config.resolution:
                width, height = config.resolution.split('x')
                # Scale and pad to maintain aspect ratio
                filters.append(f"scale={width}:{height}:force_original_aspect_ratio=decrease")
                filters.append(f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2")
            
            # Duration limit
            if config.max_duration:
                cmd.extend(['-t', str(config.max_duration)])
            
            # Apply filters
            if filters:
                cmd.extend(['-vf', ','.join(filters)])
            
            # Quality settings
            if config.quality == 'low':
                cmd.extend(['-crf', '28', '-preset', 'fast'])
            elif config.quality == 'medium':
                cmd.extend(['-crf', '23', '-preset', 'medium'])
            else:  # high
                cmd.extend(['-crf', '18', '-preset', 'slow'])
            
            # Audio settings
            cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
            
            # Format settings
            cmd.extend(['-f', 'mp4', '-movflags', '+faststart'])
            
            # Overwrite output
            cmd.extend(['-y', output_path])
            
            # Run ffmpeg
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                logger.error(f"ffmpeg processing failed for {platform}: {result.stderr}")
                return False, None
            
            # Extract metadata from processed video
            metadata = self.extract_metadata(output_path)
            
            # Check file size constraint
            if config.max_file_size:
                max_bytes = config.max_file_size * 1024 * 1024
                if metadata.file_size > max_bytes:
                    logger.warning(f"Processed video exceeds size limit for {platform}")
                    # Try reprocessing with lower quality
                    return self._reprocess_with_lower_quality(
                        input_path, output_path, platform, max_bytes
                    )
            
            return True, metadata
            
        except subprocess.TimeoutExpired:
            logger.error(f"ffmpeg processing timed out for {platform}")
            return False, None
        except Exception as e:
            logger.error(f"Error processing video for {platform}: {e}")
            return False, None
    
    def _reprocess_with_lower_quality(
        self,
        input_path: str,
        output_path: str,
        platform: VideoPlatform,
        max_bytes: int
    ) -> Tuple[bool, Optional[VideoMetadata]]:
        """Reprocess video with lower quality to meet size constraints"""
        try:
            # Calculate target bitrate
            metadata = self.extract_metadata(input_path)
            duration = metadata.duration
            if duration <= 0:
                return False, None
            
            # Target 90% of max size to leave buffer
            target_bitrate = int((max_bytes * 0.9 * 8) / duration)
            
            config = PLATFORM_CONFIGS.get(platform)
            
            cmd = [
                'ffmpeg', '-i', input_path,
                '-b:v', f'{target_bitrate}',
                '-maxrate', f'{target_bitrate * 2}',
                '-bufsize', f'{target_bitrate * 2}',
                '-c:a', 'aac', '-b:a', '96k',
                '-f', 'mp4', '-movflags', '+faststart',
                '-y', output_path
            ]
            
            if config.resolution:
                width, height = config.resolution.split('x')
                cmd.extend(['-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease'])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                return False, None
            
            metadata = self.extract_metadata(output_path)
            return True, metadata
            
        except Exception as e:
            logger.error(f"Error reprocessing video: {e}")
            return False, None
    
    async def process_video(self, video_id: str, gcs_path: str):
        """Main video processing pipeline"""
        service = get_video_asset_service()
        
        try:
            # Update status to processing
            await service.update_video_status(video_id, VideoStatus.PROCESSING)
            
            # Download video from GCS to temp file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_input:
                blob = self.bucket.blob(gcs_path)
                blob.download_to_filename(temp_input.name)
                input_path = temp_input.name
            
            # Extract metadata
            metadata = await asyncio.get_event_loop().run_in_executor(
                executor, self.extract_metadata, input_path
            )
            
            # Generate thumbnail
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_thumb:
                thumb_path = temp_thumb.name
                
            success = await asyncio.get_event_loop().run_in_executor(
                executor, self.generate_thumbnail, input_path, thumb_path
            )
            
            if success:
                # Upload thumbnail to GCS
                thumb_gcs_path = f"videos/thumbnails/{video_id}.jpg"
                thumb_blob = self.bucket.blob(thumb_gcs_path)
                thumb_blob.upload_from_filename(thumb_path)
                thumb_url = f"https://storage.googleapis.com/{self.bucket_name}/{thumb_gcs_path}"
            else:
                thumb_url = None
                thumb_gcs_path = None
            
            # Update metadata and thumbnail
            await service.update_video_metadata(
                video_id, metadata, thumb_url, thumb_gcs_path
            )
            
            # Process for different platforms
            platforms_to_process = [
                VideoPlatform.TIKTOK,
                VideoPlatform.INSTAGRAM_REEL,
                VideoPlatform.EMAIL
            ]
            
            for platform in platforms_to_process:
                try:
                    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
                        output_path = temp_output.name
                    
                    # Process video
                    success, platform_metadata = await asyncio.get_event_loop().run_in_executor(
                        executor, self.process_for_platform, input_path, output_path, platform
                    )
                    
                    if success and platform_metadata:
                        # Upload to GCS
                        platform_gcs_path = f"videos/processed/{video_id}_{platform.value}.mp4"
                        platform_blob = self.bucket.blob(platform_gcs_path)
                        platform_blob.upload_from_filename(output_path)
                        
                        # Create version record
                        version = VideoVersion(
                            url=f"https://storage.googleapis.com/{self.bucket_name}/{platform_gcs_path}",
                            gcs_path=platform_gcs_path,
                            size=platform_metadata.file_size,
                            duration=platform_metadata.duration,
                            resolution=platform_metadata.resolution,
                            format="mp4",
                            created_at=datetime.utcnow()
                        )
                        
                        # Add version to video
                        await service.add_video_version(video_id, platform.value, version)
                    
                    # Clean up temp file
                    os.unlink(output_path)
                    
                except Exception as e:
                    logger.error(f"Error processing for {platform}: {e}")
                    continue
            
            # Clean up temp files
            os.unlink(input_path)
            if os.path.exists(thumb_path):
                os.unlink(thumb_path)
            
            # Update status to ready
            await service.update_video_status(video_id, VideoStatus.READY)
            
        except Exception as e:
            logger.error(f"Error processing video {video_id}: {e}")
            await service.update_video_status(
                video_id, 
                VideoStatus.ERROR,
                error=str(e)
            )

# Async wrapper for background processing
async def process_video_async(video_id: str, gcs_path: str):
    """Async wrapper for video processing"""
    try:
        processor = VideoProcessingService()
        await processor.process_video(video_id, gcs_path)
    except Exception as e:
        logger.error(f"Video processing failed for {video_id}: {e}")

# Synchronous wrapper for background tasks
def process_video_background(video_id: str, gcs_path: str):
    """Synchronous wrapper for FastAPI BackgroundTasks"""
    asyncio.create_task(process_video_async(video_id, gcs_path))