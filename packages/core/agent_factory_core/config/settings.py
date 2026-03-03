"""Shared configuration for all studio agents."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", GOOGLE_API_KEY)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gemini-3-pro-image-preview")
VIDEO_MODEL = os.getenv("VIDEO_MODEL", "veo-3.1-generate-preview")

# Per-agent model overrides (fall back to DEFAULT_MODEL)
ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL", DEFAULT_MODEL)
IDEA_MODEL = os.getenv("IDEA_MODEL", DEFAULT_MODEL)
WRITER_MODEL = os.getenv("WRITER_MODEL", DEFAULT_MODEL)
EDIT_MODEL = os.getenv("EDIT_MODEL", IMAGE_MODEL)
CAMPAIGN_MODEL = os.getenv("CAMPAIGN_MODEL", DEFAULT_MODEL)
CAPTION_MODEL = os.getenv("CAPTION_MODEL", DEFAULT_MODEL)
ANIMATION_MODEL = os.getenv("ANIMATION_MODEL", DEFAULT_MODEL)

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
HOST = os.getenv("HOST", "0.0.0.0")
DEBUG = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent  # agent-factory/
UPLOAD_DIR = BASE_DIR / "uploads"
GENERATED_DIR = BASE_DIR / "generated"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
STORAGE_BUCKET = os.getenv("STORAGE_BUCKET", "")
STORAGE_CDN_URL = os.getenv("STORAGE_CDN_URL", "")

# ---------------------------------------------------------------------------
# Upload Limits
# ---------------------------------------------------------------------------
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/png", "image/jpeg", "image/gif", "image/webp",
}
MAX_IMAGE_DIMENSION = int(os.getenv("MAX_IMAGE_DIMENSION", "4096"))

# ---------------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------------
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
RATE_LIMIT_WINDOW = 60  # seconds

# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------
SESSION_TIMEOUT_HOURS = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))

# ---------------------------------------------------------------------------
# Persistence (LangGraph Checkpointer)
# ---------------------------------------------------------------------------
DATABASE_BACKEND = os.getenv("DATABASE_BACKEND", "sqlite")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'studio.db'}")

# ---------------------------------------------------------------------------
# Tracing
# ---------------------------------------------------------------------------
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() in ("true", "1")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "agent-factory")

# Auto-configure LangSmith tracing at import time
if LANGSMITH_TRACING and LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT


def get_checkpointer():
    """Create a checkpointer based on DATABASE_BACKEND config.

    Returns None in development if no database is configured.
    For production, use DATABASE_BACKEND=postgres with a proper DATABASE_URL.
    """
    if DATABASE_BACKEND == "postgres":
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            return AsyncPostgresSaver.from_conn_string(DATABASE_URL)
        except ImportError:
            import warnings
            warnings.warn(
                "langgraph-checkpoint-postgres not installed. "
                "Install it with: pip install langgraph-checkpoint-postgres",
                stacklevel=2,
            )
            return None
    elif DATABASE_BACKEND == "sqlite":
        try:
            from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
            # Ensure data directory exists
            db_path = DATABASE_URL.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            return AsyncSqliteSaver.from_conn_string(db_path)
        except ImportError:
            return None
    return None


def setup_langsmith():
    """Configure LangSmith tracing if enabled."""
    if LANGSMITH_TRACING and LANGSMITH_API_KEY:
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        os.environ.setdefault("LANGCHAIN_API_KEY", LANGSMITH_API_KEY)
        os.environ.setdefault("LANGCHAIN_PROJECT", LANGSMITH_PROJECT)
