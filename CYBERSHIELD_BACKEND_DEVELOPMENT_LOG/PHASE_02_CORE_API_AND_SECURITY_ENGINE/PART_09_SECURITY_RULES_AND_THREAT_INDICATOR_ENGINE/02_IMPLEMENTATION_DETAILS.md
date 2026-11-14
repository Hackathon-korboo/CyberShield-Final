# PART 09: SECURITY RULES AND THREAT INDICATOR ENGINE — IMPLEMENTATION DETAILS

## 1. Work Performed
1. Designed and structured a modular, deterministic rules engine under `backend/app/engines/rules/`:
   - `base.py`: `BaseSecurityRule` protocol defining `rule_id`, `category`, `severity`, `explanation`, `mitigation`, and `evaluate()`.
   - `url_rules.py`:
     - `RULE-URL-001` (IpHyphenRule): Direct IP literal in hostname.
     - `RULE-URL-002` (PunycodeHomoglyphRule): Punycode (`xn--`) domain spoofing.
     - `RULE-URL-003` (SuspiciousAuthKeywordsRule): Credential lure keywords combined with hyphens.
     - `RULE-URL-004` (ExcessiveSubdomainRule): Nested subdomains >= 5 labels.
     - `RULE-URL-005` (SuspiciousTldRule): High-abuse TLDs (`.zip`, `.top`, `.tk`, etc.).
   - `email_rules.py`:
     - `RULE-EML-001` (EmailUrgencyRule): Artificial panic trigger phrases.
     - `RULE-EML-002` (EmailPaymentFraudRule): Gift card, wire transfer, crypto solicitations.
     - `RULE-EML-003` (EmailJobScamRule): Implausible work-from-home compensation lures.
     - `RULE-EML-004` (EmailCredentialHarvestRule): Password and identity verification requests.
   - `sms_rules.py`:
     - `RULE-SMS-001` (SmsOtpExtractionRule): Explicit 4-6 digit OTP or PIN extraction prompts.
     - `RULE-SMS-002` (SmsCardBlockageRule): Urgent debit/credit card blockage alerts.
     - `RULE-SMS-003` (SmsLotteryPrizeRule): Unsolicited lottery, prize, or cash gift lures.
   - `engine.py`: `SecurityRuleEngine` and `calculate_risk_level()` providing weighted scoring (`CRITICAL`: 40, `HIGH`: 25, `MEDIUM`: 15, `LOW`: 5) and classification into standard `RiskLevel` tiers (`CLEAN`, `LOW_RISK`, `SUSPICIOUS`, `HIGH_RISK`).
2. Created 8 unit tests in `backend/tests/test_rules.py`.
3. Executed full test suite (53 tests passed).

## 2. Technical Decisions
- **Decision 1: Transparent Rule Finding Provenance:** Every `SecurityIndicator` captures the exact triggering substring (`evidence`), preventing blackbox assumptions.
- **Decision 2: Deterministic Linear Evaluation:** All rules use bounded regex and string operations without exponential backtracking ($O(N)$), preventing ReDoS.
- **Decision 3: Risk Classification Tiers:** Scores map to transparent brackets (0-14: CLEAN, 15-39: LOW_RISK, 40-69: SUSPICIOUS, 70-100: HIGH_RISK).
