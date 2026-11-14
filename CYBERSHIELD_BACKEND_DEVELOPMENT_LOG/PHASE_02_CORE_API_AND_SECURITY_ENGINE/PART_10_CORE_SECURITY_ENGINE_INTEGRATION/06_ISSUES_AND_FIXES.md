# PART 10: CORE SECURITY ENGINE INTEGRATION — ISSUES AND FIXES

## 1. Resolved Issues

### Issue 1: IPv6 Literal Bracket Handling in URL Normalization
- **Symptom:** During SSRF Guard integration with `normalize_target_url`, `urllib.parse.urlsplit` threw `ValueError: Port could not be cast to integer value as ':1'` when parsing IPv6 netlocs like `[::1]`.
- **Root Cause:** Converting the host to ASCII stripped the enclosing RFC 3986 brackets `[` and `]`.
- **Resolution:** Updated `normalize_target_url` in `backend/app/utils/sanitizer.py` to preserve IPv6 bracket notation `f"[{ascii_host}]"` if colons are detected in the hostname.
- **Verification:** `backend/tests/test_ssrf.py` passed with 10/10 tests.

### Issue 2: Sub-analysis Embedded SSRF Detection Propagation
- **Symptom:** Embedded URLs inside SMS and Email bodies needed to register high-severity threat indicators if pointing to loopback or cloud metadata services.
- **Root Cause:** Initial implementation only checked the primary URL in `/analyze/url`.
- **Resolution:** Added embedded URL preflight validation within `analyze_email` and `analyze_sms` in `ThreatAnalysisService`, generating `RULE-URL-EMBEDDED` and `RULE-SMS-SSRF-001` indicators.
- **Verification:** `test_analyze_sms_with_embedded_ssrf_url` and `test_analyze_email_with_embedded_urls` pass with verified indicators.

## 2. Unresolved Issues / Blockers
- **None.** All 57 unit and integration tests are passing.
