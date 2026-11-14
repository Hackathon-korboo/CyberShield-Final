# CYBERSHIELD AI 2.0 — MEMBER 3 FILE MERGE MAPPING

**Generated:** 2026-11-14T13:45:00Z  
**Project:** CyberShield AI 2.0  
**Source Directory:** `Blockchain/Adamas/`  
**Destination Directory:** `backend/app/services/blockchain/`, `backend/app/engines/`, `blockchain/`, `backend/tests/`  
**Backup Snapshot:** `Brain/BACKUP_MEMBER3_MERGE_20261114_133000/`  

---

## 1. FILE-BY-FILE MERGE INVENTORY & CLASSIFICATION

| # | Source File (`Blockchain/Adamas/`) | Destination File | Category | Rationale & Action Summary |
|---|---|---|---|---|
| 1 | `contracts/ThreatReportRegistry.sol` (v2.2) | `blockchain/contracts/ThreatReportRegistry.sol`<br>`backend/app/services/blockchain/contracts/ThreatReportRegistry.sol` | **COPIED** | Mirrored production Solidity 0.8.24 registry smart contract with non-reentrant state, owner registrar revocation, and `generateReportId` namespacing. |
| 2 | `artifacts/ThreatReportRegistry.json` | `blockchain/artifacts/ThreatReportRegistry.json`<br>`artifacts/ThreatReportRegistry.json`<br>`backend/app/services/blockchain/artifacts/ThreatReportRegistry.json` | **COPIED** | Production compiled contract artifact containing complete ABI (23 items) and EVM bytecode for local node instantiation. |
| 3 | `security/evidence_hasher.py` | `backend/app/services/blockchain/evidence_hasher.py` | **COPIED & ENHANCED** | Integrated pure-Python Keccak-256 bit-exact engine, `EvidenceHasher` canonical serializer, `IntegrityResult` dataclass, and added `_keccak256` module export. |
| 4 | `security/blockchain_adapter.py` | `backend/app/services/blockchain/adapter.py` | **MERGED** | Merged Member 3 Web3 contract interaction logic (unlocked account safety, dynamic chain detection, nonce management, receipt polling, post-transaction readback) into Member 1's Pydantic-based `BlockchainAdapter`. Maintained honest `NOT_REGISTERED` fallback. |
| 5 | `security/ssrf_validator.py` | `backend/app/engines/ssrf_guard.py`<br>`Blockchain/Adamas/security/ssrf_validator.py` | **MERGED & REMEDIATED** | Remediated Phase 5 known issue in source `ssrf_validator.py` by supporting relative and protocol-relative redirect URLs with port preservation and traversal normalization. Extended `backend/app/engines/ssrf_guard.py` with `validate_redirect`. |
| 6 | `security/__init__.py` | `backend/app/services/blockchain/__init__.py` | **MERGED** | Re-exported `BlockchainAdapter`, `EvidenceHasher`, `IntegrityResult`, `compute_keccak_hash`, and `derive_report_id` to unify import semantics. |
| 7 | `tests/test_cryptography.py` | `backend/tests/test_member3_cryptography.py` | **COPIED & INTEGRATED** | Verified canonical normalization determinism, genuine Keccak-256 vs SHA-256 distinctness, Ethereum test vectors, and tamper detection directly on backend modules. |
| 8 | `tests/test_api_contract.py` | `backend/tests/test_member3_api_contract.py` | **COPIED & INTEGRATED** | Verified Member 1/Member 3 shared contract `{"integrity": {"status": "...", "evidence_hash": "..."}}` and Pydantic v2 schema compliance. |
| 9 | `tests/test_ssrf_security.py` | `backend/tests/test_member3_ssrf_security.py`<br>`Blockchain/Adamas/tests/test_ssrf_security.py` | **ENHANCED & INTEGRATED** | Added 12 new regression subtests verifying relative redirects, parent traversal, port preservation, and private network rejection. |
| 10 | `tests/test_blockchain.py` | `backend/tests/test_member3_blockchain_modes.py` | **SYNTHESIZED & EXPANDED** | Built comprehensive 5-mode test suite covering unconfigured (Mode A), Hardhat devnet (Mode B), unreachable/undeployed (Mode C), transaction revert (Mode D), and full registration/readback (Mode E). |
| 11 | `docs/*` (10 Markdown files) | `Blockchain/Adamas/docs/` | **NOT COPIED (PRESERVED AS REFERENCE)** | Preserved Member 3's original handover documentation, audit reports, and threat modeling in place to avoid duplicate documentation clutter in the core tree. |
| 12 | `FINAL_SHAREABLE_PACKAGE/*` | `Blockchain/Adamas/FINAL_SHAREABLE_PACKAGE/` | **NOT COPIED (STANDALONE ARTIFACT)** | Standalone offline zip and HTML handover package created by Member 3 for offline submission; left intact in source tree. |
| 13 | `build_shareable_package.py`, `generate_handover_html.py`, `verify_package.py`, `run_security_suite.py` | `Blockchain/Adamas/` | **NOT COPIED (STANDALONE SCRIPTS)** | Standalone utility and verification scripts specific to Member 3 standalone packaging; left untouched in source directory. |

---

## 2. MODIFIED EXISTING DESTINATION FILES

| File Path | Nature of Modification | Regression Protection |
|---|---|---|
| `backend/app/services/blockchain/adapter.py` | Integrated Web3 contract calls, account safety checks, receipt polling, and readback verification while preserving Pydantic response models (`ReportIntegrityInfo`, `ReportVerificationResult`). | Fully backward-compatible; passes all `test_part19_db_blockchain.py` tests. |
| `backend/app/services/blockchain/canonical_hasher.py` | Added Keccak-256 computation (`compute_keccak_hash`) and EVM report ID derivation (`derive_report_id`) alongside RFC 8785 canonical SHA-256. | RFC 8785 canonical hashing untouched. |
| `backend/app/engines/ssrf_guard.py` | Added `validate_redirect` supporting relative paths, scheme changes, and port preservation. | Loopback, private IP, and cloud metadata blocking preserved without regressions. |
| `backend/app/services/risk/report_generator.py` | Wired `BlockchainAdapter.generate_integrity_info()` into report construction. | Unconfigured mode generates honest `NOT_REGISTERED` without fake transactions. |

---

## 3. NEW INTEGRATED TEST SUITES

| Test File | Target Modules | Number of Tests | Status |
|---|---|---|---|
| `backend/tests/test_member3_blockchain_modes.py` | `BlockchainAdapter`, `ThreatReportRegistry` contract | 6 tests (Modes A–E) | **PASSED** |
| `backend/tests/test_member3_cryptography.py` | `EvidenceHasher`, `canonical_hasher` | 11 tests | **PASSED** |
| `backend/tests/test_member3_api_contract.py` | `IntegrityResult`, `ReportIntegrityInfo` | 5 tests | **PASSED** |
| `backend/tests/test_member3_ssrf_security.py` | `SSRFGuard`, `validate_redirect` | 5 tests | **PASSED** |
| `Blockchain/Adamas/tests/*` (Source) | Member 3 original test suite | 39 tests, 45 subtests | **PASSED** |
