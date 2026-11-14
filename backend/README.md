# CyberShield AI 2.0 — Backend Service

Enterprise-grade, AI-augmented cyber threat intelligence and defensive API platform built with Python and FastAPI.

---

## 1. Prerequisites
- **Python:** 3.11+
- **Package Manager:** `pip`

---

## 2. Environment Setup

### Step A: Create and Activate Virtual Environment (Recommended)
On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

On Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step B: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step C: Configure Environment Variables
Copy the example environment file to `.env`:
```bash
# From workspace root
copy .env.example .env
# Or in Linux/macOS
cp .env.example .env
```
Edit `.env` to configure network binding, CORS origins, or optional API keys.

---

## 3. Running the Backend Locally

Start the full CyberShield AI 2.0 application (mounting Stage 4 & Stage 5 core scan & report routers):
```bash
python -m uvicorn backend.app.risk_app:app --reload --host 127.0.0.1 --port 8000
```

Once running, access:
- **Root Service Info:** `http://127.0.0.1:8000/`
- **Health Check Endpoint:** `http://127.0.0.1:8000/api/v1/health`
- **Core URL Scan Endpoint:** `POST http://127.0.0.1:8000/api/v1/scan-url`
- **Scan Retrieval Endpoint:** `GET http://127.0.0.1:8000/api/v1/scans/{scan_id}`
- **Scan History Endpoint:** `GET http://127.0.0.1:8000/api/v1/scans?limit=20&offset=0`
- **Cryptographic Verification:** `POST http://127.0.0.1:8000/api/v1/reports/verify`
- **Interactive OpenAPI Docs (Swagger UI):** `http://127.0.0.1:8000/docs`
- **Alternative API Docs (ReDoc):** `http://127.0.0.1:8000/redoc`

---

## 4. Running the Test Suite

Execute the automated test suite with pytest:
```bash
python -m pytest backend/tests -v
```

Run focused Stage 5 test suites:
```bash
python -m pytest backend/tests/test_part17_core_api.py -v
python -m pytest backend/tests/test_part18_threat_intel.py -v
python -m pytest backend/tests/test_part19_db_blockchain.py -v
python -m pytest backend/tests/test_part20_security_e2e.py -v
```

---

## 5. Security Principles & Architecture
- **Secret Masking:** All API keys and secrets are loaded as Pydantic `SecretStr` instances and scrubbed from logs by a dedicated logging filter.
- **Defensive Triad:** Observed evidence, heuristic rules, and probabilistic AI inferences are strictly segregated in data schemas.
- **SSRF Protection:** Built-in safeguards protect against intranet and loopback probes.
- **CORS & Security Headers:** Explicit whitelist and browser hardening headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-Correlation-ID`).
