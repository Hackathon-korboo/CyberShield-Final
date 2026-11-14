# CyberShield AI 2.0 — Production API Integration & Contract Audit

**Document Reference:** `Brain/FINAL_VERIFICATION/API_INTEGRATION_AUDIT.md`  
**API Prefix:** `/api/v1`  
**Host & Port:** `http://127.0.0.1:8000`  
**Documentation:** Swagger UI (`/docs`), ReDoc (`/redoc`), OpenAPI Schema (`/openapi.json`)  
**Status:** **AUDITED, LIVE TESTED & PRODUCTION READY**

---

## 1. Executive API Overview

The CyberShield AI 2.0 backend exposes a standardized, high-performance RESTful API adhering strictly to Pydantic V2 schemas and standardized envelope patterns.

All responses use the canonical envelope structure:
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

In the event of client or server errors, the response structure transitions to:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input validation failed for the requested resource.",
    "correlation_id": "37b8d11c-a82e-468b-a745-739c5b1e4586",
    "details": [
      {
        "field": "body -> url",
        "message": "Field required",
        "error_code": "missing"
      }
    ]
  }
}
```

---

## 2. Core Endpoint Specifications

### 1. Unified URL Threat Scan
- **Path:** `POST /api/v1/scan-url`
- **Summary:** End-to-end URL threat investigation, deterministic risk evaluation, AI contextual inference, and database persistence.
- **Request Body (`ScanUrlRequest`):**
  ```json
  {
    "url": "https://secure-login-portal.com/auth"
  }
  ```
  *(Note: `extra='forbid'` is active. Extra keys such as `target_url` are rejected).*
- **Response Model (`StandardResponse[UnifiedThreatReport]`):**
  - Returns `scan_id` (UUID), `submitted_input`, `risk_assessment` (score, classification, rules triggered), `technical_findings`, `ai_inferences`, `recommendations`, `limitations`, and `report_integrity` (canonical SHA-256).
- **Status Codes:** `200 OK`, `400 Bad Request`, `422 Unprocessable Content`.

### 2. Retrieve Persisted Scan Report
- **Path:** `GET /api/v1/scans/{scan_id}`
- **Summary:** Retrieves a historically generated scan report by its unique UUID.
- **Path Parameter:** `scan_id` (UUID string).
- **Response Model (`StandardResponse[UnifiedThreatReport]`):**
  - Returns the exact stored JSON report from SQLite.
- **Status Codes:** `200 OK`, `404 Not Found` (with code `SCAN_NOT_FOUND`).

### 3. Paginated Scan History
- **Path:** `GET /api/v1/scans`
- **Summary:** Lists past scan summaries sorted chronologically descending.
- **Query Parameters:**
  - `limit` (integer, default 20, max 100)
  - `offset` (integer, default 0, min 0)
- **Response Model (`StandardResponse[ScanHistoryResponse]`):**
  ```json
  {
    "success": true,
    "data": {
      "items": [
        {
          "scan_id": "3ca6f66e-7aa1-473f-8b0d-7b56eddb9497",
          "submitted_input": "https://secure-login-portal.com/auth",
          "input_type": "url",
          "classification": "HIGH_RISK",
          "risk_score": 70,
          "timestamp": "2026-11-14T07:40:03.003507Z",
          "canonical_sha256": "9746775d4cb5c92e6d4c523c4d74e3b543a1bb9dfcc000e656c5b5ccf2a84370",
          "blockchain_status": "NOT_REGISTERED"
        }
      ],
      "total_count": 1,
      "limit": 20,
      "offset": 0
    },
    "error": null
  }
  ```
- **Status Codes:** `200 OK`.

### 4. Cryptographic Report Integrity Verification
- **Path:** `POST /api/v1/reports/verify`
- **Summary:** Recomputes RFC 8785 canonical hash from report data and compares it against stored hash to detect unauthorized data modification.
- **Request Body (`VerifyReportRequest`):**
  ```json
  {
    "scan_id": "3ca6f66e-7aa1-473f-8b0d-7b56eddb9497"
  }
  ```
  *(Alternatively accepts an inline `report` object).*
- **Response Model (`StandardResponse[ReportVerificationResult]`):**
  ```json
  {
    "success": true,
    "data": {
      "scan_id": "3ca6f66e-7aa1-473f-8b0d-7b56eddb9497",
      "canonical_sha256": "9746775d4cb5c92e6d4c523c4d74e3b543a1bb9dfcc000e656c5b5ccf2a84370",
      "recomputed_sha256": "9746775d4cb5c92e6d4c523c4d74e3b543a1bb9dfcc000e656c5b5ccf2a84370",
      "integrity_status": "MATCH",
      "is_valid": true,
      "blockchain_status": "NOT_REGISTERED",
      "verified_at": "2026-11-14T07:40:30.143818Z",
      "message": "Cryptographic integrity verified locally; report is NOT_REGISTERED on public blockchain."
    },
    "error": null
  }
  ```
- **Status Codes:** `200 OK`, `404 Not Found`.

### 5. Subsystem Health Probe
- **Path:** `GET /api/v1/health`
- **Summary:** Comprehensive health status of database, heuristic rules, AI provider, threat intel feeds, and blockchain trust registry.
- **Response Model (`StandardResponse[HealthResponse]`):**
  - Returns `status: "healthy"`, `version: "2.0.0"`, and breakdown of each subsystem.
- **Status Codes:** `200 OK`.

### 6. Stage 4 Risk Assessment Engine (Multi-Input)
- **Path:** `POST /api/v1/unified-report`
- **Summary:** Evaluates URLs, emails, or SMS inputs through the Stage 4 deterministic risk pipeline.
- **Request Body (`UnifiedReportRequest`):** Accepts `target_url`, `email_content`, or `sms_content`.
- **Response Model (`StandardResponse[UnifiedThreatReport]`):** Returns the comprehensive threat assessment.
- **Status Codes:** `200 OK`, `422 Unprocessable Content`.

---

## 3. Integration Verification Summary

All endpoints have been live-verified against the running FastAPI instance. Schemas strictly adhere to OpenAPI 3.1 and are ready for consumption by Member 4's React frontend and Member 2/3 adapters.
