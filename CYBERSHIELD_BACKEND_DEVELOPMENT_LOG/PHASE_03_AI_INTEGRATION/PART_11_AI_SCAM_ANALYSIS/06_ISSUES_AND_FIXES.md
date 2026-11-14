# PART 11: AI-BASED SCAM ANALYSIS & EXPLANATION — ISSUES AND FIXES

**Part Identifier:** PART_11  
**Parent Phase:** PHASE 03 — AI Integration  

---

## 1. Technical Issues Encountered & Resolved

### Issue 1: Assertions on Free-Form LLM Summary vs Explanation Fields
- **Description:** In `test_url_scam_analysis_phishing`, the test assertion initially checked for `"credential harvesting"` exclusively inside `result.summary.lower()`, whereas the mock response placed the detailed technical phrase inside `result.explanation` and a concise sentence in `result.summary`.
- **Resolution:** Updated assertion to verify `result.explanation` for in-depth technical phrases and `result.summary` for threat intent.
