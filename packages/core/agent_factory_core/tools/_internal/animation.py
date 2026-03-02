"""
Animation Tools using Google Veo 3.1 API.

Provides image-to-video animation and text-to-video generation
capabilities with proper error handling and polling.
"""

import os
import io
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

load_dotenv()


class AnimationError(Exception):
    """Custom exception for animation/video generation errors."""
    pass


def _get_client():
    """Get Gemini client with validation."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise AnimationError(
            "API key not configured. Please set GOOGLE_API_KEY in your environment."
        )
    return genai.Client(api_key=api_key)


def _format_error(error: Exception, context: str = "") -> dict:
    """Format error into user-friendly response."""
    error_str = str(error).lower()

    if "quota" in error_str or "rate" in error_str:
        message = "The video generation service is busy. Please wait a moment and try again."
    elif "safety" in error_str or "blocked" in error_str:
        message = "The video couldn't be generated due to content guidelines. Try adjusting your prompt."
    elif "api" in error_str and "key" in error_str:
        message = "There's an issue with the API configuration. Please contact support."
    elif "timeout" in error_str:
        message = "The video generation took too long. Try a simpler prompt."
    elif "not found" in error_str:
        message = "The requested model or resource wasn't found. Please try again."
    else:
        message = f"Video generation failed. {context}" if context else "Video generation failed. Please try again."

    return {
        "status": "error",
        "message": message,
        "technical_details": str(error)
    }


def animate_image(
    image_path: str,
    motion_prompt: str,
    duration_seconds: int = 8,
    output_dir: str = "generated",
    aspect_ratio: str = "9:16",
    with_audio: bool = True,
    negative_prompt: str = ""
) -> dict:
    """
    Animate a static image to create a short video using Veo 3.1.

    Uses Google's Veo 3.1 model for high-quality image-to-video generation
    with optional audio generation.

    Args:
        image_path: Path to the static image to animate (can be web URL like /generated/file.png or full filesystem path)
        motion_prompt: Description of desired motion and scene
        duration_seconds: Length of video (5-8 seconds recommended)
        output_dir: Directory to save the generated video
        aspect_ratio: Video aspect ratio ("16:9", "9:16" for vertical)
        with_audio: Generate audio with the video (Veo 3.1 feature)
        negative_prompt: What to avoid in the video

    Returns:
        Dictionary with video path or error information
    """
    print(f"🎬 Animating image with Veo 3.1: {image_path}")
    print(f"   Motion: {motion_prompt[:50]}...")
    print(f"   Duration: {duration_seconds}s, Aspect: {aspect_ratio}, Audio: {with_audio}")

    try:
        client = _get_client()

        # Convert web URL path to filesystem path if needed
        resolved_path = image_path
        if image_path.startswith("/generated/"):
            project_root = Path(__file__).parent.parent
            resolved_path = str(project_root / image_path.lstrip("/"))
            print(f"   📁 Resolved path: {resolved_path}")
        elif not os.path.isabs(image_path):
            project_root = Path(__file__).parent.parent
            resolved_path = str(project_root / image_path)
            print(f"   📁 Resolved relative path: {resolved_path}")

        if not os.path.exists(resolved_path):
            return {
                "status": "error",
                "message": f"Image not found: {image_path} (resolved: {resolved_path})"
            }

        # Build the animation prompt
        full_prompt = f"""Create a smooth, professional video animation from this image.

MOTION DESCRIPTION: {motion_prompt}

GUIDELINES:
- Smooth, cinematic motion
- Keep brand elements (logo, text) stable and readable
- Professional quality suitable for Instagram Reels/Stories
"""
        if negative_prompt:
            full_prompt += f"\nAVOID: {negative_prompt}"

        # Use Veo 3.1 model from env or default
        video_model = os.getenv("VIDEO_MODEL", "veo-3.1-generate-preview")
        print(f"   Model: {video_model}")

        # Clamp duration to valid range (5-8 seconds)
        duration_seconds = max(5, min(8, duration_seconds))

        try:
            print("   📤 Starting video generation with Veo 3.1...")

            # Step 1: Load the source image and create an Image object for the API
            source_image = Image.open(resolved_path)
            if source_image.mode in ('RGBA', 'LA', 'P'):
                source_image = source_image.convert('RGB')

            # Save to bytes for upload
            img_byte_arr = io.BytesIO()
            source_image.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()

            # Create image object the way the API expects it
            source_image_obj = types.Image(
                image_bytes=img_bytes,
                mime_type="image/jpeg"
            )

            # Step 2: Configure video generation
            video_config = types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                number_of_videos=1,
                duration_seconds=duration_seconds,
            )

            # Step 3: Generate video with image input
            operation = client.models.generate_videos(
                model=video_model,
                prompt=full_prompt,
                image=source_image_obj,
                config=video_config,
            )

            # Step 4: Poll for completion
            max_wait_time = 300  # 5 minutes max
            poll_interval = 10

            print("   ⏳ Waiting for video generation...")
            while not operation.done:
                time.sleep(poll_interval)
                operation = client.operations.get(operation)
                max_wait_time -= poll_interval
                print(f"   ⏳ Processing... (waiting...)")
                if max_wait_time <= 0:
                    return {
                        "status": "timeout",
                        "message": "Video generation is taking longer than expected. Please try again later.",
                        "source_image": image_path,
                        "motion_prompt": motion_prompt
                    }

            # Step 5: Get result
            result = operation.result
            if not result:
                return {
                    "status": "error",
                    "message": "Video generation completed but no result was returned.",
                    "source_image": image_path,
                    "motion_prompt": motion_prompt
                }

            generated_videos = result.generated_videos
            if not generated_videos:
                return {
                    "status": "error",
                    "message": "Video generation completed but no videos were generated.",
                    "source_image": image_path,
                    "motion_prompt": motion_prompt
                }

            # Step 6: Download and save the video
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            video = generated_videos[0]
            video_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"animated_{timestamp}_{video_id}.mp4"
            video_path = output_path / filename

            print(f"   📥 Downloading video: {video.video.uri}")
            client.files.download(file=video.video)
            video.video.save(str(video_path))
            print(f"   ✅ Video saved: {video_path}")

            return {
                "status": "success",
                "video_path": str(video_path),
                "filename": filename,
                "url": f"/generated/{filename}",
                "motion_prompt": motion_prompt,
                "duration_seconds": duration_seconds,
                "source_image": image_path,
                "aspect_ratio": aspect_ratio,
                "with_audio": with_audio,
                "model": video_model,
                "type": "video"
            }

        except Exception as model_error:
            error_str = str(model_error).lower()
            print(f"   ⚠️ Video generation error: {model_error}")

            if "not found" in error_str or "invalid" in error_str or "unavailable" in error_str or "not supported" in error_str or "permission" in error_str:
                return {
                    "status": "model_unavailable",
                    "message": f"Veo 3.1 video generation error: {str(model_error)[:200]}",
                    "source_image": image_path,
                    "motion_prompt": motion_prompt,
                }
            raise

    except Exception as e:
        return _format_error(e, "Video generation may not be available in your region.")


def generate_video_from_text(
    prompt: str,
    duration_seconds: int = 8,
    aspect_ratio: str = "9:16",
    output_dir: str = "generated",
    with_audio: bool = True,
    negative_prompt: str = ""
) -> dict:
    """
    Generate a video directly from text prompt using Veo 3.1.

    Creates a new video from scratch based on the text description.

    Args:
        prompt: Detailed description of the video to generate
        duration_seconds: Length of video (5-8 seconds)
        aspect_ratio: Video aspect ratio ("16:9", "9:16")
        output_dir: Directory to save the generated video
        with_audio: Generate audio with the video
        negative_prompt: What to avoid in the video

    Returns:
        Dictionary with video path or error information
    """
    print(f"🎬 Generating video from text with Veo 3.1")
    print(f"   Prompt: {prompt[:50]}...")
    print(f"   Duration: {duration_seconds}s, Aspect: {aspect_ratio}, Audio: {with_audio}")

    try:
        client = _get_client()

        video_model = os.getenv("VIDEO_MODEL", "veo-3.1-generate-preview")
        print(f"   Model: {video_model}")

        # Clamp duration to valid range (5-8 seconds)
        duration_seconds = max(5, min(8, duration_seconds))

        try:
            print("   📤 Starting video generation with Veo 3.1...")

            # Configure video generation
            video_config = types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                number_of_videos=1,
                duration_seconds=duration_seconds,
                person_generation="ALLOW_ADULT",
            )

            # Generate video from text prompt
            operation = client.models.generate_videos(
                model=video_model,
                prompt=prompt,
                config=video_config,
            )

            # Poll for completion
            max_wait_time = 300  # 5 minutes max

            print("   ⏳ Waiting for video generation...")
            while not operation.done:
                time.sleep(10)
                operation = client.operations.get(operation)
                max_wait_time -= 10
                print(f"   ⏳ Processing... (waiting...)")
                if max_wait_time <= 0:
                    return {
                        "status": "timeout",
                        "message": "Video generation is taking longer than expected.",
                        "prompt": prompt
                    }

            # Get result
            result = operation.result
            if not result:
                return {
                    "status": "error",
                    "message": "Video generation completed but no result was returned.",
                    "prompt": prompt
                }

            generated_videos = result.generated_videos
            if not generated_videos:
                return {
                    "status": "error",
                    "message": "Video generation completed but no videos were generated.",
                    "prompt": prompt
                }

            # Download and save the video
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            video = generated_videos[0]
            video_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"video_{timestamp}_{video_id}.mp4"
            video_path = output_path / filename

            print(f"   📥 Downloading video: {video.video.uri}")
            client.files.download(file=video.video)
            video.video.save(str(video_path))
            print(f"   ✅ Video saved: {video_path}")

            return {
                "status": "success",
                "video_path": str(video_path),
                "filename": filename,
                "url": f"/generated/{filename}",
                "prompt": prompt,
                "duration_seconds": duration_seconds,
                "aspect_ratio": aspect_ratio,
                "with_audio": with_audio,
                "model": video_model,
                "type": "video"
            }

        except Exception as model_error:
            error_str = str(model_error).lower()
            print(f"   ⚠️ Video generation error: {model_error}")

            if "not found" in error_str or "invalid" in error_str or "unavailable" in error_str:
                return {
                    "status": "model_unavailable",
                    "message": f"Veo 3.1 video generation error: {str(model_error)[:200]}",
                    "prompt": prompt,
                }
            raise

    except Exception as e:
        return _format_error(e, "Video generation may not be available in your region.")
