"""CyberShield AI 2.0 — Extended Risk & Threat Report Application Entry Point.

Unified master FastAPI application integrating:
- Member 1: Core backend, deterministic risk engine, SQLite persistence, and unified threat reports
- Member 2: AI scam intelligence, safe file analysis, PII redaction, prompt injection guard, and provider configuration
- Member 3: Blockchain smart contract artifacts, canonical JSON hashing, and ledger verification
- Member 4: Interactive Web UI, Medusa JF-4 3D Platform, Three.js, and Configuration Wizard
"""

from pathlib import Path
from datetime import datetime, timezone
import sys
import types

# Vercel serverless environment compatibility
_backend_dir = Path(__file__).resolve().parent.parent
if "backend" not in sys.modules:
    backend_pkg = types.ModuleType("backend")
    backend_pkg.__path__ = [str(_backend_dir)]
    sys.modules["backend"] = backend_pkg

for _p in [str(_backend_dir), str(_backend_dir.parent)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.app.ai_app import create_ai_application
from backend.app.api.routes.scans import router as scans_router
from backend.app.api.routes.unified_report import router as unified_report_router
from backend.app.api.routes.member2_routes import router as member2_router
from backend.app.core.config import get_settings
from backend.app.schemas.common import StandardResponse

settings = get_settings()

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
INDEX_HTML_PATH = FRONTEND_DIR / "index.html"
STYLES_PATH = FRONTEND_DIR / "styles.css"
MAIN_JS_PATH = FRONTEND_DIR / "main.js"
ASSETS_DIR = FRONTEND_DIR / "assets"
FONTS_DIR = FRONTEND_DIR / "fonts"
WIZARD_TEMPLATE_PATH = Path(__file__).parent / "api" / "templates" / "wizard.html"


def create_risk_application() -> FastAPI:
    """Build the unified master application instance with all Member routes registered."""
    app = create_ai_application()

    # Mount Stage 4 & 5 Core Scans & Report routers under /api/v1
    app.include_router(unified_report_router, prefix=settings.api_v1_str)
    app.include_router(scans_router, prefix=settings.api_v1_str)

    # Mount Member 2 AI Intelligence, File Analysis, and Configuration routers under /api/v1
    app.include_router(member2_router, prefix=settings.api_v1_str)

    # Mount frontend static directories
    if ASSETS_DIR.exists():
        app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")
    if FONTS_DIR.exists():
        app.mount("/fonts", StaticFiles(directory=str(FONTS_DIR)), name="fonts")

    @app.get("/styles.css", include_in_schema=False)
    def serve_styles():
        if STYLES_PATH.exists():
            return FileResponse(STYLES_PATH, media_type="text/css")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="styles.css not found")

    @app.get("/main.js", include_in_schema=False)
    def serve_main_js():
        if MAIN_JS_PATH.exists():
            return FileResponse(MAIN_JS_PATH, media_type="application/javascript")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="main.js not found")

    @app.get("/wizard", response_class=HTMLResponse, tags=["Configuration Wizard"])
    @app.get("/setup", response_class=HTMLResponse, tags=["Configuration Wizard"])
    def serve_wizard():
        if not WIZARD_TEMPLATE_PATH.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wizard template file missing."
            )
        return HTMLResponse(content=WIZARD_TEMPLATE_PATH.read_text(encoding="utf-8"))

    # Remove existing root route from base app to enable dual HTML / JSON root resolution
    app.router.routes = [r for r in app.router.routes if getattr(r, "path", None) != "/"]

    @app.get(
        "/",
        response_model=StandardResponse[dict],
        status_code=status.HTTP_200_OK,
        tags=["System"],
        summary="Application Root & Interactive UI",
    )
    @app.get("/api/index.py", include_in_schema=False)
    @app.get("/api/index", include_in_schema=False)
    @app.get("/api", include_in_schema=False)
    def serve_root(request: Request):
        accept = request.headers.get("accept", "")
        if "application/json" in accept and "text/html" not in accept:
            return StandardResponse(
                success=True,
                data={
                    "name": settings.app_name,
                    "version": settings.app_version,
                    "environment": settings.environment,
                    "status": "online",
                    "docs_url": f"{settings.api_v1_str}/docs",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        if INDEX_HTML_PATH.exists():
            return HTMLResponse(content=INDEX_HTML_PATH.read_text(encoding="utf-8"))
        if WIZARD_TEMPLATE_PATH.exists():
            return HTMLResponse(content=WIZARD_TEMPLATE_PATH.read_text(encoding="utf-8"))
        return RedirectResponse(url="/wizard")

    return app


app = create_risk_application()
