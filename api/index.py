import sys
import urllib.parse
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
            # 1. Check query_string for __vercel_path injected by vercel.json rewrite
            qs_bytes = scope.get("query_string", b"")
            target_path = None
            if qs_bytes:
                try:
                    qs_str = qs_bytes.decode("latin1")
                    parsed = urllib.parse.parse_qs(qs_str, keep_blank_values=True)
                    if "__vercel_path" in parsed:
                        raw_target = parsed.pop("__vercel_path")[0]
                        if raw_target:
                            target_path = raw_target if raw_target.startswith("/") else f"/{raw_target}"
                        # Reconstruct query string without __vercel_path
                        new_qs_pairs = [(k, v) for k, vs in parsed.items() for v in vs if k]
                        scope["query_string"] = urllib.parse.urlencode(new_qs_pairs).encode("latin1")
                except Exception:
                    pass

            # 2. Check for Vercel's original matched path header if query_string didn't set it
            if not target_path:
                headers = dict(scope.get("headers", []))
                matched_path = headers.get(b"x-matched-path") or headers.get(b"x-vercel-matched-path")
                if matched_path:
                    try:
                        decoded = matched_path.decode("utf-8")
                        if decoded and not decoded.startswith("/api/index.py"):
                            target_path = decoded if decoded.startswith("/") else f"/{decoded}"
                    except Exception:
                        pass

            # 3. Apply resolved path or normalize serverless script prefix
            if target_path:
                scope["path"] = target_path
            else:
                path = scope.get("path", "")
                if path in ("/api/index.py", "/api/index", "/api/index/", "/api/"):
                    scope["path"] = "/"
                elif path.startswith("/api/index.py/"):
                    scope["path"] = path[len("/api/index.py"):]
                elif path.startswith("/api/index/"):
                    scope["path"] = path[len("/api/index"):]

        await self.app(scope, receive, send)


app = VercelPathFixMiddleware(fastapi_app)
