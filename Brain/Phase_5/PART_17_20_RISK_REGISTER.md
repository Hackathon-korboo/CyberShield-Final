# STAGE 5 (PARTS 17–20) RISK REGISTER

**Document ID:** `Brain/Phase_5/PART_17_20_RISK_REGISTER.md`  
**Date:** 2026-11-14  
**Project:** CyberShield AI 2.0  
**Phase:** Stage 5 — Risk & Threat Defense Subsystem  
**Status:** `ACTIVE_AND_MITIGATED`  

---

## 1. Risk Matrix

| Risk ID | Risk Description | Likelihood | Impact | Severity | Mitigation Implemented | Residual Status |
|---|---|:---:|:---:|:---:|---|:---:|
| **RSK-S5-001** | SSRF bypass via DNS rebinding or dual-homed DNS answers | Low | Critical | High | `SSRFGuard` inspects all resolved IP addresses; if ANY address is prohibited, request is blocked. | **MITIGATED** |
| **RSK-S5-002** | External Threat Intel feed outage crashing URL scan | Medium | High | High | `ThreatIntelligenceAdapter` implements try/except per feed; failure marks feed as `ERROR` and proceeds with partial results. | **MITIGATED** |
| **RSK-S5-003** | SQLite database lock contention during concurrent writes | Low | Medium | Low | Enabled WAL mode (`PRAGMA journal_mode=WAL;`), foreign keys, and 10.0s connection timeouts. | **MITIGATED** |
| **RSK-S5-004** | Prompt injection overriding system instructions or scam scores | Medium | High | High | Prompt injection quarantine traps injection keywords, isolates untrusted text, and protects deterministic score. | **MITIGATED** |
| **RSK-S5-005** | Accidental on-chain leak of sensitive credentials or message text | Low | Critical | High | `BlockchainAdapter` accepts only the 32-byte `canonical_sha256` digest; raw text is strictly excluded from payload. | **MITIGATED** |
| **RSK-S5-006** | Report tampering by unauthorized actors altering stored risk scores | Low | High | Medium | RFC 8785 canonical hash recomputation in `/reports/verify` immediately detects discrepancies as `MISMATCH`. | **MITIGATED** |
| **RSK-S5-007** | Conflating unconfigured feeds with proof of website safety | Medium | High | Medium | Non-negotiable invariant: Absence of match or unconfigured status attaches mandatory disclaimer. | **MITIGATED** |
| **RSK-S5-008** | Secret key leakage through error traces or OpenAPI schemas | Low | Critical | High | SecretStr masking, global sanitized exception handlers, and exclusion of credentials from public routes. | **MITIGATED** |

---

## 2. Residual Operational Considerations

1. **Live Threat Feeds:** When deploying to production with live API keys for Google Safe Browsing and URLhaus, external egress must be restricted strictly to provider API endpoints.
2. **Blockchain Gas & RPC Costs:** When connecting to a live EVM network, gas limits and transaction queueing must be configured to prevent unhandled node timeouts.
3. **Database Archival:** Over high-volume enterprise operations, historical reports in SQLite should be partitioned or archived periodically.
