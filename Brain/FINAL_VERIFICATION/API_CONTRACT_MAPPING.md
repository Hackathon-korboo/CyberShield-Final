# CYBERSHIELD AI 2.0 — API CONTRACT MAPPING
## Comprehensive Route Specification, Request Schemas & Response Serialization

**Project:** CyberShield AI 2.0  
**Base URL:** `http://127.0.0.1:8000/api/v1`  
**Execution Timestamp:** 2026-11-14T15:24:00+05:30  

---

## 1. ENDPOINT REGISTRY

| Method | Endpoint | Source Member | Description | Auth / Security |
|---|---|---|---|---|
| `GET` | `/health` | Member 1 | System operational readiness & subsystem statuses | Public |
| `GET` | `/` | Member 4 / Member 1 | Dual resolution: Web UI (HTML) or API metadata (JSON) | Public |
| `GET` | `/styles.css` | Member 4 | Application stylesheet | Public |
| `GET` | `/main.js` | Member 4 | Application client JavaScript | Public |
| `GET` | `/wizard` | Member 2 | Interactive API Configuration Wizard UI | Public |
| `GET` | `/setup` | Member 2 | Setup wizard alias | Public |
| `POST` | `/api/v1/analyze/url` | Member 1 | Heuristic URL deep scan with SSRF protection | Public |
| `POST` | `/api/v1/analyze/email` | Member 1 | Email header, sender spoofing, and body inspection | Public |
| `POST` | `/api/v1/analyze/sms` | Member 1 | SMS smishing and social engineering analysis | Public |
| `POST` | `/api/v1/analyze/text` | Member 2 | Evidence-based scam text analysis with PII minimization | Public |
| `POST` | `/api/v1/analyze/file` | Member 2 | Safe in-memory static file inspection | Public |
| `POST` | `/api/v1/privacy/redact` | Member 2 | Standalone PII detection and redaction | Public |
| `POST` | `/api/v1/security/check-injection`| Member 2 | Standalone prompt injection / jailbreak detection | Public |
| `GET` | `/api/v1/config/providers` | Member 2 | Masked status of external cyber threat providers | Public |
| `POST` | `/api/v1/config/test` | Member 2 | Live backend authentication check | **Localhost Only (403)** |
| `POST` | `/api/v1/config/save` | Member 2 | Persist credentials to local `.env` | **Localhost Only (403)** |
| `GET` | `/api/v1/meta/categories` | Member 2 | Enumeration of supported threat categories | Public |
| `GET` | `/api/v1/integrations` | Member 2 | Status of 4-member integration registry | Public |
| `GET` | `/api/v1/scans` | Member 1 | Paginated history of submitted threat scans | Public |
| `GET` | `/api/v1/reports/unified/{id}` | Member 1 | Unified Threat Report with RFC 8785 canonical hash | Public |
| `GET` | `/api/v1/reports/unified/{id}/verify-blockchain`| Member 1/3 | On-chain / cryptographic report verification | Public |

---

## 2. KEY REQUEST & RESPONSE SCHEMAS

### A. Text Scam Analysis (`POST /api/v1/analyze/text`)
```json
// Request:
{
  "content": "string (1 - 50,000 characters)",
  "source_type": "sms | email | social_media | messaging | unknown",
  "enable_gemini": true,
  "enable_virustotal": true,
  "redact_pii": true
}

// Response:
{
  "analysis_id": "uuid-string",
  "timestamp": "ISO-8601-UTC",
  "risk_level": "BENIGN | LOW | MEDIUM | HIGH | CRITICAL",
  "risk_score": 0.0 - 100.0,
  "primary_category": "SCAM_SMS | PHISHING_EMAIL | ...",
  "detected_categories": ["string"],
  "confidence_score": 0.0 - 1.0,
  "observed_evidence": [...],
  "ai_assessment": "string",
  "mitigation_recommendations": [...],
  "pii_redacted_content": "string",
  "pii_entities_found": [...],
  "engine_used": "string",
  "prompt_injection_detected": false
}
```

### B. Safe File Analysis (`POST /api/v1/analyze/file`)
- **Content-Type:** `multipart/form-data`
- **Field:** `file` (Binary upload)
- **Response:**
  - `filename`, `file_size_bytes`, `sha256`, `md5`, `mime_type`, `detected_file_type`
  - `is_executable`, `is_archive`, `risk_level`, `risk_score`
  - `suspicious_indicators`, `archive_report` (if ZIP/archive)

### C. Unified Threat Report (`GET /api/v1/reports/unified/{id}`)
- **Response Model:** `UnifiedThreatReport`
  - `scan_id`, `submitted_input`, `input_type`, `timestamp`
  - `risk_assessment`: `classification`, `risk_score`, `rules_triggered`, `has_policy_violation`
  - `report_integrity`: `canonical_sha256`, `blockchain_status`, `network`, `contract_address`, `transaction_hash`
