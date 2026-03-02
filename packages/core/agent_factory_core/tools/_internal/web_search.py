"""
Knowledge and Research Tools using Gemini API.

NOTE: These tools use LLM knowledge, not real-time web search.
They provide AI-generated insights based on training data.
"""

import os
from datetime import datetime
from typing import Any
import time

from google import genai
from dotenv import load_dotenv

load_dotenv()


class APIError(Exception):
    """Custom exception for API errors with user-friendly messages."""
    pass


def _get_client():
    """Get Gemini client with validation."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise APIError("API key not configured. Please set GOOGLE_API_KEY in your environment.")
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
        message = "Service is temporarily busy. Please try again in a few moments."
    elif "api" in error_str and "key" in error_str:
        message = "There's an issue with the API configuration. Please contact support."
    elif "timeout" in error_str:
        message = "The request took too long. Please try a simpler query."
    else:
        message = "Something went wrong. Please try again."
    
    return {"status": "error", "message": message, "technical_details": str(error)}


def get_ai_knowledge(query: str, context: str = "") -> dict:
    """
    Get AI-generated knowledge about a topic.
    
    NOTE: This uses the AI's training knowledge, not real-time web search.
    Results reflect information available at the AI's training cutoff date.
    
    Args:
        query: Topic or question to research
        context: Additional context for the query
        
    Returns:
        Dictionary with AI-generated insights
    """
    try:
        client = _get_client()
        
        prompt = f"""Provide helpful information about this topic based on your knowledge:

Topic: {query}
{f"Context: {context}" if context else ""}
Current Date: {datetime.now().strftime("%B %d, %Y")}

Provide accurate, practical information that would be useful for social media content creation.
If you're uncertain about current/recent information, acknowledge that limitation.

Focus on:
- Key facts and insights
- Actionable takeaways
- Relevant trends (from your training data)"""

        def make_request():
            response = client.models.generate_content(
                model=os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
                contents=prompt
            )
            return response.text.strip()
        
        result = _retry_with_backoff(make_request)
        
        return {
            "status": "success",
            "query": query,
            "insights": result,
            "note": "Information is AI-generated based on training data, not real-time web search.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return _format_error(e)


def search_trending_topics(
    niche: str,
    region: str = "global",
    platform: str = "instagram"
) -> dict:
    """
    Get AI-generated trending topic suggestions for a niche.
    
    NOTE: These are AI predictions based on typical patterns, not real-time trends.
    
    Args:
        niche: Industry or topic niche
        region: Geographic region (global, US, India, etc.)
        platform: Social media platform (instagram, twitter, etc.)
        
    Returns:
        Dictionary with suggested topics and content ideas
    """
    try:
        client = _get_client()
        
        current_month = datetime.now().strftime("%B %Y")
        
        prompt = f"""As a social media strategist, suggest relevant topics for {platform} in the {niche} niche.

Region: {region}
Current Month: {current_month}

Provide:
1. **5 Evergreen Topics** - Topics that consistently perform well in this niche
2. **3 Seasonal Ideas** - Topics relevant for {current_month}
3. **Popular Content Formats** - What works best for this niche on {platform}
4. **10 Relevant Hashtags** - Mix of popular and niche-specific
5. **3 Content Ideas** - Specific, actionable post ideas

Be specific and practical for content creators.

NOTE: Base suggestions on typical patterns and best practices, as real-time trend data isn't available."""

        def make_request():
            response = client.models.generate_content(
                model=os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
                contents=prompt
            )
            return response.text.strip()
        
        result = _retry_with_backoff(make_request)
        
        return {
            "status": "success",
            "niche": niche,
            "region": region,
            "platform": platform,
            "suggestions": result,
            "note": "Suggestions are AI-generated based on typical patterns, not real-time trends.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return _format_error(e)


def get_competitor_insights(
    competitor_handles: str,
    platform: str = "instagram"
) -> dict:
    """
    Get AI-generated insights about competitor content strategies.
    
    NOTE: This provides general strategic advice, not actual competitor analysis.
    For real competitor data, use official platform APIs.
    
    Args:
        competitor_handles: Comma-separated list of competitor account types/categories
        platform: Social media platform
        
    Returns:
        Dictionary with strategic insights
    """
    try:
        client = _get_client()
        
        prompt = f"""As a social media strategist, provide insights for competing in the same space as: {competitor_handles}

Platform: {platform}

Provide general strategic advice:
1. **Content Strategy Patterns** - What typically works in this space
2. **Posting Frequency** - Recommended posting schedule
3. **Engagement Tactics** - Ways to build audience engagement
4. **Content Themes** - Topics that resonate with this audience
5. **Differentiation Opportunities** - How to stand out

This is general strategic advice based on best practices in this industry/niche.
For actual competitor data, official platform analytics tools should be used."""

        def make_request():
            response = client.models.generate_content(
                model=os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
                contents=prompt
            )
            return response.text.strip()
        
        result = _retry_with_backoff(make_request)
        
        return {
            "status": "success",
            "competitors": competitor_handles,
            "platform": platform,
            "insights": result,
            "note": "Strategic advice based on best practices, not actual competitor data."
        }
    except Exception as e:
        return _format_error(e)


# Backward compatibility alias
search_web = get_ai_knowledge
