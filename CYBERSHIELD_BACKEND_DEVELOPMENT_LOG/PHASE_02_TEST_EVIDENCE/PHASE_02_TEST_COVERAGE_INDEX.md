# PHASE 02 TEST EVIDENCE: TEST COVERAGE INDEX

**Project:** CyberShield AI 2.0  
**Workspace:** `D:\Adamas offline Hackathon`  
**Execution Date:** 2026-11-14T09:44:00+05:30  
**Total Tests Indexed:** 67  
**Category Mapping:** 100% Non-Duplicated Coverage  
**Current Phase Status:** **AWAITING HUMAN VERIFICATION**  

---

## 1. Test Distribution Across Source Modules

| Test Module File | Component Under Test | Number of Tests | Pass Count | Pass Rate |
|---|---|:---:|:---:|:---:|
| `backend/tests/test_api_analysis.py` | API Controllers & End-to-End Analysis Pipelines | 12 | 12 | 100% |
| `backend/tests/test_config.py` | Configuration, Secret Masking & Log Filtering | 7 | 7 | 100% |
| `backend/tests/test_health.py` | Health Probes, Root Descriptor, Security Headers & Tracing | 6 | 6 | 100% |
| `backend/tests/test_rules.py` | Deterministic Rules Catalog & Severity Floor Model | 13 | 13 | 100% |
| `backend/tests/test_sanitizer.py` | Normalization, Extraction & Character Sanitization | 8 | 8 | 100% |
| `backend/tests/test_schemas.py` | Pydantic V2 Schemas, Boundaries & Timezone Awareness | 11 | 11 | 100% |
| `backend/tests/test_ssrf.py` | SSRF Guard Defensive Network Boundaries | 10 | 10 | 100% |
| **TOTAL** | **Consolidated Automated Test Suite** | **67** | **67** | **100%** |

---

## 2. Category Folder Mapping & Evidence Links

Every test is assigned to exactly one primary category folder without count duplication:

| Category Folder | Report Document | Test IDs | Count | Pass Rate |
|---|---|---|:---:|:---:|
| `01_URL_TESTS` | [URL_TEST_REPORT.md](file:///d:/Adamas%20offline%20Hackathon/CYBERSHIELD_BACKEND_DEVELOPMENT_LOG/PHASE_02_TEST_EVIDENCE/01_URL_TESTS/URL_TEST_REPORT.md) | `TEST-URL-01` to `TEST-URL-14` | 14 | 100% |
| `02_EMAIL_TESTS` | [EMAIL_TEST_REPORT.md](file:///d:/Adamas%20offline%20Hackathon/CYBERSHIELD_BACKEND_DEVELOPMENT_LOG/PHASE_02_TEST_EVIDENCE/02_EMAIL_TESTS/EMAIL_TEST_REPORT.md) | `TEST-EML-01` to `TEST-EML-09` | 9 | 100% |
| `03_SMS_TESTS` | [SMS_TEST_REPORT.md](file:///d:/Adamas%20offline%20Hackathon/CYBERSHIELD_BACKEND_DEVELOPMENT_LOG/PHASE_02_TEST_EVIDENCE/03_SMS_TESTS/SMS_TEST_REPORT.md) | `TEST-SMS-01` to `TEST-SMS-12` | 12 | 100% |
| `04_SECURITY_AND_SSRF_TESTS` | [SECURITY_SSRF_TEST_REPORT.md](file:///d:/Adamas%20offline%20Hackathon/CYBERSHIELD_BACKEND_DEVELOPMENT_LOG/PHASE_02_TEST_EVIDENCE/04_SECURITY_AND_SSRF_TESTS/SECURITY_SSRF_TEST_REPORT.md) | `TEST-SEC-01` to `TEST-SEC-15` | 15 | 100% |
| `05_API_SCHEMA_AND_INTEGRATION_TESTS` | [API_SCHEMA_INTEGRATION_TEST_REPORT.md](file:///d:/Adamas%20offline%20Hackathon/CYBERSHIELD_BACKEND_DEVELOPMENT_LOG/PHASE_02_TEST_EVIDENCE/05_API_SCHEMA_AND_INTEGRATION_TESTS/API_SCHEMA_INTEGRATION_TEST_REPORT.md) | `TEST-INT-01` to `TEST-INT-17` | 17 | 100% |
| **TOTAL** | **Consolidated Evidence Suite** | | **67** | **100%** |

---

## 3. Exhaustive Master Test Inventory (67 Tests)

| # | Test ID | Test Function Node | Source File | Category | Result |
|---|---|---|---|---|:---:|
| 1 | `TEST-URL-01` | `test_normalize_target_url_basic` | `test_sanitizer.py` | 01_URL_TESTS | **PASS** |
| 2 | `TEST-URL-02` | `test_normalize_target_url_punycode` | `test_sanitizer.py` | 01_URL_TESTS | **PASS** |
| 3 | `TEST-URL-03` | `test_normalize_target_url_dot_segments` | `test_sanitizer.py` | 01_URL_TESTS | **PASS** |
| 4 | `TEST-URL-04` | `test_normalize_target_url_invalid` | `test_sanitizer.py` | 01_URL_TESTS | **PASS** |
| 5 | `TEST-URL-05` | `test_extract_urls_from_text` | `test_sanitizer.py` | 01_URL_TESTS | **PASS** |
| 6 | `TEST-URL-06` | `test_url_rule_ip_hostname` | `test_rules.py` | 01_URL_TESTS | **PASS** |
| 7 | `TEST-URL-07` | `test_url_rule_punycode` | `test_rules.py` | 01_URL_TESTS | **PASS** |
| 8 | `TEST-URL-08` | `test_url_rule_suspicious_keywords` | `test_rules.py` | 01_URL_TESTS | **PASS** |
| 9 | `TEST-URL-09` | `test_valid_url_analysis_request` | `test_schemas.py` | 01_URL_TESTS | **PASS** |
| 10 | `TEST-URL-10` | `test_invalid_url_analysis_request` | `test_schemas.py` | 01_URL_TESTS | **PASS** |
| 11 | `TEST-URL-11` | `test_url_analysis_response_schema` | `test_schemas.py` | 01_URL_TESTS | **PASS** |
| 12 | `TEST-URL-12` | `test_analyze_url_endpoint_benign` | `test_api_analysis.py` | 01_URL_TESTS | **PASS** |
| 13 | `TEST-URL-13` | `test_analyze_url_endpoint_phishing_lure` | `test_api_analysis.py` | 01_URL_TESTS | **PASS** |
| 14 | `TEST-URL-14` | `test_analyze_url_endpoint_invalid_scheme` | `test_api_analysis.py` | 01_URL_TESTS | **PASS** |
| 15 | `TEST-EML-01` | `test_parse_email_sender` | `test_sanitizer.py` | 02_EMAIL_TESTS | **PASS** |
| 16 | `TEST-EML-02` | `test_email_rules_urgency_and_fraud` | `test_rules.py` | 02_EMAIL_TESTS | **PASS** |
| 17 | `TEST-EML-03` | `test_email_job_scam` | `test_rules.py` | 02_EMAIL_TESTS | **PASS** |
| 18 | `TEST-EML-04` | `test_valid_email_analysis_request` | `test_schemas.py` | 02_EMAIL_TESTS | **PASS** |
| 19 | `TEST-EML-05` | `test_invalid_email_analysis_request` | `test_schemas.py` | 02_EMAIL_TESTS | **PASS** |
| 20 | `TEST-EML-06` | `test_email_body_length_boundary` | `test_schemas.py` | 02_EMAIL_TESTS | **PASS** |
| 21 | `TEST-EML-07` | `test_analyze_email_endpoint_fraud_and_urgency` | `test_api_analysis.py` | 02_EMAIL_TESTS | **PASS** |
| 22 | `TEST-EML-08` | `test_analyze_email_with_embedded_urls` | `test_api_analysis.py` | 02_EMAIL_TESTS | **PASS** |
| 23 | `TEST-EML-09` | `test_analyze_email_endpoint_empty_body` | `test_api_analysis.py` | 02_EMAIL_TESTS | **PASS** |
| 24 | `TEST-SMS-01` | `test_extract_phone_numbers` | `test_sanitizer.py` | 03_SMS_TESTS | **PASS** |
| 25 | `TEST-SMS-02` | `test_sms_otp_extraction` | `test_rules.py` | 03_SMS_TESTS | **PASS** |
| 26 | `TEST-SMS-03` | `test_sms_urgency_rule_positive_cases` | `test_rules.py` | 03_SMS_TESTS | **PASS** |
| 27 | `TEST-SMS-04` | `test_sms_urgency_rule_negative_cases` | `test_rules.py` | 03_SMS_TESTS | **PASS** |
| 28 | `TEST-SMS-05` | `test_sms_dual_trigger_otp_and_urgency` | `test_rules.py` | 03_SMS_TESTS | **PASS** |
| 29 | `TEST-SMS-06` | `test_valid_sms_analysis_request` | `test_schemas.py` | 03_SMS_TESTS | **PASS** |
| 30 | `TEST-SMS-07` | `test_invalid_sms_analysis_request` | `test_schemas.py` | 03_SMS_TESTS | **PASS** |
| 31 | `TEST-SMS-08` | `test_sms_message_length_boundary` | `test_schemas.py` | 03_SMS_TESTS | **PASS** |
| 32 | `TEST-SMS-09` | `test_analyze_sms_endpoint_otp_extraction` | `test_api_analysis.py` | 03_SMS_TESTS | **PASS** |
| 33 | `TEST-SMS-10` | `test_analyze_sms_with_embedded_ssrf_url` | `test_api_analysis.py` | 03_SMS_TESTS | **PASS** |
| 34 | `TEST-SMS-11` | `test_analyze_sms_clean` | `test_api_analysis.py` | 03_SMS_TESTS | **PASS** |
| 35 | `TEST-SMS-12` | `test_analyze_sms_compound_urgency_endpoint` | `test_api_analysis.py` | 03_SMS_TESTS | **PASS** |
| 36 | `TEST-SEC-01` | `test_ssrf_rejects_loopback_ipv4` | `test_ssrf.py` | 04_SECURITY_AND_SSRF_TESTS | **PASS** |
| 37 | `TEST-SEC-02` | `test_ssrf_rejects_localhost_hostname` | `test_ssrf.py` | 04_SECURITY_AND_SSRF_TESTS | **PASS** |
| 38 | `TEST-SEC-03` | `test_ssrf_rejects_private_subnets` | `test_ssrf.py` | 04_SECURITY_AND_SSRF_TESTS | **PASS** |
| 39 | `TEST-SEC-04` | `test_ssrf_rejects_cloud_metadata` | `test_ssrf.py` | 04_SECURITY_AND_SSRF_TESTS | **PASS** |
| 40 | `TEST-SEC-05` | `test_ssrf_rejects_ipv6_loopback_and_link_local` | `test_ssrf.py` | 04_SECURITY_AND_SSRF_TESTS | **PASS** |
| 41 | `TEST-SEC-06` | `test_ssrf_rejects_ipv4_mapped_ipv6` | `test_ssrf.py` | 04_SECURITY_AND_SSRF_TESTS | **PASS** |
| 42 | `TEST-SEC-07` | `test_ssrf_rejects_restricted_ports` | `test_ssrf.py` | 04_SECURITY_AND_SSRF_TESTS | **PASS** |
| 43 | `TEST-SEC-08` | `test_ssrf_permits_public_ip` | `test_ssrf.py` | 04_SECURITY_AND_SSRF_TESTS | **PASS** |
| 44 | `TEST-SEC-09` | `test_ssrf_blocks_dual_homed_dns` | `test_ssrf.py` | 04_SECURITY_AND_SSRF_TESTS | **PASS** |
| 45 | `TEST-SEC-10` | `test_ssrf_raises_exception_when_requested` | `test_ssrf.py` | 04_SECURITY_AND_SSRF_TESTS | **PASS** |
| 46 | `TEST-SEC-11` | `test_analyze_url_endpoint_ssrf_detection` | `test_api_analysis.py` | 04_SECURITY_AND_SSRF_TESTS | **PASS** |
| 47 | `TEST-SEC-12` | `test_secret_masking_in_summary` | `test_config.py` | 04_SECURITY_AND_SSRF_TESTS | **PASS** |
| 48 | `TEST-SEC-13` | `test_mask_secret_helper_edge_cases` | `test_config.py` | 04_SECURITY_AND_SSRF_TESTS | **PASS** |
| 49 | `TEST-SEC-14` | `test_secret_scrubbing_log_filter` | `test_config.py` | 04_SECURITY_AND_SSRF_TESTS | **PASS** |
| 50 | `TEST-SEC-15` | `test_security_headers_present` | `test_health.py` | 04_SECURITY_AND_SSRF_TESTS | **PASS** |
| 51 | `TEST-INT-01` | `test_default_settings_instantiation` | `test_config.py` | 05_API_SCHEMA_AND_INTEGRATION_TESTS | **PASS** |
| 52 | `TEST-INT-02` | `test_environment_validation_valid` | `test_config.py` | 05_API_SCHEMA_AND_INTEGRATION_TESTS | **PASS** |
| 53 | `TEST-INT-03` | `test_environment_validation_invalid` | `test_config.py` | 05_API_SCHEMA_AND_INTEGRATION_TESTS | **PASS** |
| 54 | `TEST-INT-04` | `test_cors_origins_parsing` | `test_config.py` | 05_API_SCHEMA_AND_INTEGRATION_TESTS | **PASS** |
| 55 | `TEST-INT-05` | `test_root_endpoint` | `test_health.py` | 05_API_SCHEMA_AND_INTEGRATION_TESTS | **PASS** |
| 56 | `TEST-INT-06` | `test_api_v1_health_endpoint` | `test_health.py` | 05_API_SCHEMA_AND_INTEGRATION_TESTS | **PASS** |
| 57 | `TEST-INT-07` | `test_root_health_alias` | `test_health.py` | 05_API_SCHEMA_AND_INTEGRATION_TESTS | **PASS** |
| 58 | `TEST-INT-08` | `test_custom_correlation_id_preserved` | `test_health.py` | 05_API_SCHEMA_AND_INTEGRATION_TESTS | **PASS** |
| 59 | `TEST-INT-09` | `test_standardized_404_error_envelope` | `test_health.py` | 05_API_SCHEMA_AND_INTEGRATION_TESTS | **PASS** |
| 60 | `TEST-INT-10` | `test_calculate_risk_level_tiers` | `test_rules.py` | 05_API_SCHEMA_AND_INTEGRATION_TESTS | **PASS** |
| 61 | `TEST-INT-11` | `test_clean_input_returns_zero_score` | `test_rules.py` | 05_API_SCHEMA_AND_INTEGRATION_TESTS | **PASS** |
| 62 | `TEST-INT-12` | `test_severity_floor_model_individual_tiers` | `test_rules.py` | 05_API_SCHEMA_AND_INTEGRATION_TESTS | **PASS** |
| 63 | `TEST-INT-13` | `test_severity_floor_model_multi_indicator_interaction` | `test_rules.py` | 05_API_SCHEMA_AND_INTEGRATION_TESTS | **PASS** |
| 64 | `TEST-INT-14` | `test_sanitize_input_text` | `test_sanitizer.py` | 05_API_SCHEMA_AND_INTEGRATION_TESTS | **PASS** |
| 65 | `TEST-INT-15` | `test_security_indicator_schema` | `test_schemas.py` | 05_API_SCHEMA_AND_INTEGRATION_TESTS | **PASS** |
| 66 | `TEST-INT-16` | `test_response_utc_timezone_awareness` | `test_schemas.py` | 05_API_SCHEMA_AND_INTEGRATION_TESTS | **PASS** |
| 67 | `TEST-INT-17` | `test_api_endpoints_emit_utc_timestamp_with_z` | `test_api_analysis.py` | 05_API_SCHEMA_AND_INTEGRATION_TESTS | **PASS** |

---

## 4. Phase Status

> **PHASE 02 STATUS: AWAITING HUMAN VERIFICATION**
