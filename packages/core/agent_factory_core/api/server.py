"""Shared FastAPI app factory for studio applications."""

from __future__ import annotations

import time
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from agent_factory_core.api.routes import router as common_router
from agent_factory_core.config.settings import (
    ALLOWED_ORIGINS,
    GENERATED_DIR,
    RATE_LIMIT_REQUESTS,
    UPLOAD_DIR,
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    EXCLUDED_PATHS = ["/static/", "/generated/", "/uploads/", "/favicon.ico", "/health"]

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        window_start = current_time - 60
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > window_start]

        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please wait a moment."},
            )
        self.requests[client_ip].append(current_time)
        return await call_next(request)


def create_app(
    *,
    title: str = "Studio Agent",
    description: str = "",
    version: str = "1.0.0",
    static_dir: str | Path | None = None,
    templates_dir: str | Path | None = None,
) -> FastAPI:
    """Create a FastAPI app with common middleware and routes.

    Args:
        title: App title.
        description: App description.
        version: App version.
        static_dir: Path to static files directory.
        templates_dir: Path to templates directory.

    Returns:
        Configured FastAPI app with common routes already included.
    """
    app = FastAPI(title=title, description=description, version=version)

    # Rate limiting
    app.add_middleware(RateLimitMiddleware, requests_per_minute=RATE_LIMIT_REQUESTS)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # Mount static file directories
    if static_dir and Path(static_dir).exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.mount("/generated", StaticFiles(directory=str(GENERATED_DIR)), name="generated")
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

    # Include common routes
    app.include_router(common_router)

    return app
