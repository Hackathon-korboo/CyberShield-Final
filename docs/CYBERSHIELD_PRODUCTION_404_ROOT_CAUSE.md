# CyberShield AI 2.0 — Production HTTP 404 Root Cause Analysis & Audit

**Document Reference**: `CYBERSHIELD_PRODUCTION_404_ROOT_CAUSE`  
**Classification**: Tier-1 Production Incident Resolution Report  
**Target Environments**:  
- Frontend: `https://cybershield-ai-web-roan.vercel.app` (Vercel Project: `cybershield-ai-web`)  
- Backend: `https://cybershield-ai-api.vercel.app` (Vercel Project: `cybershield-ai-api`)  
- Repository: `https://github.com/Hackathon-korboo/CyberShield-Final` (`main` branch)  
**Date**: November 14, 2026  
**Status**: RESOLVED & VERIFIED  

---

## 1. Executive Incident Summary

Following the initial deployment of CyberShield AI 2.0, users reported that entering a target URL (such as `http://google.com`) and initiating analysis via the "ANALYZE WEB URL" button resulted in an immediate failure:
```
URL Analysis Failed
Server returned HTTP 404
```
A comprehensive full-stack diagnostic was conducted across the Vercel edge infrastructure, frontend client scripts, FastAPI router registration, and live REST endpoints. The audit revealed a compound two-tier root cause involving client-side routing resolution and incomplete ASGI router registration on the serverless backend.

---

## 2. Root Cause Breakdown

### Root Cause A: Client-Side Base URL Evaluation on Production Origin
In `frontend/main.js`, the API base URL resolver was configured as follows:
```javascript
// BEFORE (Buggy Implementation):
const API_BASE = window.location.origin.includes(':8000')
  ? ''
  : (window.location.protocol.startsWith('http') ? '' : 'http://127.0.0.1:8000');
```
* **Failure Mechanism**:  
  When accessing the production application over `https://cybershield-ai-web-roan.vercel.app`, `window.location.protocol` evaluates to `'https:'`.  
  Because `'https:'` starts with `'http'`, the ternary expression evaluated to `''` (an empty relative string).
* **Consequence**:  
  All subsequent network calls (e.g. `fetch(`${API_BASE}/api/v1/analyze/text`)`) were dispatched to:
  ```
  POST https://cybershield-ai-web-roan.vercel.app/api/v1/analyze/text
  ```
  Because the frontend project on Vercel is a static web hosting deployment without backend serverless function routing, the Vercel CDN correctly returned **HTTP 404 Not Found**.

---

### Root Cause B: Incomplete FastAPI Router Mounting in Serverless Entry Point
In `backend/app/main.py`, the production FastAPI application factory (`create_application()`) originally only mounted the core health and basic Phase 2 analysis routers:
```python
# BEFORE (backend/app/main.py):
app.include_router(health_router, prefix=settings.api_v1_str)
app.include_router(health_router, prefix="")
app.include_router(analysis_router, prefix=settings.api_v1_str)
```
* **Failure Mechanism**:  
  Vercel's Python runtime natively inspects and loads `backend/app/main.py:app`.  
  However, the multi-member integrated threat analysis endpoints—specifically:
  - `POST /api/v1/analyze/text` (Member 2 unified threat, URL, SMS, email, prompt injection & PII redaction pipeline)
  - `POST /api/v1/analyze/file` (Member 2 static safe file analysis)
  - `GET /api/v1/config/providers` (Provider discovery)
  - `POST /api/v1/scan-url` & `GET /api/v1/scans` (Stage 4 & 5 scan engine)
  - `POST /api/v1/reports/verify` (Stage 5 reports)
  were defined in `member2_routes.py`, `scans.py`, and `unified_report.py`, but were never mounted in `backend/app/main.py`.
* **Consequence**:  
  Even when requests directly reached `https://cybershield-ai-api.vercel.app/api/v1/analyze/text`, FastAPI returned an application-level **HTTP 404 Not Found** with error code `NOT_FOUND`.

---

### Root Cause C: Vercel Dashboard "No Production Deployment" Status on Backend Project
The `cybershield-ai-api` Vercel project had previously completed only a preview build or had its production alias unassigned, leaving the production deployment in an unpromoted state until actively triggered and linked via the Vercel CLI.

---

## 3. Incident Remediation Matrix

| Defect Area | Location | Root Cause | Remediated Action | Verification State |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend API Base** | `frontend/main.js` | `window.location.protocol.startsWith('http')` defaulted to empty string | Built host-aware IIFE defaulting to `https://cybershield-ai-api.vercel.app` on non-local origins | **PASSED** (Live client dispatches to API domain) |
| **Backend Endpoints** | `backend/app/main.py` | `member2_router`, `scans_router`, `unified_report_router`, `ai_api_router` omitted | Mounted all module routers under `settings.api_v1_str` | **PASSED** (26 endpoints live in `/openapi.json`) |
| **Error Handling** | `frontend/main.js` | Did not unpack nested `errJson.error.message` | Unified error extraction: `errJson.detail \|\| errJson.error?.message \|\| status` | **PASSED** (Clear diagnostic alerts) |
| **Vercel Backend** | `cybershield-ai-api` | Production alias unpromoted | Executed `vercel --prod --yes` | **PASSED** (`READY` on `https://cybershield-ai-api.vercel.app`) |
| **Vercel Frontend** | `cybershield-ai-web` | Stale bundle before `main.js` fix | Redeployed production bundle via `vercel --prod --yes` | **PASSED** (`READY` on `https://cybershield-ai-web-roan.vercel.app`) |

---

## 4. Live Verification Proof
Direct REST query to the production backend:
```bash
POST https://cybershield-ai-api.vercel.app/api/v1/analyze/text
Body: {"content": "http://google.com", "source_type": "url"}
```
**HTTP Status**: `200 OK`  
**Payload**:
```json
{
  "risk_level": "BENIGN",
  "risk_score": 5.0,
  "primary_category": "BENIGN",
  "verdict": "NO_THREAT_DETECTED",
  "iocs": {
    "urls": ["http://google.com"],
    "domains": ["google.com"]
  },
  "processing_time_ms": 127.08
}
```
The HTTP 404 error is completely eliminated.
