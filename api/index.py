import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.risk_app import app as fastapi_app


class VercelPathFixMiddleware:
    """ASGI Middleware to resolve Vercel serverless path rewrites."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            headers = dict(scope.get("headers", []))

            # 1. Check for Vercel's original matched path header
            matched_path = headers.get(b"x-matched-path")
            if matched_path:
                try:
                    scope["path"] = matched_path.decode("utf-8")
                except Exception:
                    pass

            # 2. Strip serverless script prefix if present
            path = scope.get("path", "")
            if path in ("/api/index.py", "/api/index", "/api/index/", "/api/"):
                scope["path"] = "/"
            elif path.startswith("/api/index.py/"):
                scope["path"] = path[len("/api/index.py"):]
            elif path.startswith("/api/index/"):
                scope["path"] = path[len("/api/index"):]

        await self.app(scope, receive, send)


app = VercelPathFixMiddleware(fastapi_app)
