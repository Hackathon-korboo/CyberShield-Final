# PHASE 02 TEST EVIDENCE: 01 — URL TESTS REPORT

**Workspace:** `D:\Adamas offline Hackathon`  
**Test Suite Directory:** `backend/tests/`  
**Category:** URL Analysis, Normalization & Threat Detection  
**Total Tests in Category:** 14  
**Category Pass Rate:** 100% (14 Passed, 0 Failed, 0 Skipped)  
**Execution Environment:** Windows (PowerShell), Python 3.11.9, pytest 9.2.0  
**Status:** **AWAITING HUMAN VERIFICATION**  

---

## 1. Category Overview & Scope

The URL Tests category validates the syntactic validation, canonical normalization, homoglyph / Punycode conversion, dot-segment traversal elimination, regex URL extraction from freeform text, deterministic URL heuristic rules (`RULE-URL-001`, `RULE-URL-002`, `RULE-URL-003`), request/response Pydantic schemas, and the `POST /api/v1/analyze/url` API controller.

---

## 2. Automated Test Evidence (14 Tests)

### Test 1: `TEST-URL-01` — `test_normalize_target_url_basic`
1. **Test ID and Test Name:** `TEST-URL-01` / `backend/tests/test_sanitizer.py::test_normalize_target_url_basic`
2. **Test Objective:** Verify standard URL normalization converts scheme and hostname to lowercase, prepends default `http://` when missing, strips default ports (80 for http, 443 for https), and preserves paths.
3. **Test Category:** URL Normalization & Sanitization
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:**
   - Case 1: `"HTTPS://EXAMPLE.COM:443/Path/To/Page"`
   - Case 2: `"HTTP://example.com:80/"`
   - Case 3: `"example.com/test"`
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_sanitizer.py -k test_normalize_target_url_basic -v`
7. **Expected Result:**
   - Case 1: `"https://example.com/Path/To/Page"`
   - Case 2: `"http://example.com/"`
   - Case 3: `"http://example.com/test"`
8. **Actual Result:** Matches expected normalized strings exactly.
9. **Evidence:** Pytest terminal output `PASSED [ 58%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** `normalize_target_url` parses the string via `urllib.parse.urlsplit`, lowercases scheme and host, checks standard default port numbers against scheme defaults, and reconstructs the canonical RFC 3986 URL.
12. **Security Significance:** Prevents normalization bypasses where attackers alter case or append redundant default port numbers to evade URL blocklists.
13. **Conclusion:** URL normalization canonicalizes basic URL formats reliably.

---

### Test 2: `TEST-URL-02` — `test_normalize_target_url_punycode`
1. **Test ID and Test Name:** `TEST-URL-02` / `backend/tests/test_sanitizer.py::test_normalize_target_url_punycode`
2. **Test Objective:** Verify internationalized domain names (IDN) with Cyrillic or Unicode characters are converted to ASCII Punycode (`xn--`).
3. **Test Category:** URL Normalization & Homoglyph Defense
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** `"http://аpple.com/login"` (using Cyrillic 'а' `\u0430` instead of Latin 'a').
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_sanitizer.py -k test_normalize_target_url_punycode -v`
7. **Expected Result:** Hostname converts to `"xn--pple-43d.com"`, full URL: `"http://xn--pple-43d.com/login"`.
8. **Actual Result:** Output equals `"http://xn--pple-43d.com/login"`.
9. **Evidence:** Pytest terminal output `PASSED [ 59%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** The function encodes the hostname using Python's IDNA codec (`host.encode("idna").decode("ascii")`), translating lookalike Unicode glyphs into standard Punycode strings prefixed with `xn--`.
12. **Security Significance:** Mitigates homoglyph spoofing attacks where visually indistinguishable domains impersonate reputable brands.
13. **Conclusion:** Unicode homoglyphs are deterministically converted to canonical Punycode representations.

---

### Test 3: `TEST-URL-03` — `test_normalize_target_url_dot_segments`
1. **Test ID and Test Name:** `TEST-URL-03` / `backend/tests/test_sanitizer.py::test_normalize_target_url_dot_segments`
2. **Test Objective:** Verify RFC 3986 dot-segment path resolution eliminates path traversal sequences (`/../` and `/./`).
3. **Test Category:** URL Normalization & Path Sanitization
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** `"https://example.com/a/b/../c/./d"`
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_sanitizer.py -k test_normalize_target_url_dot_segments -v`
7. **Expected Result:** Normalized path resolves to `"https://example.com/a/c/d"`.
8. **Actual Result:** Output equals `"https://example.com/a/c/d"`.
9. **Evidence:** Pytest terminal output `PASSED [ 61%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** Utilizes `posixpath.normpath` on the URL path component to resolve parent directory traversals and current directory segments according to RFC 3986 Section 5.2.4.
12. **Security Significance:** Eliminates path traversal trickery intended to evade path-based signature detection rules.
13. **Conclusion:** Dot-segment traversals are eliminated prior to rule analysis.

---

### Test 4: `TEST-URL-04` — `test_normalize_target_url_invalid`
1. **Test ID and Test Name:** `TEST-URL-04` / `backend/tests/test_sanitizer.py::test_normalize_target_url_invalid`
2. **Test Objective:** Verify malformed inputs, unsupported protocols, and control character injections raise `ValueError`.
3. **Test Category:** URL Validation & Sanitization
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** `""` (empty), `"ftp://example.com"`, `"https://example.com\n/bad"`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_sanitizer.py -k test_normalize_target_url_invalid -v`
7. **Expected Result:** Raises `ValueError` with clear descriptive message for each invalid input.
8. **Actual Result:** `ValueError` raised on each test vector.
9. **Evidence:** Pytest terminal output `PASSED [ 62%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** Strict validator enforces non-empty input, allowed protocol whitelist (`http`, `https`), and rejects ASCII control characters (`\n`, `\r`, `\x00`).
12. **Security Significance:** Prevents header injection, smuggling, and protocol confusion attacks.
13. **Conclusion:** URL normalization strictly rejects malformed and unsupported protocol payloads.

---

### Test 5: `TEST-URL-05` — `test_extract_urls_from_text`
1. **Test ID and Test Name:** `TEST-URL-05` / `backend/tests/test_sanitizer.py::test_extract_urls_from_text`
2. **Test Objective:** Verify URL extraction correctly parses multiple URLs embedded within unstructured text and trailing punctuation.
3. **Test Category:** URL Extraction & Parsing
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** `"Visit https://example.com/login and http://bank.com:8080/portal?id=12. Also see secure.site.org/home."`
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_sanitizer.py -k test_extract_urls_from_text -v`
7. **Expected Result:** List containing extracted URLs with trailing dots stripped.
8. **Actual Result:** Returns 3 extracted normalized URLs.
9. **Evidence:** Pytest terminal output `PASSED [ 64%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** High-precision regex identifies full HTTP/HTTPS schemes and valid domain-pattern structures, stripping trailing grammatical periods.
12. **Security Significance:** Enables extraction of hidden or obfuscated URLs embedded inside phishing emails and SMS lures.
13. **Conclusion:** Embedded URLs are extracted reliably without trailing sentence punctuation.

---

### Test 6: `TEST-URL-06` — `test_url_rule_ip_hostname`
1. **Test ID and Test Name:** `TEST-URL-06` / `backend/tests/test_rules.py::test_url_rule_ip_hostname`
2. **Test Objective:** Verify `RULE-URL-001` triggers when a URL uses a raw IP address as its hostname.
3. **Test Category:** URL Threat Rule
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** `UrlObservedEvidence` with `hostname="198.51.100.5"`, `normalized_url="http://198.51.100.5/test"`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_rules.py -k test_url_rule_ip_hostname -v`
7. **Expected Result:** `RULE-URL-001` triggered, severity `HIGH`, exact evidence substring captured, risk score floored to $\ge 40$.
8. **Actual Result:** `RULE-URL-001` present in indicators, risk score = 40 (`SUSPICIOUS`).
9. **Evidence:** Pytest terminal output `PASSED [ 40%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** `IpHyphenRule.evaluate` tests hostname against `ipaddress.ip_address()`. On successful parsing, emits `SecurityIndicator` with `category=IP_HOST`.
12. **Security Significance:** Phishing operators often use raw IP addresses to bypass domain reputation blocklists and domain registration requirements.
13. **Conclusion:** Direct IP hostnames are flagged as suspicious threats.

---

### Test 7: `TEST-URL-07` — `test_url_rule_punycode`
1. **Test ID and Test Name:** `TEST-URL-07` / `backend/tests/test_rules.py::test_url_rule_punycode`
2. **Test Objective:** Verify `RULE-URL-002` triggers on Punycode-encoded hostnames (`xn--`).
3. **Test Category:** URL Threat Rule
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** `UrlObservedEvidence` with `hostname="xn--pple-43d.com"`, `has_homoglyphs=True`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_rules.py -k test_url_rule_punycode -v`
7. **Expected Result:** `RULE-URL-002` triggered, severity `HIGH`, category `HOMOGLYPH_SPOOFING`.
8. **Actual Result:** `RULE-URL-002` triggered with evidence `"Punycode encoded domain: xn--pple-43d.com"`.
9. **Evidence:** Pytest terminal output `PASSED [ 41%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** Evaluates presence of `"xn--"` in the canonical hostname string or `evidence.has_homoglyphs == True`.
12. **Security Significance:** Detects homograph phishing attacks impersonating legitimate financial or consumer platforms.
13. **Conclusion:** Punycode spoofing indicators trigger deterministic `HIGH` severity findings.

---

### Test 8: `TEST-URL-08` — `test_url_rule_suspicious_keywords`
1. **Test ID and Test Name:** `TEST-URL-08` / `backend/tests/test_rules.py::test_url_rule_suspicious_keywords`
2. **Test Objective:** Verify `RULE-URL-003` triggers on suspicious authentication keywords combined with hyphenated hostnames.
3. **Test Category:** URL Threat Rule
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** `UrlObservedEvidence` with `hostname="secure-login-bank-update.com"`, `path="/verify"`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_rules.py -k test_url_rule_suspicious_keywords -v`
7. **Expected Result:** `RULE-URL-003` triggered, severity `HIGH`, category `SUSPICIOUS_KEYWORD`.
8. **Actual Result:** `RULE-URL-003` detected with evidence capturing matching keywords.
9. **Evidence:** Pytest terminal output `PASSED [ 43%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** `SuspiciousAuthKeywordsRule` evaluates hostname and path against curated regex tokens: `\b(?:login|verify|account|update|banking|secure)\b`.
12. **Security Significance:** Attackers routinely register hyphenated domains containing brand and security keywords to engineer fraudulent trust.
13. **Conclusion:** Authentication lure keywords in domain names are detected reliably.

---

### Test 9: `TEST-URL-09` — `test_valid_url_analysis_request`
1. **Test ID and Test Name:** `TEST-URL-09` / `backend/tests/test_schemas.py::test_valid_url_analysis_request`
2. **Test Objective:** Verify Pydantic schema `UrlAnalysisRequest` parses valid URLs and handles optional scheme omission.
3. **Test Category:** URL Pydantic Schema
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** `url="https://example.com/login?param=1"`, `url="example.com/verify"`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_schemas.py -k test_valid_url_analysis_request -v`
7. **Expected Result:** Instantiation succeeds without validation errors.
8. **Actual Result:** Schema instances created successfully.
9. **Evidence:** Pytest terminal output `PASSED [ 70%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** Pydantic V2 model validates string length (3 to 2048 characters) and format.
12. **Security Significance:** Guarantees well-formed payload ingress before execution of heavy security engines.
13. **Conclusion:** Request schema validates valid URL inputs cleanly.

---

### Test 10: `TEST-URL-10` — `test_invalid_url_analysis_request`
1. **Test ID and Test Name:** `TEST-URL-10` / `backend/tests/test_schemas.py::test_invalid_url_analysis_request`
2. **Test Objective:** Verify `UrlAnalysisRequest` rejects empty strings, whitespace, illegal control characters, forbidden protocols, and unexpected extra fields.
3. **Test Category:** URL Pydantic Schema
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** `""`, `"   "`, `"ftp://malicious.com"`, `"https://example.com\n/bad"`, `extra_field="bad"`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_schemas.py -k test_invalid_url_analysis_request -v`
7. **Expected Result:** `pydantic.ValidationError` raised on every invalid input with strict field error messages.
8. **Actual Result:** `ValidationError` raised consistently.
9. **Evidence:** Pytest terminal output `PASSED [ 71%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** `field_validator` validates content, while `extra="forbid"` blocks mass assignment and parameter pollution.
12. **Security Significance:** Enforces input validation boundaries preventing injection and parameter pollution attacks.
13. **Conclusion:** Invalid URL requests fail closed at the boundary.

---

### Test 11: `TEST-URL-11` — `test_url_analysis_response_schema`
1. **Test ID and Test Name:** `TEST-URL-11` / `backend/tests/test_schemas.py::test_url_analysis_response_schema`
2. **Test Objective:** Verify `UrlAnalysisResponse` schema serializes observed evidence, heuristic findings, unique UUID analysis ID, and UTC timestamp.
3. **Test Category:** URL Pydantic Schema
4. **Test Environment:** Python 3.11.9, pytest 9.2.0, local venv
5. **Input / Test Data:** Synthetic `UrlObservedEvidence` and `HeuristicFindings` payload.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_schemas.py -k test_url_analysis_response_schema -v`
7. **Expected Result:** Successful serialization via `.model_dump()` and `.model_dump_json()`.
8. **Actual Result:** Serialized dictionary and JSON match specification.
9. **Evidence:** Pytest terminal output `PASSED [ 80%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** Pydantic V2 serialization generates strict typed response adhering to the Phase 02 API contract.
12. **Security Significance:** Guarantees deterministic, predictable JSON outputs for frontend consumption and automated SIEM ingestion.
13. **Conclusion:** Response schema serialization satisfies all contract constraints.

---

### Test 12: `TEST-URL-12` — `test_analyze_url_endpoint_benign`
1. **Test ID and Test Name:** `TEST-URL-12` / `backend/tests/test_api_analysis.py::test_analyze_url_endpoint_benign`
2. **Test Objective:** Verify `POST /api/v1/analyze/url` with a clean, benign URL returns HTTP 200, status `COMPLETED`, `risk_level: CLEAN`, score 0, and `ssrf_safe: true`.
3. **Test Category:** URL API Integration
4. **Test Environment:** Python 3.11.9, FastAPI TestClient, local venv
5. **Input / Test Data:** `POST /api/v1/analyze/url` with JSON `{"url": "https://example.com/about-us"}`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_api_analysis.py -k test_analyze_url_endpoint_benign -v`
7. **Expected Result:** HTTP 200, `success: true`, `risk_level: CLEAN`, `risk_score: 0`, `indicators: []`, `ssrf_safe: true`.
8. **Actual Result:** Matches expected output exactly.
9. **Evidence:** Pytest terminal output `PASSED [  1%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** Full pipeline execution: Normalizer -> SSRF Preflight -> Heuristic Engine -> Response synthesis -> StandardResponse wrapper.
12. **Security Significance:** Confirms zero false positives on benign legitimate traffic.
13. **Conclusion:** Benign URLs are correctly evaluated with clean status.

---

### Test 13: `TEST-URL-13` — `test_analyze_url_endpoint_phishing_lure`
1. **Test ID and Test Name:** `TEST-URL-13` / `backend/tests/test_api_analysis.py::test_analyze_url_endpoint_phishing_lure`
2. **Test Objective:** Verify `POST /api/v1/analyze/url` triggers `RULE-URL-003` on a phishing lure URL and assigns elevated risk.
3. **Test Category:** URL API Integration
4. **Test Environment:** Python 3.11.9, FastAPI TestClient, local venv
5. **Input / Test Data:** `POST /api/v1/analyze/url` with JSON `{"url": "https://verify-banking-security.com/login"}`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_api_analysis.py -k test_analyze_url_endpoint_phishing_lure -v`
7. **Expected Result:** HTTP 200, `success: true`, `RULE-URL-003` in indicators, `risk_level` in `("SUSPICIOUS", "HIGH_RISK")`, `risk_score >= 40`.
8. **Actual Result:** HTTP 200, `RULE-URL-003` triggered, `risk_score: 40`, `risk_level: SUSPICIOUS`.
9. **Evidence:** Pytest terminal output `PASSED [  2%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** Normalizer canonicalizes URL; heuristic rule engine evaluates hyphenated hostname and keyword `/login`, triggering `RULE-URL-003` (severity `HIGH`), which floors score to 40.
12. **Security Significance:** Accurately flags credential harvesting sites mimicking legitimate banking infrastructure.
13. **Conclusion:** Phishing lure URLs are correctly categorized with elevated risk scores.

---

### Test 14: `TEST-URL-14` — `test_analyze_url_endpoint_invalid_scheme`
1. **Test ID and Test Name:** `TEST-URL-14` / `backend/tests/test_api_analysis.py::test_analyze_url_endpoint_invalid_scheme`
2. **Test Objective:** Verify `POST /api/v1/analyze/url` rejects unsupported protocol schemes (e.g. `ftp://`) with HTTP 422 and a standardized error envelope.
3. **Test Category:** URL API Integration & Boundary Validation
4. **Test Environment:** Python 3.11.9, FastAPI TestClient, local venv
5. **Input / Test Data:** `POST /api/v1/analyze/url` with JSON `{"url": "ftp://malicious.com/file"}`.
6. **Execution Command or API Request:** `backend\venv\Scripts\python.exe -m pytest backend/tests/test_api_analysis.py -k test_analyze_url_endpoint_invalid_scheme -v`
7. **Expected Result:** HTTP 422 Unprocessable Content, `success: false`, `error.code: "VALIDATION_ERROR"`, correlation ID included.
8. **Actual Result:** HTTP 422 returned with standard error wrapper.
9. **Evidence:** Pytest terminal output `PASSED [  5%]`.
10. **PASS / FAIL / NOT EXECUTED:** **PASS**
11. **Detailed Technical Explanation:** FastAPI request validation intercepts schema violation before route controller execution; global exception handler formats standardized error envelope.
12. **Security Significance:** Rejects dangerous protocols (`ftp`, `file`, `gopher`, `dict`) preventing protocol confusion attacks.
13. **Conclusion:** Non-HTTP(S) schemes are rejected with standardized HTTP 422 errors.

---

## 3. Manual Live API Verification Evidence

In addition to the automated pytest suite, live manual API verification was executed via Python against the running application:

### Manual Test: Live Benign URL Inspection
- **Command:** `client.post('/api/v1/analyze/url', json={'url': 'https://example.com'})`
- **HTTP Status:** 200 OK
- **Actual Payload Received:**
```json
{
  "success": true,
  "data": {
    "target": "https://example.com",
    "target_type": "url",
    "analysis_id": "c71a39f0-2f19-4f81-9b16-43b9db8d4a67",
    "timestamp": "2026-11-14T04:12:32.378909Z",
    "observed_evidence": {
      "normalized_url": "https://example.com",
      "scheme": "https",
      "hostname": "example.com",
      "port": 443,
      "path": "",
      "query": null,
      "resolved_ips": ["93.184.216.34"],
      "is_ip_hostname": false,
      "ssrf_safe": true,
      "has_homoglyphs": false
    },
    "heuristic_findings": {
      "risk_level": "CLEAN",
      "risk_score": 0,
      "indicators": []
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
| Total URL Tests | 14 |
| Passed Tests | 14 |
| Failed Tests | 0 |
| Category Status | **100% PASSED** |
