# CYBERSHIELD AI 2.0 — PHASE 02 IMPLEMENTATION PLAN
## CORE API AND SECURITY ENGINE (PART 05 TO PART 10)

**Document Version:** 2.0.0  
**Phase:** 02 — Core API and Security Engine  
**Status:** In Progress (Execution Plan)  
**Workspace:** `D:\Adamas offline Hackathon`  
**Engineer:** Senior Backend Engineer & Security Architect  

---

## 1. Executive Summary & Phase Objectives

Phase 02 builds upon the frozen Phase 01 backend foundation by introducing the deterministic core security engine, input normalization layers, Server-Side Request Forgery (SSRF) defense mechanisms, rule-based threat indicator extractors, and the core API endpoints (`POST /api/v1/analyze/url`, `POST /api/v1/analyze/email`, `POST /api/v1/analyze/sms`).

In strict alignment with Phase 01 architecture and Master Rules:
- No Gemini AI or Blockchain logic is implemented in this phase (reserved for Phase 03 & 04).
- The heuristic security engine operates purely deterministically, extracting evidence without fabricating predictions.
- Observed evidence is explicitly separated from heuristic indicators and risk classifications.
- SSRF defenses prevent DNS rebinding, internal loopback scanning, and cloud metadata access.
- All Phase 01 health checks and routes remain fully compatible.

---

## 2. Part Breakdown & Work Packages

### PART 05: Pydantic Schema Development
- Request models: `UrlAnalysisRequest`, `EmailAnalysisRequest`, `SmsAnalysisRequest`.
- Response models: `UrlAnalysisResponse`, `EmailAnalysisResponse`, `SmsAnalysisResponse`, `SecurityIndicator`, `ObservedEvidence`.
- Input validation: Field length boundaries, format regex, defensive defaults.
- Schema modularity in `backend/app/schemas/`.

### PART 06: API Endpoint Development
- Routes:
  - `POST /api/v1/analyze/url`
  - `POST /api/v1/analyze/email`
  - `POST /api/v1/analyze/sms`
- Integration with application factory in `backend/app/main.py`.
- Preservation of `/` and `/api/v1/health` routes.
- Swagger UI and OpenAPI documentation generation.

### PART 07: Input Validation and Normalization
- Validation and sanitization in `backend/app/utils/sanitizer.py` and dedicated validators.
- URL scheme enforcement (http/https only), lowercase normalization, punycode decoding.
- Email header/body parsing and whitespace normalization.
- SMS/message text cleaning and control character removal.

### PART 08: SSRF Protection and Safe URL Handling
- Preflight security validator in `backend/app/engines/ssrf_guard.py`.
- IP address classification (IPv4, IPv6, mapped IPv6, link-local, loopback, private RFC 1918, cloud metadata 169.254.169.254).
- Safe DNS resolution and multi-A/AAAA record inspection.
- Defensive preflight checks without arbitrary external requests.

### PART 09: Security Rules and Threat Indicator Engine
- Deterministic heuristic rule engine in `backend/app/engines/rules/`.
- Detection catalog:
  - Homoglyph & Punycode brand spoofing.
  - IP-based hostnames.
  - Credential harvesting keywords ("login", "verify", "password", "bank").
  - Urgent social engineering markers ("immediate action required", "account suspended").
  - Fake job/internship phishing lures.
  - Phone and URL extraction from email/SMS text.
- Transparent rule reporting: Rule ID, severity, evidence snippet, explanation, recommended mitigation.

### PART 10: Core Security Engine Integration
- Service orchestration in `backend/app/services/threat_service.py`.
- End-to-end integration: API Route -> Validation -> SSRF Guard -> Rule Engine -> Standardized Response.
- Integration tests in `backend/tests/test_api_analysis.py`, `backend/tests/test_ssrf.py`, `backend/tests/test_rules.py`.

---

## 3. Strict Phase Constraints
- Zero AI/Gemini calls; AI subsystem remains explicitly flagged `disabled / not configured in Phase 2`.
- Zero Web3/Blockchain calls; Blockchain subsystem remains explicitly flagged `disabled / not configured in Phase 2`.
- Never claim confirmed fraud; findings are reported as deterministic heuristic evidence and risk indicators.
- Phase 1 frozen code remains intact.
