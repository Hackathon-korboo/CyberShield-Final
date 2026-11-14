# PART 08: SSRF PROTECTION AND SAFE URL HANDLING — FILES CREATED OR MODIFIED

## 1. Files Created
1. `backend/app/engines/ssrf_guard.py` — `SSRFGuard` engine with IP parsing, DNS inspection, and metadata blocking.
2. `backend/tests/test_ssrf.py` — 10 SSRF unit tests covering loopbacks, cloud metadata, IPv6, ports, and dual-record DNS.

## 2. Files Modified
1. `backend/app/engines/__init__.py` — Exported `SSRFGuard` and `SSRFValidationResult`.
2. `backend/app/utils/sanitizer.py` — Fixed bracket preservation for IPv6 netloc strings.
