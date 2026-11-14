# CYBERSHIELD AI 2.0 — BACKEND DATA FLOW SPECIFICATION

**Document Version:** 2.0.0  
**Phase:** 01 — Backend Foundation & Architecture  
**Part:** 02 — Backend Architecture Planning  
**Status:** Approved for Implementation  

---

## 1. Overview

This document specifies the end-to-end data lifecycle for CyberShield AI 2.0, tracing an inbound request from the client through middleware, routing, validation, service orchestration, security engines, and back as a structured, defensive response.

---

## 2. Sequence Diagram: Comprehensive Threat Analysis

```
Client             FastAPI Gateway           Orchestration Service       Heuristic Engine      AI Engine (Gemini)      Blockchain Engine
  |                       |                            |                        |                      |                       |
  |--- POST /analyze ---->|                            |                        |                      |                       |
  |    (Payload JSON)     |-- 1. Assign Correlation ID |                        |                      |                       |
  |                       |-- 2. CORS & Security Hdr   |                        |                      |                       |
  |                       |-- 3. Pydantic Validation   |                        |                      |                       |
  |                       |                            |                        |                      |                       |
  |                       |------ Call analyze() ----->|                        |                      |                       |
  |                       |                            |                        |                      |                       |
  |                       |                            |--- Fast Heuristic ---->|                      |                       |
  |                       |                            |    (SSRF, Lexical,     |                      |                       |
  |                       |                            |     Homoglyphs, IP)    |                      |                       |
  |                       |                            |<-- Return Evidence ----|                      |                       |
  |                       |                            |                                               |                       |
  |                       |                            |--- Request AI Analysis (Context + Sanitized) >|                       |
  |                       |                            |    (Probabilistic Intent / Social Eng.)       |                       |
  |                       |                            |<-- AI Reasoning & Confidence -----------------|                       |
  |                       |                            |                                                                       |
  |                       |                            |--- Query Trust Registry / Web3 Contract ----------------------------->|
  |                       |                            |<-- On-Chain Trust / Blacklist Status ---------------------------------|
  |                       |                            |
  |                       |                            |-- Synthesize Triad Results:
  |                       |                            |   - Observed Evidence (Deterministic)
  |                       |                            |   - Heuristic Score & Flags
  |                       |                            |   - AI Analysis (Probabilistic)
  |                       |                            |   - Blockchain Trust Status
  |                       |                            |   - Composite Risk Level
  |                       |                            |
  |                       |<--- Composite Verdict -----|
  |                       |
  |                       |-- Format Response Model
  |                       |-- Log Request (Masked)
  |<-- 200 OK (JSON) -----|
```

---

## 3. Step-by-Step Processing Pipeline

### Step 1: Ingress & Gateway Middleware
- Inbound HTTP request hits Uvicorn ASGI server and enters Starlette/FastAPI middleware stack.
- `CorrelationIdMiddleware` extracts incoming `X-Correlation-ID` or generates a UUIDv4, attaching it to request state and response headers.
- `CORSMiddleware` validates the `Origin` header against permitted frontend origins.
- `SecurityHeadersMiddleware` injects modern browser defensive headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`).

### Step 2: Route Handling & Input Validation
- Request is dispatched to the matching router (e.g., `backend/app/api/routes/analyze.py`).
- Pydantic models automatically validate incoming JSON structure, types, string constraints, and reject malformed payloads with HTTP 422 Unprocessable Entity.
- Dependency injection supplies singleton service instances and configuration.

### Step 3: Service Layer Orchestration (`ThreatAnalysisService`)
- The service acts as the controller, executing detection engines in an optimal, non-blocking pipeline:
  1. **SSRF Guard & URL Normalizer:** Prevents queries against private IP blocks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.1`, `::1`, link-local, cloud metadata services).
  2. **Deterministic Heuristic Engine:** Runs offline checks (punycode/homoglyph detection, excessive subdomains, known phishing keywords, suspicious TLDs, entropy analysis).
  3. **AI Reasoning Engine (Optional / Asynchronous):** If the URL or message contains social engineering indicators and Gemini API is configured, invokes LLM with structured JSON output schema.
  4. **Blockchain Trust Engine (Optional / Asynchronous):** If the entity involves a decentralized domain (.eth, .crypto) or crypto wallet/contract, queries the Web3 provider for verification.

### Step 4: Separation of Evidence and AI Predictions
To strictly uphold Non-Negotiable Rule 12 & 13:
- Response payloads partition findings into explicit categories:
  ```json
  {
    "target": "example-login-verify.com",
    "risk_level": "HIGH",
    "risk_score": 85,
    "observed_evidence": {
      "ip_address": "198.51.100.24",
      "is_private_ip": false,
      "homoglyph_detected": true,
      "suspicious_keywords": ["login", "verify"]
    },
    "heuristic_findings": {
      "score": 80,
      "flags": ["PUNYCODE_HOMOGLYPH_MATCH", "SUSPICIOUS_KEYWORD_DENSITY"]
    },
    "ai_analysis": {
      "enabled": true,
      "intent_classification": "SUSPECTED_CREDENTIAL_PHISHING",
      "confidence": 0.88,
      "reasoning": "The domain emulates an authentication portal with high likelihood of social engineering intent.",
      "disclaimer": "AI predictions represent probabilistic inferences and must not be treated as confirmed empirical evidence."
    },
    "blockchain_verification": {
      "checked": false,
      "status": "NOT_APPLICABLE"
    }
  }
  ```

### Step 5: Response Serialization & Safe Logging
- Pydantic serializes the response.
- Access logging records HTTP method, endpoint, status code, latency, and correlation ID.
- No sensitive input payloads, authorization headers, or secrets are ever recorded in logs.
