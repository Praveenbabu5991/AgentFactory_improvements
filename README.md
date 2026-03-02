# AgentFactory Improvements

Multi-agent social media content creation platform built on LangGraph + deepagents.

## Fixes Applied

### 1. Subagent Empty Response Fix
- **Problem**: `format_response_for_user` tool in subagents caused empty ToolMessage back to orchestrator
- **Fix**: Removed `format_response_for_user` from all subagent tool lists; only orchestrator uses it
- **Files**: `packages/content-studio/content_studio/subagents.py`, `packages/video-studio/video_studio/subagents.py`, and 4 prompt files

### 2. Logo Mandatory in All Generated Images
- **Problem**: Subagent used virtual filesystem `ls` to verify logo path, failed, skipped logo
- **Fix**: Updated image_agent/campaign_agent prompts with mandatory logo instructions and "do NOT use ls to verify"
- **Files**: `packages/content-studio/content_studio/prompts/image_agent.py`, `campaign_agent.py`, `orchestrator.py`

### 3. Gemini INVALID_ARGUMENT Retry Fix
- **Problem**: `_retry_with_backoff()` immediately raised on "invalid" errors; Gemini free tier returns INVALID_ARGUMENT for rate-limits
- **Fix**: Only skip retry for "model not found" and "api key" errors; retry everything else with exponential backoff; added 1s inter-request delay
- **File**: `packages/core/agent_factory_core/tools/_internal/image_gen.py`

### 4. Subagent Recursion Limit Fix
- **Problem**: Subagent graphs had default 25-step LangGraph limit; VideoAgent with write_todos + video + caption + hashtags exceeded it
- **Fix**: Added `.with_config({"recursion_limit": 100})` to subagent creation
- **File**: `deepagents/middleware/subagents.py` (see `deepagents-recursion-limit-fix.patch`)

## Architecture

- **Backend**: LangGraph + deepagents middleware
- **Frontend**: Vanilla JS (Content Studio port 5001, Video Studio port 5002)
- **Image Model**: Gemini (gemini-3-pro-image-preview)
- **Video Model**: Veo 3.1 (veo-3.1-generate-preview)
