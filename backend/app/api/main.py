"""CyberShield AI 2.0 — API Module Router & Compatibility Entry Point.

Exposes the unified FastAPI application for compatibility with Member 2 test suites
and legacy client integrations.
"""

from backend.app.risk_app import app

__all__ = ["app"]
