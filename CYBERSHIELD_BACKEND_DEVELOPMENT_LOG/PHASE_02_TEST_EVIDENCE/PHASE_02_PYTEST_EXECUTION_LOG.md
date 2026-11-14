# PHASE 02 TEST EVIDENCE: PYTEST EXECUTION LOG

**Project:** CyberShield AI 2.0  
**Workspace:** `D:\Adamas offline Hackathon`  
**Execution Timestamp:** 2026-11-14T09:44:00+05:30  
**Operating System:** Windows 11 (PowerShell)  
**Python Runtime:** Python 3.11.9 (`D:\Adamas offline Hackathon\backend\venv\Scripts\python.exe`)  
**Test Framework:** pytest 9.2.0, pluggy 1.7.0, anyio 4.16.0, asyncio 1.5.0  
**Configuration File:** `pytest.ini` (`asyncio_default_fixture_loop_scope = function`)  
**Execution Command:**  
```powershell
.\backend\venv\Scripts\python.exe -m pytest backend/tests -v
```

---

## 1. Raw Execution Output Stream

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0 -- D:\Adamas offline Hackathon\backend\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\Adamas offline Hackathon
configfile: pytest.ini
plugins: anyio-4.16.0, asyncio-1.5.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 67 items

backend/tests/test_api_analysis.py::test_analyze_url_endpoint_benign PASSED [  1%]
backend/tests/test_api_analysis.py::test_analyze_url_endpoint_phishing_lure PASSED [  2%]
backend/tests/test_api_analysis.py::test_analyze_url_endpoint_ssrf_detection PASSED [  4%]
backend/tests/test_api_analysis.py::test_analyze_url_endpoint_invalid_scheme PASSED [  5%]
backend/tests/test_api_analysis.py::test_analyze_email_endpoint_fraud_and_urgency PASSED [  7%]
backend/tests/test_api_analysis.py::test_analyze_email_with_embedded_urls PASSED [  8%]
backend/tests/test_api_analysis.py::test_analyze_email_endpoint_empty_body PASSED [ 10%]
backend/tests/test_api_analysis.py::test_analyze_sms_endpoint_otp_extraction PASSED [ 11%]
backend/tests/test_api_analysis.py::test_analyze_sms_with_embedded_ssrf_url PASSED [ 13%]
backend/tests/test_api_analysis.py::test_analyze_sms_clean PASSED        [ 14%]
backend/tests/test_api_analysis.py::test_analyze_sms_compound_urgency_endpoint PASSED [ 16%]
backend/tests/test_api_analysis.py::test_api_endpoints_emit_utc_timestamp_with_z PASSED [ 17%]
backend/tests/test_config.py::test_default_settings_instantiation PASSED [ 19%]
backend/tests/test_config.py::test_secret_masking_in_summary PASSED      [ 20%]
backend/tests/test_config.py::test_mask_secret_helper_edge_cases PASSED  [ 22%]
backend/tests/test_config.py::test_environment_validation_valid PASSED   [ 23%]
backend/tests/test_config.py::test_environment_validation_invalid PASSED [ 25%]
backend/tests/test_config.py::test_cors_origins_parsing PASSED           [ 26%]
backend/tests/test_config.py::test_secret_scrubbing_log_filter PASSED    [ 28%]
backend/tests/test_health.py::test_root_endpoint PASSED                  [ 29%]
backend/tests/test_health.py::test_api_v1_health_endpoint PASSED         [ 31%]
backend/tests/test_health.py::test_root_health_alias PASSED              [ 32%]
backend/tests/test_health.py::test_security_headers_present PASSED       [ 34%]
backend/tests/test_health.py::test_custom_correlation_id_preserved PASSED [ 35%]
backend/tests/test_health.py::test_standardized_404_error_envelope PASSED [ 37%]
backend/tests/test_rules.py::test_calculate_risk_level_tiers PASSED      [ 38%]
backend/tests/test_rules.py::test_url_rule_ip_hostname PASSED            [ 40%]
backend/tests/test_rules.py::test_url_rule_punycode PASSED               [ 41%]
backend/tests/test_rules.py::test_url_rule_suspicious_keywords PASSED    [ 43%]
backend/tests/test_email_rules_urgency_and_fraud PASSED                  [ 44%]
backend/tests/test_rules.py::test_email_job_scam PASSED                  [ 46%]
backend/tests/test_rules.py::test_sms_otp_extraction PASSED              [ 47%]
backend/tests/test_rules.py::test_clean_input_returns_zero_score PASSED  [ 49%]
backend/tests/test_rules.py::test_severity_floor_model_individual_tiers PASSED [ 50%]
backend/tests/test_rules.py::test_severity_floor_model_multi_indicator_interaction PASSED [ 52%]
backend/tests/test_rules.py::test_sms_urgency_rule_positive_cases PASSED [ 53%]
backend/tests/test_rules.py::test_sms_urgency_rule_negative_cases PASSED [ 55%]
backend/tests/test_rules.py::test_sms_dual_trigger_otp_and_urgency PASSED [ 56%]
backend/tests/test_sanitizer.py::test_normalize_target_url_basic PASSED  [ 58%]
backend/tests/test_sanitizer.py::test_normalize_target_url_punycode PASSED [ 59%]
backend/tests/test_sanitizer.py::test_normalize_target_url_dot_segments PASSED [ 61%]
backend/tests/test_sanitizer.py::test_normalize_target_url_invalid PASSED [ 62%]
backend/tests/test_sanitizer.py::test_extract_urls_from_text PASSED      [ 64%]
backend/tests/test_sanitizer.py::test_extract_phone_numbers PASSED       [ 65%]
backend/tests/test_sanitizer.py::test_parse_email_sender PASSED          [ 67%]
backend/tests/test_sanitizer.py::test_sanitize_input_text PASSED         [ 68%]
backend/tests/test_schemas.py::test_valid_url_analysis_request PASSED    [ 70%]
backend/tests/test_schemas.py::test_invalid_url_analysis_request PASSED  [ 71%]
backend/tests/test_schemas.py::test_valid_email_analysis_request PASSED  [ 73%]
backend/tests/test_schemas.py::test_invalid_email_analysis_request PASSED [ 74%]
backend/tests/test_schemas.py::test_valid_sms_analysis_request PASSED    [ 76%]
backend/tests/test_schemas.py::test_invalid_sms_analysis_request PASSED  [ 77%]
backend/tests/test_schemas.py::test_security_indicator_schema PASSED     [ 79%]
backend/tests/test_schemas.py::test_url_analysis_response_schema PASSED  [ 80%]
backend/tests/test_schemas.py::test_email_body_length_boundary PASSED    [ 82%]
backend/tests/test_schemas.py::test_sms_message_length_boundary PASSED   [ 83%]
backend/tests/test_schemas.py::test_response_utc_timezone_awareness PASSED [ 85%]
backend/tests/test_ssrf.py::test_ssrf_rejects_loopback_ipv4 PASSED       [ 86%]
backend/tests/test_ssrf.py::test_ssrf_rejects_localhost_hostname PASSED  [ 88%]
backend/tests/test_ssrf.py::test_ssrf_rejects_private_subnets PASSED     [ 89%]
backend/tests/test_ssrf.py::test_ssrf_rejects_cloud_metadata PASSED      [ 91%]
backend/tests/test_ssrf.py::test_ssrf_rejects_ipv6_loopback_and_link_local PASSED [ 92%]
backend/tests/test_ssrf.py::test_ssrf_rejects_ipv4_mapped_ipv6 PASSED    [ 94%]
backend/tests/test_ssrf.py::test_ssrf_rejects_restricted_ports PASSED    [ 95%]
backend/tests/test_ssrf.py::test_ssrf_permits_public_ip PASSED           [ 97%]
backend/tests/test_ssrf.py::test_ssrf_blocks_dual_homed_dns PASSED       [ 98%]
backend/tests/test_ssrf.py::test_ssrf_raises_exception_when_requested PASSED [100%]

============================== warnings summary ===============================
backend\venv\Lib\site-packages\starlette\testclient.py:45
  D:\Adamas offline Hackathon\backend\venv\Lib\site-packages\starlette\testclient.py:45: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]

backend/tests/test_api_analysis.py::test_analyze_url_endpoint_invalid_scheme
backend/tests/test_api_analysis.py::test_analyze_email_endpoint_empty_body
  D:\Adamas offline Hackathon\backend\venv\Lib\site-packages\starlette\_exception_handler.py:59: DeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    response = await handler(conn, exc)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 67 passed, 3 warnings in 0.33s ========================
```

---

## 2. Test Execution Summary

- **Total Tests Collected:** 67
- **Passed:** 67
- **Failed:** 0
- **Skipped:** 0
- **Pass Rate:** 100.0%
- **Execution Wall-Clock Time:** 0.33 seconds
- **Exit Code:** 0

---

## 3. Detailed Warnings Audit

| Warning Index | Emitting File | Warning Class | Warning Text | Nature & Resolution |
|---|---|---|---|---|
| **1** | `starlette\testclient.py:45` | `DeprecationWarning` | `The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.` | Upstream Starlette test client library warning. Harmless; not an application defect. |
| **2** | `starlette\_exception_handler.py:59` | `DeprecationWarning` | `'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.` | Upstream Starlette exception handler warning on invalid scheme test. Harmless. |
| **3** | `starlette\_exception_handler.py:59` | `DeprecationWarning` | `'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.` | Upstream Starlette exception handler warning on empty email body test. Harmless. |

*Note: The previous `pytest-asyncio` fixture loop scope warning has been completely eliminated through `pytest.ini`.*
