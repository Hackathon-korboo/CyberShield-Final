"""CyberShield AI 2.0 — Extended AI Application Entry Point.

Mounts Phase 03 AI-augmented analysis routes alongside the frozen Phase 01/02
deterministic engine without modifying frozen base application files.
"""

from fastapi import FastAPI

from backend.app.api.ai_router import ai_api_router
from backend.app.core.config import get_settings
from backend.app.main import create_application

settings = get_settings()


def create_ai_application() -> FastAPI:
    """Build the extended application instance with AI routes registered."""
    app = create_application()

    # Mount Phase 03 AI router under /api/v1
    app.include_router(ai_api_router, prefix=settings.api_v1_str)

    return app


app = create_ai_application()
