"""CyberShield AI 2.0 — Dedicated Server Process Runner.

Records the active process PID to `.cybershield.pid` and starts the Uvicorn
ASGI server hosting the complete CyberShield AI 2.0 unified application.
"""

import os
from pathlib import Path
import sys
import uvicorn

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PID_FILE = PROJECT_ROOT / ".cybershield.pid"


def main():
    # Record PID
    current_pid = os.getpid()
    try:
        with open(PID_FILE, "w", encoding="utf-8") as f:
            f.write(str(current_pid))
        print(f"[CYBERSHIELD] Process PID {current_pid} recorded to {PID_FILE.name}")
    except Exception as exc:
        print(f"[WARN] Could not record PID to {PID_FILE}: {exc}")

    try:
        uvicorn.run(
            "backend.app.risk_app:app",
            host="127.0.0.1",
            port=8000,
            log_level="info",
            reload=False,
        )
    finally:
        # Clean up PID file on graceful shutdown
        if PID_FILE.exists():
            try:
                PID_FILE.unlink()
                print(f"[CYBERSHIELD] Cleaned up {PID_FILE.name}")
            except Exception:
                pass


if __name__ == "__main__":
    main()
