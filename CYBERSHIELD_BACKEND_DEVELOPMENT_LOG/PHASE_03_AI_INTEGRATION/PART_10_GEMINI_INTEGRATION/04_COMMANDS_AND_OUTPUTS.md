# PART 10: GEMINI API INTEGRATION — COMMANDS AND OUTPUTS

**Part Identifier:** PART_10  
**Parent Phase:** PHASE 03 — AI Integration  

---

## 1. Package Installation Command

```powershell
.\backend\venv\Scripts\python.exe -m pip install google-genai
```

**Output:**
```text
Successfully installed cffi-2.1.1 cryptography-50.0.2 distro-1.9.0 google-auth-2.62.2 google-genai-3.3.0 httpcore2-2.16.0 httpx2-2.16.0 pyasn1-0.6.5 pyasn1-modules-0.4.2 pycparser-3.12 sniffio-1.3.1 tenacity-9.1.4 truststore-0.10.5
```

---

## 2. Unit & Mock Testing Command

```powershell
.\backend\venv\Scripts\python.exe -m pytest backend/tests/test_ai_client.py backend/tests/test_ai_live.py -v
```

**Output:**
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0 -- D:\Adamas offline Hackathon\backend\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\Adamas offline Hackathon
configfile: pytest.ini
plugins: anyio-4.16.0, asyncio-1.5.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 12 items

backend/tests/test_ai_client.py::test_gemini_client_init_without_key PASSED [  8%]
backend/tests/test_ai_client.py::test_gemini_client_init_with_key PASSED [ 16%]
backend/tests/test_ai_client.py::test_gemini_client_init_with_pydantic_secret_str PASSED [ 25%]
backend/tests/test_ai_client.py::test_gemini_client_timeout_handling PASSED [ 33%]
backend/tests/test_ai_client.py::test_gemini_client_rate_limit_handling PASSED [ 41%]
backend/tests/test_ai_client.py::test_gemini_client_auth_error_handling PASSED [ 50%]
backend/tests/test_ai_client.py::test_gemini_client_retry_logic_transient_error PASSED [ 58%]
backend/tests/test_ai_client.py::test_mock_provider_basic_generation PASSED [ 66%]
backend/tests/test_ai_client.py::test_mock_provider_error_simulations PASSED [ 75%]
backend/tests/test_ai_client.py::test_mock_provider_health_check PASSED  [ 83%]
backend/tests/test_ai_live.py::test_live_gemini_api_connectivity SKIPPED [ 91%]
backend/tests/test_ai_live.py::test_live_gemini_health_check SKIPPED     [100%]

================== 10 passed, 2 skipped, 1 warning in 3.04s ===================
```
