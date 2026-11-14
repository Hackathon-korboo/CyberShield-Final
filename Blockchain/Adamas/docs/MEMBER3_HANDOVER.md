# CyberShield AI 2.0 — Member 3 Integration & Handover Guide

**Target Audience:** Member 1 (Core Backend Lead) & Member 4 (Frontend Lead)  
**Author:** Member 3 (Security Engineering, Cryptography & Blockchain)  
**Modules Delivered:**
1. `security/ssrf_validator.py` (`SSRFValidator`, `SSRFValidationResult`)
2. `security/evidence_hasher.py` (`EvidenceHasher`, `IntegrityResult`)
3. `security/blockchain_adapter.py` (`BlockchainAdapter`)
4. `contracts/ThreatReportRegistry.sol` (Audited Smart Contract with RBAC)

---

## 1. Quick Integration for Member 1 (FastAPI Backend)

### Step 1: Add SSRF Preflight to `/api/v1/scan-url`

Before fetching headers or making external network requests to user-submitted URLs, run the preflight check:

```python
from fastapi import HTTPException
from security.ssrf_validator import SSRFValidator

@app.post("/api/v1/scan-url")
async def scan_url(request: ScanUrlRequest):
    # 1. Enforce SSRF preflight protection
    validation = SSRFValidator.validate_url(request.url, resolve_dns=True)
    if not validation.is_safe:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "URL failed security preflight checks",
                "reason": validation.blocked_reason,
                "violation_category": validation.violation_category,
            }
        )

    # 2. Proceed with safe inspection using validation.normalized_url
    target_url = validation.normalized_url
    # ... inspection logic ...
```

### Step 2: Handle Redirects Safely

If your HTTP client follows redirects, revalidate the destination before following:

```python
redirect_validation = SSRFValidator.validate_redirect(current_url, redirect_location)
if not redirect_validation.is_safe:
    raise HTTPException(
        status_code=400,
        detail=f"Prohibited redirect destination blocked: {redirect_validation.blocked_reason}"
    )
```

### Step 3: Embed Evidence Hashing in Final Report Generation

When compiling the final report dictionary, compute the integrity block:

```python
from security.evidence_hasher import EvidenceHasher

# In your report generation function:
def finalize_threat_report(report_data: dict) -> dict:
    # Compute deterministic SHA-256 evidence fingerprint
    evidence_hash = EvidenceHasher.hash_report(report_data, algorithm="sha256")

    # Inject Member 1's shared API integrity structure:
    report_data["integrity"] = {
        "status": "verified",
        "evidence_hash": evidence_hash,
    }
    return report_data
```

### Step 4: Add `/api/v1/reports/verify` Endpoint

```python
@app.post("/api/v1/reports/verify")
async def verify_report_integrity(payload: VerifyReportRequest):
    result = EvidenceHasher.verify_integrity(
        report_data=payload.report_data,
        expected_hash=payload.expected_hash,
        algorithm="sha256",
    )
    # Returns strictly: {"integrity": {"status": "verified" | "failed", "evidence_hash": "..."}}
    return result.to_api_contract()
```

---

## 2. Quick Integration for Member 4 (Frontend)

The frontend can display the integrity badge in the report view based on `report.integrity.status`:

| Status | Badge Color | Label | Tooltip / Description |
|---|---|---|---|
| `verified` | 🟢 Green | **Integrity Verified** | Cryptographic fingerprint matches analytical evidence bit-for-bit. |
| `failed` | 🔴 Red | **Tampering Detected** | Report data has been modified since fingerprint registration. |
| `not_available` | ⚪ Gray | **Integrity Unavailable** | Cryptographic fingerprint was not provided or could not be computed. |

### Sample JSON Response from Backend:
```json
{
  "scan_id": "CSR-20261114-001",
  "submitted_input": {
    "type": "url",
    "value": "https://suspicious-login.com"
  },
  "risk": {
    "classification": "high",
    "score": 85
  },
  "observed_evidence": [
    "Domain registered 2 days ago",
    "TLS certificate issuer mismatch",
    "LoginForm targeting external credentials"
  ],
  "integrity": {
    "status": "verified",
    "evidence_hash": "a45e75faee6006f0e34c9c1b712c40c7e29bb315b8cf0f1a92ce8df981e4b3fc"
  }
}
```

---

## 3. Running Verification Tests
To run all tests and verify all security gates anytime:
```bash
python run_security_suite.py
```
Expected output: `22 passed, 0 failed, 100% pass rate`.
