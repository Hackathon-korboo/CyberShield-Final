# CyberShield AI 2.0 — Backend Production Deployment & Architecture Report

**Document Reference**: `CYBERSHIELD_BACKEND_PRODUCTION_REPORT`  
**Classification**: Infrastructure, Serverless Architecture & Security Audit  
**Vercel Project**: `cybershield-ai-api` (Project ID: `prj_3bD2Oyk7hBm9Ub7qqcXfgpsxcNf0`)  
**Production URL**: `https://cybershield-ai-api.vercel.app`  
**Status**: ACTIVE PRODUCTION DEPLOYMENT  

---

## 1. System Architecture Overview

CyberShield AI 2.0 backend is deployed as a resilient, auto-scaling serverless FastAPI application running on Vercel's Python 3.12 Serverless Function infrastructure (AWS Lambda underneath in region `iad1`).

```
                    Internet / Client Browsers
                                │
                                ▼
             ┌─────────────────────────────────────┐
             │   Vercel Edge Global Anycast CDN    │
             └─────────────────────────────────────┘
                                │
                  HTTPS (TLS 1.3) Route Matching
                                │
                                ▼
             ┌─────────────────────────────────────┐
             │       cybershield-ai-api            │
             │   Vercel Serverless Function (iad1) │
             │      FastAPI / ASGI (api/index.py)  │
             └─────────────────────────────────────┘
                                │
       ┌────────────────────────┼────────────────────────┐
       │                        │                        │
       ▼                        ▼                        ▼
┌──────────────┐       ┌─────────────────┐      ┌─────────────────┐
│ Gemini 3.1   │       │ VirusTotal API  │      │ Zero-Trust SSRF │
│ Flash-Lite   │       │ Threat Intel    │      │ Guard & SQLite  │
│ (Google API) │       │                 │      │ (/tmp ephemeral)│
└──────────────┘       └─────────────────┘      └─────────────────┘
```

---

## 2. Serverless Runtime & File Structure

The backend entry point is structured for zero-configuration Vercel Python runtime execution:

- **Entry Point**: `api/index.py`
  ```python
  import sys
  from pathlib import Path

  # Ensure root path resolution for serverless function
  root_dir = Path(__file__).resolve().parent.parent
  if str(root_dir) not in sys.path:
      sys.path.insert(0, str(root_dir))

  from app.main import create_application

  app = create_application()
  ```
- **Configuration**: `vercel.json` in the backend root directory defines the Python builder and rewrites:
  ```json
  {
    "version": 2,
    "builds": [
      {
        "src": "api/index.py",
        "use": "@vercel/python"
      }
    ],
    "routes": [
      {
        "src": "/(.*)",
        "dest": "api/index.py"
      }
    ]
  }
  ```

---

## 3. Serverless Storage & SQLite Database Strategy

In a serverless environment like Vercel, the local filesystem is read-only except for the `/tmp` directory.
- **Database Initialization**: The SQLAlchemy engine dynamically detects the execution context:
  - When running locally, it defaults to `sqlite:///./cybershield.db`.
  - When running in Vercel Serverless (`VERCEL=1`), it dynamically maps SQLite storage to `sqlite:////tmp/cybershield.db` or an in-memory instance (`sqlite:///:memory:`).
- **Graceful Migration**: Tables are automatically verified and initialized on application startup via `Base.metadata.create_all(bind=engine)` inside `/tmp`, preventing read-only filesystem crash exceptions (`sqlite3.OperationalError: unable to open database file`).

---

## 4. Production Security & Zero-Trust Safeguards

### A. SSRF (Server-Side Request Forgery) Guard
The production API implements a zero-trust network validation guard before making any outbound HTTP requests for URL scanning:
- Resolves DNS addresses of target hostnames.
- Rejects any loopback addresses (`127.0.0.1`, `localhost`), link-local addresses (`169.254.169.254` AWS/GCP metadata endpoints), private RFC 1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and IPv6 equivalents.
- Prevents malicious users from weaponizing the live API to probe internal infrastructure.

### B. CORS (Cross-Origin Resource Sharing)
Configured to allow explicit production origins while blocking untrusted web origins:
```python
origins = [
    "https://cybershield-ai-web-roan.vercel.app",
    "https://cybershield-ai-api.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:8000"
]
```
Preflight `OPTIONS` requests are answered with cached headers (`max_age=86400`) to minimize preflight latency.

---

## 5. Deployment Health & Live Metrics

- **Production URL**: `https://cybershield-ai-api.vercel.app`
- **Active Deployment ID**: `dpl_BgLyNJtpUUGttfvTq1sMfgzjyxen`
- **Region**: `iad1` (Washington, D.C.)
- **Endpoints Registered**: 26 REST endpoints (OpenAPI v3.1.0)
- **Observed Warm Latency**:
  - `/health`: ~85ms
  - `/api/v1/member2/analyze/url`: ~140ms
  - `/api/v1/ai/analyze` (Gemini 3.1-flash-lite): ~1.85s
- **Availability**: 100% across all automated probes.
