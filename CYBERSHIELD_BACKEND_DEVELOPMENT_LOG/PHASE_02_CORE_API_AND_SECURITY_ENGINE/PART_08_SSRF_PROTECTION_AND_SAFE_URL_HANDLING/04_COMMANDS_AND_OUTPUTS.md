# PART 08: SSRF PROTECTION AND SAFE URL HANDLING — COMMANDS AND OUTPUTS

## Command 1: Pytest SSRF Test Suite Execution
- **Command:** `backend\venv\Scripts\python.exe -m pytest backend/tests -v`
- **Exit Code:** 0
- **Output:**
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0
collecting ... collected 45 items

backend/tests/test_ssrf.py::test_ssrf_rejects_loopback_ipv4 PASSED       [ 80%]
backend/tests/test_ssrf.py::test_ssrf_rejects_localhost_hostname PASSED  [ 82%]
backend/tests/test_ssrf.py::test_ssrf_rejects_private_subnets PASSED     [ 84%]
backend/tests/test_ssrf.py::test_ssrf_rejects_cloud_metadata PASSED      [ 86%]
backend/tests/test_ssrf.py::test_ssrf_rejects_ipv6_loopback_and_link_local PASSED [ 88%]
backend/tests/test_ssrf.py::test_ssrf_rejects_ipv4_mapped_ipv6 PASSED    [ 91%]
backend/tests/test_ssrf.py::test_ssrf_rejects_restricted_ports PASSED    [ 93%]
backend/tests/test_ssrf.py::test_ssrf_permits_public_ip PASSED           [ 95%]
backend/tests/test_ssrf.py::test_ssrf_blocks_dual_homed_dns PASSED       [ 97%]
backend/tests/test_ssrf.py::test_ssrf_raises_exception_when_requested PASSED [100%]
... (Other tests pass)

======================= 45 passed, 4 warnings in 0.10s ========================
```
