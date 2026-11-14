# PART 04: ENVIRONMENT AND CONFIGURATION — COMMANDS AND OUTPUTS

## Command 1: Pytest Configuration & Health Test Execution (Secondary Review)
- **Command:** `python -m pytest backend/tests -v`
- **Exit Code:** 0
- **Output:**
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
collecting ... collected 13 items

backend/tests/test_config.py::test_default_settings_instantiation PASSED [  7%]
backend/tests/test_config.py::test_secret_masking_in_summary PASSED      [ 15%]
backend/tests/test_config.py::test_mask_secret_helper_edge_cases PASSED  [ 23%]
backend/tests/test_config.py::test_environment_validation_valid PASSED   [ 30%]
backend/tests/test_config.py::test_environment_validation_invalid PASSED [ 38%]
backend/tests/test_config.py::test_cors_origins_parsing PASSED           [ 46%]
backend/tests/test_config.py::test_secret_scrubbing_log_filter PASSED    [ 53%]
backend/tests/test_health.py::test_root_endpoint PASSED                  [ 61%]
backend/tests/test_api_v1_health_endpoint PASSED         [ 69%]
backend/tests/test_root_health_alias PASSED              [ 76%]
backend/tests/test_security_headers_present PASSED                       [ 84%]
backend/tests/test_custom_correlation_id_preserved PASSED                [ 92%]
backend/tests/test_standardized_404_error_envelope PASSED                 [100%]

======================== 13 passed, 1 warning in 0.08s ========================
```

## Command 2: Application Entry Point Diagnostic Verification
- **Command:** `python -c "from backend.app.main import app; print('App title:', app.title, 'Version:', app.version)"`
- **Exit Code:** 0
- **Output:**
```
App title: CyberShield AI 2.0 Version: 2.0.0
```
