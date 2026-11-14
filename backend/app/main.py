"""CyberShield AI 2.0 — Main Application Entry Point.

This module initializes the FastAPI application, mounts middlewares (CORS,
Correlation ID, Security Headers), registers global exception handlers,
and includes versioned API routers.
"""

import sys
import types
from pathlib import Path

# Vercel serverless environment compatibility:
_backend_dir = Path(__file__).resolve().parent.parent
if "backend" not in sys.modules:
    backend_pkg = types.ModuleType("backend")
    backend_pkg.__path__ = [str(_backend_dir)]
    sys.modules["backend"] = backend_pkg

for _p in [str(_backend_dir), str(_backend_dir.parent)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app import __version__
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.analysis import router as analysis_router
from backend.app.core.config import get_settings
from backend.app.core.exceptions import (
    CyberShieldBaseException,
    cybershield_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from backend.app.core.logging import setup_logging
from backend.app.middleware.correlation import CorrelationIdMiddleware
from backend.app.middleware.security_headers import SecurityHeadersMiddleware
from backend.app.schemas.common import StandardResponse

# Retrieve settings and initialize logging
settings = get_settings()
logger = setup_logging(log_level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown routines."""
    # Startup: log masked environment summary (safe, zero secrets)
    logger.info("Initializing %s v%s in [%s] mode", settings.app_name, settings.app_version, settings.environment)
    logger.debug("Configuration active: %s", settings.get_masked_summary())
    yield
    # Shutdown
    logger.info("Shutting down %s gracefully.", settings.app_name)


def create_application() -> FastAPI:
    """Factory function to build and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "CyberShield AI 2.0 is an enterprise-grade cyber threat defense platform "
            "providing heuristic security analysis, AI intent verification, and Web3 trust registries."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 1. Register Custom Middlewares (order matters: outer wraps inner)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    # 2. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID"],
    )

    # 3. Global Exception Handlers (sanitized, zero secret leakage)
    app.add_exception_handler(CyberShieldBaseException, cybershield_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # 4. Mount API Routers
    app.include_router(health_router, prefix=settings.api_v1_str)
    # Also mount health directly at root /health for generic container/cluster probes
    app.include_router(health_router, prefix="")
    # Mount Phase 02 Threat Analysis Routers
    app.include_router(analysis_router, prefix=settings.api_v1_str)

    # Root Info Endpoint
    @app.get(
        "/",
        response_model=StandardResponse[dict],
        status_code=status.HTTP_200_OK,
        tags=["System"],
        summary="Application Root Info",
    )
    async def get_root_info() -> StandardResponse[dict]:
        """Provides basic service identity and documentation links."""
        return StandardResponse(
            success=True,
            data={
                "name": settings.app_name,
                "version": settings.app_version,
                "environment": settings.environment,
                "status": "online",
                "docs": "/docs",
                "health": f"{settings.api_v1_str}/health",
            },
            error=None,
        )

    return app


# Canonical ASGI entry point
app = create_application()
