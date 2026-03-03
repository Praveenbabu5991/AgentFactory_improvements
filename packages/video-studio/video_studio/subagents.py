"""SubAgent definitions for Video Studio.

Each SubAgent TypedDict replaces a Google ADK LlmAgent.
"""

from deepagents import SubAgent

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
)

from video_studio.prompts.video_agent import VIDEO_AGENT_PROMPT
from video_studio.prompts.animation_agent import ANIMATION_AGENT_PROMPT
from video_studio.prompts.caption_agent import CAPTION_AGENT_PROMPT


VIDEO_AGENT: SubAgent = {
    "name": "video-agent",
    "description": "Creates branded story videos: suggests ideas based on brand context, generates 8-second videos with company name and logo, provides captions and hashtags.",
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
    "description": "Transforms static images into animated videos/cinemagraphs using Veo 3.1 with audio support. Maintains company branding.",
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

ALL_SUBAGENTS = [
    VIDEO_AGENT,
    ANIMATION_AGENT,
    CAPTION_AGENT,
]
