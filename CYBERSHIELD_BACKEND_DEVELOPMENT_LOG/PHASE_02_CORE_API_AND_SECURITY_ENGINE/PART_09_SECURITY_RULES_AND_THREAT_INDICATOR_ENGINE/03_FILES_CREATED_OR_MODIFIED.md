# PART 09: SECURITY RULES AND THREAT INDICATOR ENGINE — FILES CREATED OR MODIFIED

## 1. Files Created
1. `backend/app/engines/rules/base.py` — `BaseSecurityRule` abstract class.
2. `backend/app/engines/rules/url_rules.py` — 5 URL detection rules (`RULE-URL-001` through `RULE-URL-005`).
3. `backend/app/engines/rules/email_rules.py` — 4 Email detection rules (`RULE-EML-001` through `RULE-EML-004`).
4. `backend/app/engines/rules/sms_rules.py` — 3 SMS detection rules (`RULE-SMS-001` through `RULE-SMS-003`).
5. `backend/app/engines/rules/engine.py` — `SecurityRuleEngine` and `calculate_risk_level()`.
6. `backend/app/engines/rules/__init__.py` — Package export.
7. `backend/tests/test_rules.py` — 8 unit tests for rule execution and scoring.

## 2. Files Modified
1. `backend/app/engines/__init__.py` — Exported `SecurityRuleEngine` and `calculate_risk_level`.
