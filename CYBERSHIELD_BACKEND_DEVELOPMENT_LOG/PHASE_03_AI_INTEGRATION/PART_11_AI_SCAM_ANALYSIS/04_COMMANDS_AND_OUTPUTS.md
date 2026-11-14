# PART 11: AI-BASED SCAM ANALYSIS & EXPLANATION — COMMANDS AND OUTPUTS

**Part Identifier:** PART_11  
**Parent Phase:** PHASE 03 — AI Integration  

---

## 1. Test Execution Command

```powershell
.\backend\venv\Scripts\python.exe -m pytest backend/tests/test_ai_scam_analysis.py -v
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
collecting ... collected 7 items

backend/tests/test_ai_scam_analysis.py::test_url_scam_analysis_phishing PASSED [ 14%]
backend/tests/test_ai_scam_analysis.py::test_url_scam_analysis_benign PASSED [ 28%]
backend/tests/test_ai_scam_analysis.py::test_email_phishing_analysis PASSED [ 42%]
backend/tests/test_ai_scam_analysis.py::test_sms_smishing_analysis PASSED [ 57%]
backend/tests/test_ai_scam_analysis.py::test_analyzer_markdown_fence_stripping PASSED [ 71%]
backend/tests/test_ai_scam_analysis.py::test_analyzer_rejects_non_json PASSED [ 85%]
backend/tests/test_ai_scam_analysis.py::test_analyzer_rejects_missing_required_fields PASSED [100%]

======================== 7 passed, 1 warning in 0.06s =========================
```
