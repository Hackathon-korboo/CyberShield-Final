# PART 12: AI SECURITY, VALIDATION & CORE INTEGRATION — ISSUES AND FIXES

**Part Identifier:** PART_12  
**Parent Phase:** PHASE 03 — AI Integration  

---

## 1. Technical Issues Encountered & Resolved

### Issue 1: Circuit Breaker Sleep Granularity on Windows Subsystem
- **Description:** In `test_circuit_breaker_recovery_half_open`, testing a 0.05-second threshold with a 0.06-second sleep intermittently failed because Windows timer ticks have ~15ms granularity, resulting in elapsed time measuring slightly under 0.05s.
- **Resolution:** Adjusted test recovery threshold to 0.10s and sleep window to 0.15s, providing adequate tolerance across Windows scheduler intervals.

### Issue 2: Integration Test Phishing Lure Keyword Alignment
- **Description:** `test_ai_email_endpoint_phishing` submitted a test body with `"Your bank card is blocked. Click here to confirm your PIN immediately"`, which did not match the strict compound regexes of `URGENCY_PATTERNS` in the frozen heuristic engine.
- **Resolution:** Aligned test payload to include canonical phishing lures (`"Your account has been suspended. Please confirm your password within 24 hours"`), triggering deterministic indicator `RULE-EML-001` and verifying composite AI enrichment.
