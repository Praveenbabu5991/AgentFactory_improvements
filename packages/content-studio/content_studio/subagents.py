"""SubAgent definitions for Content Studio.

Each SubAgent TypedDict replaces a Google ADK LlmAgent.
deepagents handles middleware (planning, filesystem, summarization)
automatically for each subagent.
"""

from deepagents import SubAgent

from agent_factory_core.config.settings import (
    ANIMATION_MODEL,
    CAMPAIGN_MODEL,
    CAPTION_MODEL,
    EDIT_MODEL,
    IDEA_MODEL,
    IMAGE_MODEL,
    WRITER_MODEL,
)

from agent_factory_core.tools.calendar import (
    get_content_calendar_suggestions,
    get_festivals_and_events,
    get_upcoming_events,
    suggest_best_posting_times,
)
from agent_factory_core.tools.content import (
    generate_hashtags,
    improve_caption,
    write_caption,
)
from agent_factory_core.tools.image_gen import (
    edit_post_image,
    extract_brand_colors,
    generate_complete_post,
    generate_post_image,
    generate_product_showcase,
    regenerate_post,
)
from agent_factory_core.tools.video_content import (
    animate_image,
    generate_animated_product_video,
    generate_motion_graphics_video,
    generate_video_from_text,
)
from agent_factory_core.tools.web_search import (
    get_competitor_insights,
    search_trending_topics,
    search_web,
)

from content_studio.prompts.idea_agent import IDEA_AGENT_PROMPT
from content_studio.prompts.writer_agent import WRITER_AGENT_PROMPT
from content_studio.prompts.image_agent import IMAGE_AGENT_PROMPT
from content_studio.prompts.caption_agent import CAPTION_AGENT_PROMPT
from content_studio.prompts.edit_agent import EDIT_AGENT_PROMPT
from content_studio.prompts.animation_agent import ANIMATION_AGENT_PROMPT
from content_studio.prompts.video_agent import VIDEO_AGENT_PROMPT
from content_studio.prompts.campaign_agent import CAMPAIGN_AGENT_PROMPT


IDEA_AGENT: SubAgent = {
    "name": "idea-agent",
    "description": "Brainstorms content ideas based on trends, calendar events, and brand context. Use when user wants content suggestions.",
    "model": f"google_genai:{IDEA_MODEL}",
    "system_prompt": IDEA_AGENT_PROMPT,
    "tools": [
        get_upcoming_events,
        get_festivals_and_events,
        search_trending_topics,
        search_web,

    ],
}

WRITER_AGENT: SubAgent = {
    "name": "writer-agent",
    "description": "Creates detailed visual briefs from selected ideas. Use after user picks an idea to develop it into a full brief.",
    "model": f"google_genai:{WRITER_MODEL}",
    "system_prompt": WRITER_AGENT_PROMPT,
    "tools": [],
}

IMAGE_AGENT: SubAgent = {
    "name": "image-agent",
    "description": "Creates complete social media posts with images, captions, and hashtags. Use when user approves a brief or wants an image generated.",
    "model": f"google_genai:{IMAGE_MODEL}",
    "system_prompt": IMAGE_AGENT_PROMPT,
    "tools": [
        generate_complete_post,
        generate_post_image,
        generate_product_showcase,
        write_caption,
        generate_hashtags,

    ],
}

CAPTION_AGENT: SubAgent = {
    "name": "caption-agent",
    "description": "Writes engaging captions with hashtags for social media content. Use when user wants caption improvements.",
    "model": f"google_genai:{CAPTION_MODEL}",
    "system_prompt": CAPTION_AGENT_PROMPT,
    "tools": [
        write_caption,
        generate_hashtags,
        improve_caption,

    ],
}

EDIT_AGENT: SubAgent = {
    "name": "edit-agent",
    "description": "Edits and regenerates posts based on user feedback. Use when user wants to tweak image, caption, or hashtags.",
    "model": f"google_genai:{EDIT_MODEL}",
    "system_prompt": EDIT_AGENT_PROMPT,
    "tools": [
        edit_post_image,
        regenerate_post,
        improve_caption,
        generate_hashtags,

    ],
}

ANIMATION_AGENT: SubAgent = {
    "name": "animation-agent",
    "description": "Transforms static images into animated videos using Veo 3.1. Use when user wants to animate a post or create video from image.",
    "model": f"google_genai:{ANIMATION_MODEL}",
    "system_prompt": ANIMATION_AGENT_PROMPT,
    "tools": [
        animate_image,
        generate_video_from_text,

    ],
}

VIDEO_AGENT: SubAgent = {
    "name": "video-agent",
    "description": "Creates video content: animated product videos, motion graphics, text-to-video. Use when user wants video/reel content.",
    "model": f"google_genai:{ANIMATION_MODEL}",
    "system_prompt": VIDEO_AGENT_PROMPT,
    "tools": [
        generate_animated_product_video,
        generate_motion_graphics_video,
        generate_video_from_text,
        animate_image,
        write_caption,
        generate_hashtags,

    ],
}

CAMPAIGN_AGENT: SubAgent = {
    "name": "campaign-agent",
    "description": "Plans multi-week content campaigns with week-by-week approval. Use when user wants a content calendar or campaign.",
    "model": f"google_genai:{CAMPAIGN_MODEL}",
    "system_prompt": CAMPAIGN_AGENT_PROMPT,
    "tools": [
        get_upcoming_events,
        get_festivals_and_events,
        get_content_calendar_suggestions,
        search_trending_topics,
        generate_complete_post,
        write_caption,
        generate_hashtags,

    ],
}

# All subagents for content studio
ALL_SUBAGENTS = [
    IDEA_AGENT,
    WRITER_AGENT,
    IMAGE_AGENT,
    CAPTION_AGENT,
    EDIT_AGENT,
    ANIMATION_AGENT,
    VIDEO_AGENT,
    CAMPAIGN_AGENT,
]
