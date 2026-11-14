# PART 10: CORE SECURITY ENGINE INTEGRATION — TEST RESULTS

## 1. Test Execution Summary
- **Execution Date:** 2026-11-14T09:20:41+05:30
- **Test Runner:** pytest 9.2.0 (Python 3.11.9)
- **Total Tests Collected:** 67
- **Total Tests Passed:** 67
- **Total Tests Failed:** 0
- **Total Tests Skipped:** 0
- **Exit Code:** 0

## 2. Integration Test Breakdown (`backend/tests/test_api_analysis.py`)
1. `test_analyze_url_endpoint_benign` — PASSED (Returns 200, CLEAN risk level, 0 indicators)
2. `test_analyze_url_endpoint_phishing_lure` — PASSED (Returns 200, HIGH_RISK, detects Punycode and auth keywords)
3. `test_analyze_url_endpoint_ssrf_detection` — PASSED (Returns 200, HIGH_RISK, score 70, detects metadata SSRF attempt)
4. `test_analyze_url_endpoint_invalid_scheme` — PASSED (Returns 422 for unsupported scheme)
5. `test_analyze_email_endpoint_fraud_and_urgency` — PASSED (Returns 200, triggers urgency and payment fraud rules)
6. `test_analyze_email_with_embedded_urls` — PASSED (Returns 200, successfully extracts and evaluates embedded URLs)
7. `test_analyze_email_endpoint_empty_body` — PASSED (Returns 422 for empty content)
8. `test_analyze_sms_endpoint_otp_extraction` — PASSED (Returns 200, triggers OTP extraction rule with phone evidence)
9. `test_analyze_sms_with_embedded_ssrf_url` — PASSED (Returns 200, detects SSRF in embedded URL)
10. `test_analyze_sms_clean` — PASSED (Returns 200, CLEAN classification for normal message)
11. `test_analyze_sms_compound_urgency_endpoint` — PASSED (Returns 200, triggers RULE-SMS-004 with score 40 SUSPICIOUS)
12. `test_api_endpoints_emit_utc_timestamp_with_z` — PASSED (Returns 200, timestamps end in Z across all 3 endpoints)

## 3. Regression Test Verification
- All 13 Phase 01 baseline tests passed (`test_config.py`, `test_health.py`).
- All 11 Schema unit tests passed (`test_schemas.py`).
- All 8 Sanitizer & Normalization tests passed (`test_sanitizer.py`).
- All 10 SSRF Guard tests passed (`test_ssrf.py`).
- All 13 Security Rules tests passed (`test_rules.py`).
- Cumulative Phase 01 + Phase 02 tests: **67 / 67 passed (100%)**.
