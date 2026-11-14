# CYBERSHIELD AI 2.0 — BACKEND ARCHITECTURE SPECIFICATION

**Document Version:** 2.0.0  
**Phase:** 01 — Backend Foundation & Architecture  
**Part:** 02 — Backend Architecture Planning  
**Status:** Approved for Implementation  
**Architect:** Senior Backend Engineer & Software Architect  

---

## 1. Architectural Vision & Core Principles

CyberShield AI 2.0 is an enterprise-grade cyber threat analysis platform engineered to protect users from malicious URLs, phishing attacks, credential harvesters, social engineering communications, and decentralized Web3 scams.

### Core Architectural Principles
1. **Separation of Concerns:** Strict isolation between API routing, payload validation, business orchestration, deterministic security heuristics, AI reasoning, and blockchain trust registries.
2. **Defensive Triad Verification (Evidence vs. Heuristic vs. AI):** 
   - *Observed Evidence:* Cryptographic, network, protocol, or DNS facts (e.g., domain age, IP address, SSL certificate, redirect chain).
   - *Heuristic Analysis:* Deterministic rule-based scoring (e.g., homoglyphs, brand spoofing keywords, entropy, lexical patterns).
   - *AI Inference:* Probabilistic intent analysis and social engineering categorization (e.g., via Google Gemini). AI predictions must **never** be presented as confirmed empirical facts or sole justification for fraud labels.
   - *Blockchain Trust Layer:* Decentralized blacklist/whitelist registry and smart contract security verification via Web3.
3. **Fail-Safe & Resilient:** If external AI or blockchain services are slow or unavailable, the deterministic security engine must still provide immediate, non-blocking threat protection.
4. **Zero-Trust Input Handling:** All input (URLs, headers, query params, email bodies) is untrusted. Robust SSRF protection prevents intranet probing, loopback resolution, and DNS rebinding.
5. **Privacy & Security by Design:** Zero persistence of plaintext credentials, zero logging of raw tokens or user secrets, and strict masking of sensitive fields.

---

## 2. High-Level System Architecture Diagram

```
+-----------------------------------------------------------------------+
|                         CLIENT CONSUMERS                              |
|   (Web Dashboard [React/Vite], Browser Extension, API Consumers)      |
+-----------------------------------------------------------------------+
                                   |  (JSON over HTTPS)
                                   v
+-----------------------------------------------------------------------+
|                    FASTAPI APPLICATION GATEWAY                        |
|  - CORS Middleware (Origin whitelist, credential support)             |
|  - Security Headers (HSTS, X-Content-Type-Options, Frame Options)     |
|  - Request Tracing (Unique Correlation ID)                           |
|  - Global Exception Sanitizer (RFC 7807 compatible error envelope)    |
+-----------------------------------------------------------------------+
                                   |
         +-------------------------+-------------------------+
         |                                                   |
         v                                                   v
+-----------------------+                         +---------------------+
|    SYSTEM ROUTES      |                         |     CORE API V1     |
| - GET /api/v1/health  |                         | - /analyze/url      |
| - GET /               |                         | - /analyze/message  |
| - GET /docs, /redoc   |                         | - /trust/verify     |
+-----------------------+                         +---------------------+
                                                             |
                                                             v
+-----------------------------------------------------------------------+
|                         ORCHESTRATION SERVICES                        |
|                     (backend/app/services/)                          |
|  Coordinates data flow across engines, aggregates risk scores,        |
|  applies fallback policies, formats structured audit responses.       |
+-----------------------------------------------------------------------+
         |                          |                           |
         v                          v                           v
+------------------+      +-------------------+      +------------------+
| HEURISTIC ENGINE |      |    AI ENGINE      |      |    BLOCKCHAIN    |
| (Local / Fast)   |      | (Google Gemini)   |      |   TRUST ENGINE   |
| - Lexical rules  |      | - Intent Analysis |      | (Web3 / EVM)     |
| - Homoglyph det. |      | - Social Eng.     |      | - Token/Contract |
| - SSRF & IP safe |      | - Nuance/Context  |      | - Trust Registry |
| - Brand mimicry  |      | - Explanation gen |      | - Tamper Log     |
+------------------+      +-------------------+      +------------------+
```

---

## 3. Layered Module Architecture

The backend codebase is structured strictly into layered tiers with unidirectional dependencies:

```
[API Layer: api/routes, api/dependencies]
         │ (calls)
         ▼
[Service Layer: services/]
         │ (orchestrates)
         ▼
[Engine Layer: engines/ (Heuristic, AI, Blockchain)]
         │ (uses)
         ▼
[Core & Schemas: core/ (config, security, exceptions), schemas/ (Pydantic models)]
         │ (shared)
         ▼
[Utility Layer: utils/]
```

### Dependency Rules:
- **Rule 1:** `core` and `schemas` must never import from `services`, `engines`, or `api`.
- **Rule 2:** `engines` must never import from `services` or `api`.
- **Rule 3:** `api/routes` must only handle HTTP concerns (request parsing, response status, dependency injection) and delegate all business logic to `services`.
- **Rule 4:** `utils` are pure helper functions without domain state.

---

## 4. Error Handling Strategy

All API endpoints return standard, predictable JSON error envelopes. Unhandled internal exceptions are intercepted by global exception handlers to prevent raw tracebacks, internal file paths, or credentials from leaking to clients.

### Standard Error Schema
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR | RESOURCE_NOT_FOUND | SERVICE_UNAVAILABLE | RATE_LIMITED | INTERNAL_ERROR",
    "message": "Human-readable sanitized error description.",
    "correlation_id": "c1f78b54-...",
    "details": []
  }
}
```

---

## 5. Security & Secret Protection Strategy

1. **Pydantic Settings with SecretStr:** All sensitive environment variables (e.g., `GEMINI_API_KEY`, `WEB3_PROVIDER_URI`) are declared as `SecretStr`. They cannot be printed or serialized in logs without explicit `.get_secret_value()`.
2. **Logging Sanitization Filter:** A custom logging filter scrubs tokens, passwords, and authorization headers from logs.
3. **Safe Defaults:** If optional services are unconfigured (e.g. Gemini key not provided), the system gracefully disables those modules and falls back to deterministic heuristics without crashing.
4. **CORS Policy:** Default configuration restricts allowed origins to explicit frontend URLs (`localhost:3000`, `localhost:5173`) with production origins configured through environment variables.

---

## 6. Future Phase Support Roadmap

This architecture forms the foundation for upcoming phases:
- **PHASE 02:** Core API and Security Engine (URL parsing, SSRF guard, lexical heuristics, threat rule catalog).
- **PHASE 03:** AI Integration (Gemini client, prompt engineering, structured AI reasoning output).
- **PHASE 04:** Risk Assessment and Trust Integration (Composite risk scoring algorithm, Web3 trust registry verification).
- **PHASE 05:** Integration Testing, Stabilization & Benchmarking.
