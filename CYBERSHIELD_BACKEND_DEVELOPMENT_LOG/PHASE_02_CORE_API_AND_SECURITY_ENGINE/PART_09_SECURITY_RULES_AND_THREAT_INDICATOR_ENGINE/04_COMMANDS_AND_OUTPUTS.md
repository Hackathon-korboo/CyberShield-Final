# PART 09: SECURITY RULES AND THREAT INDICATOR ENGINE — COMMANDS AND OUTPUTS

## Command 1: Pytest Security Rules Test Execution
- **Command:** `backend\venv\Scripts\python.exe -m pytest backend/tests -v`
- **Exit Code:** 0
- **Output:**
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0
collecting ... collected 53 items

backend/tests/test_rules.py::test_calculate_risk_level_tiers PASSED      [ 37%]
backend/tests/test_rules.py::test_url_rule_ip_hostname PASSED            [ 39%]
backend/tests/test_rules.py::test_url_rule_punycode PASSED               [ 41%]
backend/tests/test_rules.py::test_url_rule_suspicious_keywords PASSED    [ 43%]
backend/tests/test_rules.py::test_email_rules_urgency_and_fraud PASSED   [ 45%]
backend/tests/test_rules.py::test_email_job_scam PASSED                  [ 47%]
backend/tests/test_sms_otp_extraction PASSED                            [ 49%]
backend/tests/test_clean_input_returns_zero_score PASSED                 [ 50%]
... (All 53 tests pass)

======================= 53 passed, 4 warnings in 0.13s ========================
```
