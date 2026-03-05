"""Video Studio FastAPI application."""

from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from agent_factory_core.api.routes import ChatRequest, build_message_text, register_asset_routes
from agent_factory_core.api.server import create_app
from agent_factory_core.api.streaming import stream_agent_response

from langgraph.checkpoint.memory import MemorySaver

from video_studio.agent import create_video_studio_agent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent (lazy init - avoids crash when API key is missing at import time)
# ---------------------------------------------------------------------------
_agent = None
_checkpointer = MemorySaver()


def _get_agent():
    global _agent
    if _agent is None:
        _agent = create_video_studio_agent(checkpointer=_checkpointer)
    return _agent


# ---------------------------------------------------------------------------
# Create FastAPI app
# ---------------------------------------------------------------------------
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "video-studio"
STATIC_DIR = FRONTEND_DIR / "static"
TEMPLATES_DIR = FRONTEND_DIR

app = create_app(
    title="Video Studio Agent",
    description="Multi-agent marketing video generation platform",
    static_dir=STATIC_DIR if STATIC_DIR.exists() else None,
)

if TEMPLATES_DIR.exists():
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})


# ---------------------------------------------------------------------------
# Chat endpoints
# ---------------------------------------------------------------------------

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat response as SSE events."""
    agent = _get_agent()
    session_id = request.session_id or str(uuid.uuid4())
    message_text = build_message_text(request)

    config = {"configurable": {"thread_id": session_id}, "recursion_limit": 1000}
    input_data = {
        "messages": [{"role": "user", "content": message_text}],
    }

    # Build brand context from attachments (frontend sends individual types)
    brand = {}
    if request.attachments:
        for att in request.attachments:
            att_type = att.get("type", "")
            if att_type == "brand_config":
                brand = att.get("config", {})
                break
            elif att_type == "logo":
                brand["logo_path"] = att.get("full_path", att.get("path", ""))
                colors = att.get("colors", {})
                if colors:
                    brand["colors"] = [colors.get("dominant", "")]
                    brand["colors"].extend(colors.get("palette", []))
            elif att_type == "company_overview":
                brand["overview"] = att.get("content", "")
            elif att_type == "target_audience":
                brand["target_audience"] = att.get("content", "")
            elif att_type == "products_services":
                brand["products_services"] = att.get("content", "")
            elif att_type == "user_images":
                brand["user_images"] = att.get("images", [])

    if brand and not brand.get("name"):
        text = request.message
        name_match = re.search(r"Company:\s*(.+?)(?:\n|$)", text)
        if name_match:
            brand["name"] = name_match.group(1).strip()
        industry_match = re.search(r"Industry:\s*(.+?)(?:\n|$)", text)
        if industry_match:
            brand["industry"] = industry_match.group(1).strip()
        tone_match = re.search(r"Tone:\s*(.+?)(?:\n|$)", text)
        if tone_match:
            brand["tone"] = tone_match.group(1).strip()

    # Fallback: extract additional fields from message text if not in attachments
    if brand:
        text = request.message
        if not brand.get("overview"):
            m = re.search(r"\[Company Overview:\s*(.+?)\]", text)
            if m:
                brand["overview"] = m.group(1).strip()
        if not brand.get("target_audience"):
            m = re.search(r"\[TARGET AUDIENCE:\s*(.+?)\]", text)
            if m:
                brand["target_audience"] = m.group(1).strip()
        if not brand.get("products_services"):
            m = re.search(r"\[PRODUCTS/SERVICES:\s*(.+?)\]", text)
            if m:
                brand["products_services"] = m.group(1).strip()
        # Extract name from [Current brand context: CompanyName, ...] format
        if not brand.get("name"):
            m = re.search(r"\[Current brand context:\s*(.+?),", text)
            if m:
                brand["name"] = m.group(1).strip()

    if brand:
        input_data["brand"] = brand

    return StreamingResponse(
        stream_agent_response(agent, input_data, config, session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Startup event
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def _startup():
    try:
        agent = _get_agent()
        register_asset_routes(app, agent)
        logger.info("Agent initialized and asset routes registered")
    except Exception as e:
        logger.warning("Agent init deferred (API key may be missing): %s", e)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def main():
    import uvicorn
    from agent_factory_core.config.settings import DEBUG, HOST

    port = int(__import__("os").getenv("VIDEO_STUDIO_PORT", "5002"))
    print(f"\n🎬 Video Studio Agent starting...")
    print(f"📍 UI: http://localhost:{port}")
    print(f"📍 API Docs: http://localhost:{port}/docs\n")
    uvicorn.run("video_studio.app:app", host=HOST, port=port, reload=DEBUG)


if __name__ == "__main__":
    main()
