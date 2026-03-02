# Agent Factory — Architecture & User Flows

## Table of Contents

- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [System Architecture](#system-architecture)
- [The Middleware Stack](#the-middleware-stack)
- [How DeepAgents Prevents Hallucination](#how-deepagents-prevents-hallucination)
- [User Flow: Single Post Creation](#user-flow-single-post-creation)
- [User Flow: Campaign Creation](#user-flow-campaign-creation)
- [User Flow: Video Generation](#user-flow-video-generation)
- [Data Flow: Chat Request Lifecycle](#data-flow-chat-request-lifecycle)
- [Agent Architecture: Content Studio](#agent-architecture-content-studio)
- [Agent Architecture: Video Studio](#agent-architecture-video-studio)
- [State Management](#state-management)
- [API Reference](#api-reference)
- [Configuration](#configuration)

---

## Overview

**Agent Factory** is a multi-agent AI platform for generating social media content — images, videos, captions, and campaigns. It is built on top of the `deepagents` framework (LangChain/LangGraph) and uses Google's Gemini and Veo models for content generation.

The core idea: a user describes their brand, then chats naturally. An **orchestrator agent** understands what they want and delegates work to **specialist subagents**, each with their own tools, prompts, and focused context window.

```
User → Chat → Orchestrator → SubAgents → Tools → Generated Content
```

---

## Repository Structure

```
agent-factory/
│
├── pyproject.toml                     # UV workspace root
│
├── packages/
│   ├── core/                          # Shared foundation
│   │   └── agent_factory_core/
│   │       ├── factory.py             # create_studio_agent() — wraps deepagents
│   │       ├── state.py               # BrandContext, MediaAsset, StudioAgentState
│   │       ├── config/
│   │       │   └── settings.py        # Models, API keys, storage, rate limits
│   │       ├── api/
│   │       │   ├── server.py          # FastAPI app factory (CORS, rate limiting)
│   │       │   ├── routes.py          # Shared endpoints (upload, brand, assets)
│   │       │   └── streaming.py       # SSE streaming via LangGraph astream_events
│   │       ├── middleware/
│   │       │   ├── brand_context.py   # Injects brand info into every LLM call
│   │       │   └── media_tracker.py   # Auto-catalogs generated images/videos
│   │       ├── tools/
│   │       │   ├── image_gen.py       # Gemini 3 Pro image generation
│   │       │   ├── video_content.py   # Veo 3.1 video generation (social media)
│   │       │   ├── video_marketing.py # Veo 3.1 video generation (marketing)
│   │       │   ├── content.py         # Caption writing, hashtag generation
│   │       │   ├── calendar.py        # Posting times, festivals, content calendar
│   │       │   ├── web_search.py      # Web search, trends, competitor insights
│   │       │   ├── web_scraper.py     # Brand info extraction from URLs
│   │       │   ├── instagram.py       # Instagram profile scraping
│   │       │   └── response_formatter.py  # Formats responses for UI rendering
│   │       └── storage/
│   │           └── local.py           # Local file storage backend
│   │
│   ├── content-studio/                # Social media post creation app
│   │   └── content_studio/
│   │       ├── app.py                 # FastAPI app (port 5000)
│   │       ├── agent.py               # create_content_studio_agent()
│   │       ├── subagents.py           # 8 specialist subagent definitions
│   │       └── prompts/               # System prompts per agent
│   │           ├── orchestrator.py
│   │           ├── idea_agent.py
│   │           ├── writer_agent.py
│   │           ├── image_agent.py
│   │           ├── caption_agent.py
│   │           ├── edit_agent.py
│   │           ├── animation_agent.py
│   │           ├── video_agent.py
│   │           └── campaign_agent.py
│   │
│   └── video-studio/                  # Marketing video generation app
│       └── video_studio/
│           ├── app.py                 # FastAPI app (port 5002)
│           ├── agent.py               # create_video_studio_agent()
│           ├── subagents.py           # 4 specialist subagent definitions
│           └── prompts/               # System prompts per agent
│               ├── orchestrator.py
│               ├── video_agent.py
│               ├── animation_agent.py
│               ├── caption_agent.py
│               └── campaign_agent.py
│
├── frontend/
│   ├── content-studio/                # HTML/CSS/JS UI
│   │   ├── index.html
│   │   └── static/
│   └── video-studio/                  # HTML/CSS/JS UI
│       ├── index.html
│       └── static/
│
├── uploads/                           # User-uploaded logos, references, images
└── generated/                         # AI-generated images and videos
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              BROWSER                                    │
│                                                                         │
│   ┌─────────────────────┐         ┌─────────────────────┐              │
│   │   Content Studio UI │         │   Video Studio UI   │              │
│   │   (port 5000)       │         │   (port 5002)       │              │
│   └────────┬────────────┘         └────────┬────────────┘              │
│            │ POST /chat/stream              │ POST /chat/stream         │
└────────────┼───────────────────────────────┼───────────────────────────┘
             │ SSE (Server-Sent Events)       │
             ▼                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          FASTAPI LAYER                                  │
│                                                                         │
│   ┌───────────────────────────────────────────────────────────┐        │
│   │  create_app() — Shared App Factory                        │        │
│   │  ├── RateLimitMiddleware (60 req/min)                     │        │
│   │  ├── CORS Middleware                                      │        │
│   │  ├── Static Files (/static, /generated, /uploads)         │        │
│   │  └── Common Routes (/health, /upload-logo, /brand, etc.)  │        │
│   └───────────────────────────────────────────────────────────┘        │
│                                                                         │
│   ┌────────────────────────┐    ┌──────────────────────────┐           │
│   │  Content Studio App    │    │  Video Studio App         │           │
│   │  └── /chat/stream      │    │  └── /chat/stream         │           │
│   │      → stream_agent()  │    │      → stream_agent()     │           │
│   └────────┬───────────────┘    └────────┬─────────────────┘           │
└────────────┼────────────────────────────┼──────────────────────────────┘
             │                             │
             ▼                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      AGENT LAYER (LangGraph)                            │
│                                                                         │
│   create_studio_agent() — wraps deepagents' create_deep_agent()        │
│                                                                         │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │              Orchestrator Agent (Gemini 2.5 Flash)             │   │
│   │                                                                │   │
│   │  Tools: search_web, scrape_instagram, get_events,              │   │
│   │         scrape_brand, format_response_for_user                 │   │
│   │                                                                │   │
│   │  Middleware Stack:                                             │   │
│   │  ┌──────────────────────────────────────────────────────┐     │   │
│   │  │ 1. TodoListMiddleware      (planning)                │     │   │
│   │  │ 2. FilesystemMiddleware    (file ops + eviction)     │     │   │
│   │  │ 3. SubAgentMiddleware      (task() tool)             │     │   │
│   │  │ 4. SummarizationMiddleware (context compression)     │     │   │
│   │  │ 5. PromptCachingMiddleware (Anthropic optimization)  │     │   │
│   │  │ 6. PatchToolCallsMiddleware(tool call fixes)         │     │   │
│   │  │ 7. BrandContextMiddleware  (brand injection)         │     │   │
│   │  │ 8. MediaTrackerMiddleware  (asset cataloging)        │     │   │
│   │  └──────────────────────────────────────────────────────┘     │   │
│   │                          │                                     │   │
│   │          task(subagent_type="...", description="...")           │   │
│   │                          │                                     │   │
│   │                          ▼                                     │   │
│   │  ┌────────────────────────────────────────────────────────┐   │   │
│   │  │             SUBAGENTS (Ephemeral Workers)              │   │   │
│   │  │                                                        │   │   │
│   │  │  Content Studio (8):          Video Studio (4):        │   │   │
│   │  │  ├── idea-agent               ├── video-agent          │   │   │
│   │  │  ├── writer-agent             ├── animation-agent      │   │   │
│   │  │  ├── image-agent (Gemini 3)   ├── caption-agent        │   │   │
│   │  │  ├── caption-agent            └── campaign-agent       │   │   │
│   │  │  ├── edit-agent (Gemini 3)                             │   │   │
│   │  │  ├── animation-agent (Veo)    Each subagent has:       │   │   │
│   │  │  ├── video-agent (Veo 3.1)    ├── Own middleware stack │   │   │
│   │  │  └── campaign-agent           ├── Own todo list        │   │   │
│   │  │                               ├── Own filesystem       │   │   │
│   │  │  Each runs in ISOLATED        └── Own summarization    │   │   │
│   │  │  context, returns ONE                                  │   │   │
│   │  │  summary message back.                                 │   │   │
│   │  └────────────────────────────────────────────────────────┘   │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                          │                                              │
│                          ▼                                              │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                      TOOL LAYER                                │   │
│   │                                                                │   │
│   │  Image:    generate_post_image, generate_complete_post,        │   │
│   │            edit_post_image, generate_product_showcase           │   │
│   │  Video:    animate_image, generate_video_from_text,            │   │
│   │            generate_motion_graphics_video                      │   │
│   │  Content:  write_caption, generate_hashtags, improve_caption   │   │
│   │  Research: search_web, search_trending_topics,                 │   │
│   │            scrape_instagram_profile, scrape_brand_from_url     │   │
│   │  Calendar: get_upcoming_events, get_festivals_and_events,      │   │
│   │            suggest_best_posting_times                           │   │
│   │  Format:   format_response_for_user                            │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                          │                                              │
│                          ▼                                              │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                    EXTERNAL APIs                               │   │
│   │  ├── Google Gemini 2.5 Flash  (text/orchestration)             │   │
│   │  ├── Google Gemini 3 Pro      (image generation)               │   │
│   │  └── Google Veo 3.1           (video generation)               │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                   PERSISTENCE                                  │   │
│   │  ├── LangGraph MemorySaver    (in-memory checkpointing)        │   │
│   │  ├── SQLite / Postgres        (session persistence)            │   │
│   │  ├── /uploads/                (user uploads)                   │   │
│   │  └── /generated/              (AI-generated assets)            │   │
│   └────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## The Middleware Stack

Every agent (orchestrator + each subagent) is wrapped in a middleware stack. Middleware intercepts LLM calls and tool calls, adding capabilities transparently.

```
                    Incoming LLM Request
                           │
              ┌────────────┼────────────┐
              │            ▼            │
              │  1. TodoListMiddleware   │  Adds write_todos tool.
              │     │                   │  Injects planning instructions
              │     │                   │  into system prompt.
              │     ▼                   │
              │  2. MemoryMiddleware     │  Loads AGENTS.md files into
              │     │                   │  system prompt. Enables the agent
              │     │                   │  to learn from past sessions.
              │     ▼                   │
              │  3. FilesystemMiddleware │  Adds ls, read_file, write_file,
              │     │                   │  edit_file, glob, grep tools.
              │     │                   │  Evicts large tool results to files.
              │     ▼                   │
              │  4. SubAgentMiddleware   │  Adds task() tool. Builds and
              │     │                   │  manages subagent lifecycle.
              │     │                   │  Injects subagent docs into prompt.
              │     ▼                   │
              │  5. SummarizationMW     │  Auto-compresses old messages
              │     │                   │  at 85% context capacity.
              │     │                   │  Saves full history to backend.
              │     ▼                   │
              │  6. PromptCachingMW     │  Anthropic-specific optimization.
              │     │                   │  Ignored for non-Anthropic models.
              │     ▼                   │
              │  7. PatchToolCallsMW    │  Fixes malformed tool calls from
              │     │                   │  the LLM before execution.
              │     ▼                   │
              │  8. BrandContextMW      │  Reads brand from state, appends
              │     │                   │  to system prompt automatically.
              │     ▼                   │
              │  9. MediaTrackerMW      │  Intercepts image/video tool
              │     │                   │  results, catalogs assets in state.
              │     ▼                   │
              │   Actual LLM API Call   │
              │            │            │
              └────────────┼────────────┘
                           ▼
                    LLM Response
```

### What Each Middleware Does

| # | Middleware | Intercepts | Purpose |
|---|-----------|-----------|---------|
| 1 | **TodoListMiddleware** | Model calls | Adds `write_todos` tool for task planning. Prevents parallel todo writes. |
| 2 | **MemoryMiddleware** | Model calls | Loads `AGENTS.md` files as persistent context. Agent can update memory via `edit_file`. |
| 3 | **FilesystemMiddleware** | Model calls + Tool calls | Adds 7 file tools. Evicts large tool results (>20k tokens) to files to prevent context overflow. |
| 4 | **SubAgentMiddleware** | Model calls | Adds `task()` tool for spawning isolated subagents. Injects subagent descriptions into prompt. |
| 5 | **SummarizationMiddleware** | Model calls | At 85% context capacity: saves old messages to file, replaces with summary, keeps recent 10%. |
| 6 | **BrandContextMiddleware** | Model calls | Reads `state.brand` and appends brand info (name, colors, tone, logo) to every system prompt. |
| 7 | **MediaTrackerMiddleware** | Tool calls | After image/video tools succeed, extracts asset info and appends to `state.media_assets`. |

---

## How DeepAgents Prevents Hallucination

The system uses 5 layered strategies to keep the LLM grounded and accurate:

### Strategy 1: Structured Planning (TodoListMiddleware)

**Problem:** LLMs lose track of multi-step tasks, skip steps, or forget where they are.

**Solution:** The agent creates a checklist before doing complex work.

```
User: "Create a 4-week campaign for my brand"

Agent internally calls write_todos():
┌──────────────────────────────────────────────┐
│  TODO LIST                                    │
│  ✅ completed:   Understand brand context     │
│  🔄 in_progress: Plan Week 1 content         │
│  ⏳ pending:     Plan Week 2 content          │
│  ⏳ pending:     Plan Week 3 content          │
│  ⏳ pending:     Plan Week 4 content          │
│  ⏳ pending:     Generate approved posts      │
└──────────────────────────────────────────────┘
```

**Rules enforced:**
- Only one `write_todos` call per LLM turn (parallel calls are rejected with errors)
- Agent must mark items `in_progress` before starting work
- Agent must mark items `completed` immediately after finishing (no batching)
- Todos can be revised as new information emerges
- Skipped for trivial tasks (<3 steps)

**Why it prevents hallucination:** Forces step-by-step reasoning. The visible checklist makes the agent accountable — it can't claim to have done something it hasn't checked off.

---

### Strategy 2: Grounded File Operations (FilesystemMiddleware)

**Problem:** LLMs fabricate file contents, make up paths, or generate output without checking what exists.

**Solution:** Strict read-before-write enforcement and exact-match editing.

```
WRONG (hallucination-prone):
  Agent: "I'll edit the config file to add the new setting"
  → Makes up what the file contains
  → Writes incorrect edit

RIGHT (grounded):
  Agent: read_file("/config.yaml")         → Sees actual contents
  Agent: edit_file(old="key: old", new="key: new")  → Exact match required
  → If old_string doesn't match: ERROR (agent must re-read)
```

**Additional safeguards:**
- **Large result eviction:** Tool outputs >20,000 tokens are saved to a file. The agent gets a truncated preview + file path, preventing context overflow.
- **Path validation:** All paths must be absolute and are validated before operations.
- **Truncation for large files:** `read_file` returns max 100 lines by default with pagination support.

**Why it prevents hallucination:** The agent can't make up file contents. Edit operations require an exact string match against real file content — wrong assumptions immediately produce errors that force the agent to re-read and correct itself.

---

### Strategy 3: Isolated Subagents (SubAgentMiddleware)

**Problem:** When one agent tries to do everything, its context window fills with noise, leading to confusion, forgotten details, and cross-contamination between tasks.

**Solution:** Delegate tasks to ephemeral subagents that run in isolated context windows.

```
┌──────────────────────────────────────────────────────────┐
│  ORCHESTRATOR (clean context)                             │
│                                                           │
│  Sees: user messages + concise subagent summaries         │
│  Does NOT see: intermediate tool calls, reasoning chains  │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  idea-agent   │  │ image-agent  │  │ caption-agent│   │
│  │              │  │              │  │              │   │
│  │ Own context  │  │ Own context  │  │ Own context  │   │
│  │ Own todos    │  │ Own todos    │  │ Own todos    │   │
│  │ Own files    │  │ Own files    │  │ Own files    │   │
│  │ Own summary  │  │ Own summary  │  │ Own summary  │   │
│  │              │  │              │  │              │   │
│  │ Returns ONE  │  │ Returns ONE  │  │ Returns ONE  │   │
│  │ message back │  │ message back │  │ message back │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                           │
│  Can run in PARALLEL — orchestrator sends multiple        │
│  task() calls in a single response                        │
└──────────────────────────────────────────────────────────┘
```

**Key properties:**
- Each subagent is **ephemeral** — created for one task, destroyed after
- Subagents get their **own middleware stack** (todos, filesystem, summarization)
- They **can't see** each other's work — only the orchestrator aggregates results
- State keys like `todos` and `structured_response` are **excluded** from being passed to subagents
- The orchestrator receives a **concise summary**, not hundreds of intermediate tool calls

**Why it prevents hallucination:** Each agent operates in a focused, narrow context. An idea agent can't accidentally invoke image tools. The orchestrator's context stays clean — it only sees summaries, not the full reasoning of every specialist. This prevents context pollution where unrelated details confuse the LLM.

---

### Strategy 4: Intelligent Context Compression (SummarizationMiddleware)

**Problem:** Long conversations overflow the context window. When the context is full, the model either crashes or silently loses old information and starts making things up.

**Solution:** Automatic summarization with full history preservation.

```
BEFORE summarization (conversation at 85% capacity):
┌─────────────────────────────────────────────────────────┐
│  Turn 1:  User sets up brand "Hylancer"                 │
│  Turn 2:  Agent acknowledges brand setup                │
│  Turn 3:  User asks for Valentine's Day ideas           │ ◄─ OLD
│  Turn 4:  idea-agent returns 3 concepts                 │    (will be
│  Turn 5:  User picks idea #2                            │     summarized)
│  Turn 6:  writer-agent creates brief                    │
│  ...                                                    │
│  Turn 45: User asks for campaign Week 3                 │
│  Turn 46: Agent generates Week 3 posts                  │ ◄─ RECENT
│  Turn 47: User approves Week 3                          │    (kept intact)
│  Turn 48: Agent asks about Week 4                       │
└─────────────────────────────────────────────────────────┘

STEP 1 — Save full history to backend:
  → /conversation_history/thread_abc123.md
  (Nothing is permanently lost)

STEP 2 — Replace old messages with summary:
┌─────────────────────────────────────────────────────────┐
│  "You are in the middle of a conversation that has      │
│   been summarized. Full history saved to                │
│   /conversation_history/thread_abc123.md                │
│                                                         │
│   Summary: User set up brand Hylancer (tech startup,    │
│   yellow/dark colors). Created Valentine's Day post.    │
│   Completed Weeks 1-3 of campaign. Currently working    │
│   on Week 4."                                           │
│                                                         │
│  Turn 46: Agent generates Week 3 posts                  │ ◄─ Recent
│  Turn 47: User approves Week 3                          │    messages
│  Turn 48: Agent asks about Week 4                       │    preserved
└─────────────────────────────────────────────────────────┘
```

**Configuration:**
- **Trigger:** At 85% of context window capacity (fraction-based)
- **Keep:** Most recent 10% of messages (intact, not summarized)
- **Arg truncation:** Old `write_file`/`edit_file` arguments are truncated to `"...(argument truncated)"` to save tokens
- **Manual compaction:** Agents can call `compact_conversation` tool proactively
- **Fallback:** If auto-summarization doesn't trigger but context overflows, summarization runs as a fallback

**Why it prevents hallucination:** The agent never silently forgets. Old context is summarized (not deleted), and the summary tells the agent where to find the full history if needed. Without this, the LLM would lose information and fill the gaps with fabricated content.

---

### Strategy 5: Always-On Brand Context (BrandContextMiddleware)

**Problem:** In a multi-agent system, the user tells the orchestrator about their brand, but subagents would never see that information. Agents might generate content with wrong colors, tone, or brand identity.

**Solution:** Brand context is automatically injected into every single LLM call.

```
Every LLM call (orchestrator AND every subagent) gets this appended:

┌─────────────────────────────────────────────────────────┐
│  ## Brand Context (use this for ALL content generation)  │
│  - Brand: Hylancer (Technology)                          │
│  - Tone: creative                                        │
│  - Colors: #FFD700, #1A1A2E, #16213E                    │
│  - Logo: Available at /uploads/logo_abc.png              │
│  - Overview: Freelance tech platform                     │
│  - Target Audience: Tech professionals, freelancers      │
│  - Products/Services: Freelance marketplace              │
│                                                          │
│  USER_IMAGES_FOR_POST:                                   │
│    - [PRODUCT_FOCUS] /uploads/user_images/product.png    │
│    USER_IMAGES_PATHS: /uploads/user_images/product.png   │
└─────────────────────────────────────────────────────────┘
```

**How it works:**
1. User uploads logo → colors extracted via `colorthief`
2. User provides brand info → stored in `state.brand`
3. `BrandContextMiddleware.wrap_model_call()` reads `state.brand`
4. Builds a formatted brand section
5. Appends to the system prompt of **every** LLM call
6. Even after summarization, brand context is re-injected fresh

**Why it prevents hallucination:** No agent can "forget" the brand. It's injected at the system prompt level every time. The image agent always knows to use `#FFD700` yellow, the caption agent always knows to use a "creative" tone.

---

## User Flow: Single Post Creation

```
┌────────┐                    ┌─────────────┐              ┌──────────────┐
│  USER  │                    │ ORCHESTRATOR │              │  SUBAGENTS   │
└───┬────┘                    └──────┬───────┘              └──────┬───────┘
    │                                │                             │
    │  "Hi! I run Hylancer, a        │                             │
    │   tech startup"                │                             │
    │ ──────────────────────────────>│                             │
    │                                │                             │
    │  Uploads logo                  │                             │
    │ ──(POST /upload-logo)────────> │                             │
    │  <── {colors: [#FFD700,...]}   │                             │
    │                                │                             │
    │  Brand config + message        │                             │
    │ ──(POST /chat/stream)────────> │                             │
    │                                │  state.brand = {            │
    │                                │    name: "Hylancer",        │
    │                                │    colors: ["#FFD700",...], │
    │                                │    tone: "creative"         │
    │                                │  }                          │
    │                                │                             │
    │  <── SSE: "What would you      │                             │
    │       like to create?"         │                             │
    │       [Single Post] [Campaign] │                             │
    │       [Carousel] [Video]       │                             │
    │                                │                             │
    │  "Single Post"                 │                             │
    │ ──────────────────────────────>│                             │
    │                                │                             │
    │  <── "Do you have an idea or   │                             │
    │       want suggestions?"       │                             │
    │                                │                             │
    │  "suggest"                     │                             │
    │ ──────────────────────────────>│                             │
    │                                │  task(idea-agent,           │
    │                                │    "Brainstorm ideas        │
    │                                │     for Hylancer...")       │
    │                                │ ───────────────────────────>│
    │                                │                             │
    │                                │              idea-agent:    │
    │                                │              - search_web() │
    │                                │              - get_events() │
    │                                │              - write_todos()│
    │                                │              - Returns 3    │
    │                                │                ideas        │
    │                                │ <───────────────────────────│
    │                                │                             │
    │  <── SSE: "Here are 3 ideas:   │                             │
    │       1. Valentine's promo     │                             │
    │       2. Tech tip series       │                             │
    │       3. Team spotlight"       │                             │
    │                                │                             │
    │  "2" (picks Tech tip)          │                             │
    │ ──────────────────────────────>│                             │
    │                                │  task(writer-agent,         │
    │                                │    "Create brief for        │
    │                                │     tech tip post...")      │
    │                                │ ───────────────────────────>│
    │                                │              writer-agent:  │
    │                                │              Creates visual │
    │                                │              brief with     │
    │                                │              layout, colors,│
    │                                │              text elements  │
    │                                │ <───────────────────────────│
    │                                │                             │
    │  <── SSE: "Here's the brief:   │                             │
    │       [visual concept, layout, │                             │
    │        color scheme, text]     │                             │
    │       Approve? [Yes] [Tweak]"  │                             │
    │                                │                             │
    │  "yes"                         │                             │
    │ ──────────────────────────────>│                             │
    │                                │  task(image-agent,          │
    │                                │    "Generate post from      │
    │                                │     approved brief...")     │
    │                                │ ───────────────────────────>│
    │                                │                             │
    │                                │            image-agent:     │
    │                                │            generate_        │
    │                                │             complete_post() │
    │                                │            → Gemini 3 Pro   │
    │                                │            → image saved to │
    │                                │              /generated/    │
    │                                │            write_caption()  │
    │                                │            generate_        │
    │                                │             hashtags()      │
    │                                │ <───────────────────────────│
    │                                │                             │
    │                                │  MediaTrackerMW catalogs:   │
    │                                │  state.media_assets += [{   │
    │                                │    asset_type: "image",     │
    │                                │    path: "/generated/...",  │
    │                                │    ...                      │
    │                                │  }]                         │
    │                                │                             │
    │  <── SSE: "Here's your post!   │                             │
    │       📸 /generated/post.png   │                             │
    │       📝 Caption: ...          │                             │
    │       #️⃣ #tech #innovation    │                             │
    │       [Perfect] [Edit] [Video]"│                             │
    │                                │                             │
    │  "animate it!"                 │                             │
    │ ──────────────────────────────>│                             │
    │                                │  task(animation-agent,      │
    │                                │    "Animate the image at    │
    │                                │     /generated/post.png")   │
    │                                │ ───────────────────────────>│
    │                                │                             │
    │                                │          animation-agent:   │
    │                                │          animate_image()    │
    │                                │          → Veo 3.1          │
    │                                │          → 8-sec video      │
    │                                │          → /generated/      │
    │                                │             video.mp4       │
    │                                │ <───────────────────────────│
    │                                │                             │
    │  <── SSE: "Here's your video!  │                             │
    │       🎬 /generated/video.mp4  │                             │
    │       [Perfect] [Edit] [New]"  │                             │
    │                                │                             │
    │  "perfect!"                    │                             │
    │ ──────────────────────────────>│                             │
    │                                │                             │
    │  <── "Glad you love it! 🎉"    │                             │
    │                                │                             │
```

---

## User Flow: Campaign Creation

```
┌────────┐              ┌─────────────┐              ┌──────────────────┐
│  USER  │              │ ORCHESTRATOR │              │  campaign-agent  │
└───┬────┘              └──────┬───────┘              └────────┬─────────┘
    │                          │                               │
    │  "I need content for     │                               │
    │   the next 3 weeks"      │                               │
    │ ────────────────────────>│                               │
    │                          │                               │
    │                          │  Intent: CAMPAIGN             │
    │                          │  Delegate IMMEDIATELY         │
    │                          │                               │
    │                          │  task(campaign-agent,          │
    │                          │    "Create 3-week campaign     │
    │                          │     for Hylancer...")          │
    │                          │ ─────────────────────────────>│
    │                          │                               │
    │                          │               campaign-agent:  │
    │                          │               write_todos([    │
    │                          │                 "Plan Week 1", │
    │                          │                 "Plan Week 2", │
    │                          │                 "Plan Week 3"  │
    │                          │               ])               │
    │                          │                               │
    │                          │               get_upcoming_    │
    │                          │                events()        │
    │                          │               get_festivals_   │
    │                          │                and_events()    │
    │                          │               search_trending_ │
    │                          │                topics()        │
    │                          │                               │
    │                          │               Plans all 3      │
    │                          │               weeks with       │
    │                          │               post concepts    │
    │                          │ <─────────────────────────────│
    │                          │                               │
    │  <── "Here's your 3-week │                               │
    │       campaign plan:     │                               │
    │       Week 1: [3 posts]  │                               │
    │       Week 2: [3 posts]  │                               │
    │       Week 3: [3 posts]  │                               │
    │       Approve Week 1?    │                               │
    │       [Yes] [Tweak]"     │                               │
    │                          │                               │
    │  "yes, generate week 1"  │                               │
    │ ────────────────────────>│                               │
    │                          │  task(campaign-agent,          │
    │                          │    "Generate Week 1 posts...") │
    │                          │ ─────────────────────────────>│
    │                          │                               │
    │                          │   FOR each post in Week 1:    │
    │                          │     generate_complete_post()   │
    │                          │     write_caption()            │
    │                          │     generate_hashtags()        │
    │                          │   END FOR                      │
    │                          │                               │
    │                          │ <─────────────────────────────│
    │                          │                               │
    │  <── "Week 1 generated!  │                               │
    │       Post 1: 📸 ...     │                               │
    │       Post 2: 📸 ...     │                               │
    │       Post 3: 📸 ...     │                               │
    │       Ready for Week 2?" │                               │
    │                          │                               │
    │  ... (repeat for weeks 2 & 3)                            │
```

---

## User Flow: Video Generation

```
┌────────┐              ┌─────────────┐              ┌──────────────┐
│  USER  │              │ ORCHESTRATOR │              │ video-agent   │
└───┬────┘              └──────┬───────┘              └──────┬───────┘
    │                          │                             │
    │  "Create a product       │                             │
    │   showcase video"        │                             │
    │ ────────────────────────>│                             │
    │                          │                             │
    │                          │  task(video-agent,           │
    │                          │    "Create product video     │
    │                          │     for Hylancer. Product    │
    │                          │     image at /uploads/       │
    │                          │     product.png...")         │
    │                          │ ───────────────────────────>│
    │                          │                             │
    │                          │           video-agent:       │
    │                          │           generate_animated_ │
    │                          │            product_video()   │
    │                          │           → Veo 3.1 API      │
    │                          │           → 8-sec video      │
    │                          │           write_caption()    │
    │                          │           generate_hashtags()│
    │                          │ <───────────────────────────│
    │                          │                             │
    │  <── "Here's your video! │                             │
    │       🎬 /generated/...  │                             │
    │       📝 Caption: ...    │                             │
    │       #️⃣ Hashtags: ..."  │                             │
```

---

## Data Flow: Chat Request Lifecycle

```
1. FRONTEND sends POST /chat/stream
   ┌──────────────────────────────────────────┐
   │ ChatRequest {                             │
   │   message: "Create a Valentine's post",  │
   │   session_id: "abc-123",                 │
   │   user_id: "default_user",               │
   │   attachments: [                          │
   │     { type: "logo",                       │
   │       full_path: "/uploads/logo.png",     │
   │       colors: { dominant: "#FFD700",      │
   │                 palette: [...] }          │
   │     }                                     │
   │   ]                                       │
   │ }                                         │
   └──────────────────────────────────────────┘

2. APP.PY processes the request:
   - build_message_text(request)
     → Appends attachment context to message
     → "[BRAND ASSETS PROVIDED] LOGO_PATH: /uploads/logo.png BRAND_COLORS: #FFD700"
   - Extracts brand config from attachments into input_data["brand"]

3. STREAMING begins:
   stream_agent_response(agent, input_data, config, session_id)
   - agent.astream_events(input_data, config)
   - Yields SSE events as they happen

4. SSE EVENT TYPES sent to frontend:
   ┌─────────────────────────────────────────────────────────┐
   │  data: {"type": "session", "session_id": "abc-123"}    │
   │  data: {"type": "text", "content": "Here are "}        │
   │  data: {"type": "text", "content": "3 ideas..."}       │
   │  data: {"type": "tool_start", "tool": "task"}          │
   │  data: {"type": "tool_end", "tool": "task",            │
   │         "content": "...result..."}                      │
   │  data: {"type": "text", "content": "Which do you..."}  │
   │  data: {"type": "done"}                                 │
   └─────────────────────────────────────────────────────────┘

5. FRONTEND renders tokens in real-time as they arrive.
```

---

## Agent Architecture: Content Studio

```
                    ┌─────────────────────────────────────┐
                    │         ORCHESTRATOR                  │
                    │         (Gemini 2.5 Flash)           │
                    │                                       │
                    │  Tools: search_web, scrape_instagram, │
                    │  get_events, scrape_brand,            │
                    │  format_response_for_user             │
                    └──────────────┬────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │     task() tool calls        │
                    ▼              ▼               ▼
        ┌───────────────┐ ┌──────────────┐ ┌──────────────┐
        │  idea-agent    │ │ writer-agent │ │ image-agent  │
        │ (Flash)        │ │ (Flash)      │ │ (Gemini 3)   │
        │                │ │              │ │              │
        │ search_web     │ │ format_      │ │ generate_    │
        │ get_events     │ │  response    │ │  complete_   │
        │ get_festivals  │ │              │ │  post        │
        │ search_trends  │ │              │ │ generate_    │
        │ format_resp    │ │              │ │  post_image  │
        └───────────────┘ └──────────────┘ │ write_caption│
                                           │ gen_hashtags │
        ┌───────────────┐ ┌──────────────┐ │ format_resp  │
        │ caption-agent  │ │  edit-agent  │ └──────────────┘
        │ (Flash)        │ │ (Gemini 3)   │
        │                │ │              │ ┌──────────────┐
        │ write_caption  │ │ edit_post_   │ │ animation-   │
        │ gen_hashtags   │ │  image       │ │  agent       │
        │ improve_       │ │ regenerate_  │ │ (Veo 3.1)    │
        │  caption       │ │  post        │ │              │
        │ format_resp    │ │ improve_cap  │ │ animate_     │
        └───────────────┘ │ gen_hashtags │ │  image       │
                          │ format_resp  │ │ gen_video_   │
                          └──────────────┘ │  from_text   │
                                           │ format_resp  │
        ┌───────────────┐                  └──────────────┘
        │ video-agent    │
        │ (Veo 3.1)      │ ┌──────────────┐
        │                │ │ campaign-    │
        │ gen_animated_  │ │  agent       │
        │  product_video │ │ (Flash)      │
        │ gen_motion_    │ │              │
        │  graphics      │ │ get_events   │
        │ gen_video_     │ │ get_festivals│
        │  from_text     │ │ get_calendar │
        │ animate_image  │ │ search_trends│
        │ write_caption  │ │ gen_complete │
        │ gen_hashtags   │ │  _post       │
        │ format_resp    │ │ write_caption│
        └───────────────┘ │ gen_hashtags │
                          │ format_resp  │
                          └──────────────┘
```

---

## Agent Architecture: Video Studio

```
                    ┌─────────────────────────────────────┐
                    │         ORCHESTRATOR                  │
                    │         (Gemini 2.5 Flash)           │
                    │                                       │
                    │  Tools: search_web, search_trending,  │
                    │  get_competitor_insights,              │
                    │  format_response_for_user             │
                    └──────────────┬────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼               ▼
        ┌───────────────┐ ┌──────────────┐ ┌──────────────┐
        │  video-agent   │ │ animation-   │ │ caption-     │
        │                │ │  agent       │ │  agent       │
        │ generate_video │ │              │ │              │
        │ gen_product_   │ │ generate_    │ │ write_caption│
        │  video         │ │  video       │ │ gen_hashtags │
        │ gen_motion_    │ │ animate_     │ │ improve_cap  │
        │  graphics      │ │  marketing_  │ │ search_trends│
        │ write_caption  │ │  image       │ │ format_resp  │
        │ gen_hashtags   │ │ gen_video_   │ └──────────────┘
        │ format_resp    │ │  from_text   │
        └───────────────┘ │ format_resp  │ ┌──────────────┐
                          └──────────────┘ │ campaign-    │
                                           │  agent       │
                                           │              │
                                           │ All calendar │
                                           │ All search   │
                                           │ All video    │
                                           │ All content  │
                                           │ format_resp  │
                                           └──────────────┘
```

---

## State Management

```
┌─────────────────────────────────────────────────────────────────┐
│                     LangGraph Agent State                        │
│                                                                  │
│  Base (from langchain create_agent):                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  messages: list[AnyMessage]       ← conversation history   │ │
│  │  structured_response: Any         ← optional structured out│ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  From TodoListMiddleware:                                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  todos: list[Todo]                ← task checklist         │ │
│  │    Todo = { content: str, status: "pending"|"in_progress"  │ │
│  │                                   |"completed" }           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  From FilesystemMiddleware:                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  files: dict[str, FileData]       ← virtual filesystem     │ │
│  │    FileData = { content, created_at, modified_at }         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  From SummarizationMiddleware:                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  _summarization_event: {          ← private, tracks cuts   │ │
│  │    cutoff_index, summary_message, file_path                │ │
│  │  }                                                         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  From agent-factory (StudioAgentState):                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  brand: BrandContext              ← brand identity          │ │
│  │    { name, industry, tone, colors, logo_path,              │ │
│  │      target_audience, products_services, user_images,      │ │
│  │      marketing_goals, brand_messaging, ... }               │ │
│  │                                                            │ │
│  │  media_assets: list[MediaAsset]   ← generated assets       │ │
│  │    { asset_id, asset_type, path, url, thread_id,           │ │
│  │      created_at, metadata: { prompt, model, caption, ... }}│ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Persistence:                                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  MemorySaver (in-memory)     ← default, dev mode           │ │
│  │  AsyncSqliteSaver            ← SQLite persistence          │ │
│  │  AsyncPostgresSaver          ← production persistence      │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Reference

### Shared Endpoints (all studios)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/` | Serves the frontend HTML |
| `POST` | `/upload-logo` | Upload logo, extract brand colors |
| `POST` | `/upload-reference` | Upload style reference image |
| `POST` | `/upload-user-image` | Upload image for use in posts |
| `DELETE` | `/delete-user-image/{session}/{id}` | Delete uploaded image |
| `GET` | `/generated-images` | List generated assets (paginated) |
| `POST` | `/brand` | Set brand configuration |
| `GET` | `/sessions/{id}/assets` | List session's generated assets |
| `GET` | `/sessions/{id}/brand` | Get session's brand context |

### Studio-Specific Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat/stream` | SSE-streamed chat (main interaction point) |

### Chat Request Schema

```json
{
  "message": "Create a Valentine's Day post",
  "user_id": "default_user",
  "session_id": "optional-uuid",
  "attachments": [
    {
      "type": "logo",
      "full_path": "/uploads/logo.png",
      "colors": { "dominant": "#FFD700", "palette": ["#1A1A2E"] }
    },
    {
      "type": "user_images",
      "images": [
        { "path": "/uploads/product.png", "usage_intent": "product_focus" }
      ]
    }
  ],
  "last_generated_image": "/generated/post_xxx.png"
}
```

### SSE Event Types

| Event Type | Payload | When |
|-----------|---------|------|
| `session` | `{ session_id }` | Connection established |
| `text` | `{ content }` | LLM token streamed |
| `tool_start` | `{ tool, tool_call_id }` | Tool invocation begins |
| `tool_end` | `{ tool, content }` | Tool returns result |
| `error` | `{ message }` | Error occurred |
| `done` | `{}` | Stream complete |

---

## Configuration

All settings are via environment variables (`.env` file supported):

### Models

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_MODEL` | `gemini-2.5-flash` | Base LLM for text/orchestration |
| `IMAGE_MODEL` | `gemini-3-pro-image-preview` | Image generation model |
| `VIDEO_MODEL` | `veo-3.1-generate-preview` | Video generation model |
| `ORCHESTRATOR_MODEL` | `DEFAULT_MODEL` | Override for orchestrator |
| `IDEA_MODEL` | `DEFAULT_MODEL` | Override for idea agent |
| `WRITER_MODEL` | `DEFAULT_MODEL` | Override for writer agent |
| `EDIT_MODEL` | `IMAGE_MODEL` | Override for edit agent |
| `CAMPAIGN_MODEL` | `DEFAULT_MODEL` | Override for campaign agent |
| `CAPTION_MODEL` | `DEFAULT_MODEL` | Override for caption agent |

### Server

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `DEBUG` | `true` | Enable hot reload |
| `ALLOWED_ORIGINS` | `*` | CORS allowed origins |
| `RATE_LIMIT_REQUESTS` | `60` | Requests per minute per IP |
| `CONTENT_STUDIO_PORT` | `5000` | Content Studio port |
| `VIDEO_STUDIO_PORT` | `5002` | Video Studio port |

### Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `STORAGE_BACKEND` | `local` | `local` or cloud provider |
| `DATABASE_BACKEND` | `sqlite` | `sqlite` or `postgres` |
| `DATABASE_URL` | `sqlite:///data/studio.db` | Database connection string |
| `MAX_UPLOAD_SIZE_MB` | `10` | Max upload file size |
| `MAX_IMAGE_DIMENSION` | `4096` | Max image width/height in pixels |

### API Keys

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Google AI / Gemini API key |
| `LANGSMITH_API_KEY` | LangSmith tracing (optional) |
| `LANGSMITH_TRACING` | Enable tracing (`true`/`false`) |
| `LANGSMITH_PROJECT` | LangSmith project name |

---

## Summary: The Anti-Hallucination Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  1. PLAN          TodoListMiddleware                             │
│     ─────────     Forces step-by-step thinking.                 │
│                   Agent writes a checklist before complex work. │
│                   Can't skip steps or lose track.               │
│                                                                  │
│  2. GROUND        FilesystemMiddleware                           │
│     ─────────     Must read before editing.                     │
│                   Exact-match edits (wrong = error).            │
│                   Large results saved to files.                  │
│                                                                  │
│  3. ISOLATE       SubAgentMiddleware                             │
│     ─────────     Each specialist in its own context bubble.    │
│                   Can't contaminate each other.                  │
│                   Orchestrator sees summaries, not noise.        │
│                                                                  │
│  4. COMPRESS      SummarizationMiddleware                        │
│     ─────────     Auto-summarizes at 85% capacity.              │
│                   Full history saved to file (never lost).       │
│                   Summary + pointer = recoverable context.       │
│                                                                  │
│  5. INJECT        BrandContextMiddleware                         │
│     ─────────     Brand info in every LLM call's system prompt. │
│                   Impossible to forget brand, colors, tone.     │
│                   Works across orchestrator + all subagents.     │
│                                                                  │
│  Together: Structure + Grounding + Isolation + Memory +          │
│            Always-On Context = Reliable, non-hallucinating       │
│            multi-agent content generation.                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
