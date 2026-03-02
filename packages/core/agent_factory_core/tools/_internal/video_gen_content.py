"""
Video Generation Tools for Content Studio Agent.

Provides specialized video generation functions:
- Animated Product Videos (Veo 3.1 image-to-video)
- Motion Graphics (Veo 3.1 text-to-video)
- AI Talking Head (external API placeholder)

Uses Google's Veo 3.1 model for high-quality video generation.
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
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# Try to import moviepy for video post-processing
try:
    from moviepy import VideoFileClip, ImageClip, CompositeVideoClip, TextClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

load_dotenv()


class VideoGenerationError(Exception):
    """Custom exception for video generation errors."""
    pass


def _get_client():
    """Get Gemini client with validation."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise VideoGenerationError(
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
        message = "Video generation took too long. Try a simpler concept."
    elif "not found" in error_str or "unavailable" in error_str:
        message = "Video generation model is not available. Try again later."
    else:
        message = f"Video generation failed. {context}" if context else "Video generation failed. Please try again."

    return {
        "status": "error",
        "message": message,
        "technical_details": str(error)
    }


def _get_available_font():
    """Get an available system font for text rendering.

    Tries multiple common fonts in order of preference.
    Returns None if no fonts work (MoviePy will use default).
    """
    if not MOVIEPY_AVAILABLE:
        return None

    font_options = [
        "Arial-Bold",
        "Arial",
        "Helvetica-Bold",
        "Helvetica",
        "DejaVu-Sans-Bold",
        "DejaVu-Sans",
        "Liberation-Sans-Bold",
        "Liberation-Sans",
    ]

    for font in font_options:
        try:
            # Test if font works by creating a small TextClip
            test = TextClip(text="test", font=font, font_size=20)
            test.close()
            print(f"✅ Using font: {font}")
            return font
        except Exception:
            continue

    print("⚠️ No preferred fonts available, using MoviePy default")
    return None


def _add_branding_to_video(
    video_path: str,
    logo_path: Optional[str] = None,
    brand_name: Optional[str] = None,
    cta_text: Optional[str] = None,
    brand_colors: Optional[list] = None
) -> str:
    """
    Add logo watermark and brand text overlay to a video.

    Args:
        video_path: Path to the input video
        logo_path: Path to logo image (optional)
        brand_name: Brand name to display (optional)
        cta_text: Call-to-action text (optional)
        brand_colors: List of brand colors for text styling

    Returns:
        Path to the branded video (or original if processing fails)
    """
    if not MOVIEPY_AVAILABLE:
        print("⚠️ moviepy not available, skipping branding overlay")
        return video_path

    try:
        project_root = Path(__file__).parent.parent

        # Resolve logo path
        resolved_logo = None
        if logo_path:
            # First check if the path already exists as-is
            if os.path.exists(logo_path):
                resolved_logo = logo_path
            elif logo_path.startswith("/"):
                # Try resolving as relative to project root
                resolved_logo = str(project_root / logo_path.lstrip("/"))
            else:
                resolved_logo = str(project_root / logo_path)

            if not os.path.exists(resolved_logo):
                print(f"⚠️ Logo not found at {resolved_logo}")
                resolved_logo = None

        # Load the video
        video = VideoFileClip(video_path)
        video_width, video_height = video.size

        clips = [video]

        # Add logo watermark (top-right corner)
        if resolved_logo:
            try:
                logo = ImageClip(resolved_logo)

                # Scale logo to ~15% of video width
                logo_scale = (video_width * 0.15) / logo.size[0]
                logo = logo.resized(logo_scale)

                # Position in top-right with padding
                logo_x = video_width - logo.size[0] - 20
                logo_y = 20

                # Make logo semi-transparent and set duration
                logo = logo.with_opacity(0.85).with_position((logo_x, logo_y)).with_duration(video.duration)
                clips.append(logo)
                print(f"✅ Added logo watermark at ({logo_x}, {logo_y})")
            except Exception as logo_err:
                print(f"⚠️ Could not add logo: {logo_err}")

        # Get available font for text overlays
        available_font = _get_available_font()

        # Add brand name text (bottom-left)
        if brand_name:
            try:
                # Determine text color based on brand colors
                text_color = brand_colors[0] if brand_colors else "#FFFFFF"

                brand_text = TextClip(
                    text=brand_name,
                    font_size=int(video_height * 0.04),  # 4% of video height
                    color=text_color,
                    font=available_font,  # Use font fallback
                    stroke_color="black",
                    stroke_width=1  # Reduced for better compatibility
                )
                brand_text = brand_text.with_position((20, video_height - 80)).with_duration(video.duration)
                clips.append(brand_text)
                print(f"✅ Added brand name: {brand_name}")
            except Exception as text_err:
                print(f"⚠️ Could not add brand text: {text_err}")

        # Add CTA text (bottom-center, appears in last 3 seconds)
        if cta_text and video.duration > 3:
            try:
                cta_color = brand_colors[0] if brand_colors else "#FF6B35"

                cta = TextClip(
                    text=cta_text,
                    font_size=int(video_height * 0.05),  # 5% of video height
                    color=cta_color,
                    font=available_font,  # Use font fallback
                    stroke_color="black",
                    stroke_width=1  # Reduced for better compatibility
                )

                # Center horizontally, position near bottom
                cta_x = (video_width - cta.size[0]) // 2
                cta_y = video_height - 150

                # Only show CTA in last 3 seconds
                cta = cta.with_position((cta_x, cta_y)).with_start(video.duration - 3).with_duration(3)
                clips.append(cta)
                print(f"✅ Added CTA: {cta_text}")
            except Exception as cta_err:
                print(f"⚠️ Could not add CTA: {cta_err}")

        # Composite all clips
        if len(clips) > 1:
            final_video = CompositeVideoClip(clips)

            # Generate output path
            output_path = video_path.replace(".mp4", "_branded.mp4")

            # Write the branded video
            final_video.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac" if video.audio else None,
                fps=video.fps,
                logger=None  # Suppress moviepy output
            )

            # Clean up
            video.close()
            final_video.close()

            print(f"✅ Branded video saved: {output_path}")
            return output_path
        else:
            video.close()
            return video_path

    except Exception as e:
        print(f"⚠️ Branding overlay failed: {e}")
        return video_path


def _resolve_image_path(image_path: str) -> str:
    """Convert web URL path to filesystem path if needed."""
    resolved_path = image_path
    project_root = Path(__file__).parent.parent

    if image_path.startswith("/generated/"):
        resolved_path = str(project_root / image_path.lstrip("/"))
    elif image_path.startswith("/uploads/"):
        resolved_path = str(project_root / image_path.lstrip("/"))
    elif image_path.startswith("/static/"):
        # Handle static preset images
        resolved_path = str(project_root / image_path.lstrip("/"))
    elif not os.path.isabs(image_path):
        resolved_path = str(project_root / image_path)

    return resolved_path


def generate_animated_product_video(
    product_image_path: str,
    product_name: str,
    animation_style: str = "showcase",
    duration_seconds: int = 8,
    aspect_ratio: str = "9:16",
    brand_context: Optional[dict] = None,
    output_dir: str = "generated",
    logo_path: Optional[str] = None,
    cta_text: Optional[str] = None,
    target_audience: str = ""
) -> dict:
    """
    Generate an animated product video from a product image using Veo 3.1.

    Creates a professional product showcase video optimized for Reels/TikTok
    with smooth motion and cinematic effects.

    Args:
        product_image_path: Path to the product image
        product_name: Name/description of the product
        animation_style: Type of animation - "showcase" (360 rotate), "zoom" (dramatic zoom),
                        "lifestyle" (product in use), "unboxing" (reveal effect)
        duration_seconds: Video length (5-8 seconds, Veo 3.1 max is 8s per clip)
        aspect_ratio: "9:16" for Reels/TikTok (default), "16:9" for YouTube, "1:1" for feed
        brand_context: Optional brand info (colors, tone, style)
        output_dir: Directory to save the generated video
        logo_path: Path to logo for watermark
        cta_text: Call-to-action text to display
        target_audience: Who the video is targeting (for marketing focus)

    Returns:
        Dictionary with video path and metadata or error information

    Note: For longer videos (10-20s), multiple clips can be generated and combined.
    """
    print(f"🎬 Generating animated product video for: {product_name}")
    print(f"   Source: {product_image_path}")
    print(f"   Style: {animation_style}, Duration: {duration_seconds}s, Aspect: {aspect_ratio}")

    try:
        client = _get_client()

        # Resolve the image path
        resolved_path = _resolve_image_path(product_image_path)
        print(f"   📁 Resolved path: {resolved_path}")

        if not os.path.exists(resolved_path):
            return {
                "status": "error",
                "message": f"Product image not found: {product_image_path}"
            }

        # Build animation-specific prompt based on style
        style_prompts = {
            "showcase": f"""Professional product showcase video for {product_name}.
                Smooth 360-degree rotation revealing all angles.
                Studio lighting with subtle reflections.
                Clean background that makes the product stand out.
                Premium, high-end commercial quality.""",

            "zoom": f"""Dramatic product reveal video for {product_name}.
                Cinematic slow zoom from wide to close-up detail.
                Focus on product textures and quality.
                Professional studio lighting with depth of field effect.
                Luxury brand commercial style.""",

            "lifestyle": f"""Lifestyle product video showing {product_name} in use.
                Natural, aspirational setting.
                Subtle movement showing product being used or admired.
                Warm, inviting atmosphere.
                Authentic yet polished visual style.""",

            "unboxing": f"""Elegant product reveal for {product_name}.
                Satisfying unboxing moment with anticipation build-up.
                Clean hands revealing product from premium packaging.
                Smooth, slow-motion effect on key moments.
                ASMR-satisfying visual quality."""
        }

        base_prompt = style_prompts.get(animation_style, style_prompts["showcase"])

        # Add brand context if provided - Colors only, NO TEXT (text added by MoviePy post-processing)
        if brand_context:
            brand_colors = brand_context.get("colors", [])
            brand_tone = brand_context.get("tone", "professional")

            if brand_colors:
                primary_color = brand_colors[0] if brand_colors else "#FF6B35"
                base_prompt += f"""

VISUAL STYLE:
- Use brand colors for visual accents and highlights: {', '.join(brand_colors[:3])}
- Primary accent color: {primary_color}
- Color grade the video to complement brand palette
- Visual tone: {brand_tone}
- DO NOT include any text, logos, or watermarks in the video - these will be added separately"""

        # Add target audience context for marketing focus
        if target_audience:
            base_prompt += f"""

TARGET AUDIENCE FOCUS:
- This video targets: {target_audience}
- Visual style and pacing should appeal to this demographic
- Product presentation should emphasize what matters to this audience
- Create an emotional connection with the target viewer"""

        full_prompt = base_prompt + """

QUALITY REQUIREMENTS:
- Professional commercial quality
- Smooth, fluid motion
- Product always clearly visible and in focus
- No jarring transitions or sudden movements
- Suitable for Instagram Reels, TikTok, Stories
- Cinematic quality with proper framing"""

        video_model = os.getenv("VIDEO_MODEL", "veo-3.1-generate-preview")
        print(f"   Model: {video_model}")

        # Clamp duration to valid range (5-8 seconds)
        duration_seconds = max(5, min(8, duration_seconds))

        try:
            print("   📤 Starting product video generation with Veo 3.1...")

            # Load and prepare the source image
            source_image = Image.open(resolved_path)
            if source_image.mode in ('RGBA', 'LA', 'P'):
                source_image = source_image.convert('RGB')

            img_byte_arr = io.BytesIO()
            source_image.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()

            source_image_obj = types.Image(
                image_bytes=img_bytes,
                mime_type="image/jpeg"
            )

            # Configure video generation
            video_config = types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                number_of_videos=1,
                duration_seconds=duration_seconds,
            )

            # Generate video with image input
            operation = client.models.generate_videos(
                model=video_model,
                prompt=full_prompt,
                image=source_image_obj,
                config=video_config,
            )

            # Poll for completion
            max_wait_time = 300  # 5 minutes max
            poll_interval = 10

            print("   ⏳ Waiting for video generation...")
            while not operation.done:
                time.sleep(poll_interval)
                operation = client.operations.get(operation)
                max_wait_time -= poll_interval
                print(f"   ⏳ Processing product video... (waiting...)")
                if max_wait_time <= 0:
                    return {
                        "status": "timeout",
                        "message": "Video generation is taking longer than expected. Please try again later.",
                        "product_name": product_name,
                        "source_image": product_image_path
                    }

            # Get result
            result = operation.result
            if not result:
                return {
                    "status": "error",
                    "message": "Video generation completed but no result was returned.",
                    "product_name": product_name
                }

            generated_videos = result.generated_videos
            if not generated_videos:
                return {
                    "status": "error",
                    "message": "Video generation completed but no videos were generated.",
                    "product_name": product_name
                }

            # Download and save the video
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            video = generated_videos[0]
            video_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"product_video_{timestamp}_{video_id}.mp4"
            video_path = output_path / filename

            print(f"   📥 Downloading video: {video.video.uri}")
            client.files.download(file=video.video)
            video.video.save(str(video_path))
            print(f"   ✅ Product video saved: {video_path}")

            # Apply branding overlay (logo, brand name, CTA)
            final_video_path = str(video_path)
            brand_name = brand_context.get("name") if brand_context else None
            brand_colors = brand_context.get("colors") if brand_context else None
            resolved_logo = logo_path or (brand_context.get("logo_path") if brand_context else None)

            if resolved_logo or brand_name or cta_text:
                print(f"   🏷️ Adding branding overlay...")
                final_video_path = _add_branding_to_video(
                    video_path=str(video_path),
                    logo_path=resolved_logo,
                    brand_name=brand_name,
                    cta_text=cta_text or (f"Book with {brand_name}" if brand_name else None),
                    brand_colors=brand_colors
                )

            # Determine final filename for URL
            final_filename = Path(final_video_path).name

            return {
                "status": "success",
                "video_path": final_video_path,
                "filename": final_filename,
                "url": f"/generated/{final_filename}",
                "product_name": product_name,
                "animation_style": animation_style,
                "duration_seconds": duration_seconds,
                "source_image": product_image_path,
                "aspect_ratio": aspect_ratio,
                "model": video_model,
                "type": "product_video",
                "branded": bool(resolved_logo or brand_name)
            }

        except Exception as model_error:
            error_str = str(model_error).lower()
            print(f"   ⚠️ Video generation error: {model_error}")

            if any(x in error_str for x in ["not found", "invalid", "unavailable", "permission"]):
                return {
                    "status": "model_unavailable",
                    "message": f"Veo 3.1 video generation not available: {str(model_error)[:200]}",
                    "product_name": product_name,
                    "source_image": product_image_path
                }
            raise

    except Exception as e:
        return _format_error(e, "Try a simpler product showcase style.")


def generate_motion_graphics_video(
    message: str,
    style: str = "modern",
    duration_seconds: int = 8,
    aspect_ratio: str = "9:16",
    brand_context: Optional[dict] = None,
    output_dir: str = "generated",
    target_audience: str = ""
) -> dict:
    """
    Generate a motion graphics video from text using Veo 3.1.

    Creates branded motion graphics optimized for Reels/TikTok,
    suitable for announcements, promos, and social media content.

    Args:
        message: The main message/text to feature in the video
        style: Visual style - "modern", "minimal", "bold", "elegant", "playful"
        duration_seconds: Video length (5-8 seconds, Veo 3.1 max is 8s per clip)
        aspect_ratio: "9:16" for Reels/TikTok (default), "16:9" for YouTube
        brand_context: Optional brand info (colors, name, tone)
        output_dir: Directory to save the generated video
        target_audience: Who the video is targeting (for marketing focus)

    Returns:
        Dictionary with video path and metadata or error information

    Note: For longer videos (10-20s), multiple clips can be generated and combined.
    """
    print(f"🎬 Generating motion graphics video")
    print(f"   Message: {message[:50]}...")
    print(f"   Style: {style}, Duration: {duration_seconds}s, Aspect: {aspect_ratio}")

    try:
        client = _get_client()

        # Build style-specific prompt
        style_prompts = {
            "modern": """Modern, sleek motion graphics with smooth transitions.
                Clean geometric shapes and lines.
                Trendy color gradients and glass morphism effects.
                Contemporary typography animation.""",

            "minimal": """Minimalist motion graphics with elegant simplicity.
                White space, subtle movements.
                Clean sans-serif typography.
                Refined, understated animations.""",

            "bold": """Bold, impactful motion graphics with strong presence.
                Large typography with kinetic text animation.
                High contrast colors.
                Dynamic, energetic movements.""",

            "elegant": """Sophisticated, luxurious motion graphics.
                Gold accents, refined color palette.
                Graceful, flowing animations.
                Premium brand aesthetic.""",

            "playful": """Fun, energetic motion graphics.
                Bouncy animations and playful transitions.
                Bright, vibrant colors.
                Friendly, approachable style."""
        }

        base_style = style_prompts.get(style, style_prompts["modern"])

        # Start building the prompt
        prompt_parts = [
            f"Create a professional motion graphics video.",
            f"",
            f"MAIN MESSAGE: \"{message}\"",
            f"",
            f"VISUAL STYLE:",
            base_style,
        ]

        # Add brand context - Colors only, NO TEXT (text added by MoviePy post-processing)
        if brand_context:
            brand_colors = brand_context.get("colors", [])
            brand_tone = brand_context.get("tone", "professional")

            prompt_parts.append("")
            prompt_parts.append("BRAND VISUAL STYLE:")
            if brand_colors:
                color_str = ", ".join(brand_colors[:3])
                prompt_parts.append(f"- Use brand colors for visual accents: {color_str}")
            prompt_parts.append(f"- Visual tone: {brand_tone}")

        # Add target audience context
        if target_audience:
            prompt_parts.append("")
            prompt_parts.append("TARGET AUDIENCE:")
            prompt_parts.append(f"- This video targets: {target_audience}")
            prompt_parts.append("- Visual style and pacing should appeal to this demographic")

        prompt_parts.extend([
            "",
            "REQUIREMENTS:",
            "- Smooth, professional motion graphics and transitions",
            "- Suitable for Instagram Reels/Stories",
            "- No stock footage - pure motion graphics/animation",
            "- DO NOT include any text, typography, or watermarks - these will be added separately",
        ])

        full_prompt = "\n".join(prompt_parts)

        video_model = os.getenv("VIDEO_MODEL", "veo-3.1-generate-preview")
        print(f"   Model: {video_model}")

        # Clamp duration to valid range (5-8 seconds)
        duration_seconds = max(5, min(8, duration_seconds))

        try:
            print("   📤 Starting motion graphics generation with Veo 3.1...")

            # Configure video generation (text-to-video, no image input)
            video_config = types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                number_of_videos=1,
                duration_seconds=duration_seconds,
            )

            # Generate video from text prompt
            operation = client.models.generate_videos(
                model=video_model,
                prompt=full_prompt,
                config=video_config,
            )

            # Poll for completion
            max_wait_time = 300
            poll_interval = 10

            print("   ⏳ Waiting for motion graphics generation...")
            while not operation.done:
                time.sleep(poll_interval)
                operation = client.operations.get(operation)
                max_wait_time -= poll_interval
                print(f"   ⏳ Processing motion graphics... (waiting...)")
                if max_wait_time <= 0:
                    return {
                        "status": "timeout",
                        "message": "Video generation is taking longer than expected.",
                        "message_text": message
                    }

            # Get result
            result = operation.result
            if not result:
                return {
                    "status": "error",
                    "message": "Video generation completed but no result was returned.",
                    "message_text": message
                }

            generated_videos = result.generated_videos
            if not generated_videos:
                return {
                    "status": "error",
                    "message": "Video generation completed but no videos were generated.",
                    "message_text": message
                }

            # Download and save the video
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            video = generated_videos[0]
            video_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"motion_graphics_{timestamp}_{video_id}.mp4"
            video_path = output_path / filename

            print(f"   📥 Downloading video: {video.video.uri}")
            client.files.download(file=video.video)
            video.video.save(str(video_path))
            print(f"   ✅ Motion graphics video saved: {video_path}")

            # Apply branding overlay (logo, brand name, CTA)
            final_video_path = str(video_path)
            brand_name = brand_context.get("name") if brand_context else None
            brand_colors = brand_context.get("colors") if brand_context else None
            logo_path = brand_context.get("logo_path") if brand_context else None

            if logo_path or brand_name:
                print(f"   🏷️ Adding branding overlay...")
                final_video_path = _add_branding_to_video(
                    video_path=str(video_path),
                    logo_path=logo_path,
                    brand_name=brand_name,
                    cta_text=f"Visit {brand_name}.com" if brand_name else None,
                    brand_colors=brand_colors
                )

            # Determine final filename for URL
            final_filename = Path(final_video_path).name

            return {
                "status": "success",
                "video_path": final_video_path,
                "filename": final_filename,
                "url": f"/generated/{final_filename}",
                "message": message,
                "style": style,
                "duration_seconds": duration_seconds,
                "aspect_ratio": aspect_ratio,
                "model": video_model,
                "type": "motion_graphics"
            }

        except Exception as model_error:
            error_str = str(model_error).lower()
            print(f"   ⚠️ Motion graphics generation error: {model_error}")

            if any(x in error_str for x in ["not found", "invalid", "unavailable", "permission"]):
                return {
                    "status": "model_unavailable",
                    "message": f"Veo 3.1 not available: {str(model_error)[:200]}",
                    "message_text": message
                }
            raise

    except Exception as e:
        return _format_error(e, "Try a simpler motion graphics style.")


def generate_talking_head_video(
    script: str,
    avatar_style: str = "professional",
    voice_style: str = "friendly",
    duration_seconds: int = 30,
    aspect_ratio: str = "9:16",
    brand_context: Optional[dict] = None,
    output_dir: str = "generated"
) -> dict:
    """
    Generate an AI talking head video.

    NOTE: This feature requires external API integration (D-ID, HeyGen, or Synthesia).
    Currently returns a placeholder response with instructions.

    Args:
        script: The script/text for the AI avatar to speak
        avatar_style: "professional", "casual", "friendly", "corporate"
        voice_style: "friendly", "professional", "energetic", "calm"
        duration_seconds: Estimated video length based on script
        aspect_ratio: "9:16" for Reels/Stories, "16:9" for YouTube
        brand_context: Optional brand info
        output_dir: Directory to save the generated video

    Returns:
        Dictionary with status and recommendations for external tools
    """
    print(f"🎬 AI Talking Head Video requested")
    print(f"   Script: {script[:100]}...")
    print(f"   Avatar: {avatar_style}, Voice: {voice_style}")

    # Calculate approximate duration based on script length
    # Average speaking rate: ~150 words per minute = 2.5 words per second
    word_count = len(script.split())
    estimated_duration = max(5, min(120, int(word_count / 2.5)))

    # Prepare the script and settings for external tools
    external_settings = {
        "script": script,
        "word_count": word_count,
        "estimated_duration_seconds": estimated_duration,
        "avatar_style": avatar_style,
        "voice_style": voice_style,
        "aspect_ratio": aspect_ratio,
    }

    if brand_context:
        external_settings["brand_name"] = brand_context.get("name", "")
        external_settings["brand_colors"] = brand_context.get("colors", [])
        external_settings["brand_tone"] = brand_context.get("tone", "")

    # Return helpful response with external tool recommendations
    return {
        "status": "external_required",
        "message": "AI Talking Head videos require an external service. Here are your options:",
        "recommendations": [
            {
                "name": "HeyGen",
                "url": "https://heygen.com",
                "features": "Realistic AI avatars, multiple languages, custom avatars",
                "pricing": "Free tier available, paid plans from $24/month"
            },
            {
                "name": "D-ID",
                "url": "https://d-id.com",
                "features": "Photo-to-video, presenter creation, API access",
                "pricing": "Free tier available, paid from $4.99/month"
            },
            {
                "name": "Synthesia",
                "url": "https://synthesia.io",
                "features": "Enterprise-grade AI presenters, 140+ languages",
                "pricing": "From $22/month"
            },
            {
                "name": "Runway",
                "url": "https://runwayml.com",
                "features": "Gen-3 Alpha for face animation",
                "pricing": "Free tier, paid from $12/month"
            }
        ],
        "prepared_settings": external_settings,
        "type": "talking_head",
        "next_steps": [
            f"Your script is {word_count} words, approximately {estimated_duration} seconds when spoken.",
            "Copy your script to one of the recommended tools above.",
            "Choose an avatar that matches your brand style.",
            "Export the video and upload it here for further editing if needed."
        ]
    }


def get_video_type_options() -> dict:
    """
    Get available video generation types with descriptions.

    Returns:
        Dictionary with video type options for UI display
    """
    return {
        "options": [
            {
                "id": "animated_product",
                "label": "Animated Product Video",
                "icon": "📦",
                "description": "Transform product images into dynamic showcase videos (8s)",
                "duration": "8 seconds",
                "requires_image": True,
                "styles": ["showcase", "zoom", "lifestyle", "unboxing"]
            },
            {
                "id": "motion_graphics",
                "label": "Motion Graphics",
                "icon": "✨",
                "description": "Create branded motion graphics for announcements (8s)",
                "duration": "8 seconds",
                "requires_image": False,
                "styles": ["modern", "minimal", "bold", "elegant", "playful"]
            },
            {
                "id": "talking_head",
                "label": "AI Talking Head",
                "icon": "🎙️",
                "description": "AI presenter explains your product (external service)",
                "duration": "15-30 seconds",
                "requires_image": False,
                "external": True,
                "styles": ["professional", "casual", "friendly", "corporate"]
            }
        ]
    }


def suggest_video_ideas(
    video_type: str,
    brand_name: str = "",
    brand_industry: str = "",
    product_name: str = "",
    occasion: str = "",
    brand_tone: str = "professional"
) -> dict:
    """
    Suggest video ideas based on brand context and video type.

    This function provides templated video ideas that the agent can use
    when presenting options to the user.

    Args:
        video_type: "animated_product", "motion_graphics", or "talking_head"
        brand_name: Name of the brand
        brand_industry: Industry/niche
        product_name: Product being featured (if any)
        occasion: Special occasion/event (if any)
        brand_tone: Brand's tone (professional, playful, etc.)

    Returns:
        Dictionary with suggested video ideas
    """
    # Product video ideas
    product_ideas = [
        {
            "title": "360° Product Showcase",
            "style": "showcase",
            "hook": "See every angle of our [product]",
            "description": "Smooth rotation revealing all product details with professional lighting",
            "duration": 8
        },
        {
            "title": "Dramatic Reveal",
            "style": "unboxing",
            "hook": "Unbox something special...",
            "description": "Elegant unboxing experience with suspense and premium feel",
            "duration": 8
        },
        {
            "title": "Feature Spotlight",
            "style": "zoom",
            "hook": "The detail that makes the difference",
            "description": "Cinematic zoom highlighting key product features",
            "duration": 8
        },
        {
            "title": "Lifestyle in Action",
            "style": "lifestyle",
            "hook": "Made for your everyday",
            "description": "Product being used naturally in an aspirational setting",
            "duration": 8
        }
    ]

    # Motion graphics ideas
    motion_ideas = [
        {
            "title": "Bold Announcement",
            "style": "bold",
            "hook": "BIG NEWS!",
            "description": "High-impact text animation with dynamic movements",
            "duration": 8
        },
        {
            "title": "Elegant Reveal",
            "style": "elegant",
            "hook": "Introducing something special...",
            "description": "Sophisticated motion graphics with premium feel",
            "duration": 8
        },
        {
            "title": "Modern Promo",
            "style": "modern",
            "hook": "The future is here",
            "description": "Sleek, trendy animation with glass morphism effects",
            "duration": 8
        },
        {
            "title": "Fun & Playful",
            "style": "playful",
            "hook": "Get ready for something fun!",
            "description": "Bouncy, energetic animation with vibrant colors",
            "duration": 8
        }
    ]

    # Talking head ideas
    talking_ideas = [
        {
            "title": "Product Explainer",
            "style": "professional",
            "hook": "Let me tell you about...",
            "description": "Clear explanation of product features and benefits",
            "duration": 20
        },
        {
            "title": "FAQ Answer",
            "style": "friendly",
            "hook": "You asked, we answered!",
            "description": "Address common customer questions in a friendly way",
            "duration": 15
        },
        {
            "title": "Brand Story",
            "style": "professional",
            "hook": "Our story begins...",
            "description": "Share your brand's mission and values",
            "duration": 30
        },
        {
            "title": "Quick Tip",
            "style": "casual",
            "hook": "Pro tip!",
            "description": "Share a useful tip related to your product/industry",
            "duration": 15
        }
    ]

    # Select ideas based on video type
    if video_type == "animated_product":
        ideas = product_ideas
    elif video_type == "motion_graphics":
        ideas = motion_ideas
    else:
        ideas = talking_ideas

    # Customize ideas with brand context
    customized_ideas = []
    for idea in ideas[:4]:  # Return top 4 ideas
        customized = idea.copy()
        if brand_name:
            customized["hook"] = customized["hook"].replace("[brand]", brand_name)
        if product_name:
            customized["hook"] = customized["hook"].replace("[product]", product_name)
            customized["description"] = customized["description"].replace("[product]", product_name)
        customized_ideas.append(customized)

    return {
        "status": "success",
        "video_type": video_type,
        "ideas": customized_ideas,
        "brand_context": {
            "name": brand_name,
            "industry": brand_industry,
            "product": product_name,
            "occasion": occasion,
            "tone": brand_tone
        }
    }
