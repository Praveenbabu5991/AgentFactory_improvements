"""Shared API routes for all studio apps."""

from __future__ import annotations

import io
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image
from pydantic import BaseModel, field_validator

from agent_factory_core.config.settings import (
    ALLOWED_IMAGE_TYPES,
    GENERATED_DIR,
    MAX_IMAGE_DIMENSION,
    MAX_UPLOAD_SIZE_BYTES,
    UPLOAD_DIR,
)
from agent_factory_core.tools._internal.image_gen import extract_brand_colors

router = APIRouter()

# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default_user"
    session_id: Optional[str] = None
    attachments: Optional[list[dict]] = None
    last_generated_image: Optional[str] = None

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        if len(v) > 10000:
            raise ValueError("Message too long (max 10000 characters)")
        return v.strip()


class BrandConfigRequest(BaseModel):
    company_name: str
    industry: str = ""
    company_overview: str = ""
    tone: str = "creative"
    target_audience: str = ""
    products_services: str = ""
    selected_palette: list[str] = []
    style_reference_url: str = ""
    # Marketing-video-specific
    marketing_goals: list[str] = []
    brand_messaging: str = ""
    competitive_positioning: str = ""


# ---------------------------------------------------------------------------
# Validation Helpers
# ---------------------------------------------------------------------------

USER_IMAGE_INTENTS = [
    "background", "product_focus", "team_people",
    "style_reference", "logo_badge", "auto",
]


def _validate_image_file(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: PNG, JPEG, GIF, WebP")
    ext = Path(file.filename).suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        raise HTTPException(status_code=400, detail="Invalid file extension")


async def _validate_image_content(content: bytes) -> None:
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=400, detail=f"File too large. Max: {MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB")
    try:
        image = Image.open(io.BytesIO(content))
        w, h = image.size
        if w > MAX_IMAGE_DIMENSION or h > MAX_IMAGE_DIMENSION:
            raise HTTPException(status_code=400, detail=f"Image too large. Max dimension: {MAX_IMAGE_DIMENSION}px")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or corrupted image file")


# ---------------------------------------------------------------------------
# Common Routes
# ---------------------------------------------------------------------------

@router.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@router.post("/upload-logo")
async def upload_logo(file: UploadFile = File(...)):
    """Upload a logo and extract brand colors."""
    _validate_image_file(file)
    content = await file.read()
    await _validate_image_content(content)

    ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / unique_filename
    filepath.write_bytes(content)

    colors = extract_brand_colors(str(filepath))
    return {
        "success": True,
        "filename": unique_filename,
        "path": f"/uploads/{unique_filename}",
        "full_path": str(filepath),
        "colors": colors,
    }


@router.post("/upload-reference")
async def upload_reference(file: UploadFile = File(...)):
    """Upload a reference image for style inspiration."""
    _validate_image_file(file)
    content = await file.read()
    await _validate_image_content(content)

    ext = Path(file.filename).suffix.lower()
    unique_filename = f"ref_{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / unique_filename
    filepath.write_bytes(content)

    return {
        "success": True,
        "filename": unique_filename,
        "path": f"/uploads/{unique_filename}",
        "full_path": str(filepath),
    }


@router.post("/upload-user-image")
async def upload_user_image(
    file: UploadFile = File(...),
    session_id: str = Form(default=""),
    usage_intent: str = Form(default="auto"),
):
    """Upload an image for use in posts (product photos, team pics, etc.)."""
    _validate_image_file(file)
    content = await file.read()
    await _validate_image_content(content)

    if usage_intent not in USER_IMAGE_INTENTS:
        usage_intent = "auto"

    image_id = str(uuid.uuid4())[:8]
    ext = Path(file.filename).suffix.lower()
    filename = f"img_{image_id}{ext}"

    folder = "user_images" / Path(session_id or "default")
    user_images_dir = UPLOAD_DIR / folder
    user_images_dir.mkdir(parents=True, exist_ok=True)
    filepath = user_images_dir / filename
    filepath.write_bytes(content)

    colors = extract_brand_colors(str(filepath))
    with Image.open(filepath) as img:
        dimensions = img.size

    url = f"/uploads/{folder}/{filename}"
    return {
        "success": True,
        "image": {
            "id": image_id,
            "filename": file.filename,
            "path": str(filepath),
            "url": url,
            "uploaded_at": datetime.now().isoformat(),
            "usage_intent": usage_intent,
            "extracted_colors": colors.get("palette", []),
            "dimensions": dimensions,
        },
    }


@router.delete("/delete-user-image/{session_id}/{image_id}")
async def delete_user_image(session_id: str, image_id: str):
    """Delete a user-uploaded image."""
    user_images_dir = UPLOAD_DIR / "user_images" / session_id
    if not user_images_dir.exists():
        raise HTTPException(status_code=404, detail="Session folder not found")
    for img_file in user_images_dir.glob(f"img_{image_id}.*"):
        img_file.unlink()
        return {"success": True, "image_id": image_id, "message": "Image deleted"}
    raise HTTPException(status_code=404, detail="Image not found")


@router.get("/generated-images")
async def list_generated_images(limit: int = 20, offset: int = 0):
    """List generated images/videos with pagination."""
    images = []
    for pattern in ["*.png", "*.jpg", "*.jpeg", "*.mp4"]:
        for img_path in GENERATED_DIR.glob(pattern):
            images.append({
                "filename": img_path.name,
                "url": f"/generated/{img_path.name}",
                "created": img_path.stat().st_mtime,
                "type": "video" if img_path.suffix == ".mp4" else "image",
            })
    images.sort(key=lambda x: x["created"], reverse=True)
    total = len(images)
    images = images[offset : offset + limit]
    return {
        "images": images, "total": total,
        "limit": limit, "offset": offset,
        "hasMore": offset + limit < total,
    }


# ---------------------------------------------------------------------------
# Brand Setup
# ---------------------------------------------------------------------------

@router.post("/brand")
async def set_brand(
    request: BrandConfigRequest,
    session_id: str = Form(default=""),
):
    """Store brand configuration for a session.

    The brand config is stored locally and returned. The POC app is
    responsible for injecting it into the agent state when invoking.
    Brand persistence across sessions is handled by LangGraph Store
    (set up in each POC's app.py).
    """
    brand_context: dict[str, Any] = {
        "name": request.company_name,
        "industry": request.industry,
        "overview": request.company_overview,
        "tone": request.tone,
        "target_audience": request.target_audience,
        "products_services": request.products_services,
        "colors": request.selected_palette,
        "style_reference_url": request.style_reference_url,
    }

    # Marketing-video-specific fields (optional)
    if request.marketing_goals:
        brand_context["marketing_goals"] = request.marketing_goals
    if request.brand_messaging:
        brand_context["brand_messaging"] = request.brand_messaging
    if request.competitive_positioning:
        brand_context["competitive_positioning"] = request.competitive_positioning

    # Check for uploaded logo in the session folder
    session = session_id or "default"
    logo_dir = UPLOAD_DIR
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        for logo_file in logo_dir.glob(f"*{ext}"):
            # Use the most recently uploaded logo
            brand_context.setdefault("logo_path", str(logo_file))
            break

    # Check for user images
    user_images_dir = UPLOAD_DIR / "user_images" / session
    if user_images_dir.exists():
        user_images = []
        for img_file in user_images_dir.iterdir():
            if img_file.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
                user_images.append({
                    "path": str(img_file),
                    "filename": img_file.name,
                    "usage_intent": "auto",
                })
        if user_images:
            brand_context["user_images"] = user_images

    return {"status": "ok", "brand": brand_context}


# ---------------------------------------------------------------------------
# Asset Management
# ---------------------------------------------------------------------------

def register_asset_routes(app_router: APIRouter, agent: Any) -> None:
    """Register asset management routes that require agent access.

    Call this from each POC's app.py after creating the agent:

        from agent_factory_core.api.routes import register_asset_routes
        register_asset_routes(app, agent)

    Args:
        app_router: The FastAPI app or router to add routes to.
        agent: The compiled LangGraph agent (CompiledStateGraph).
    """

    @app_router.get("/sessions/{session_id}/assets")
    async def list_session_assets(session_id: str):
        """List all generated assets for a conversation session."""
        try:
            config = {"configurable": {"thread_id": session_id}}
            state = await agent.aget_state(config)
            if state and state.values:
                assets = state.values.get("media_assets", [])
                return {
                    "session_id": session_id,
                    "assets": assets,
                    "total": len(assets),
                }
            return {"session_id": session_id, "assets": [], "total": 0}
        except Exception:
            return {"session_id": session_id, "assets": [], "total": 0}

    @app_router.get("/sessions/{session_id}/brand")
    async def get_session_brand(session_id: str):
        """Get brand context for a session."""
        try:
            config = {"configurable": {"thread_id": session_id}}
            state = await agent.aget_state(config)
            if state and state.values:
                brand = state.values.get("brand", {})
                return {"session_id": session_id, "brand": brand}
            return {"session_id": session_id, "brand": {}}
        except Exception:
            return {"session_id": session_id, "brand": {}}


# ---------------------------------------------------------------------------
# Message Builder
# ---------------------------------------------------------------------------

def build_message_text(request: ChatRequest) -> str:
    """Build the full message text including attachment context."""
    message_text = request.message

    if request.last_generated_image:
        message_text += f"\n\n[LAST GENERATED IMAGE: {request.last_generated_image}]"

    if not request.attachments:
        return message_text

    attachment_context = "\n\n[BRAND ASSETS PROVIDED - USE THESE FOR IMAGE GENERATION:]"
    for att in request.attachments:
        att_type = att.get("type", "")
        if att_type == "logo":
            logo_path = att.get('full_path') or att.get('path') or ''
            attachment_context += f"\nLOGO_PATH: {logo_path}"
            colors = att.get("colors")
            if colors:
                attachment_context += f"\nBRAND_COLORS: {colors.get('dominant')}"
                palette = colors.get("palette", [])
                if palette:
                    attachment_context += f", {','.join(palette)}"
        elif att_type == "reference_images":
            ref_paths = att.get("paths", [])
            if ref_paths:
                attachment_context += f"\nREFERENCE_IMAGES: {','.join(ref_paths)}"
        elif att_type == "user_images":
            user_imgs = att.get("images", [])
            if user_imgs:
                attachment_context += "\nUSER_IMAGES_FOR_POST:"
                for img in user_imgs:
                    intent = img.get("usage_intent", "auto").upper()
                    path = img.get("path", img.get("full_path", ""))
                    attachment_context += f"\n  - [{intent}] {path}"
                all_paths = [
                    img.get("path", img.get("full_path", ""))
                    for img in user_imgs
                    if img.get("path") or img.get("full_path")
                ]
                attachment_context += f"\n  USER_IMAGES_PATHS: {','.join(all_paths)}"
        elif att_type == "company_overview":
            attachment_context += f"\nCOMPANY_OVERVIEW: {att.get('content', '')}"
        elif att_type == "target_audience":
            attachment_context += f"\nTARGET_AUDIENCE: {att.get('content', '')}"
        elif att_type == "products_services":
            attachment_context += f"\nPRODUCTS_SERVICES: {att.get('content', '')}"

    return message_text + attachment_context
