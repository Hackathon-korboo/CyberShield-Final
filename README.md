# CyberShield-Final — CyberShield AI 2.0

**Next-Generation Multi-Vector Autonomous Cybersecurity & Threat Intelligence Platform**  
*Team:* **DON'T STOP** | *Adamas Offline Hackathon* · *Track:* **Cybersecurity & Digital Trust**

---

## 🌐 Live Platform & Release Links

| Resource | URL |
|---|---|
| **Production Web Application** | [https://cybershield-ai-web-roan.vercel.app](https://cybershield-ai-web-roan.vercel.app) |
| **Production Backend API** | [https://cybershield-ai-api.vercel.app](https://cybershield-ai-api.vercel.app) |
| **Interactive API Documentation (Swagger)** | [https://cybershield-ai-api.vercel.app/docs](https://cybershield-ai-api.vercel.app/docs) |
| **Formal ReDoc Reference** | [https://cybershield-ai-api.vercel.app/redoc](https://cybershield-ai-api.vercel.app/redoc) |
| **GitHub Organization Repository** | [https://github.com/Hackathon-korboo/CyberShield-Final](https://github.com/Hackathon-korboo/CyberShield-Final) |
| **Project Presentation (Slide Deck)** | `ADD_GOOGLE_DRIVE_PRESENTATION_LINK_HERE` |

---

## 🛑 Problem Statement

Modern cyber threats have evolved rapidly beyond traditional malware binaries. Attackers now weaponize human psychology through sophisticated, multi-vector social engineering schemes:

1. **Multi-Vector Threat Proliferation:** Deceptive digital threats arrive across disconnected channels—SMS smishing (electricity bill cutoffs, fake traffic e-challans), targeted email phishing (enterprise credential harvesting), high-pressure chat coercion ("Digital Arrest" CBI intimidation), fake remote job/loan traps, and typosquatted URLs.
2. **Failure of Conventional Antivirus:** Legacy signature-based endpoint tools inspect files on disk; they cannot parse psychological urgency, manipulative linguistic intent, or evasive web redirection patterns.
3. **Flaws in Naive LLM Implementations:** Generic AI wrappers suffer from severe privacy vulnerabilities (leaking sensitive user PII to external models), prompt injection susceptibility (attackers instructing the model to return "SAFE"), and hallucinated, non-reproducible risk scores.

---

## 💡 Proposed Solution: CyberShield AI 2.0

**CyberShield AI 2.0** solves these challenges through a defense-in-depth, zero-trust architecture:

- **Multi-Vector Ingestion:** Dedicated specialized analyzers for URLs, SMS, Emails, Raw Text, and Static Files.
- **Automated PII Minimization:** Real-time sanitization of Aadhaar, PAN, credit card numbers, phone numbers, and UPI IDs *before* any external reasoning.
- **Prompt Injection Defense:** Multi-layer quarantine isolating system instruction overrides, jailbreaks, and delimiter escapes.
- **Decoupled AI & Calibrated Scoring:** Google Gemini 2.0 provides deep contextual and linguistic threat reasoning, while an authoritative **Deterministic Risk Engine** computes reproducible, calibrated scores (0–100) using correlation deduplication (`CORRELATION_CONFIG`) and strict severity baselines.
- **Decentralized Evidence Tamper-Proofing:** Threat report data is hashed using RFC 8785 canonical JSON digests and anchored to an Ethereum smart contract registry (`ThreatReportRegistry.sol`).
- **Interactive 3D WebGL Command Center:** Real-time cyber operations interface featuring a persistent procedural Three.js robotic jellyfish visualizer, responsive telemetry, and transparent verdict breakdowns.

---

## ⚡ Core Architecture & Integrated Subsystems

```
                                      ┌─────────────────────────────────────────┐
                                      │        CyberShield AI 2.0 Engine        │
                                      └────────────────────┬────────────────────┘
                                                           │
          ┌───────────────────────┬────────────────────────┼────────────────────────┬───────────────────────┐
          │                       │                        │                        │                       │
          ▼                       ▼                        ▼                        ▼                       ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  URL / Web Scan  │    │  SMS / Smishing  │    │  Email Phishing  │    │  Text / Fraud    │    │ File Safe Audit  │
│  SSRF Protection │    │  KYC / Utility   │    │  Brand Spoofing  │    │  Digital Arrest  │    │  Magic Bytes     │
│  Domain Anomaly  │    │  Lottery / Prize │    │  Credential Lure │    │  UPI Fraud / Job │    │  Archive Bomb    │
└─────────┬────────┘    └─────────┬────────┘    └─────────┬────────┘    └─────────┬────────┘    └─────────┬────────┘
          │                       │                        │                        │                       │
          └───────────────────────┴────────────────────────┼────────────────────────┴───────────────────────┘
                                                           │
                                                           ▼
                                      ┌─────────────────────────────────────────┐
                                      │   Layer 1: Input Sanitization & Bounds  │
                                      │   Layer 2: PII Redaction & Prompt Shield│
                                      │   Layer 3: External Threat Intel (VT)   │
                                      │   Layer 4: Gemini AI Contextual Analysis│
                                      │   Layer 5: Calibrated Deterministic Risk│
                                      │   Layer 6: Blockchain RFC 8785 Hashing  │
                                      └────────────────────┬────────────────────┘
                                                           │
                                                           ▼
                                      ┌─────────────────────────────────────────┐
                                      │ Interactive Web UI & Unified Reports    │
                                      │ http://127.0.0.1:8000/ (WebGL Dashboard)│
                                      └─────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend Core** | Python 3.13 / 3.12, FastAPI 0.115+, Starlette, Pydantic v2, Pydantic-Settings |
| **AI Intelligence** | Google Gemini 2.0 API (`google-genai`), Zero-Downtime Deterministic Fallback Engine |
| **External Threat Intel** | VirusTotal v3 REST API, Google Safe Browsing Adapter |
| **Privacy & Security** | Regex & Token PII Redactor (PAN/Aadhaar/Cards/UPI), Prompt Injection Shield |
| **Blockchain & Trust** | Solidity (`ThreatReportRegistry.sol`), Web3.py, RFC 8785 Canonical JSON Hasher |
| **Frontend UI/UX** | Pure HTML5, CSS3 Custom Properties, Modern JavaScript (ES6+), Three.js r128 (WebGL) |
| **Testing & Quality** | Pytest 9.2+, Pytest-Asyncio, HTTPX TestClient (245 Automated Tests) |
| **Hosting & DevOps** | Vercel Serverless Functions (FastAPI Python Runtime), GitHub Actions / CI |

---

## 👥 Hackathon Team — DON'T STOP

| Member | Module & Responsibility | Status |
|---|---|---|
| **Member 1** | **Backend Foundation & Deterministic Security Architecture:** Core FastAPI foundation, deterministic scoring pipeline, SSRF defense, SQLite persistence, and Parts 01–22 security engine. | **Active & Integrated** |
| **Member 2 (Lead)** | **AI Scam Intelligence & Threat Intelligence Service:** Dual-engine Gemini 2.0 integration, PII redaction, prompt injection guard, VirusTotal enrichment, and static file inspection. | **Active & Integrated** |
| **Member 3** | **Blockchain Trust & Cryptographic Verification:** Smart contract registry (`ThreatReportRegistry.sol`), RFC 8785 canonical JSON hashing, and evidence tamper-proofing. | **Active & Integrated** |
| **Member 4** | **Frontend Experience & 3D WebGL Command Center:** Cyberpunk operations UI, persistent procedural Three.js jellyfish background, responsive lab controls, and live telemetry. | **Active & Integrated** |

---

## 🚀 Quick Start Guide

### Prerequisites
- Windows 10/11, Linux, or macOS
- Python 3.11, 3.12, or 3.13
- Google Chrome, Edge, or modern web browser

### One-Click Windows Launchers

#### 1. Start CyberShield AI 2.0
Double-click `Start.bat` or run in terminal:
```cmd
Start.bat
```
`Start.bat` automatically:
- Resolves the project directory and detects the virtual environment.
- Pre-flights module imports and validates network configuration.
- Checks port 8000 availability.
- Spawns the dedicated server console.
- Polls the active health probe until operational.
- Launches the interactive Web Application at `http://127.0.0.1:8000/`.

#### 2. Safe Server Shutdown
Double-click `STOP_CyberShield.bat` or run:
```cmd
STOP_CyberShield.bat
```
Safely terminates background server process trees on port 8000 and cleans up temporary state without affecting other applications.

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env` in the project root:

```cmd
copy .env.example .env
```

Configure your API keys in `.env`:
```env
# Server Network Configuration
HOST=127.0.0.1
PORT=8000
ENVIRONMENT=development
LOG_LEVEL=INFO

# Google Gemini API (Contextual Threat Reasoning)
GEMINI_API_KEY="your_gemini_api_key_here"
GEMINI_MODEL=gemini-3.1-flash-lite

# VirusTotal API (External Domain & URL Threat Intelligence)
VIRUSTOTAL_API_KEY="your_virustotal_api_key_here"

# Security & Privacy Controls
ENABLE_PROMPT_INJECTION_SHIELD=true
ENABLE_PII_REDACTION=true
ENFORCE_ZERO_TRUST_VALIDATION=true
```

> **Note:** If external API keys are left blank or offline, CyberShield AI 2.0 automatically fails over to the local deterministic heuristic engine with zero downtime.

---

## 📡 Operational API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Interactive Web Application & Security Lab |
| `/docs` | GET | Interactive Swagger UI API Explorer |
| `/redoc` | GET | Formal ReDoc API Reference |
| `/api/v1/health` | GET | Full Subsystem Telemetry & Health Probe |
| `/api/v1/analyze/text` | POST | Evidence-Based Scam & Threat Analysis (SMS/Email/Text) |
| `/api/v1/analyze/file` | POST | Safe Static Non-Execution File & Archive Inspection |
| `/api/v1/scan-url` | POST | Core URL Analysis & Unified Threat Report Pipeline |
| `/api/v1/reports/verify` | POST | RFC 8785 Canonical Hash & Blockchain Verification |
| `/api/v1/config/providers` | GET | Live Provider Connectivity & Quota Telemetry |

---

## 🧪 Comprehensive Regression Testing

The platform includes 245 automated unit, integration, and security tests.

To run the complete test suite:
```cmd
.venv\Scripts\activate.bat
pytest backend/tests -v
```

### Verified Test Subsystems
- **SSRF Defense Suite:** Loopback, private IP ranges, cloud metadata, IPv6 dual-homing evasion.
- **Prompt Injection Guard:** System instruction override, delimiter evasion, and jailbreak quarantine.
- **Risk Scoring Calibration:** Monotonicity, correlation deduplication, and differentiated category scoring.
- **Blockchain Verification:** RFC 8785 canonical digest computation and contract state simulation.
- **API Contract Conformance:** URL, Email, SMS, File, and Health check schemas.

---

## 🔒 Security & Privacy Policy

- **Zero-Trust Input Handling:** Every payload is treated as untrusted, sanitized, and boundary-checked.
- **Real-Time PII Minimization:** Phone numbers, email addresses, and financial identifiers are redacted prior to external AI reasoning.
- **Zero Secrets in Code:** Actual credentials and `.env` files are strictly excluded from version control via hardened `.gitignore`.
