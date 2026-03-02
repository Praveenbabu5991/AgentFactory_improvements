"""
Content Creation Tools for captions and hashtags.

Provides caption writing, hashtag generation, and content optimization
with proper error handling.
"""

import os
import time
from typing import Any

from google import genai
from dotenv import load_dotenv

load_dotenv()


def _get_client():
    """Get Gemini client with validation."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("API key not configured. Please set GOOGLE_API_KEY.")
    return genai.Client(api_key=api_key)


def _retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """Execute function with exponential backoff retry."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
    raise last_error


def _format_error(error: Exception) -> dict:
    """Format error into user-friendly response."""
    error_str = str(error).lower()
    
    if "quota" in error_str or "rate" in error_str:
        message = "Service is busy. Please try again in a moment."
    elif "api" in error_str:
        message = "Service configuration issue. Please contact support."
    else:
        message = "Could not generate content. Please try again."
    
    return {"status": "error", "message": message, "technical_details": str(error)}


def write_caption(
    topic: str,
    brand_voice: str = "professional yet friendly",
    target_audience: str = "general",
    key_message: str = "",
    occasion: str = "",
    tone: str = "engaging",
    max_length: int = 500,
    include_cta: bool = True,
    emoji_level: str = "moderate",
    company_overview: str = "",
    brand_name: str = "",
    image_description: str = ""
) -> dict:
    """
    Write an engaging Instagram caption.
    
    Args:
        topic: Main topic/theme of the post
        brand_voice: Brand's tone of voice
        target_audience: Who the content is for
        key_message: Main message to convey
        occasion: Special occasion/event
        tone: Desired tone (engaging, professional, playful, inspirational)
        max_length: Maximum character length
        include_cta: Include call-to-action
        emoji_level: none, minimal, moderate, heavy
        company_overview: Description of what the company does
        brand_name: Name of the brand
        image_description: Description of the image this caption is for
        
    Returns:
        Dictionary with generated caption
    """
    try:
        client = _get_client()
        
        emoji_map = {
            "none": "Do not use any emojis.",
            "minimal": "Use 1-2 emojis strategically.",
            "moderate": "Use 3-5 emojis to enhance the message.",
            "heavy": "Use emojis liberally throughout."
        }
        emoji_instruction = emoji_map.get(emoji_level, emoji_map["moderate"])
        
        # Build context
        context_parts = []
        if brand_name:
            context_parts.append(f"Brand: {brand_name}")
        if company_overview:
            context_parts.append(f"About: {company_overview}")
        context = "\n".join(context_parts)
        
        prompt = f"""Write a SHORT Instagram caption (50-150 words max):

**Topic:** {topic}
**Brand Voice:** {brand_voice}
**Audience:** {target_audience}
**Message:** {key_message or "Engage and connect"}
**Occasion:** {occasion or "Regular post"}
**Tone:** {tone}
{context}
{f"**Image shows:** {image_description}" if image_description else ""}

**REQUIREMENTS:**
- 50-150 words MAXIMUM
- First line = attention-grabbing HOOK
- 1-2 sentences of value
- {"End with clear CTA" if include_cta else "No CTA needed"}
- {emoji_instruction}
- Easy to copy-paste to Instagram

**FORMAT:**
[Hook line]

[Value content]

[CTA if applicable] 👇

Write ONLY the caption text:"""

        def make_request():
            response = client.models.generate_content(
                model=os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
                contents=prompt
            )
            return response.text.strip()
        
        caption = _retry_with_backoff(make_request)
        
        return {
            "status": "success",
            "caption": caption,
            "character_count": len(caption),
            "topic": topic,
            "tone": tone
        }
    except Exception as e:
        return _format_error(e)


def generate_hashtags(
    topic: str,
    niche: str = "",
    brand_name: str = "",
    trending_context: str = "",
    max_hashtags: int = 15
) -> dict:
    """
    Generate relevant hashtags for an Instagram post.
    
    Args:
        topic: Main topic of the post
        niche: Industry/niche for targeted hashtags
        brand_name: Brand name for branded hashtag
        trending_context: Any trending topics to incorporate
        max_hashtags: Maximum number of hashtags (default 15)
        
    Returns:
        Dictionary with hashtags
    """
    try:
        client = _get_client()
        
        prompt = f"""Generate {max_hashtags} strategic Instagram hashtags for:

**Topic:** {topic}
**Niche:** {niche or "general"}
**Brand:** {brand_name or "N/A"}
{f"**Trending:** {trending_context}" if trending_context else ""}

**Strategy:**
- Mix high-volume (1M+ posts) and niche-specific tags
- Include 1-2 branded hashtags if brand name provided
- Mix different reach levels for discovery
- Relevant to the specific topic

Return ONLY hashtags, one per line, each starting with #:"""

        def make_request():
            response = client.models.generate_content(
                model=os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
                contents=prompt
            )
            return response.text.strip()
        
        result = _retry_with_backoff(make_request)
        
        # Parse and clean hashtags
        hashtags = []
        for line in result.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                # Clean the hashtag
                tag = ''.join(c for c in line.split()[0] if c.isalnum() or c == '#')
                if tag and tag != "#" and len(tag) > 1:
                    hashtags.append(tag)
        
        # Remove duplicates while preserving order
        hashtags = list(dict.fromkeys(hashtags))[:max_hashtags]
        
        return {
            "status": "success",
            "hashtags": hashtags,
            "hashtag_string": " ".join(hashtags),
            "count": len(hashtags),
            "topic": topic
        }
    except Exception as e:
        return _format_error(e)


def improve_caption(
    original_caption: str,
    feedback: str,
    preserve_tone: bool = True
) -> dict:
    """
    Improve an existing caption based on feedback.
    
    Args:
        original_caption: The current caption
        feedback: What changes to make
        preserve_tone: Keep the same overall tone
        
    Returns:
        Dictionary with improved caption
    """
    try:
        client = _get_client()
        
        prompt = f"""Improve this Instagram caption based on feedback:

**Original:**
{original_caption}

**Feedback:**
{feedback}

**Instructions:**
- {"Maintain the same tone and voice" if preserve_tone else "Adjust tone as needed"}
- Keep it engaging and authentic
- Keep it concise (50-150 words)
- Ensure it's suitable for Instagram

Write ONLY the improved caption:"""

        def make_request():
            response = client.models.generate_content(
                model=os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
                contents=prompt
            )
            return response.text.strip()
        
        improved = _retry_with_backoff(make_request)
        
        return {
            "status": "success",
            "improved_caption": improved,
            "character_count": len(improved),
            "changes_applied": feedback
        }
    except Exception as e:
        return _format_error(e)


def create_complete_post(
    topic: str,
    brand_name: str = "",
    brand_voice: str = "professional",
    niche: str = "",
    occasion: str = "",
    include_hashtags: bool = True
) -> dict:
    """
    Create a complete post with caption and hashtags.
    
    Args:
        topic: Main topic/theme
        brand_name: Brand name
        brand_voice: Brand's tone
        niche: Industry/niche
        occasion: Special occasion
        include_hashtags: Whether to include hashtags
        
    Returns:
        Dictionary with complete post content
    """
    # Generate caption
    caption_result = write_caption(
        topic=topic,
        brand_voice=brand_voice,
        occasion=occasion,
        brand_name=brand_name,
        include_cta=True
    )
    
    if caption_result["status"] != "success":
        return caption_result
    
    result = {
        "status": "success",
        "caption": caption_result["caption"],
        "caption_length": caption_result["character_count"]
    }
    
    # Generate hashtags if requested
    if include_hashtags:
        hashtag_result = generate_hashtags(
            topic=topic,
            niche=niche,
            brand_name=brand_name
        )
        
        if hashtag_result["status"] == "success":
            result["hashtags"] = hashtag_result["hashtags"]
            result["hashtag_string"] = hashtag_result["hashtag_string"]
            result["full_post"] = f"{caption_result['caption']}\n\n.\n.\n.\n\n{hashtag_result['hashtag_string']}"
        else:
            result["full_post"] = caption_result["caption"]
    else:
        result["full_post"] = caption_result["caption"]
    
    return result
