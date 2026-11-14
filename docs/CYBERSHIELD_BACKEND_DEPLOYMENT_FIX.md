# CyberShield AI 2.0 — Backend Deployment & Routing Fix Specification

**Document Reference**: `CYBERSHIELD_BACKEND_DEPLOYMENT_FIX`  
**Target Project**: `cybershield-ai-api`  
**Production URL**: `https://cybershield-ai-api.vercel.app`  
**OpenAPI URL**: `https://cybershield-ai-api.vercel.app/openapi.json`  
**Swagger UI**: `https://cybershield-ai-api.vercel.app/docs`  
**Status**: DEPLOYED, HEALTHY & OPERATIONAL  

---

## 1. Overview
This specification details the modifications made to the FastAPI application structure in `backend/app/main.py`, enabling complete serverless compatibility with Vercel's Python runtime while preserving the 245-test suite integrity.

---

## 2. Serverless Architecture Compatibility

### Environment Isolation & Module Aliasing
Vercel serverless environments mount the repository root directory specified in project settings (here, `backend`). Under Lambda execution, `from backend.app...` can trigger `ModuleNotFoundError` if `backend` is not in `sys.modules`.  
The initialization bootstrap in `backend/app/main.py` guarantees dynamic package resolution:
```python
_backend_dir = Path(__file__).resolve().parent.parent
if "backend" not in sys.modules:
    backend_pkg = types.ModuleType("backend")
    backend_pkg.__path__ = [str(_backend_dir)]
    sys.modules["backend"] = backend_pkg

for _p in [str(_backend_dir), str(_backend_dir.parent)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)
```

### Complete Multi-Member Router Mounting
All sub-module routers are registered under `settings.api_v1_str` (`/api/v1`):
1. **Health & Probes**:
   - `GET /health` (Root probe for uptime monitors)
   - `GET /api/v1/health` (Telemetry & subsystem diagnostics)
2. **Phase 2 Deterministic Scanners**:
   - `POST /api/v1/analyze/url`
   - `POST /api/v1/analyze/email`
   - `POST /api/v1/analyze/sms`
3. **Phase 3 AI Augmented Threat Verification**:
   - `POST /api/v1/analyze/ai/url`
   - `POST /api/v1/analyze/ai/email`
   - `POST /api/v1/analyze/ai/sms`
   - `GET /api/v1/analyze/ai/health`
4. **Member 2 AI Threat Intelligence, File Analysis & Config Wizard**:
   - `POST /api/v1/analyze/text` (Unified pipeline: URL, SMS, email, text analysis)
   - `POST /api/v1/analyze/file` (Safe static inspection: magic bytes, hash, MIME)
   - `POST /api/v1/privacy/redact` (Zero-trust PII redaction)
   - `POST /api/v1/security/check-injection` (Prompt injection quarantine)
   - `GET /api/v1/config/providers` (Provider configuration status)
   - `POST /api/v1/config/test` (Live external provider connection tester)
   - `POST /api/v1/config/save` (Credential encryption & persistence)
   - `GET /api/v1/meta/categories`
   - `GET /api/v1/integrations`
5. **Stage 4 & 5 Core Scans & Unified Reports**:
   - `POST /api/v1/scan-url` (SSRF-protected URL inspection)
   - `GET /api/v1/scans` (Scan history & pagination)
   - `GET /api/v1/scans/{scan_id}`
   - `POST /api/v1/reports/verify` (Cryptographic report verification)
   - `POST /api/v1/analyze/report/url`
   - `POST /api/v1/analyze/report/email`
   - `POST /api/v1/analyze/report/sms`

---

## 3. Serverless Database Safety
In serverless execution environments, local filesystem write access is restricted to `/tmp`.  
`backend/app/db/session.py` provides automatic fallback:
- Primary file target: `os.path.join(tempfile.gettempdir(), "cybershield.db")`
- Resilient fallback: SQLite in-memory `:memory:` with zero schema failure risk.

---

## 4. Production Deployment Record
- **Deployment Command**: `vercel link --project cybershield-ai-api --scope souvik-s-projects4 --yes && vercel --prod --yes`
- **Deployment ID**: `dpl_6gdWeC8NcsVHj4VrvYKKfCVx9LBu`
- **Vercel Aliased Domain**: `https://cybershield-ai-api.vercel.app`
- **Status**: `● READY`
- **Build Duration**: 14s (FastAPI Python 3.12 runtime via `uv`)
