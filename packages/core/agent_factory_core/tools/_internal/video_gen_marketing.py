"""
Video Generation Tools for Marketing Video Agent Factory.

Provides specialized video generation functions:
- Video from Image (Veo 3.1 image-to-video)
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
    """Get an available system font for text rendering."""
    if not MOVIEPY_AVAILABLE:
        return None

    font_options = [
        "Arial-Bold", "Arial", "Helvetica-Bold", "Helvetica",
        "DejaVu-Sans-Bold", "DejaVu-Sans", "Liberation-Sans-Bold", "Liberation-Sans",
    ]

    for font in font_options:
        try:
            test = TextClip(text="test", font=font, font_size=20)
            test.close()
            return font
        except Exception:
            continue

    return None


def _add_branding_to_video(
    video_path: str,
    logo_path: Optional[str] = None,
    brand_name: Optional[str] = None,
    cta_text: Optional[str] = None,
    brand_colors: Optional[list] = None
) -> str:
    """Add logo watermark and brand text overlay to a video."""
    if not MOVIEPY_AVAILABLE:
        return video_path

    try:
        project_root = Path(__file__).parent.parent
        resolved_logo = None
        if logo_path:
            if os.path.exists(logo_path):
                resolved_logo = logo_path
            elif logo_path.startswith("/"):
                resolved_logo = str(project_root / logo_path.lstrip("/"))
            else:
                resolved_logo = str(project_root / logo_path)
            if not os.path.exists(resolved_logo):
                resolved_logo = None

        video = VideoFileClip(video_path)
        video_width, video_height = video.size
        clips = [video]

        if resolved_logo:
            try:
                logo = ImageClip(resolved_logo)
                logo_scale = (video_width * 0.15) / logo.size[0]
                logo = logo.resized(logo_scale)
                logo_x = video_width - logo.size[0] - 20
                logo = logo.with_opacity(0.85).with_position((logo_x, 20)).with_duration(video.duration)
                clips.append(logo)
            except Exception:
                pass

        available_font = _get_available_font()

        if brand_name:
            try:
                text_color = brand_colors[0] if brand_colors else "#FFFFFF"
                brand_text = TextClip(
                    text=brand_name, font_size=int(video_height * 0.04),
                    color=text_color, font=available_font,
                    stroke_color="black", stroke_width=1
                )
                brand_text = brand_text.with_position((20, video_height - 80)).with_duration(video.duration)
                clips.append(brand_text)
            except Exception:
                pass

        if cta_text and video.duration > 3:
            try:
                cta_color = brand_colors[0] if brand_colors else "#FF6B35"
                cta = TextClip(
                    text=cta_text, font_size=int(video_height * 0.05),
                    color=cta_color, font=available_font,
                    stroke_color="black", stroke_width=1
                )
                cta_x = (video_width - cta.size[0]) // 2
                cta = cta.with_position((cta_x, video_height - 150)).with_start(video.duration - 3).with_duration(3)
                clips.append(cta)
            except Exception:
                pass

        if len(clips) > 1:
            final_video = CompositeVideoClip(clips)
            output_path = video_path.replace(".mp4", "_branded.mp4")
            final_video.write_videofile(
                output_path, codec="libx264",
                audio_codec="aac" if video.audio else None,
                fps=video.fps, logger=None
            )
            video.close()
            final_video.close()
            return output_path
        else:
            video.close()
            return video_path

    except Exception:
        return video_path


def _resolve_image_path(image_path: str) -> str:
    """Convert web URL path to filesystem path if needed."""
    resolved_path = image_path
    project_root = Path(__file__).parent.parent

    if image_path.startswith(("/generated/", "/uploads/", "/static/")):
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

    Args:
        product_image_path: Path to the product image
        product_name: Name/description of the product
        animation_style: "showcase", "zoom", "lifestyle", "unboxing"
        duration_seconds: Video length (5-8 seconds)
        aspect_ratio: "9:16" for Reels/TikTok, "16:9" for YouTube, "1:1" for feed
        brand_context: Optional brand info (colors, tone, style)
        output_dir: Directory to save the generated video
        logo_path: Path to logo for watermark
        cta_text: Call-to-action text to display
        target_audience: Who the video is targeting

    Returns:
        Dictionary with video path and metadata or error information
    """
    print(f"Generating animated product video for: {product_name}")

    try:
        client = _get_client()
        resolved_path = _resolve_image_path(product_image_path)

        if not os.path.exists(resolved_path):
            return {"status": "error", "message": f"Product image not found: {product_image_path}"}

        style_prompts = {
            "showcase": f"Professional product showcase video for {product_name}. Smooth 360-degree rotation revealing all angles. Studio lighting with subtle reflections. Clean background. Premium commercial quality.",
            "zoom": f"Dramatic product reveal video for {product_name}. Cinematic slow zoom from wide to close-up detail. Focus on textures and quality. Professional lighting with depth of field.",
            "lifestyle": f"Lifestyle product video showing {product_name} in use. Natural, aspirational setting. Subtle movement. Warm, inviting atmosphere. Authentic yet polished.",
            "unboxing": f"Elegant product reveal for {product_name}. Satisfying unboxing moment with anticipation. Clean hands revealing product from premium packaging. Smooth slow-motion."
        }

        base_prompt = style_prompts.get(animation_style, style_prompts["showcase"])

        if brand_context:
            brand_colors = brand_context.get("colors", [])
            brand_tone = brand_context.get("tone", "professional")
            if brand_colors:
                base_prompt += f"\n\nVISUAL STYLE:\n- Brand colors: {', '.join(brand_colors[:3])}\n- Visual tone: {brand_tone}\n- DO NOT include text, logos, or watermarks"

        if target_audience:
            base_prompt += f"\n\nTARGET AUDIENCE: {target_audience}\n- Visual style should appeal to this demographic"

        base_prompt += "\n\nQUALITY: Professional commercial quality. Smooth fluid motion. Product always in focus. Suitable for Instagram Reels, TikTok, Stories."

        video_model = os.getenv("VIDEO_MODEL", "veo-3.1-generate-preview")
        duration_seconds = max(5, min(8, duration_seconds))

        try:
            source_image = Image.open(resolved_path)
            if source_image.mode in ('RGBA', 'LA', 'P'):
                source_image = source_image.convert('RGB')

            img_byte_arr = io.BytesIO()
            source_image.save(img_byte_arr, format='JPEG')

            source_image_obj = types.Image(image_bytes=img_byte_arr.getvalue(), mime_type="image/jpeg")
            video_config = types.GenerateVideosConfig(aspect_ratio=aspect_ratio, number_of_videos=1, duration_seconds=duration_seconds)

            operation = client.models.generate_videos(model=video_model, prompt=base_prompt, image=source_image_obj, config=video_config)

            max_wait_time = 300
            while not operation.done:
                time.sleep(10)
                operation = client.operations.get(operation)
                max_wait_time -= 10
                if max_wait_time <= 0:
                    return {"status": "timeout", "message": "Video generation is taking longer than expected.", "product_name": product_name, "source_image": product_image_path}

            result = operation.result
            if not result or not result.generated_videos:
                return {"status": "error", "message": "Video generation completed but no videos were generated.", "product_name": product_name}

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            video = result.generated_videos[0]
            video_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"product_video_{timestamp}_{video_id}.mp4"
            video_path = output_path / filename

            client.files.download(file=video.video)
            video.video.save(str(video_path))

            final_video_path = str(video_path)
            brand_name = brand_context.get("name") if brand_context else None
            brand_colors = brand_context.get("colors") if brand_context else None
            resolved_logo = logo_path or (brand_context.get("logo_path") if brand_context else None)

            if resolved_logo or brand_name or cta_text:
                final_video_path = _add_branding_to_video(
                    video_path=str(video_path), logo_path=resolved_logo, brand_name=brand_name,
                    cta_text=cta_text or (f"Book with {brand_name}" if brand_name else None),
                    brand_colors=brand_colors
                )

            final_filename = Path(final_video_path).name
            return {
                "status": "success", "video_path": final_video_path, "filename": final_filename,
                "url": f"/generated/{final_filename}", "product_name": product_name,
                "animation_style": animation_style, "duration_seconds": duration_seconds,
                "source_image": product_image_path, "aspect_ratio": aspect_ratio,
                "model": video_model, "type": "product_video", "branded": bool(resolved_logo or brand_name)
            }

        except Exception as model_error:
            error_str = str(model_error).lower()
            if any(x in error_str for x in ["not found", "invalid", "unavailable", "permission"]):
                return {"status": "model_unavailable", "message": f"Veo 3.1 not available: {str(model_error)[:200]}", "product_name": product_name, "source_image": product_image_path}
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

    Args:
        message: The main message/text to feature
        style: "modern", "minimal", "bold", "elegant", "playful"
        duration_seconds: Video length (5-8 seconds)
        aspect_ratio: "9:16" for Reels/TikTok, "16:9" for YouTube
        brand_context: Optional brand info
        output_dir: Directory to save the generated video
        target_audience: Who the video is targeting

    Returns:
        Dictionary with video path and metadata or error information
    """
    print(f"Generating motion graphics video: {message[:50]}...")
    print(f"  brand_context={brand_context}")
    print(f"  target_audience={target_audience}")
    print(f"  style={style}")

    try:
        client = _get_client()

        style_prompts = {
            "modern": "Modern, sleek motion graphics with smooth transitions. Clean geometric shapes. Trendy color gradients and glass morphism effects.",
            "minimal": "Minimalist motion graphics with elegant simplicity. White space, subtle movements. Refined, understated animations.",
            "bold": "Bold, impactful motion graphics. Large kinetic text animation. High contrast colors. Dynamic, energetic movements.",
            "elegant": "Sophisticated, luxurious motion graphics. Gold accents, refined palette. Graceful flowing animations. Premium aesthetic.",
            "playful": "Fun, energetic motion graphics. Bouncy animations. Bright, vibrant colors. Friendly, approachable style."
        }

        base_style = style_prompts.get(style, style_prompts["modern"])
        prompt_parts = [f"Create a professional motion graphics video.", f"MAIN MESSAGE: \"{message}\"", f"VISUAL STYLE: {base_style}"]

        if brand_context:
            brand_name = brand_context.get("name", "")
            brand_colors = brand_context.get("colors", [])
            brand_tone = brand_context.get("tone", "professional")
            brand_industry = brand_context.get("industry", "")
            if brand_name:
                prompt_parts.append(f"BRAND: {brand_name}" + (f" ({brand_industry})" if brand_industry else ""))
            if brand_colors:
                prompt_parts.append(f"BRAND COLORS: Use these colors prominently: {', '.join(brand_colors[:3])}")
            prompt_parts.append(f"TONE: {brand_tone}")

        if target_audience:
            prompt_parts.append(f"TARGET AUDIENCE: {target_audience}")

        prompt_parts.append("REQUIREMENTS: Smooth professional transitions. Suitable for Instagram Reels/Stories. No text/watermarks - added separately.")
        full_prompt = "\n".join(prompt_parts)
        print(f"  FULL PROMPT:\n{full_prompt}")

        video_model = os.getenv("VIDEO_MODEL", "veo-3.1-generate-preview")
        duration_seconds = max(5, min(8, duration_seconds))

        try:
            video_config = types.GenerateVideosConfig(aspect_ratio=aspect_ratio, number_of_videos=1, duration_seconds=duration_seconds)
            operation = client.models.generate_videos(model=video_model, prompt=full_prompt, config=video_config)

            max_wait_time = 300
            while not operation.done:
                time.sleep(10)
                operation = client.operations.get(operation)
                max_wait_time -= 10
                if max_wait_time <= 0:
                    return {"status": "timeout", "message": "Video generation is taking longer than expected.", "message_text": message}

            result = operation.result
            if not result or not result.generated_videos:
                return {"status": "error", "message": "No videos were generated.", "message_text": message}

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            video = result.generated_videos[0]
            video_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"motion_graphics_{timestamp}_{video_id}.mp4"
            video_path = output_path / filename

            client.files.download(file=video.video)
            video.video.save(str(video_path))

            final_video_path = str(video_path)
            brand_name = brand_context.get("name") if brand_context else None
            brand_colors = brand_context.get("colors") if brand_context else None
            logo_path = brand_context.get("logo_path") if brand_context else None

            if logo_path or brand_name:
                final_video_path = _add_branding_to_video(
                    video_path=str(video_path), logo_path=logo_path, brand_name=brand_name,
                    cta_text=f"Visit {brand_name}.com" if brand_name else None, brand_colors=brand_colors
                )

            final_filename = Path(final_video_path).name
            return {
                "status": "success", "video_path": final_video_path, "filename": final_filename,
                "url": f"/generated/{final_filename}", "message": message, "style": style,
                "duration_seconds": duration_seconds, "aspect_ratio": aspect_ratio,
                "model": video_model, "type": "motion_graphics"
            }

        except Exception as model_error:
            error_str = str(model_error).lower()
            if any(x in error_str for x in ["not found", "invalid", "unavailable", "permission"]):
                return {"status": "model_unavailable", "message": f"Veo 3.1 not available: {str(model_error)[:200]}", "message_text": message}
            raise

    except Exception as e:
        return _format_error(e, "Try a simpler motion graphics style.")


def generate_talking_head_video(
    script: str, avatar_style: str = "professional", voice_style: str = "friendly",
    duration_seconds: int = 30, aspect_ratio: str = "9:16",
    brand_context: Optional[dict] = None, output_dir: str = "generated"
) -> dict:
    """Generate an AI talking head video (external service required)."""
    word_count = len(script.split())
    estimated_duration = max(5, min(120, int(word_count / 2.5)))

    external_settings = {
        "script": script, "word_count": word_count,
        "estimated_duration_seconds": estimated_duration,
        "avatar_style": avatar_style, "voice_style": voice_style, "aspect_ratio": aspect_ratio,
    }

    if brand_context:
        external_settings["brand_name"] = brand_context.get("name", "")
        external_settings["brand_colors"] = brand_context.get("colors", [])

    return {
        "status": "external_required",
        "message": "AI Talking Head videos require an external service.",
        "recommendations": [
            {"name": "HeyGen", "url": "https://heygen.com", "features": "Realistic AI avatars, multiple languages"},
            {"name": "D-ID", "url": "https://d-id.com", "features": "Photo-to-video, presenter creation, API access"},
            {"name": "Synthesia", "url": "https://synthesia.io", "features": "Enterprise-grade AI presenters, 140+ languages"},
        ],
        "prepared_settings": external_settings,
        "type": "talking_head",
        "next_steps": [
            f"Your script is {word_count} words, approximately {estimated_duration} seconds when spoken.",
            "Copy your script to one of the recommended tools above.",
            "Choose an avatar that matches your brand style.",
        ]
    }


def generate_video(
    prompt: str,
    image_path: str = "",
    reference_image_paths: list[str] = [],
    duration_seconds: int = 8,
    aspect_ratio: str = "9:16",
    output_dir: str = "generated",
) -> dict:
    """
    Generate a video using Veo 3.1 — the unified video generation tool.

    This is the ONLY tool needed for ALL video types. The prompt determines
    what kind of video is created (brand story, product launch, motion graphics,
    talking head, explainer, etc.). Write a detailed, cinematic prompt.

    Args:
        prompt: The complete video generation prompt. Must be detailed and include:
            - Scene description (what happens visually)
            - Camera work (close-up, wide shot, slow pan, tracking shot)
            - Lighting & mood (warm golden hour, moody studio, bright airy)
            - Brand colors (e.g. "Color palette features #FF6B35 orange")
            - Motion & pacing (smooth slow-motion, energetic cuts)
            - Style (cinematic, modern minimal, bold, elegant)
            - Audio/music mood (upbeat electronic, inspiring orchestral)
        image_path: Optional. Path to a starting image for image-to-video mode.
            Use for product showcases where you have a product photo.
        reference_image_paths: Optional. List of paths to reference images
            (logo, brand assets, style references) for Veo to use as visual guides.
        duration_seconds: Video length in seconds (5-8). Default 8.
        aspect_ratio: "9:16" (Reels/TikTok), "16:9" (YouTube), "1:1" (Feed).
        output_dir: Directory to save the generated video.

    Returns:
        Dictionary with video path, URL, and metadata on success.
        Dictionary with error info on failure.
    """
    print(f"\n{'='*60}")
    print(f"🎬 GENERATE VIDEO")
    print(f"  Prompt: {prompt[:200]}...")
    print(f"  Image: {image_path or 'None (text-to-video)'}")
    print(f"  References: {reference_image_paths or 'None'}")
    print(f"  Duration: {duration_seconds}s | Aspect: {aspect_ratio}")
    print(f"{'='*60}\n")

    try:
        client = _get_client()
        video_model = os.getenv("VIDEO_MODEL", "veo-3.1-generate-preview")
        # Clamp duration to valid Veo range (5-8 seconds)
        clamped_duration = max(5, min(8, duration_seconds))

        # Build config
        config_kwargs = {
            "aspect_ratio": aspect_ratio,
            "number_of_videos": 1,
            "duration_seconds": clamped_duration,
        }

        # Handle reference images (only for text-to-video; Veo API does NOT
        # support reference_images + image together in image-to-video mode)
        if reference_image_paths and not image_path:
            ref_images = []
            for ref_path in reference_image_paths:
                resolved = _resolve_image_path(ref_path)
                if os.path.exists(resolved):
                    try:
                        ref_img = Image.open(resolved)
                        if ref_img.mode in ('RGBA', 'LA', 'P'):
                            ref_img = ref_img.convert('RGB')
                        buf = io.BytesIO()
                        ref_img.save(buf, format='JPEG')
                        ref_image_obj = types.Image(
                            image_bytes=buf.getvalue(), mime_type="image/jpeg"
                        )
                        ref_images.append(
                            types.VideoGenerationReferenceImage(
                                image=ref_image_obj, reference_type="asset"
                            )
                        )
                        print(f"  ✅ Loaded reference image: {ref_path}")
                    except Exception as e:
                        print(f"  ⚠️ Could not load reference image {ref_path}: {e}")
                else:
                    print(f"  ⚠️ Reference image not found: {resolved}")
            if ref_images:
                config_kwargs["reference_images"] = ref_images
        elif reference_image_paths and image_path:
            print(f"  ℹ️ Skipping reference images (not supported with image-to-video mode)")

        video_config = types.GenerateVideosConfig(**config_kwargs)

        # Build generate_videos kwargs
        gen_kwargs = {
            "model": video_model,
            "prompt": prompt,
            "config": video_config,
        }

        # Handle starting image (image-to-video mode)
        if image_path:
            resolved_img = _resolve_image_path(image_path)
            if os.path.exists(resolved_img):
                try:
                    source_image = Image.open(resolved_img)
                    if source_image.mode in ('RGBA', 'LA', 'P'):
                        source_image = source_image.convert('RGB')
                    print(f"  ✅ Loaded starting image: {image_path} ({source_image.size})")

                    # Composite logo onto image if reference_image_paths has a logo
                    if reference_image_paths:
                        for ref_path in reference_image_paths:
                            resolved_logo = _resolve_image_path(ref_path)
                            if os.path.exists(resolved_logo):
                                try:
                                    logo_img = Image.open(resolved_logo)
                                    # Resize logo to ~15% of image width
                                    img_w, img_h = source_image.size
                                    logo_target_w = int(img_w * 0.15)
                                    logo_w, logo_h = logo_img.size
                                    logo_scale = logo_target_w / logo_w
                                    logo_new_size = (logo_target_w, int(logo_h * logo_scale))
                                    logo_resized = logo_img.resize(logo_new_size, Image.LANCZOS)

                                    # Position: top-right corner with padding
                                    padding = int(img_w * 0.03)
                                    x = img_w - logo_new_size[0] - padding
                                    y = padding

                                    # Paste with transparency if logo has alpha
                                    if logo_resized.mode == 'RGBA':
                                        source_image.paste(logo_resized, (x, y), logo_resized)
                                    else:
                                        source_image.paste(logo_resized, (x, y))
                                    print(f"  ✅ Composited logo onto image: {ref_path} ({logo_new_size})")
                                except Exception as logo_err:
                                    print(f"  ⚠️ Could not composite logo {ref_path}: {logo_err}")

                    buf = io.BytesIO()
                    source_image.save(buf, format='JPEG')
                    gen_kwargs["image"] = types.Image(
                        image_bytes=buf.getvalue(), mime_type="image/jpeg"
                    )
                    print(f"  ✅ Using composited image for Veo")
                except Exception as e:
                    print(f"  ⚠️ Could not load starting image {image_path}: {e}")
            else:
                print(f"  ⚠️ Starting image not found: {resolved_img}")

        # Generate video
        print(f"  🚀 Calling Veo 3.1 ({video_model})...")
        try:
            operation = client.models.generate_videos(**gen_kwargs)

            max_wait_time = 300
            while not operation.done:
                time.sleep(10)
                operation = client.operations.get(operation)
                max_wait_time -= 10
                elapsed = 300 - max_wait_time
                print(f"  ⏳ Waiting... ({elapsed}s elapsed)")
                if max_wait_time <= 0:
                    return {
                        "status": "timeout",
                        "message": "Video generation timed out after 5 minutes. Please try again.",
                    }

            result = operation.result
            if not result or not result.generated_videos:
                return {
                    "status": "error",
                    "message": "Video generation completed but no videos were produced. Try a different prompt.",
                }

            video = result.generated_videos[0]
            print(f"  ✅ {clamped_duration}s video generated")

            # Save the video
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            video_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"video_{timestamp}_{video_id}.mp4"
            video_path = output_path / filename

            client.files.download(file=video.video)
            video.video.save(str(video_path))

            file_size = video_path.stat().st_size
            print(f"  ✅ Video saved: {video_path} ({file_size:,} bytes, ~{clamped_duration}s)")

            return {
                "status": "success",
                "video_path": str(video_path),
                "filename": filename,
                "url": f"/generated/{filename}",
                "duration_seconds": clamped_duration,
                "aspect_ratio": aspect_ratio,
                "model": video_model,
                "type": "generated",
                "file_size": file_size,
            }

        except Exception as model_error:
            error_str = str(model_error).lower()
            print(f"  ❌ Video generation error: {model_error}")
            import traceback
            traceback.print_exc()
            if any(x in error_str for x in ["not found", "invalid", "unavailable", "permission"]):
                return {
                    "status": "model_unavailable",
                    "message": f"Veo 3.1 error: {str(model_error)[:300]}",
                }
            return {
                "status": "error",
                "message": f"Video generation failed: {str(model_error)[:300]}",
            }

    except Exception as e:
        return _format_error(e, "Try simplifying your video prompt.")


def get_video_type_options() -> dict:
    """Get available video generation types with descriptions."""
    return {
        "options": [
            {"id": "video_from_image", "label": "Video from Image", "icon": "🖼️", "description": "Upload your image and we create a promotional video around it (8s)", "requires_image": True, "styles": ["showcase", "cinematic_reveal", "promo", "social_ad"]},
            {"id": "motion_graphics", "label": "Motion Graphics", "icon": "✨", "description": "Create branded motion graphics for announcements (8s)", "requires_image": False, "styles": ["modern", "minimal", "bold", "elegant", "playful"]},
            {"id": "talking_head", "label": "AI Talking Head", "icon": "🎙️", "description": "AI presenter explains your product (external service)", "requires_image": False, "external": True, "styles": ["professional", "casual", "friendly", "corporate"]},
        ]
    }


def suggest_video_ideas(
    video_type: str, brand_name: str = "", brand_industry: str = "",
    product_name: str = "", occasion: str = "", brand_tone: str = "professional"
) -> dict:
    """Suggest video ideas based on brand context and video type."""
    product_ideas = [
        {"title": "360 Product Showcase", "style": "showcase", "hook": "See every angle of our [product]", "description": "Smooth rotation revealing all product details", "duration": 8},
        {"title": "Dramatic Reveal", "style": "unboxing", "hook": "Unbox something special...", "description": "Elegant unboxing experience with premium feel", "duration": 8},
        {"title": "Feature Spotlight", "style": "zoom", "hook": "The detail that makes the difference", "description": "Cinematic zoom highlighting key features", "duration": 8},
        {"title": "Lifestyle in Action", "style": "lifestyle", "hook": "Made for your everyday", "description": "Product being used naturally in an aspirational setting", "duration": 8},
    ]

    motion_ideas = [
        {"title": "Bold Announcement", "style": "bold", "hook": "BIG NEWS!", "description": "High-impact text animation with dynamic movements", "duration": 8},
        {"title": "Elegant Reveal", "style": "elegant", "hook": "Introducing something special...", "description": "Sophisticated motion graphics with premium feel", "duration": 8},
        {"title": "Modern Promo", "style": "modern", "hook": "The future is here", "description": "Sleek, trendy animation with glass morphism effects", "duration": 8},
        {"title": "Fun & Playful", "style": "playful", "hook": "Get ready for something fun!", "description": "Bouncy, energetic animation with vibrant colors", "duration": 8},
    ]

    talking_ideas = [
        {"title": "Product Explainer", "style": "professional", "hook": "Let me tell you about...", "description": "Clear explanation of product features and benefits", "duration": 20},
        {"title": "FAQ Answer", "style": "friendly", "hook": "You asked, we answered!", "description": "Address common customer questions", "duration": 8},
        {"title": "Brand Story", "style": "professional", "hook": "Our story begins...", "description": "Share your brand's mission and values", "duration": 30},
        {"title": "Quick Tip", "style": "casual", "hook": "Pro tip!", "description": "Share a useful tip related to your product/industry", "duration": 8},
    ]

    ideas = product_ideas if video_type in ("animated_product", "video_from_image") else motion_ideas if video_type == "motion_graphics" else talking_ideas

    customized_ideas = []
    for idea in ideas[:4]:
        customized = idea.copy()
        if brand_name:
            customized["hook"] = customized["hook"].replace("[brand]", brand_name)
        if product_name:
            customized["hook"] = customized["hook"].replace("[product]", product_name)
            customized["description"] = customized["description"].replace("[product]", product_name)
        customized_ideas.append(customized)

    return {
        "status": "success", "video_type": video_type, "ideas": customized_ideas,
        "brand_context": {"name": brand_name, "industry": brand_industry, "product": product_name, "occasion": occasion, "tone": brand_tone}
    }
