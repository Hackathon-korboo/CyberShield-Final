# CyberShield AI 2.0 — Server Launcher Guide

This document describes how to start, monitor, and safely shut down the CyberShield AI 2.0 backend server using the one-click Windows launcher utilities.

---

## 1. Quick Start

### Start the Server
Double-click `Start.bat` or run it from a Command Prompt:

```cmd
Start.bat
```

### Stop the Server
Double-click `STOP_CyberShield.bat` or run it from a Command Prompt:

```cmd
STOP_CyberShield.bat
```

To run in automated scripts without interactive pauses:
```cmd
STOP_CyberShield.bat --quiet
```

---

## 2. Architecture of the Launcher Utilities

### `Start.bat` Workflow
1. **Dynamic Project Root Resolution:** Automatically determines project root path (`%~dp0`), ensuring the script works regardless of which working directory launched it.
2. **Virtual Environment Detection:** Checks for `backend\venv\Scripts\python.exe` and `backend\venv\Scripts\activate.bat`. Falls back to root `venv` or system Python if necessary.
3. **Pre-flight Module Verification:** Tests importing `backend.app.risk_app:app` before spawning processes to catch missing dependencies or syntax errors immediately.
4. **Port 8000 Conflict Detection:** Uses a fast Python socket probe to test if `127.0.0.1:8000` is already in use. If occupied, offers to safely terminate the conflicting process using `STOP_CyberShield.bat` and proceed.
5. **Dedicated Process Spawning:** Spawns a labeled Command Prompt window titled `CYBERSHIELD AI 2.0 - BACKEND SERVER (Port 8000)` running `backend/run_server.py`.
6. **Process PID Tracking:** `backend/run_server.py` writes its active PID into `.cybershield.pid` at the project root.
7. **Active Health Probe:** Loops up to 15 seconds polling `http://127.0.0.1:8000/api/v1/health` via PowerShell `Invoke-WebRequest`.
8. **Interactive Browser Launch:** Displays active endpoints and prompts whether to automatically open the interactive Swagger UI (`http://127.0.0.1:8000/docs`).

### `STOP_CyberShield.bat` Workflow
1. **PID File Inspection:** Reads `.cybershield.pid` if present, validates that the recorded PID corresponds to a `python.exe` process (protecting against stale PIDs reused by other applications), and cleanly terminates the process tree with `taskkill /PID <PID> /F /T`.
2. **Port 8000 Verification:** Inspects `netstat -ano` for any remaining listening processes on port 8000. If bound to `python.exe`, securely terminates them.
3. **Artifact Cleanup:** Safely deletes `.cybershield.pid`.
4. **Targeted Scope:** Unrelated background processes, browsers, and terminal windows are completely untouched.

---

## 3. Operational Endpoints

Once `Start.bat` reports `[SUCCESS]`, the following endpoints are live:

| Endpoint | Method | Description |
|---|---|---|
| `http://127.0.0.1:8000/docs` | GET | Swagger UI Interactive API Explorer |
| `http://127.0.0.1:8000/redoc` | GET | ReDoc Formal API Reference |
| `http://127.0.0.1:8000/api/v1/health` | GET | Subsystem Health Check (DB, AI, Threat Intel, Blockchain) |
| `http://127.0.0.1:8000/api/v1/scan-url` | POST | Core URL Analysis & Unified Threat Report Pipeline |
| `http://127.0.0.1:8000/api/v1/scans/{scan_id}` | GET | Scan Report Retrieval by UUID |
| `http://127.0.0.1:8000/api/v1/scans` | GET | Paginated Scan History Query |
| `http://127.0.0.1:8000/api/v1/reports/verify` | POST | RFC 8785 Canonical Hash & Blockchain Verification |
| `http://127.0.0.1:8000/api/v1/unified-report` | POST | Stage 4 Risk Assessment Engine (URL / Email / SMS) |

---

## 4. Troubleshooting & FAQs

### Q: Port 8000 is occupied by another application
`Start.bat` will notify you and ask if you want to stop the existing process. Press `Y` to automatically invoke `STOP_CyberShield.bat` and restart. If you have another service on port 8000, you can edit `PORT=8000` in `.env`.

### Q: "Backend import verification failed!"
The virtual environment may need dependency reinstallation:
```cmd
cd backend
venv\Scripts\activate.bat
pip install -r requirements.txt
```

### Q: Server console closes immediately
Run `backend\venv\Scripts\python.exe backend\run_server.py` in an open terminal to see any missing system libraries or configuration syntax errors.
