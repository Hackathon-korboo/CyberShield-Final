# CYBERSHIELD AI 2.0 — PHASE 02 API CONTRACT SPECIFICATION

**Document Version:** 2.0.0  
**Phase:** 02 — Core API and Security Engine  
**Status:** Approved for Implementation  
**Base URL:** `http://127.0.0.1:8000/api/v1`  

---

## 1. Global Response Standards

All API responses conform strictly to the frozen Phase 01 standard response envelope:

### 1.1 Success Response Wrapper
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

### 1.2 Error Response Wrapper
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR | SSRF_PROTECTION_VIOLATION | BAD_REQUEST | INTERNAL_SERVER_ERROR",
    "message": "Human-readable description of error.",
    "correlation_id": "uuid-v4-string",
    "details": [
      {
        "field": "body -> url",
        "message": "Invalid URL scheme. Only http and https are supported.",
        "error_code": "value_error"
      }
    ]
  }
}
```

---

## 2. API Endpoints

### 2.1 POST `/api/v1/analyze/url`
Analyzes a submitted target URL for structural anomalies, SSRF risks, homoglyphs, and known malicious patterns.

#### Request Schema: `UrlAnalysisRequest`
```json
{
  "url": "https://secure-login-bank-verification.com/login"
}
```
- Constraints:
  - `url`: String, min 3 chars, max 2048 chars, valid format, mandatory.

#### Response Schema: `UrlAnalysisResponse`
```json
{
  "success": true,
  "data": {
    "target": "https://secure-login-bank-verification.com/login",
    "target_type": "url",
    "analysis_id": "c71a39f0-2f19-4f81-9b16-43b9db8d4a67",
    "timestamp": "2026-11-14T09:07:00Z",
    "observed_evidence": {
      "normalized_url": "https://secure-login-bank-verification.com/login",
      "scheme": "https",
      "hostname": "secure-login-bank-verification.com",
      "port": 443,
      "path": "/login",
      "ip_address": "198.51.100.24",
      "is_ip_hostname": false,
      "ssrf_safe": true,
      "has_homoglyphs": false
    },
    "heuristic_findings": {
      "risk_level": "SUSPICIOUS",
      "risk_score": 65,
      "indicators_detected": [
        {
          "rule_id": "RULE-URL-002",
          "category": "CREDENTIAL_HARVESTING",
          "severity": "HIGH",
          "evidence": "Path contains 'login' keyword combined with financial lure in hostname.",
          "explanation": "URL mimics legitimate banking authentication portal.",
          "mitigation": "Do not enter credentials or MFA tokens on this site."
        }
      ]
    },
    "status": "COMPLETED"
  },
  "error": null
}
```

---

### 2.2 POST `/api/v1/analyze/email`
Analyzes email text (subject, sender, body) for phishing indicators, social engineering urgency, fake job lures, and suspicious links.

#### Request Schema: `EmailAnalysisRequest`
```json
{
  "subject": "URGENT: Immediate Account Verification Required",
  "sender": "security-alert@bank-verify-service.com",
  "body": "Your bank account has been suspended. Click here to verify your OTP immediately: https://verify-acc.com/login"
}
```
- Constraints:
  - `subject`: String, optional, max 256 chars.
  - `sender`: String, optional, max 256 chars.
  - `body`: String, mandatory, min 1 char, max 50000 chars.

#### Response Schema: `EmailAnalysisResponse`
Contains normalized metadata, extracted URLs, extracted phone numbers, heuristic rule matches, and evidence.

---

### 2.3 POST `/api/v1/analyze/sms`
Analyzes short text messages (SMS, WhatsApp, chat alerts) for urgent lures, OTP/PIN requests, malicious links, and lottery/job fraud.

#### Request Schema: `SmsAnalysisRequest`
```json
{
  "sender": "+1234567890",
  "message": "Dear customer, your card is blocked. Send your 6-digit OTP to unblock now or click http://card-unblock-fake.com"
}
```
- Constraints:
  - `sender`: String, optional, max 64 chars.
  - `message`: String, mandatory, min 1 char, max 2000 chars.

---

## 3. Strict Boundary Rules
- **No AI Claims:** Phase 02 responses contain zero AI assertions.
- **No Blockchain Claims:** Phase 02 responses contain zero on-chain claims.
- **Evidence Provenance:** Every heuristic finding must reference an exact evidence match.
