# CyberShield AI 2.0 — Frontend API Integration Fix Specification

**Document Reference**: `CYBERSHIELD_FRONTEND_API_FIX`  
**Target Project**: `cybershield-ai-web`  
**Production URL**: `https://cybershield-ai-web-roan.vercel.app`  
**Backend API Target**: `https://cybershield-ai-api.vercel.app`  
**Status**: DEPLOYED, LINKED & VERIFIED  

---

## 1. Overview
This document specifies the client-side architectural corrections made in `frontend/main.js` to ensure reliable communication between the static production frontend and the live serverless backend API.

---

## 2. API Base URL Resolution Logic

### Previous Defect
The previous `API_BASE` ternary logic failed in HTTPS production:
```javascript
// BUGGY:
const API_BASE = window.location.origin.includes(':8000')
  ? ''
  : (window.location.protocol.startsWith('http') ? '' : 'http://127.0.0.1:8000');
```
Because `window.location.protocol` on `https://cybershield-ai-web-roan.vercel.app` starts with `http`, `API_BASE` evaluated to `''`, forcing calls to hit the static frontend host.

### Production Solution
A robust host-aware IIFE was implemented:
```javascript
// RESOLVED:
const API_BASE = (function() {
  if (typeof window === 'undefined') return 'https://cybershield-ai-api.vercel.app';
  if (window.VITE_API_BASE_URL) return window.VITE_API_BASE_URL.replace(/\/+$/, '');
  const host = window.location.hostname;
  if (host === 'localhost' || host === '127.0.0.1') {
    return window.location.origin.includes(':8000') ? '' : 'http://127.0.0.1:8000';
  }
  return 'https://cybershield-ai-api.vercel.app';
})();
```

### Operational Behavior Matrix
- **Local Unified Server (`python backend/run_server.py`)**: Host is `127.0.0.1:8000`. Returns `''` (same-origin static + API).
- **Local Dev Server (`localhost:3000` / Vite / LiveServer)**: Host is `localhost:3000`. Returns `'http://127.0.0.1:8000'`.
- **Production Vercel Host (`cybershield-ai-web-roan.vercel.app`)**: Returns `'https://cybershield-ai-api.vercel.app'`.

---

## 3. Analysis Request Mapping & Error Unpacking

All analysis buttons dispatch to the verified backend endpoints:
1. **URL Inspection**: `POST ${API_BASE}/api/v1/analyze/text` with `{ content: url, source_type: "url" }`
2. **SMS Inspection**: `POST ${API_BASE}/api/v1/analyze/text` with `{ content: sms, source_type: "sms", sender: sender }`
3. **Email Inspection**: `POST ${API_BASE}/api/v1/analyze/text` with `{ content: body, source_type: "email", sender: sender, subject: subject }`
4. **General Text Inspection**: `POST ${API_BASE}/api/v1/analyze/text` with `{ content: text, source_type: "general" }`
5. **Static File Inspection**: `POST ${API_BASE}/api/v1/analyze/file` with `multipart/form-data`
6. **Health Telemetry**: `GET ${API_BASE}/health`

### Enhanced Error Recovery
Response verification now safely unwraps FastAPI standard errors:
```javascript
if (!res.ok) {
  const errJson = await res.json().catch(() => ({}));
  throw new Error(
    errJson.detail ||
    (errJson.error && errJson.error.message) ||
    `Server returned HTTP ${res.status}`
  );
}
```

---

## 4. Production Deployment Record
- **Deployment Command**: `vercel link --project cybershield-ai-web --scope souvik-s-projects4 --yes && vercel --prod --yes`
- **Deployment ID**: `dpl_AeCMSH6ZwdK25QhfnCp2BXBpdSox`
- **Production Alias**: `https://cybershield-ai-web-roan.vercel.app`
- **Framework Preset**: Static (`vercel.json` framework: null, buildCommand: null)
- **Status**: `● READY`
