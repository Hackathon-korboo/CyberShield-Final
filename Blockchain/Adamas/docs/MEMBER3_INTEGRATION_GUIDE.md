# CyberShield AI 2.0 — Member 3 Integration Guide (v2.2)

**Audience:** Member 1 (FastAPI Backend Lead) & Member 4 (React Frontend Lead)  
**Author:** Member 3 (Security Engineering, Cryptography & Blockchain)  
**Date:** November 14, 2026  
**Status:** 🟡 **B. READY WITH DOCUMENTED LIMITATIONS**  

---

## 1. Quick Component Overview

Member 3 delivers three audited, battle-tested Python modules located in `security/`:

| Module | Core Classes | Primary Responsibility |
|---|---|---|
| `security/ssrf_validator.py` | `SSRFValidator`, `PinnedSession`, `PinnedHTTPAdapter` | Outbound URL preflight validation, DNS pinning, loopback/private IP blocking, redirect revalidation, proxy bypass prevention. |
| `security/evidence_hasher.py` | `EvidenceHasher`, `IntegrityResult` | Deterministic SHA-256 evidence hashing, bit-exact Keccak-256 derivation, canonical serialization, tamper detection. |
| `security/blockchain_adapter.py` | `BlockchainAdapter` | Smart contract anchoring on Ethereum/Hardhat, readback verification, dynamic chain ID query, transparent off-chain fallback. |

---

## 2. Drop-In Code for Member 1 (FastAPI Backend)

### 2.1 Non-Blocking Outbound Scan Endpoint (`POST /api/v1/scan-url`)

This endpoint ensures:
1. **Preflight SSRF Check:** Blocks private/internal IPs before opening connections.
2. **Zero Double-Resolution Drift:** Passes `validation_result=val` to `PinnedSession.get()`, reusing the validated IP.
3. **No Proxy Bypass:** `PinnedSession` enforces `trust_env = False` so environment proxies cannot redirect the connection.
4. **No Event Loop Starvation:** Uses `await asyncio.to_thread` to run blocking network I/O outside FastAPI's event loop.

```python
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from security.ssrf_validator import (
    SSRFValidator,
    PinnedSession,
    SSRFSecurityException,
    SSRFRedirectBlockedException,
)

app = FastAPI()

# Create a shared, thread-safe pinned session for outbound scanning
scanner_session = PinnedSession(max_redirects=3, timeout=5.0)

class ScanUrlRequest(BaseModel):
    url: str

@app.post("/api/v1/scan-url")
async def scan_url(request: ScanUrlRequest):
    # STEP 1: Preflight URL validation & DNS resolution
    val = SSRFValidator.validate_url(request.url, resolve_dns=True)
    if not val.is_safe:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "URL blocked by security preflight policy",
                "reason": val.blocked_reason,
                "violation_category": val.violation_category,
                "normalized_url": val.normalized_url,
            }
        )

    # STEP 2: Execute DNS-pinned HTTP GET without blocking the async event loop
    try:
        response = await asyncio.to_thread(
            scanner_session.get,
            val.normalized_url,
            validation_result=val,
        )
    except SSRFRedirectBlockedException as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "SSRF Redirect Blocked",
                "reason": str(e),
                "violation_category": "redirect_violation"
            }
        )
    except SSRFSecurityException as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "SSRF Security Violation",
                "reason": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Target connection failed: {e}")

    # STEP 3: Return inspected data to threat analysis engine
    return {
        "status_code": response.status_code,
        "resolved_ip": val.resolved_ip,
        "connected_ip": response.pinned_ip,
        "normalized_url": val.normalized_url,
        "headers": dict(response.headers),
        "content_length": len(response.content),
    }
```

---

### 2.2 Report Finalization with Evidence Hashing

When Member 1's AI & threat scoring pipeline completes the report dictionary, inject the integrity block before returning:

```python
from security.evidence_hasher import EvidenceHasher

def finalize_threat_report(raw_report: dict) -> dict:
    """
    Computes a canonical SHA-256 fingerprint of the report evidence
    and injects the schema-compliant integrity dictionary.
    Supports both string list indicators and dictionary indicators.
    """
    # 1. Compute canonical SHA-256 evidence hash
    evidence_hash = EvidenceHasher.hash_report(raw_report, algorithm="sha256")

    # 2. Inject Member 1 contract schema:
    # {"integrity": {"status": "verified", "evidence_hash": "<64-hex>"}}
    raw_report["integrity"] = {
        "status": "verified",
        "evidence_hash": evidence_hash
    }
    return raw_report
```

---

### 2.3 Report Verification Endpoint (`POST /api/v1/reports/verify`)

Allows clients or downstream auditors to verify whether a report has been altered:

```python
class VerifyReportRequest(BaseModel):
    report_data: dict
    expected_hash: str

@app.post("/api/v1/reports/verify")
async def verify_report_integrity(payload: VerifyReportRequest):
    # Verify report integrity using EvidenceHasher
    result = EvidenceHasher.verify_integrity(
        report_data=payload.report_data,
        expected_hash=payload.expected_hash,
        algorithm="sha256"
    )

    # Returns:
    # {"integrity": {"status": "verified" | "failed", "evidence_hash": "..."}}
    return result.to_api_contract()
```

---

### 2.4 Blockchain Anchoring Endpoint (`POST /api/v1/reports/anchor`)

Optional endpoint to anchor a finalized report to the smart contract:

```python
from security.blockchain_adapter import BlockchainAdapter

# Initialize blockchain adapter (reads configuration from environment variables)
# If no RPC URL or contract address is configured, automatically runs in fallback mode
blockchain = BlockchainAdapter()

class AnchorReportRequest(BaseModel):
    report: dict

@app.post("/api/v1/reports/anchor")
async def anchor_report_to_blockchain(payload: AnchorReportRequest):
    result = blockchain.register_threat_report(payload.report)
    return {
        "report_id": result.get("report_id"),
        "report_hash": result.get("report_hash"),
        "is_on_chain": result.get("is_on_chain"),
        "transaction_hash": result.get("transaction_hash"),
        "block_number": result.get("block_number"),
        "blockchain_network": result.get("blockchain_network"),
        "integrity": result.get("report_integrity", {}).get("integrity", {
            "status": "verified",
            "evidence_hash": result.get("sha256_evidence_hash")
        })
    }
```

---

## 3. Configuration & Environment Variables

```bash
# ==============================================================================
# CyberShield AI 2.0 — Security & Blockchain Environment Configuration
# ==============================================================================

# Blockchain RPC Provider URL (optional; if omitted, operates in transparent fallback mode)
ETH_RPC_URL=http://127.0.0.1:8545

# Deployed ThreatReportRegistry Smart Contract Address
CONTRACT_ADDRESS=0x5FbDB2315678afecb367f032d93F642f64180aa3

# Signer Private Key (Required for writing transactions to external chains like Sepolia)
ETH_PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

# SSRF Timeout Configuration (seconds)
SSRF_REQUEST_TIMEOUT=5.0
SSRF_MAX_REDIRECTS=3
```

---

## 4. Integration Guide for Member 4 (Frontend Lead)

### 4.1 TypeScript Types

```typescript
export interface ReportIntegrity {
  status: "verified" | "failed" | "not_available";
  evidence_hash: string | null;
}

export interface ThreatReportResponse {
  report_id?: string;
  url: string;
  threat_level: "low" | "medium" | "high" | "critical";
  confidence: number;
  indicators: string[];
  integrity: ReportIntegrity;
  blockchain?: {
    is_on_chain: boolean;
    network: string;
    transaction_hash?: string;
  };
}
```

### 4.2 React Badge Component (`IntegrityBadge.tsx`)

```tsx
import React from "react";
import { ReportIntegrity } from "./types";

interface Props {
  integrity: ReportIntegrity;
}

export const IntegrityBadge: React.FC<Props> = ({ integrity }) => {
  if (integrity.status === "verified") {
    return (
      <div className="flex items-center gap-2 px-3 py-1 bg-green-950/40 border border-green-500/50 rounded-full text-green-400 text-xs font-mono">
        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
        <span>Integrity Verified</span>
        <span className="text-gray-400 text-[10px]">({integrity.evidence_hash?.substring(0, 8)}...)</span>
      </div>
    );
  }

  if (integrity.status === "failed") {
    return (
      <div className="flex items-center gap-2 px-3 py-1 bg-red-950/40 border border-red-500/50 rounded-full text-red-400 text-xs font-mono">
        <span className="w-2 h-2 rounded-full bg-red-500" />
        <span>Tamper Warning: Digest Mismatch!</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 px-3 py-1 bg-gray-900 border border-gray-700 rounded-full text-gray-400 text-xs font-mono">
      <span>Integrity Not Available</span>
    </div>
  );
};
```
