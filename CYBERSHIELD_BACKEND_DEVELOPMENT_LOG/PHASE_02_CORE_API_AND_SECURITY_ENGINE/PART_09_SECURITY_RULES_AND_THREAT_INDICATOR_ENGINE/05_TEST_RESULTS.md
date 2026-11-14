# PART 09: SECURITY RULES AND THREAT INDICATOR ENGINE — TEST RESULTS

## 1. Unit Test Results

| Test Identifier | Description | Expected Outcome | Actual Outcome | Status |
|---|---|---|---|---|
| `test_calculate_risk_level_tiers` | Verify score to RiskLevel tier mapping | Correct mappings for 0, 15, 40, 70, 100 | Clean, Low, Suspicious, High | PASSED |
| `test_url_rule_ip_hostname` | Verify `RULE-URL-001` triggers on direct IP | Indicator added, score increased | Triggered properly | PASSED |
| `test_url_rule_punycode` | Verify `RULE-URL-002` triggers on Punycode | Indicator added | Triggered properly | PASSED |
| `test_url_rule_suspicious_keywords` | Verify `RULE-URL-003` triggers on auth keywords | Indicator added | Triggered properly | PASSED |
| `test_email_rules_urgency_and_fraud` | Verify `RULE-EML-001` and `RULE-EML-002` | Urgency + payment fraud indicators | Triggered properly | PASSED |
| `test_email_job_scam` | Verify `RULE-EML-003` job scam lure | Job scam indicator | Triggered properly | PASSED |
| `test_sms_otp_extraction` | Verify `RULE-SMS-001` OTP solicitation | Critical indicator with mitigation | Triggered properly | PASSED |
| `test_clean_input_returns_zero_score` | Verify benign target produces zero score | Score 0, RiskLevel CLEAN, 0 indicators | Evaluated as CLEAN | PASSED |
| `test_severity_floor_model_individual_tiers` | Verify Decision A individual severity floors | 0->CLEAN, 5->LOW, 15->LOW, 40->SUSPICIOUS, 70->HIGH | Verified | PASSED |
| `test_severity_floor_model_multi_indicator_interaction` | Verify additive + floor interaction | 1C+1H=70, 2H=50, 3H=75, 3C=100, 1L+1C=70 | Verified | PASSED |
| `test_sms_urgency_rule_positive_cases` | Verify `RULE-SMS-004` triggers on compound urgency | Triggers on 8 smishing samples | Triggered properly | PASSED |
| `test_sms_urgency_rule_negative_cases` | Verify `RULE-SMS-004` ignores benign messages | Medical, delivery, community notices clean | Clean | PASSED |
| `test_sms_dual_trigger_otp_and_urgency` | Verify dual trigger of `RULE-SMS-001` and `RULE-SMS-004` | Both indicators recorded, floor 70 applied | Triggered properly | PASSED |

**Total:** 13 rule engine unit tests executed, 13 passed, 0 failed. Cumulative suite: 67 passed, 0 failed.
