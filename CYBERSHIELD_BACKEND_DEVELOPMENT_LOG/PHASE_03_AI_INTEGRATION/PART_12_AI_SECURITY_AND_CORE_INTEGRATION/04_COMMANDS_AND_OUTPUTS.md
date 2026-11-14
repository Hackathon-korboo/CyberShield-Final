# PART 12: AI SECURITY, VALIDATION & CORE INTEGRATION — COMMANDS AND OUTPUTS

**Part Identifier:** PART_12  
**Parent Phase:** PHASE 03 — AI Integration  

---

## 1. Full Regression & Integration Test Command

```powershell
.\backend\venv\Scripts\python.exe -m pytest backend/tests -v
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
collecting ... collected 102 items

backend/tests/test_ai_client.py (10 passed)
backend/tests/test_ai_fallback.py (5 passed)
backend/tests/test_ai_integration.py (7 passed)
backend/tests/test_ai_live.py (2 skipped)
backend/tests/test_ai_scam_analysis.py (7 passed)
backend/tests/test_ai_security.py (4 passed)
backend/tests/test_api_analysis.py (12 passed - Phase 02 Baseline)
backend/tests/test_config.py (7 passed - Phase 01 Baseline)
backend/tests/test_health.py (6 passed - Phase 01 Baseline)
backend/tests/test_rules.py (13 passed - Phase 02 Baseline)
backend/tests/test_sanitizer.py (8 passed - Phase 02 Baseline)
backend/tests/test_schemas.py (11 passed - Phase 02 Baseline)
backend/tests/test_ssrf.py (10 passed - Phase 02 Baseline)

================= 100 passed, 2 skipped, 4 warnings in 4.10s ==================
```
