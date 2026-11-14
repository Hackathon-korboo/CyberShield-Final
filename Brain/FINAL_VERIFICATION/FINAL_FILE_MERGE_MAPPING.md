# CYBERSHIELD AI 2.0 — FINAL FILE MERGE MAPPING
## Comprehensive Source-to-Destination Lineage & Integration Directory Map

**Project:** CyberShield AI 2.0  
**Authoritative Destination:** `D:\Adamas offline Hackathon`  
**Execution Timestamp:** 2026-11-14T15:24:00+05:30  

---

## 1. COMPREHENSIVE COMPONENT MAPPING TABLE

| Original Source Location | Unified Destination Path | Integration Status | Role / Content |
|---|---|---|---|
| `member-2-main/.../ai_engine/` | `backend/app/ai_engine/` | Merged & Verified | Heuristic scam engines, IOC extraction, fraud detectors |
| `member-2-main/.../file_analysis/` | `backend/app/file_analysis/` | Merged & Verified | Safe static file & archive inspection |
| `member-2-main/.../gemini/` | `backend/app/gemini/` | Merged & Verified | Google Gemini REST client & fallback logic |
| `member-2-main/.../privacy/` | `backend/app/privacy/` | Merged & Verified | PII detection and redaction engine |
| `member-2-main/.../security/` | `backend/app/security/` | Merged & Verified | Prompt injection guard and input sanitizer |
| `member-2-main/.../threat_models.py` | `backend/app/schemas/threat_models.py` | Merged & Verified | Pydantic v2 schemas for Member 2 features |
| `member-2-main/.../file_service.py` | `backend/app/services/file_service.py` | Merged & Verified | File threat analysis coordinator |
| `member-2-main/.../config_service.py` | `backend/app/services/config_service.py` | Merged & Verified | Dynamic .env credential manager |
| `member-2-main/.../threat_service.py` | `backend/app/services/scam_threat_service.py` | Merged & Verified | Zero-trust scam analysis service |
| `member-2-main/.../virustotal_client.py`| `backend/app/threat_intel/virustotal_client.py`| Merged & Verified | VirusTotal v3 safe reputation adapter |
| `member-2-main/.../wizard.html` | `backend/app/api/templates/wizard.html` | Merged & Verified | Interactive Web UI setup wizard template |
| `member-2-main/.../integrations/` | `integrations/` | Merged & Verified | Multi-member registry & communication adapters |
| `member-2-main/.../index.html` | `frontend/index.html` | Merged & Verified | Medusa JF-4 3D Platform web interface |
| `member-2-main/.../styles.css` | `frontend/styles.css` | Merged & Verified | High-tech dark cyberpunk theme styling |
| `member-2-main/.../main.js` | `frontend/main.js` | Merged & Verified | Client-side API orchestration & Three.js controller |
| `member-2-main/.../assets/` | `frontend/assets/` | Merged & Verified | Three.js r128, procedural jellyfish, icons |
| `member-2-main/.../fonts/` | `frontend/fonts/` | Merged & Verified | Offline-bundled Rajdhani & Orbitron fonts |
| `Blockchain/Adamas/contracts/` | `backend/app/services/blockchain/contracts/` | Preserved | `ThreatReportRegistry.sol` Solidity contract |
| `Blockchain/Adamas/artifacts/` | `backend/app/services/blockchain/artifacts/` | Preserved | Compiled contract ABI & bytecode artifacts |
| `Blockchain/Adamas/adapter/` | `backend/app/services/blockchain/adapter.py` | Preserved | Web3 adapter with honest fallback |
| `Blockchain/Adamas/security/` | `backend/app/services/blockchain/ssrf_validator.py` | Preserved | SSRF validator for EVM endpoints |

---

## 2. MODIFIED & ENHANCED SYSTEM FILES

| File Path | Description of Enhancements |
|---|---|
| `backend/app/risk_app.py` | Extended with Member 2 routes, static asset mounts, and dual HTML/JSON root resolution |
| `backend/app/api/main.py` | Created compatibility re-export routing Member 2 test client to unified `risk_app` |
| `backend/app/api/routes/member2_routes.py` | Created unified REST endpoints for Member 2 capabilities with localhost security protection |
| `backend/app/services/threat_service.py` | Extended with re-exports for `threat_service_instance` and `ThreatIntelligenceService` |
| `backend/app/engine/facade.py` | Created unified facade bridging adapter requests to scam threat & file services |
| `backend/app/engines/ai/client.py` | Refined model fallback to `gemini-3.1-flash-lite` and safe `_UNSPECIFIED` sentinel handling |
| `backend/app/services/config_service.py` | Added automated timestamped backup before credential persistence |
| `integrations/registry.py` | Dynamically connected all 4 member modules with real runtime health status |
| `integrations/member3/adapter.py` | Connected Member 3 adapter directly to canonical RFC 8785 hasher and `BlockchainAdapter` |
| `.env` | Preserved user configuration, configured active operational model `gemini-3.1-flash-lite` |
| `pytest.ini` | Added `pythonpath = .` ensuring seamless module resolution across root and submodules |
