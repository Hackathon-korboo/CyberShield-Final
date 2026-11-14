# PART 05: PYDANTIC SCHEMA DEVELOPMENT — COMMANDS AND OUTPUTS

## Command 1: Pytest Schema Validation Suite
- **Command:** `backend\venv\Scripts\python.exe -m pytest backend/tests -v`
- **Exit Code:** 0
- **Output:**
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0
collecting ... collected 21 items

backend/tests/test_config.py::test_default_settings_instantiation PASSED [  4%]
... (Phase 1 tests pass)
backend/tests/test_schemas.py::test_valid_url_analysis_request PASSED    [ 66%]
backend/tests/test_schemas.py::test_invalid_url_analysis_request PASSED  [ 71%]
backend/tests/test_schemas.py::test_valid_email_analysis_request PASSED  [ 76%]
backend/tests/test_schemas.py::test_invalid_email_analysis_request PASSED [ 80%]
backend/tests/test_schemas.py::test_valid_sms_analysis_request PASSED    [ 85%]
backend/tests/test_schemas.py::test_invalid_sms_analysis_request PASSED  [ 90%]
backend/tests/test_schemas.py::test_security_indicator_schema PASSED     [ 95%]
backend/tests/test_schemas.py::test_url_analysis_response_schema PASSED  [100%]

======================== 21 passed, 1 warning in 0.06s ========================
```
