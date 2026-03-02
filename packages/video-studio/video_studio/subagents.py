"""SubAgent definitions for Video Studio.

Each SubAgent TypedDict replaces a Google ADK LlmAgent.
"""

from deepagents import SubAgent

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
from agent_factory_core.tools.video_marketing import (
    animate_marketing_image,
    generate_marketing_motion_graphics,
    generate_marketing_product_video,
    generate_marketing_video_from_text,
    generate_video,
)
from agent_factory_core.tools.web_search import (
    search_trending_topics,
    search_web,
)

from video_studio.prompts.video_agent import VIDEO_AGENT_PROMPT
from video_studio.prompts.animation_agent import ANIMATION_AGENT_PROMPT
from video_studio.prompts.caption_agent import CAPTION_AGENT_PROMPT
from video_studio.prompts.campaign_agent import CAMPAIGN_AGENT_PROMPT


VIDEO_AGENT: SubAgent = {
    "name": "video-agent",
    "description": "Creates Reels/TikTok videos: suggests ideas, generates 8-second videos, provides captions and hashtags.",
    "system_prompt": VIDEO_AGENT_PROMPT,
    "tools": [
        generate_video,
        generate_marketing_product_video,
        generate_marketing_motion_graphics,
        write_caption,
        generate_hashtags,

    ],
}

ANIMATION_AGENT: SubAgent = {
    "name": "animation-agent",
    "description": "Transforms static images into animated videos/cinemagraphs using Veo 3.1 with audio support.",
    "system_prompt": ANIMATION_AGENT_PROMPT,
    "tools": [
        generate_video,
        animate_marketing_image,
        generate_marketing_video_from_text,

    ],
}

CAPTION_AGENT: SubAgent = {
    "name": "caption-agent",
    "description": "Creates scroll-stopping captions and strategic hashtag sets for video content.",
    "system_prompt": CAPTION_AGENT_PROMPT,
    "tools": [
        write_caption,
        generate_hashtags,
        improve_caption,
        search_trending_topics,

    ],
}

CAMPAIGN_AGENT: SubAgent = {
    "name": "campaign-agent",
    "description": "Plans multi-week video content campaigns with week-by-week approval. Generates videos with auto-captions and hashtags.",
    "system_prompt": CAMPAIGN_AGENT_PROMPT,
    "tools": [
        get_content_calendar_suggestions,
        get_upcoming_events,
        get_festivals_and_events,
        suggest_best_posting_times,
        search_trending_topics,
        search_web,
        generate_video,
        generate_marketing_product_video,
        generate_marketing_motion_graphics,
        write_caption,
        generate_hashtags,

    ],
}

ALL_SUBAGENTS = [
    VIDEO_AGENT,
    ANIMATION_AGENT,
    CAPTION_AGENT,
    CAMPAIGN_AGENT,
]
