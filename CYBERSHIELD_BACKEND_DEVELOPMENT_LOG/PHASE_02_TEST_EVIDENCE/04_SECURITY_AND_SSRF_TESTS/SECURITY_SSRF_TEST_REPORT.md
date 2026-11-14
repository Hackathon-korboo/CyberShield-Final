# PHASE 02 TEST EVIDENCE: 04 — SECURITY AND SSRF TESTS REPORT

**Workspace:** `D:\Adamas offline Hackathon`  
**Test Suite Directory:** `backend/tests/`  
**Category:** Server-Side Request Forgery (SSRF) Protection, Secret Masking & HTTP Security Headers  
**Total Tests in Category:** 15  
**Category Pass Rate:** 100% (15 Passed, 0 Failed, 0 Skipped)  
**Execution Environment:** Windows (PowerShell), Python 3.11.9, pytest 9.2.0  
**Status:** **AWAITING HUMAN VERIFICATION**  

---

## 1. Category Overview & Scope

The Security and SSRF Tests category validates the preflight network boundaries implemented in `backend/app/engines/ssrf_guard.py`, endpoint-level SSRF interception in `POST /api/v1/analyze/url`, defensive secret masking (`get_masked_summary`, `mask_secret`), secret scrubbing log filters (`SecretScrubbingFilter`), and HTTP security response headers (`X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, etc.).

---

## 2. Automated Test Evidence (15 Tests)

### Test 1: `TEST-SEC-01` — `test_ssrf_rejects_loopback_ipv4`
1. **Test ID and Test Name:** `TEST-SEC-01` / `backend/tests/test_ssrf.py::test_ssrf_rejects_loopback_ipv4`
2. **Test Objective:** Verify `SSRFGuard` rejects IPv4 loopback addresses across the entire `127.0.0.0/8` block.
3. **Test Category:** SSRF Defense (IPv4 Loopback)
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** `"http://127.0.0.1/admin"`, `"http://127.0.1.5:8080/metrics"`, `"http://0.0.0.0/"`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_ssrf.py -k test_ssrf_rejects_loopback_ipv4 -v`
7. **Expected Result:** `SSRFValidationResult.is_safe == False`, `blocked_reason` specifies loopback / private IP.
8. **Actual Result:** `is_safe == False` on all 3 loopback URLs.
9. **Evidence:** Pytest terminal output `PASSED [ 86%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** `SSRFGuard.is_ip_private_or_restricted` evaluates destination IPs with Python's `ipaddress` library, flagging `ip_obj.is_loopback` and `ip_obj.is_unspecified`.
12. **Security Significance:** Prevents attackers from scanning, querying, or interacting with services bound strictly to localhost on the backend server.
13. **Conclusion:** IPv4 loopback destinations are completely blocked.

---

### Test 2: `TEST-SEC-02` — `test_ssrf_rejects_localhost_hostname`
1. **Test ID and Test Name:** `TEST-SEC-02` / `backend/tests/test_ssrf.py::test_ssrf_rejects_localhost_hostname`
2. **Test Objective:** Verify `SSRFGuard` blocks the literal hostname `"localhost"` and internal domain suffix namespaces.
3. **Test Category:** SSRF Defense (Internal Hostnames)
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** `"http://localhost/"`, `"http://localhost:8000/api"`, `"http://app.local/"`, `"http://db.internal/"`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_ssrf.py -k test_ssrf_rejects_localhost_hostname -v`
7. **Expected Result:** `is_safe == False` without executing DNS resolution.
8. **Actual Result:** `is_safe == False` across all internal hostname strings.
9. **Evidence:** Pytest terminal output `PASSED [ 88%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** Pre-resolution check in `validate_url` compares hostname against `BLOCKED_HOSTNAMES = {"localhost", "metadata.google.internal", "metadata.internal", "instance-data"}` and checks `.endswith((".local", ".internal"))`.
12. **Security Significance:** Fast-path rejection stops requests directed at local container hostnames or mDNS/Bonjour namespaces.
13. **Conclusion:** Localhost and internal hostname namespaces are rejected before DNS resolution.

---

### Test 3: `TEST-SEC-03` — `test_ssrf_rejects_private_subnets`
1. **Test ID and Test Name:** `TEST-SEC-03` / `backend/tests/test_ssrf.py::test_ssrf_rejects_private_subnets`
2. **Test Objective:** Verify `SSRFGuard` rejects private RFC 1918 IPv4 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).
3. **Test Category:** SSRF Defense (Private RFC 1918)
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** `"http://10.0.0.1/"`, `"http://172.16.0.5:8080/"`, `"http://192.168.1.1/"`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_ssrf.py -k test_ssrf_rejects_private_subnets -v`
7. **Expected Result:** `is_safe == False`, `blocked_reason` identifies private network.
8. **Actual Result:** `is_safe == False` on all private RFC 1918 test vectors.
9. **Evidence:** Pytest terminal output `PASSED [ 89%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** Evaluates `ip_obj.is_private` covering all standard RFC 1918 address allocations.
12. **Security Significance:** Blocks attackers from using CyberShield as a proxy to probe internal corporate intranets, VPC subnets, or staging environments.
13. **Conclusion:** RFC 1918 private subnets are strictly blocked.

---

### Test 4: `TEST-SEC-04` — `test_ssrf_rejects_cloud_metadata`
1. **Test ID and Test Name:** `TEST-SEC-04` / `backend/tests/test_ssrf.py::test_ssrf_rejects_cloud_metadata`
2. **Test Objective:** Verify `SSRFGuard` blocks cloud provider instance metadata IP addresses.
3. **Test Category:** SSRF Defense (Cloud Metadata)
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:**
   - AWS / GCP / Azure: `"http://169.254.169.254/latest/meta-data/"`
   - Secondary AWS: `"http://169.254.169.253/"`
   - Alibaba Cloud: `"http://100.100.100.200/latest/meta-data/"`
   - AWS IPv6 Metadata: `"http://[fd00:ec2::254]/"`
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_ssrf.py -k test_ssrf_rejects_cloud_metadata -v`
7. **Expected Result:** `is_safe == False`, metadata access prohibited.
8. **Actual Result:** `is_safe == False` on all 4 cloud metadata IP targets.
9. **Evidence:** Pytest terminal output `PASSED [ 91%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** Explicit checking against `CLOUD_METADATA_IPS` set and IPv4/IPv6 link-local evaluation (`169.254.0.0/16` and `fe80::/10`).
12. **Security Significance:** Protects IAM credentials, service account tokens, and cloud instance metadata from exfiltration during cloud deployment.
13. **Conclusion:** Cloud metadata endpoints are blocked across all major cloud providers.

---

### Test 5: `TEST-SEC-05` — `test_ssrf_rejects_ipv6_loopback_and_link_local`
1. **Test ID and Test Name:** `TEST-SEC-05` / `backend/tests/test_ssrf.py::test_ssrf_rejects_ipv6_loopback_and_link_local`
2. **Test Objective:** Verify `SSRFGuard` blocks IPv6 loopback (`::1`), link-local (`fe80::/10`), and unique local (`fc00::/7`).
3. **Test Category:** SSRF Defense (IPv6)
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** `"http://[::1]/"`, `"http://[fe80::1]/"`, `"http://[fc00::1]:8080/"`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_ssrf.py -k test_ssrf_rejects_ipv6_loopback_and_link_local -v`
7. **Expected Result:** `is_safe == False` on all IPv6 internal targets.
8. **Actual Result:** `is_safe == False` across all test vectors.
9. **Evidence:** Pytest terminal output `PASSED [ 92%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** Validates IPv6 bracket formatting according to RFC 3986, parses as `ipaddress.IPv6Address`, and checks `is_loopback`, `is_link_local`, and `is_private`.
12. **Security Significance:** Prevents dual-stack SSRF bypasses where attackers target IPv6 loopback when IPv4 loopback is blocked.
13. **Conclusion:** IPv6 internal and link-local destinations are fully blocked.

---

### Test 6: `TEST-SEC-06` — `test_ssrf_rejects_ipv4_mapped_ipv6`
1. **Test ID and Test Name:** `TEST-SEC-06` / `backend/tests/test_ssrf.py::test_ssrf_rejects_ipv4_mapped_ipv6`
2. **Test Objective:** Verify `SSRFGuard` unwraps and blocks IPv4-mapped IPv6 addresses referencing loopback or private ranges.
3. **Test Category:** SSRF Defense (IPv4-Mapped IPv6)
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** `"http://[::ffff:127.0.0.1]/"`, `"http://[::ffff:10.0.0.1]/"`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_ssrf.py -k test_ssrf_rejects_ipv4_mapped_ipv6 -v`
7. **Expected Result:** `is_safe == False` on both IPv4-mapped IPv6 targets.
8. **Actual Result:** `is_safe == False` for both targets.
9. **Evidence:** Pytest terminal output `PASSED [ 94%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** In `is_ip_private_or_restricted`, checks `if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped: ip_obj = ip_obj.ipv4_mapped` and inspects the extracted IPv4 object.
12. **Security Significance:** Thwarts sophisticated SSRF evasion techniques that encode `127.0.0.1` as an IPv6 hybrid literal to fool naive regex filters.
13. **Conclusion:** IPv4-mapped IPv6 bypasses are thwarted.

---

### Test 7: `TEST-SEC-07` — `test_ssrf_rejects_restricted_ports`
1. **Test ID and Test Name:** `TEST-SEC-07` / `backend/tests/test_ssrf.py::test_ssrf_rejects_restricted_ports`
2. **Test Objective:** Verify `SSRFGuard` blocks URLs targeting non-standard or restricted internal service ports.
3. **Test Category:** SSRF Defense (Port Whitelisting)
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:**
   - SSH: `"http://93.184.216.34:22/"`
   - SMTP: `"http://93.184.216.34:25/"`
   - MySQL: `"http://93.184.216.34:3306/"`
   - PostgreSQL: `"http://93.184.216.34:5432/"`
   - Redis: `"http://93.184.216.34:6379/"`
   - MongoDB: `"http://93.184.216.34:27017/"`
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_ssrf.py -k test_ssrf_rejects_restricted_ports -v`
7. **Expected Result:** `is_safe == False`, `blocked_reason` indicates port is restricted by policy.
8. **Actual Result:** All 6 restricted ports rejected before DNS resolution.
9. **Evidence:** Pytest terminal output `PASSED [ 95%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** Compares URL port against `ALLOWED_PORTS: Set[int] = {80, 443, 8080, 8443, 8000, 3000, 5000}`. Any port outside this whitelist is immediately rejected.
12. **Security Significance:** Prevents internal service exploitation (e.g. Redis unauthenticated command injection, database connection fuzzing) via HTTP SSRF.
13. **Conclusion:** Non-web ports are rejected deterministically.

---

### Test 8: `TEST-SEC-08` — `test_ssrf_permits_public_ip`
1. **Test ID and Test Name:** `TEST-SEC-08` / `backend/tests/test_ssrf.py::test_ssrf_permits_public_ip`
2. **Test Objective:** Verify `SSRFGuard` permits legitimate routable public IP addresses on standard web ports.
3. **Test Category:** SSRF Defense (Public Routable IPs)
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** `"http://93.184.216.34/"` (example.com public IPv4).
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_ssrf.py -k test_ssrf_permits_public_ip -v`
7. **Expected Result:** `SSRFValidationResult.is_safe == True`, `blocked_reason == None`.
8. **Actual Result:** `is_safe == True`.
9. **Evidence:** Pytest terminal output `PASSED [ 97%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** Public IP address is verified as non-private, non-loopback, and non-metadata, and allowed port 80 is accepted.
12. **Security Significance:** Confirms that SSRF protection does not block legitimate public web destinations.
13. **Conclusion:** Public routable destinations pass preflight verification cleanly.

---

### Test 9: `TEST-SEC-09` — `test_ssrf_blocks_dual_homed_dns`
1. **Test ID and Test Name:** `TEST-SEC-09` / `backend/tests/test_ssrf.py::test_ssrf_blocks_dual_homed_dns`
2. **Test Objective:** Verify `SSRFGuard` fails closed if a domain resolves to multiple IP addresses and ANY of them is private (DNS rebinding / dual-homed defense).
3. **Test Category:** SSRF Defense (DNS Rebinding Defense)
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** Mocked DNS resolution returning `["93.184.216.34", "10.0.0.1"]` for hostname `"dual-homed.example.com"`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_ssrf.py -k test_ssrf_blocks_dual_homed_dns -v`
7. **Expected Result:** `is_safe == False`, `blocked_reason` cites restricted IP `10.0.0.1`.
8. **Actual Result:** `is_safe == False`, rejected due to private IP.
9. **Evidence:** Pytest terminal output `PASSED [ 98%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** `validate_url` iterates through all IP addresses returned by `socket.getaddrinfo`. If any single resolved IP fails `is_ip_private_or_restricted`, the entire result is marked unsafe.
12. **Security Significance:** Neutralizes DNS rebinding attacks where an attacker configures their authoritative nameserver to return both public and private IPs to slip past naive checks.
13. **Conclusion:** Multi-homed DNS resolutions containing private IPs fail closed.

---

### Test 10: `TEST-SEC-10` — `test_ssrf_raises_exception_when_requested`
1. **Test ID and Test Name:** `TEST-SEC-10` / `backend/tests/test_ssrf.py::test_ssrf_raises_exception_when_requested`
2. **Test Objective:** Verify `SSRFGuard.validate_url` raises `SSRFProtectionError` when `raise_exception=True` is requested.
3. **Test Category:** SSRF Defense (Exception Handling)
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** `"http://127.0.0.1/"`, `raise_exception=True`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_ssrf.py -k test_ssrf_raises_exception_when_requested -v`
7. **Expected Result:** Raises `backend.app.core.exceptions.SSRFProtectionError`.
8. **Actual Result:** `SSRFProtectionError` raised cleanly.
9. **Evidence:** Pytest terminal output `PASSED [100%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** Allows callers to choose between soft verdict reporting (`is_safe=False`) and hard exception aborts.
12. **Security Significance:** Provides flexibility for both passive indicator logging and active fetcher pre-condition aborts.
13. **Conclusion:** Exception-raising behavior functions as designed.

---

### Test 11: `TEST-SEC-11` — `test_analyze_url_endpoint_ssrf_detection`
1. **Test ID and Test Name:** `TEST-SEC-11` / `backend/tests/test_api_analysis.py::test_analyze_url_endpoint_ssrf_detection`
2. **Test Objective:** Verify `POST /api/v1/analyze/url` flags internal loopback URL submissions as SSRF risks (`RULE-SSRF-001`, `CRITICAL`), sets `ssrf_safe: false`, and floors score to 70 (`HIGH_RISK`).
3. **Test Category:** SSRF API Integration (Decision A Floor)
4. **Test Environment:** Python 3.11.9, FastAPI TestClient, local venv
5. **Input / Test Data:** `POST /api/v1/analyze/url` with `{"url": "http://127.0.0.1/admin"}`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_api_analysis.py -k test_analyze_url_endpoint_ssrf_detection -v`
7. **Expected Result:** HTTP 200, `observed_evidence.ssrf_safe == False`, `RULE-SSRF-001` in indicators, `risk_level == "HIGH_RISK"`, `risk_score >= 70`.
8. **Actual Result:** HTTP 200, `ssrf_safe: false`, `RULE-SSRF-001` present (CRITICAL), `risk_score: 70`, `risk_level: HIGH_RISK`.
9. **Evidence:** Pytest terminal output `PASSED [  4%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** Threat service validates destination; SSRF guard reports unsafe loopback; service attaches `RULE-SSRF-001` with `CRITICAL` severity; `aggregate_indicators` floors score to 70 and sets `HIGH_RISK`.
12. **Security Significance:** End-to-end confirmation that SSRF attempts submitted to the analysis API are categorized as high-risk threats.
13. **Conclusion:** SSRF detection via API endpoint is verified with high-risk classification.

---

### Test 12: `TEST-SEC-12` — `test_secret_masking_in_summary`
1. **Test ID and Test Name:** `TEST-SEC-12` / `backend/tests/test_config.py::test_secret_masking_in_summary`
2. **Test Objective:** Verify `Settings.get_masked_summary()` redacts all API keys, private keys, passwords, and sensitive credentials.
3. **Test Category:** Configuration & Secret Masking (Phase 01 Frozen)
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** `Settings` instance with configured `gemini_api_key="AIzaSyTestSecretKey12345"`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_config.py -k test_secret_masking_in_summary -v`
7. **Expected Result:** Summary dictionary contains masked representation (`"AIza...2345"`), never raw full key.
8. **Actual Result:** Key is redacted; full secret is absent from summary.
9. **Evidence:** Pytest terminal output `PASSED [ 20%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** `mask_secret` helper preserves first 4 and last 4 characters separated by ellipses (`...`), protecting sensitive entropy.
12. **Security Significance:** Prevents accidental leakage of production API keys and private keys in application startup logs or diagnostic outputs.
13. **Conclusion:** Secret masking functions reliably.

---

### Test 13: `TEST-SEC-13` — `test_mask_secret_helper_edge_cases`
1. **Test ID and Test Name:** `TEST-SEC-13` / `backend/tests/test_config.py::test_mask_secret_helper_edge_cases`
2. **Test Objective:** Verify `mask_secret` handles edge cases (empty strings, short secrets $\le 8$ chars, `None`) without index errors.
3. **Test Category:** Configuration & Secret Masking (Phase 01 Frozen)
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** `None`, `""`, `"short"`, `"12345678"`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_config.py -k test_mask_secret_helper_edge_cases -v`
7. **Expected Result:** Returns `"[NOT SET]"` for empty/None, `"***"` for short strings without exceptions.
8. **Actual Result:** Matches expected safe redactions.
9. **Evidence:** Pytest terminal output `PASSED [ 22%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** Guard clauses handle nullability and string length checks before slicing operations.
12. **Security Significance:** Prevents crashes and data exposure during handling of misconfigured credentials.
13. **Conclusion:** Secret masking edge cases behave defensively.

---

### Test 14: `TEST-SEC-14` — `test_secret_scrubbing_log_filter`
1. **Test ID and Test Name:** `TEST-SEC-14` / `backend/tests/test_config.py::test_secret_scrubbing_log_filter`
2. **Test Objective:** Verify `SecretScrubbingFilter` intercepts and scrubs secrets embedded inside logging records.
3. **Test Category:** Logging Security & Secret Scrubbing (Phase 01 Frozen)
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** Log message containing simulated private key `"0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d"`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_config.py -k test_secret_scrubbing_log_filter -v`
7. **Expected Result:** Filter scrubs private key string, replacing it with `[REDACTED_SECRET]`.
8. **Actual Result:** Log record message contains `[REDACTED_SECRET]`.
9. **Evidence:** Pytest terminal output `PASSED [ 28%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** Custom `logging.Filter` executes compiled regular expressions over all emitted log messages.
12. **Security Significance:** Prevents developer error from logging raw credentials to disk, console, or centralized log aggregators.
13. **Conclusion:** Log scrubbing filter neutralizes secret leakage in logs.

---

### Test 15: `TEST-SEC-15` — `test_security_headers_present`
1. **Test ID and Test Name:** `TEST-SEC-15` / `backend/tests/test_health.py::test_security_headers_present`
2. **Test Objective:** Verify `SecurityHeadersMiddleware` injects mandatory enterprise security headers on all HTTP responses.
3. **Test Category:** HTTP Security Headers (Phase 01 Frozen)
4. **Test Environment:** Python 3.11.9, FastAPI TestClient, local venv
5. **Input / Test Data:** `GET /health`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_health.py -k test_security_headers_present -v`
7. **Expected Result:** Response headers include:
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `X-XSS-Protection: 1; mode=block`
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
   - `Content-Security-Policy: default-src 'self'`
8. **Actual Result:** All 5 security headers present with exact expected directives.
9. **Evidence:** Pytest terminal output `PASSED [ 34%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** ASGI middleware wraps downstream response and attaches defensive HTTP headers prior to socket flush.
12. **Security Significance:** Mitigates clickjacking, MIME-type sniffing, cross-site scripting (XSS), and insecure transport downgrade attacks.
13. **Conclusion:** Security headers middleware is verified active and functioning.

---

## 3. Manual Live API Verification Evidence

Manual verification was performed via Python against the running application:

### Manual Test: Live SSRF Loopback Attack Inspection
- **Command:** `client.post('/api/v1/analyze/url', json={'url': 'http://127.0.0.1/'})`
- **HTTP Status:** 200 OK
- **Actual Payload Received:**
```json
{
  "success": true,
  "data": {
    "target": "http://127.0.0.1/",
    "target_type": "url",
    "analysis_id": "e5759e74-a382-4c0d-b378-23f2bd3008b8",
    "timestamp": "2026-11-14T04:12:32.378909Z",
    "observed_evidence": {
      "normalized_url": "http://127.0.0.1/",
      "scheme": "http",
      "hostname": "127.0.0.1",
      "port": 80,
      "path": "/",
      "query": null,
      "resolved_ips": ["127.0.0.1"],
      "is_ip_hostname": true,
      "ssrf_safe": false,
      "has_homoglyphs": false
    },
    "heuristic_findings": {
      "risk_level": "HIGH_RISK",
      "risk_score": 70,
      "indicators": [
        {
          "rule_id": "RULE-URL-001",
          "category": "IP_HOST",
          "severity": "HIGH",
          "evidence": "Direct IP hostname: 127.0.0.1",
          "explanation": "The URL specifies a raw IP address instead of a legitimate registered domain name.",
          "mitigation": "Do not submit credentials or navigate to raw IP address targets."
        },
        {
          "rule_id": "RULE-SSRF-001",
          "category": "SSRF_ATTEMPT",
          "severity": "CRITICAL",
          "evidence": "Blocked destination: Target IP '127.0.0.1' belongs to a private, loopback, or metadata network.",
          "explanation": "Destination resolves to private, loopback, link-local, or cloud metadata network prohibited by security policy.",
          "mitigation": "Target points to internal or restricted network infrastructure and cannot be accessed."
        }
      ]
    },
    "status": "COMPLETED"
  },
  "error": null
}
```
- **Manual Verification Verdict:** **PASS**

---

## 4. Category Summary

| Metric | Value |
|---|---|
| Total Security & SSRF Tests | 15 |
| Passed Tests | 15 |
| Failed Tests | 0 |
| Category Status | **100% PASSED** |
