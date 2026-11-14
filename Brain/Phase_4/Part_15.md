# PART 15 — DETERMINISTIC RISK ENGINE

**Document ID:** `Brain/Phase_4/Part_15.md`  
**Date:** 2026-11-14  
**Project:** CyberShield AI 2.0  
**Phase:** Stage 4 — Risk Assessment Engine  
**Part:** Part 15  
**Status:** `IMPLEMENTATION_COMPLETED_AND_VERIFIED`

---

## 1. Objective & Scope

Part 15 aggregates classified findings into an explainable, deterministic threat evaluation using codified rules, correlation deduplication, and severity floors.

### Implemented Threat Classifications
1. `LOW_RISK`: No significant malicious indicators detected. Explicit disclaimer that this does not prove the website is safe.
2. `SUSPICIOUS`: One or more indicators requiring further investigation.
3. `HIGH_RISK`: Multiple significant independent indicators (e.g. 2+ independent HIGH findings or score >= 70), OR internal security policy violations (e.g. SSRF prohibited egress to loopback/private/metadata ranges).
4. `CONFIRMED_MALICIOUS`: Strictly backed by verified authoritative external threat intelligence blocklist matches (`RULE-INTEL-001`). Score is 100.
5. `INCONCLUSIVE`: Core investigation failed (e.g. DNS failure) or checks were unavailable.

### Codified Security Invariants
- An LLM opinion alone cannot produce `CONFIRMED_MALICIOUS` (capped at `SUSPICIOUS`).
- Policy Separation: An SSRF policy violation alone never asserts external target maliciousness. It is classified as `HIGH_RISK` (severity floor 70) with `has_policy_violation=True` and `has_authoritative_match=False`.
- Valid HTTPS is never treated as proof of legitimacy.
- Missing threat intelligence or clean heuristic scans are not treated as proof of safety.
- Failed checks do not crash the engine and are evaluated conservatively.
- Correlated indicators sharing a root cause (`CORR-URGENCY`, `CORR-IP-DESTINATION`) contribute once, preventing blind double-counting.

---

## 2. Files Created or Modified

1. `backend/app/schemas/risk.py`:
   - Added `DeterministicRiskAssessment` Pydantic model (`extra="forbid"`) with `has_policy_violation` field.
2. `backend/app/services/risk/deterministic_engine.py`:
   - Implemented `DeterministicRiskEngine.evaluate()`.
   - Integrated correlated score aggregation with `SEVERITY_FLOORS` and policy violation vs. authoritative gating.
   - Separated policy violation summary and explanation from general threat classification.
3. `backend/tests/test_part15_risk_engine.py`:
   - 13 comprehensive unit test scenarios directly mapped to roadmap requirements and SSRF policy separation.

---

## 3. Test Evidence

Executed: `.\backend\venv\Scripts\python.exe -m pytest backend/tests/test_part15_risk_engine.py -v`
- `test_scenario_01_benign_input_completed_checks`: **PASSED**
- `test_scenario_02_suspicious_url_indicators`: **PASSED**
- `test_scenario_03_multiple_significant_indicators`: **PASSED**
- `test_scenario_04_authoritative_malicious_match`: **PASSED** (verifies threat intelligence yields `CONFIRMED_MALICIOUS`, score 100)
- `test_scenario_ssrf_policy_violation_yields_high_risk_not_confirmed_malicious`: **PASSED** (verifies SSRF yields `HIGH_RISK`, score 70, `has_policy_violation=True`, `has_authoritative_match=False`)
- `test_scenario_05_missing_or_unavailable_checks`: **PASSED**
- `test_scenario_06_dns_failure_returns_inconclusive`: **PASSED**
- `test_scenario_07_conflicting_evidence_handled_conservatively`: **PASSED**
- `test_scenario_08_duplicate_indicators_do_not_inflate_score`: **PASSED**
- `test_scenario_09_correlated_evidence_prevents_double_counting`: **PASSED**
- `test_scenario_10_ai_only_prediction_never_confirmed_malicious`: **PASSED**
- `test_scenario_11_valid_https_does_not_override_suspicious_indicators`: **PASSED**
- `test_scenario_12_no_threat_intel_match_with_incomplete_checks`: **PASSED**
- **Result:** 13 passed in 0.07s.

---

## 4. Definition of Done Checklist

- [x] The same input evidence consistently produces the exact same classification and score.
- [x] Every risk classification is accompanied by an empirical summary and supporting citations.
- [x] `CONFIRMED_MALICIOUS` strictly requires documented authoritative validation.
- [x] Missing/failed information (e.g. DNS failure) results in `INCONCLUSIVE` rather than `LOW_RISK`.
- [x] All 12 required test scenarios pass.
