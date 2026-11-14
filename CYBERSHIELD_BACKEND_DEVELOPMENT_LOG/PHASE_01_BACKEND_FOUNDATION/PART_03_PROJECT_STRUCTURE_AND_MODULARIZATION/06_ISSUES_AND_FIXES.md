# PART 03: PROJECT STRUCTURE AND MODULARIZATION — ISSUES AND FIXES

## Issues Encountered and Resolved

### Issue 1: Starlette TestClient Deprecation Warning with httpx
- **Description:** Pytest reported a warning: `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`
- **Resolution:** Updated `conftest.py` and `test_health.py` to import `TestClient` from `fastapi.testclient`, which is FastAPI's standard recommended import pattern.
- **Status:** Resolved cleanly.
