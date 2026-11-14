# PART 09: SECURITY RULES AND THREAT INDICATOR ENGINE — ISSUES AND FIXES

## Issues Encountered and Resolved

### 1. Distinguishing Genuine Auth Portals from Impersonation Lures
- **Issue:** Simple keyword matching on "login" or "verify" would flag legitimate internal pages on clean sites as suspicious.
- **Resolution:** Configured `SuspiciousAuthKeywordsRule` to trigger only when auth keywords are compounded with domain hyphens (e.g. `bank-verify-portal.com`) or when multiple lure keywords appear together in deep subdomains.
- **Status:** Resolved and verified with zero false positives on clean URLs.
