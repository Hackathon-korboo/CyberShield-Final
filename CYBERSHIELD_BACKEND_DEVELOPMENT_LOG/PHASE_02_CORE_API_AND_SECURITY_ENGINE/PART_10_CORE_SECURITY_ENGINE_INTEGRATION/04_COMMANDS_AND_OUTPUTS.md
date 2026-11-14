# PART 10: CORE SECURITY ENGINE INTEGRATION — COMMANDS AND OUTPUTS

## 1. Test Suite Execution Command
Executed full pytest suite across all Phase 01 and Phase 02 tests:
```powershell
backend\venv\Scripts\python.exe -m pytest backend/tests -v
```

### Terminal Output:
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0 -- D:\Adamas offline Hackathon\backend\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\Adamas offline Hackathon
plugins: anyio-4.16.0, asyncio-1.5.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 57 items

backend/tests/test_api_analysis.py::test_analyze_url_endpoint_benign PASSED [  1%]
backend/tests/test_api_analysis.py::test_analyze_url_endpoint_phishing_lure PASSED [  3%]
backend/tests/test_api_analysis.py::test_analyze_url_endpoint_ssrf_detection PASSED [  5%]
backend/tests/test_api_analysis.py::test_analyze_url_endpoint_invalid_scheme PASSED [  7%]
backend/tests/test_api_analysis.py::test_analyze_email_endpoint_fraud_and_urgency PASSED [  8%]
backend/tests/test_api_analysis.py::test_analyze_email_with_embedded_urls PASSED [ 10%]
backend/tests/test_api_analysis.py::test_analyze_email_endpoint_empty_body PASSED [ 12%]
backend/tests/test_api_analysis.py::test_analyze_sms_endpoint_otp_extraction PASSED [ 14%]
backend/tests/test_api_analysis.py::test_analyze_sms_with_embedded_ssrf_url PASSED [ 15%]
backend/tests/test_api_analysis.py::test_analyze_sms_clean PASSED        [ 17%]
backend/tests/test_config.py::test_default_settings_instantiation PASSED [ 19%]
backend/tests/test_config.py::test_secret_masking_in_summary PASSED      [ 21%]
backend/tests/test_config.py::test_mask_secret_helper_edge_cases PASSED  [ 22%]
backend/tests/test_config.py::test_environment_validation_valid PASSED   [ 24%]
backend/tests/test_config.py::test_environment_validation_invalid PASSED [ 26%]
backend/tests/test_config.py::test_cors_origins_parsing PASSED           [ 28%]
backend/tests/test_config.py::test_secret_scrubbing_log_filter PASSED    [ 29%]
backend/tests/test_health.py::test_root_endpoint PASSED                  [ 31%]
backend/tests/test_health.py::test_api_v1_health_endpoint PASSED         [ 33%]
backend/tests/test_health.py::test_root_health_alias PASSED              [ 35%]
backend/tests/test_health.py::test_security_headers_present PASSED       [ 36%]
backend/tests/test_custom_correlation_id_preserved PASSED                [ 38%]
backend/tests/test_health.py::test_standardized_404_error_envelope PASSED [ 40%]
backend/tests/test_rules.py::test_calculate_risk_level_tiers PASSED      [ 42%]
backend/tests/test_rules.py::test_url_rule_ip_hostname PASSED            [ 43%]
backend/tests/test_rules.py::test_url_rule_punycode PASSED               [ 45%]
backend/tests/test_rules.py::test_url_rule_suspicious_keywords PASSED    [ 47%]
backend/tests/test_rules.py::test_email_rules_urgency_and_fraud PASSED   [ 49%]
backend/tests/test_rules.py::test_email_job_scam PASSED                  [ 50%]
backend/tests/test_rules.py::test_sms_otp_extraction PASSED              [ 52%]
backend/tests/test_rules.py::test_clean_input_returns_zero_score PASSED  [ 54%]
backend/tests/test_sanitizer.py::test_normalize_target_url_basic PASSED  [ 56%]
backend/tests/test_sanitizer.py::test_normalize_target_url_punycode PASSED [ 57%]
backend/tests/test_sanitizer.py::test_normalize_target_url_dot_segments PASSED [ 59%]
backend/tests/test_sanitizer.py::test_normalize_target_url_invalid PASSED [ 61%]
backend/tests/test_sanitizer.py::test_extract_urls_from_text PASSED      [ 63%]
backend/tests/test_sanitizer.py::test_extract_phone_numbers PASSED       [ 64%]
backend/tests/test_sanitizer.py::test_parse_email_sender PASSED          [ 66%]
backend/tests/test_sanitizer.py::test_sanitize_input_text PASSED         [ 68%]
backend/tests/test_schemas.py::test_valid_url_analysis_request PASSED    [ 70%]
backend/tests/test_schemas.py::test_invalid_url_analysis_request PASSED  [ 71%]
backend/tests/test_schemas.py::test_valid_email_analysis_request PASSED  [ 73%]
backend/tests/test_schemas.py::test_invalid_email_analysis_request PASSED [ 75%]
backend/tests/test_schemas.py::test_valid_sms_analysis_request PASSED    [ 77%]
backend/tests/test_schemas.py::test_invalid_sms_analysis_request PASSED  [ 78%]
backend/tests/test_schemas.py::test_security_indicator_schema PASSED     [ 80%]
backend/tests/test_schemas.py::test_url_analysis_response_schema PASSED  [ 82%]
backend/tests/test_ssrf.py::test_ssrf_rejects_loopback_ipv4 PASSED       [ 84%]
backend/tests/test_ssrf.py::test_ssrf_rejects_localhost_hostname PASSED  [ 85%]
backend/tests/test_ssrf.py::test_ssrf_rejects_private_subnets PASSED     [ 87%]
backend/tests/test_ssrf.py::test_ssrf_rejects_cloud_metadata PASSED      [ 89%]
backend/tests/test_ssrf.py::test_ssrf_rejects_ipv6_loopback_and_link_local PASSED [ 91%]
backend/tests/test_ssrf.py::test_ssrf_rejects_ipv4_mapped_ipv6 PASSED    [ 92%]
backend/tests/test_ssrf.py::test_ssrf_rejects_restricted_ports PASSED    [ 94%]
backend/tests/test_ssrf.py::test_ssrf_permits_public_ip PASSED           [ 96%]
backend/tests/test_ssrf.py::test_ssrf_blocks_dual_homed_dns PASSED       [ 98%]
backend/tests/test_ssrf.py::test_ssrf_raises_exception_when_requested PASSED [100%]

======================= 57 passed, 3 warnings in 0.22s ========================
```
