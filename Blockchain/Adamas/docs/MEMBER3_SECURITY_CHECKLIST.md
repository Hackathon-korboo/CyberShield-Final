# CyberShield AI 2.0 — Member 3 Security Checklist (v2.2)

**Author:** Member 3 (Security Engineering, Cryptography & Blockchain)  
**Date:** November 14, 2026  
**Status Decision:** 🟡 **B. READY WITH DOCUMENTED LIMITATIONS**  

---

## 1. SSRF & Outbound Inspection Preflight Checklist

| Item # | Security Control | Verification Method | Status | Notes |
|---|---|---|---|---|
| **SSRF-01** | Loopback IPv4 addresses (`127.0.0.0/8`) blocked | Automated unit test | ✅ PASSED | All `127.x.x.x` addresses blocked |
| **SSRF-02** | Loopback IPv6 addresses (`::1`) blocked | Automated unit test | ✅ PASSED | `[::1]` blocked |
| **SSRF-03** | RFC 1918 Private Class A (`10.0.0.0/8`) blocked | Automated unit test | ✅ PASSED | `10.0.0.1` blocked |
| **SSRF-04** | RFC 1918 Private Class B (`172.16.0.0/12`) blocked | Automated unit test | ✅ PASSED | `172.16.0.1` to `172.31.255.255` blocked |
| **SSRF-05** | RFC 1918 Private Class C (`192.168.0.0/16`) blocked | Automated unit test | ✅ PASSED | `192.168.1.1` blocked |
| **SSRF-06** | Link-Local IPv4 (`169.254.0.0/16`) blocked | Automated unit test | ✅ PASSED | Cloud metadata `169.254.169.254` blocked |
| **SSRF-07** | Link-Local IPv6 (`fe80::/10`) blocked | Automated unit test | ✅ PASSED | `[fe80::1]` blocked |
| **SSRF-08** | Decimal integer IP representation blocked | Automated unit test | ✅ PASSED | `http://2130706433/` resolved and blocked |
| **SSRF-09** | Hexadecimal IP representation blocked | Automated unit test | ✅ PASSED | `http://0x7f.1/` resolved and blocked |
| **SSRF-10** | Octal IP representation blocked | Automated unit test | ✅ PASSED | `http://017700000001/` resolved and blocked |
| **SSRF-11** | Dangerous schemes (`file://`, `ftp://`, `gopher://`) blocked | Automated unit test | ✅ PASSED | Only `http` and `https` allowed |
| **SSRF-12** | Non-numeric / malformed ports handled safely | Automated unit test | ✅ PASSED | `:bad` and `:99999` caught without crashing |
| **SSRF-13** | IPv6 square brackets preserved in normalized authority | Automated unit test | ✅ PASSED | RFC 3986 format `[2001:...]` preserved |
| **SSRF-14** | Legitimate non-standard ports preserved | Automated unit test | ✅ PASSED | Port `:8443` preserved for legitimate URLs |
| **SSRF-15** | DNS Pinning implemented for TCP socket | Functional test | ✅ PASSED | `PinnedHTTPAdapter` connects directly to validated IP |
| **SSRF-16** | TLS SNI hostname preservation | Code & test verification | ✅ PASSED | TLS handshake passes `server_hostname` |
| **SSRF-17** | HTTP `Host` header preservation | Code & test verification | ✅ PASSED | Requests send proper `Host: <hostname>` |
| **SSRF-18** | Outbound 3xx redirect revalidation | Automated unit test | ✅ PASSED | `PinnedSession` intercepts 3xx and rechecks policy |
| **SSRF-19** | Environment proxy bypass blocked | Automated unit test | ✅ PASSED | `requests.Session.trust_env = False` enforced |
| **SSRF-20** | Double DNS resolution avoided | Automated unit test | ✅ PASSED | Pass pre-computed `validation_result` to reuse IP |
| **SSRF-21** | Sub-5ms preflight validation latency | Benchmark | ✅ PASSED | Typical latency < 2ms |

---

## 2. Cryptographic Hashing & Integrity Checklist

| Item # | Security Control | Verification Method | Status | Notes |
|---|---|---|---|---|
| **CRYP-01** | SHA-256 evidence hashing implemented | Automated unit test | ✅ PASSED | Standard 64-char hex digest |
| **CRYP-02** | Ethereum Keccak-256 implemented | Automated unit test | ✅ PASSED | Pure-Python bit-exact Keccak-f[1600] engine |
| **CRYP-03** | Keccak-256 distinct from SHA-256 | Automated unit test | ✅ PASSED | No identical digests between algorithms |
| **CRYP-04** | Standard Ethereum test vectors verified | Automated unit test | ✅ PASSED | Tested against official Ethereum vectors |
| **CRYP-05** | Cross-language test vector match | Cross-test | ✅ PASSED | Matches TypeScript & Hardhat baseline |
| **CRYP-06** | Unsupported algorithm throws `ValueError` | Automated unit test | ✅ PASSED | Rejects `"md5"`, `"sha1"` explicitly |
| **CRYP-07** | Canonical JSON serialization determinism | Automated unit test | ✅ PASSED | Independent of dict insertion order |
| **CRYP-08** | Array element sorting determinism | Automated unit test | ✅ PASSED | Indicators list order normalized |
| **CRYP-09** | Resilient normalizer for string lists | Automated unit test | ✅ PASSED | Supports plain string lists and dicts |
| **CRYP-10** | Tamper detection on `severity` field | Automated unit test | ✅ PASSED | Detects modification from `"high"` to `"low"` |
| **CRYP-11** | Tamper detection on `confidence` field | Automated unit test | ✅ PASSED | Detects modification from `0.94` to `0.50` |
| **CRYP-12** | Tamper detection on `indicators` IOC array | Automated unit test | ✅ PASSED | Detects injected/modified IOC |
| **CRYP-13** | Fast hashing throughput | Benchmark | ✅ PASSED | < 0.2ms (SHA-256), < 1.5ms (Keccak-256) |

---

## 3. Smart Contract & Blockchain Controls Checklist

| Item # | Security Control | Verification Method | Status | Notes |
|---|---|---|---|---|
| **BC-01** | Role-Based Access Control (RBAC) enforced | Hardhat EVM test | ✅ PASSED | `onlyAuthorized` modifier restricts registration |
| **BC-02** | Owner can authorize new registrars | Hardhat EVM test | ✅ PASSED | `setRegistrar(addr, true)` works |
| **BC-03** | Owner can revoke existing registrars | Hardhat EVM test | ✅ PASSED | `setRegistrar(addr, false)` works |
| **BC-04** | Unauthorized accounts cannot register reports | Hardhat EVM test | ✅ PASSED | Reverts with `"ThreatReportRegistry: caller is not authorized"` |
| **BC-05** | Ownership transfer revokes prior owner rights | Hardhat EVM test | ✅ PASSED | Prior owner registrar privileges automatically revoked |
| **BC-06** | Zero-hash registration rejected | Hardhat EVM test | ✅ PASSED | Reverts with `"ThreatReportRegistry: invalid report hash"` |
| **BC-07** | Duplicate report hash registration rejected | Hardhat EVM test | ✅ PASSED | Reverts with `"ThreatReportRegistry: report already registered"` |
| **BC-08** | Incremental `reportCount` tracking | Hardhat EVM test | ✅ PASSED | Increments by 1 on every successful registration |
| **BC-09** | On-chain report verification function | Hardhat EVM test | ✅ PASSED | `verifyReport` returns true for matching hashes |
| **BC-10** | On-chain state readback function | Hardhat EVM test | ✅ PASSED | `getReport` returns full struct |
| **BC-11** | Dynamic chain ID query | Automated unit test | ✅ PASSED | Automatically queries `w3.eth.chain_id` |
| **BC-12** | Signer enforcement on external chains | Automated unit test | ✅ PASSED | Rejects unlocked accounts on Sepolia (11155111) |
| **BC-13** | Honest off-chain fallback transparency | Automated unit test | ✅ PASSED | Sets `is_on_chain=False`, network="off-chain" |
| **BC-14** | Fallback tamper detection operational | Automated unit test | ✅ PASSED | Detects modified evidence in fallback mode |
| **BC-15** | Report ID mathematical derivation consistency | Automated unit test | ✅ PASSED | `derive_report_id(report_hash) == report_id` |

---

## 4. FastAPI & API Contract Checklist

| Item # | Security Control | Verification Method | Status | Notes |
|---|---|---|---|---|
| **API-01** | Exact schema match: `{"integrity": {"status": ..., "evidence_hash": ...}}` | Automated unit test | ✅ PASSED | Verified against Member 1 specifications |
| **API-02** | `status` restricted to `"verified"`, `"failed"`, `"not_available"` | Automated unit test | ✅ PASSED | Rejects arbitrary string states |
| **API-03** | `evidence_hash` contains exact 64-character hex string | Automated unit test | ✅ PASSED | Canonical SHA-256 fingerprint |
| **API-04** | Pydantic v2 `BaseModel` parsing compatibility | Automated unit test | ✅ PASSED | Validates via `model_validate` |
| **API-05** | Report finalizer preserves existing fields intact | Automated unit test | ✅ PASSED | Upstream detector fields never corrupted |
| **API-06** | Non-blocking async event loop offload | Automated unit test | ✅ PASSED | Compatible with `asyncio.to_thread` |

---

## 5. Integration Boundaries & Handover Status

* **Status:** 🟡 **B. READY WITH DOCUMENTED LIMITATIONS**
* **Standalone Modules:** 100% Verified and Passing (51/51 tests).
* **Live System Integration:** Requires wiring into Member 1's FastAPI repository and Member 4's React dashboard.
