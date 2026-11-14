# CYBERSHIELD AI 2.0 — BACKEND INTEGRATION DEPENDENCIES

**Document Version:** 2.0.0  
**Phase:** 01 — Backend Foundation & Architecture  
**Part:** 02 — Backend Architecture Planning  
**Status:** Approved for Implementation  

---

## 1. Overview

This document specifies the integration boundaries, protocols, and external interfaces between the CyberShield AI 2.0 FastAPI backend and its interacting subsystems.

---

## 2. Subsystem Integration Matrix

| Subsystem | Integration Protocol | Communication Pattern | Key Integration Requirements | Fallback Mechanism |
|---|---|---|---|---|
| **Frontend UI (React/Vite)** | HTTP / REST (JSON) | Request-Response via CORS | Clear Pydantic response models, HTTP status codes, Correlation ID tracing | Standardized error envelope with actionable error codes |
| **Browser Extension** | HTTP / REST (JSON) | Asynchronous scan calls | Low-latency response (<200ms for heuristic engine), lightweight payloads | Heuristic evaluation returned immediately; AI analysis deferred |
| **AI Engine (Google Gemini)** | HTTPS (REST or SDK) | Asynchronous client call | API key authentication via `GEMINI_API_KEY` (SecretStr), prompt templating, response schema enforcement | If unconfigured or timed out, system returns heuristic findings and flags AI as `UNAVAILABLE` |
| **Blockchain / Web3 (EVM)** | JSON-RPC over HTTPS/WSS | Read-only smart contract calls | Provider URL via `WEB3_PROVIDER_URI` (SecretStr), contract address & ABI | If RPC unavailable, system returns `BLOCKCHAIN_VERIFICATION_SKIPPED` |
| **Local Threat Feeds / Heuristics** | In-process execution | Synchronous / Async Python calls | Pure offline computation, regex matching, homoglyph character tables | Zero external dependency; always active |

---

## 3. Frontend Integration Contract
1. **Endpoint Versioning:** All public endpoints follow `/api/v1/` prefix.
2. **CORS Headers:** Backend dynamically reflects configured allowed origins (`http://localhost:3000`, `http://localhost:5173`) while denying wildcard origins when credentials/cookies are enabled.
3. **Response Structure Uniformity:** Every successful response carries a standard root structure with `success: true` and relevant data payload.
4. **Error Predictability:** All errors conform to `{ "success": false, "error": { "code": "...", "message": "...", "correlation_id": "..." } }`.

---

## 4. AI Engine Integration Contract (Phase 03 Preparation)
1. **Secret Isolation:** The Gemini API key is loaded via `Settings.gemini_api_key` as a `SecretStr`.
2. **Sanitization:** User input is stripped of dangerous characters or injection markers before inclusion in LLM prompt templates.
3. **Structured JSON Output:** Prompts will require the model to return valid JSON with explicit confidence metrics and reasoning.
4. **Resilience & Timeouts:** AI engine calls must enforce strict timeouts (e.g. 5.0 seconds max) to avoid blocking HTTP workers.

---

## 5. Blockchain Integration Contract (Phase 04 Preparation)
1. **Web3 Connection:** Configured with `WEB3_PROVIDER_URI`. If omitted, Web3 services initialize in disabled/mock state.
2. **Read-Only Operation:** Phase 01–04 backend only performs read-only contract calls (e.g. checking whether a contract or domain hash is present in a verified trust registry).
3. **Non-Blocking Execution:** Blockchain RPC calls must be executed within asynchronous worker pools or async Web3 methods to prevent event loop starvation.

---

## 6. Runtime & Operating System Compatibility
- **OS Support:** Windows 10/11 (PowerShell & Command Prompt), Linux (Ubuntu 22.04+), macOS.
- **Python Version:** Python 3.11+ strictly supported.
- **Path Handling:** All internal path resolution uses standard `pathlib.Path` with OS-agnostic separators.
