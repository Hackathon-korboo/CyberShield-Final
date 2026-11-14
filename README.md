# CyberShield-Final — CyberShield AI 2.0

**Next-Generation Multi-Vector Autonomous Cybersecurity & Threat Intelligence Platform**  
*Team:* **DON'T STOP** | *Adamas Offline Hackathon*

---

## 🛡️ Executive Summary

**CyberShield AI 2.0** is an enterprise-grade, zero-trust cybersecurity threat intelligence platform designed to detect, analyze, and neutralize modern cyber threats across multiple communication vectors. It unifies deterministic heuristics, external threat intelligence feeds, Google Gemini generative AI reasoning, cryptographic tamper-proofing on the Ethereum blockchain, and an interactive 3D WebGL cyber operations dashboard.

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

### 1. Multi-Vector Security Lab (Member 1 & Member 2)
- **URL / Web Threat Analyzer:** Comprehensive URL normalization, homoglyph punycode detection, suspicious TLD flagging, deep subdomain inspection, and multi-layer SSRF validation (RFC 1918, RFC 3927 link-local, loopback, and cloud metadata blocking).
- **SMS / Smishing Intelligence:** Deep pattern recognition for KYC expiration threats, banking suspension lures, electricity bill disconnection extortion, unsolicited lottery prizes, and advance-fee demands.
- **Email Phishing Defense:** Detects brand impersonation, urgent credential verification deadlines, deceptive account restoration links, and payment fraud lures.
- **Universal Text Analyzer:** Identifies high-pressure social engineering coercion, "Digital Arrest" intimidation schemes, fake law enforcement threats (CBI, Police, ED), and deceptive UPI QR payment directives.
- **Safe Static File Inspection:** Safe, non-execution inspection validating MIME types, magic byte headers, SHA-256 hashes, executable disguise evasion, and compressed archive safety (zip bomb & path traversal detection).

### 2. Calibrated Deterministic Risk Scoring & Scam Differentiation
- **Decoupled AI Architecture:** AI models provide contextual extraction, intent detection, and tactical breakdown without hallucinating arbitrary numerical scores.
- **Correlation-Based Deduplication:** Indicators are grouped into documented correlation groups (`CORR-OTP-THEFT`, `CORR-ADVANCE-FEE`, `CORR-CREDENTIAL-HARVEST`, `CORR-IMPERSONATION`, `CORR-URGENCY`, `CORR-SUSPICIOUS-LINK`), suppressing score inflation from repetitive or rephrased indicators.
- **Severity Floor Model:** Calibrated severity baselines guarantee that identical evidence yields identical scores, while distinct scam categories receive evidence-calibrated scores.
- **Strict Authority Policy:** `CONFIRMED MALICIOUS` status is strictly reserved for verified external threat intelligence matches (e.g. VirusTotal confirmed malicious domains), while synthetic scam patterns are accurately classified as `LIKELY FRAUDULENT MESSAGE` or `SUSPICIOUS`.

### 3. Blockchain Evidence & Trust Registry (Member 3)
- **RFC 8785 Canonical JSON Hashing:** Produces deterministic, byte-identical SHA-256 evidence digests from threat report payloads.
- **Smart Contract Registry:** `ThreatReportRegistry.sol` deployed on EVM-compatible networks records scan report hashes, timestamps, reporter identities, and tamper-proof verification states.
- **Verification Endpoint:** `POST /api/v1/reports/verify` independently validates report integrity against the canonical hash.

### 4. Interactive 3D Cyber Operations Dashboard (Member 4)
- **WebGL Dynamic Scene:** Built with pure HTML5/CSS3/ES6 and Three.js, rendering a responsive real-time cybersecurity command center.
- **5 Dedicated Input Modes:** Independent panels for URL, SMS, Email, Text, and File analysis with 1-click clipboard paste, input clearing, format validators, and live test presets.
- **Transparent Verdict Cards:** Real-time presentation of risk level, calibrated score, detected threat category, "Why this score?" breakdown, AI confidence, and mitigation advice.

---

## 🚀 Quick Start Guide

### Prerequisites
- Windows 10/11, Linux, or macOS
- Python 3.10, 3.11, or 3.12
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
| `http://127.0.0.1:8000/` | GET | Interactive Web Application & Security Lab |
| `http://127.0.0.1:8000/docs` | GET | Interactive Swagger UI API Explorer |
| `http://127.0.0.1:8000/redoc` | GET | Formal ReDoc API Reference |
| `http://127.0.0.1:8000/api/v1/health` | GET | Full Subsystem Telemetry & Health Probe |
| `http://127.0.0.1:8000/api/v1/analyze/text` | POST | Evidence-Based Scam & Threat Analysis (SMS/Email/Text) |
| `http://127.0.0.1:8000/api/v1/analyze/file` | POST | Safe Static Non-Execution File & Archive Inspection |
| `http://127.0.0.1:8000/api/v1/scan-url` | POST | Core URL Analysis & Unified Threat Report Pipeline |
| `http://127.0.0.1:8000/api/v1/reports/verify` | POST | RFC 8785 Canonical Hash & Blockchain Verification |
| `http://127.0.0.1:8000/api/v1/config/providers` | GET | Live Provider Connectivity & Quota Telemetry |

---

## 🧪 Comprehensive Regression Testing

The platform includes 245+ automated unit, integration, and security tests.

To run the complete test suite:
```cmd
backend\venv\Scripts\activate.bat
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

---

## 👥 Hackathon Team — DON'T STOP

- **Member 1:** Backend Foundation, Deterministic Security Architecture & Parts 01–22 Engine
- **Member 2:** Threat Intelligence Service, File Inspection, Gemini AI & VirusTotal Integration
- **Member 3:** Blockchain Registry, Canonical Hashing & Evidence Tamper-Proofing
- **Member 4:** Frontend UI/UX, Three.js 3D WebGL Dashboard & Security Lab Controls
