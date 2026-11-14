# PART 08: SSRF PROTECTION AND SAFE URL HANDLING — ISSUES AND FIXES

## Issues Encountered and Resolved

### 1. IPv6 Netloc Bracket Dropping in URL Normalization
- **Description:** When an IPv6 literal (e.g. `http://[::1]/`) was processed by `normalize_target_url()`, the reconstructed netloc was saved as `::1` without enclosing square brackets. Downstream re-parsing via `urllib.parse.urlsplit` resulted in `ValueError: Port could not be cast to integer value as ':1'`.
- **Root Cause:** Standard RFC 3986 mandates square brackets around IPv6 addresses in netloc. `idna.encode(hostname)` stripped the brackets.
- **Resolution:** Updated `normalize_target_url()` in `backend/app/utils/sanitizer.py` to format IPv6 netlocs with brackets: `f"[{ascii_host}]"` whenever `:` is present in `ascii_host`.
- **Status:** Resolved and verified with 100% test pass rate.
