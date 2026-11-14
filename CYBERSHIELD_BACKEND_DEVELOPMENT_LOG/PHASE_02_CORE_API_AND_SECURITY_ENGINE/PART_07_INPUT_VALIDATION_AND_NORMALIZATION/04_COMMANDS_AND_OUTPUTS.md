# PART 07: INPUT VALIDATION AND NORMALIZATION — COMMANDS AND OUTPUTS

## Command 1: Pytest Sanitizer & Normalization Test Execution
- **Command:** `backend\venv\Scripts\python.exe -m pytest backend/tests -v`
- **Exit Code:** 0
- **Output:**
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0
collecting ... collected 35 items

backend/tests/test_sanitizer.py::test_normalize_target_url_basic PASSED  [ 57%]
backend/tests/test_sanitizer.py::test_normalize_target_url_punycode PASSED [ 60%]
backend/tests/test_sanitizer.py::test_normalize_target_url_dot_segments PASSED [ 62%]
backend/tests/test_sanitizer.py::test_normalize_target_url_invalid PASSED [ 65%]
backend/tests/test_extract_urls_from_text PASSED                         [ 68%]
backend/tests/test_sanitizer.py::test_extract_phone_numbers PASSED       [ 71%]
backend/tests/test_sanitizer.py::test_parse_email_sender PASSED          [ 74%]
backend/tests/test_sanitizer.py::test_sanitize_input_text PASSED         [ 77%]
... (Other tests pass)

======================= 35 passed, 4 warnings in 0.09s ========================
```
