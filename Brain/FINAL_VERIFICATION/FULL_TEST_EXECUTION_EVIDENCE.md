# CYBERSHIELD AI 2.0 — FULL TEST EXECUTION EVIDENCE DOSSIER

**Test Runner:** `pytest 9.2.0`  
**Python Runtime:** `Python 3.11.9` (`backend\venv\Scripts\python.exe`)  
**OS Platform:** Windows 10/11 (win32)  
**Execution Timestamp:** 2026-11-14T13:55:34Z  
**Overall Result:** **265 PASSED, 2 SKIPPED, 0 FAILED**  

---

## 1. PRIMARY BACKEND TEST EXECUTION LOG (`backend/tests`)

Command Executed:
`.\backend\venv\Scripts\python.exe -m pytest backend/tests -v`

### Execution Metrics:
- **Total Tests Collected:** 228
- **Passed:** 226
- **Skipped:** 2
- **Failed:** 0
- **Duration:** 16.09 seconds
- **Pass Rate:** **100% of runnable tests**

### Module Breakdown:

| Test Module | Scope / Description | Collected | Passed | Failed | Skipped | Status |
|---|---|:---:|:---:|:---:|:---:|:---:|
| `test_ai_client.py` | Gemini client initialization, timeout, rate limits | 10 | 10 | 0 | 0 | **PASS** |
| `test_ai_fallback.py` | Circuit breaker, timeout fallback, disabled toggle | 5 | 5 | 0 | 0 | **PASS** |
| `test_ai_integration.py` | Composite AI endpoints, SSRF blocking, envelopes | 7 | 7 | 0 | 0 | **PASS** |
| `test_ai_live.py` | Live Gemini API network connectivity | 2 | 0 | 0 | 2 | **SKIPPED** |
| `test_ai_scam_analysis.py` | Scam analysis, fence stripping, schema validation | 7 | 7 | 0 | 0 | **PASS** |
| `test_ai_security.py` | Prompt injection defense, boundary delimiters | 10 | 10 | 0 | 0 | **PASS** |
| `test_api_analysis.py` | Deterministic URL/Email/SMS analysis endpoints | 10 | 10 | 0 | 0 | **PASS** |
| `test_config.py` | Pydantic settings, env loading, secret masking | 5 | 5 | 0 | 0 | **PASS** |
| `test_health.py` | Health check routes (`/api/v1/health`, `/health`) | 4 | 4 | 0 | 0 | **PASS** |
| `test_member3_api_contract.py` | Member 1/3 shared integrity envelope contract | 5 | 5 | 0 | 0 | **PASS** |
| `test_member3_blockchain_modes.py` | Modes A, B, C, D, E blockchain execution | 6 | 6 | 0 | 0 | **PASS** |
| `test_member3_cryptography.py` | Pure Keccak-256 vectors, canonical JSON, tampering | 11 | 11 | 0 | 0 | **PASS** |
| `test_member3_ssrf_security.py` | Redirect revalidation, loopback, private IP | 5 | 5 | 0 | 0 | **PASS** |
| `test_part13_evidence.py` | Evidence collection and standardization | 7 | 7 | 0 | 0 | **PASS** |
| `test_part14_severity.py` | Severity classification and indicator floor | 6 | 6 | 0 | 0 | **PASS** |
| `test_part15_risk_engine.py` | Deterministic risk scoring and floor guarantees | 15 | 15 | 0 | 0 | **PASS** |
| `test_part16_report_generator.py` | Unified Threat Report schemas and recommendations | 13 | 13 | 0 | 0 | **PASS** |
| `test_part17_core_api.py` | Core scan routes (`/scan-url`, `/scans`, pagination) | 9 | 9 | 0 | 0 | **PASS** |
| `test_part18_threat_intel.py` | Threat Intelligence aggregation and offline corpus | 5 | 5 | 0 | 0 | **PASS** |
| `test_part19_db_blockchain.py` | SQLite WAL persistence, canonical hashing | 7 | 7 | 0 | 0 | **PASS** |
| `test_part20_security_e2e.py` | End-to-end security scenarios and risk invariants | 30 | 30 | 0 | 0 | **PASS** |
| `test_risk_pipeline_integration.py` | Multi-stage pipeline integration | 5 | 5 | 0 | 0 | **PASS** |
| `test_rules.py` | Heuristic detection rules (URL, Email, SMS) | 13 | 13 | 0 | 0 | **PASS** |
| `test_sanitizer.py` | Normalization, Punycode, dot segments, regex | 8 | 8 | 0 | 0 | **PASS** |
| `test_schemas.py` | Request/Response schema validation boundaries | 11 | 11 | 0 | 0 | **PASS** |
| `test_ssrf.py` | Zero-egress SSRF guard preflight checks | 10 | 10 | 0 | 0 | **PASS** |

---

## 2. MEMBER 3 STANDALONE TEST SUITE EXECUTION (`Blockchain/Adamas/tests`)

Command Executed:
`.\backend\venv\Scripts\python.exe -m pytest Blockchain/Adamas/tests -v`

### Execution Metrics:
- **Total Tests Collected:** 39
- **Passed:** 39 (with 45 subtests)
- **Failed:** 0
- **Duration:** 8.90 seconds
- **Pass Rate:** **100%**

### Breakdown by File:
1. `test_api_contract.py`: 7 passed (contract structure, Pydantic v2, async loop offload).
2. `test_blockchain.py`: 5 passed (compilation artifact integrity, off-chain fallback, unlocked account rejection).
3. `test_cryptography.py`: 11 passed (canonical serialization, genuine Keccak-256 test vectors, tamper detection).
4. `test_ssrf_security.py`: 16 passed, 45 subtests passed (redirect revalidation, link-local, loopback, private IPs).

---

## 3. ANALYSIS OF SKIPPED TESTS

Two tests were skipped in `backend/tests/test_ai_live.py`:
1. `test_live_gemini_api_connectivity`: Decorated with `@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="Live Gemini tests require GEMINI_API_KEY")`.
2. `test_live_gemini_health_check`: Decorated with `@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="Live Gemini tests require GEMINI_API_KEY")`.

**Rationale:** These tests are intentionally gated on live credentials to allow the test suite to run in offline, air-gapped competition environments. When the key is unconfigured, the system automatically falls back to deterministic analysis, as verified in `test_ai_fallback.py`.

---

## 4. ANALYSIS OF WARNINGS

A total of 20 warnings were emitted:
- `DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated`: Emitted by Starlette's `TestClient` compatibility layer with AnyIO.
- `DeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead`: Emitted by Starlette's internal exception handler.

**Assessment:** Both warnings originate inside third-party dependencies (`starlette` 0.52.1) and have zero impact on application correctness, performance, or security.
