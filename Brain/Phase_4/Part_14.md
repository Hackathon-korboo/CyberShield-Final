# PART 14 — SEVERITY & INDICATOR CLASSIFICATION

**Document ID:** `Brain/Phase_4/Part_14.md`  
**Date:** 2026-11-14  
**Project:** CyberShield AI 2.0  
**Phase:** Stage 4 — Risk Assessment Engine  
**Part:** Part 14  
**Status:** `IMPLEMENTATION_COMPLETED_AND_VERIFIED`

---

## 1. Objective & Scope

Part 14 enriches standardized findings with consistent severity assignments, authority tiers, documented severity bases, and correlation groups. It provides:
- Authority categorization: `AUTHORITATIVE`, `POLICY_VIOLATION`, `HEURISTIC`, `INFORMATIONAL`, `INCONCLUSIVE`.
- Clear invariant enforcement: Heuristic findings and AI inferences are NEVER represented as authoritative confirmation.
- Policy Separation: SSRF destination checks (`RULE-SSRF-001`, `002`, `003`) are classified under `POLICY_VIOLATION` (not `AUTHORITATIVE`), ensuring an internal network egress violation never asserts that an external target is a confirmed malicious website.
- Authoritative tier is strictly reserved for verified threat intelligence matches (`RULE-INTEL-001`).
- Documented rationale registry for each security rule.
- Correlation group tracking (`CORR-IP-DESTINATION`, `CORR-URGENCY`, `CORR-OTP-HARVEST`, etc.) to prevent double-counting of correlated findings.
- Quantitative check coverage and calibrated confidence scoring.

---

## 2. Files Created or Modified

1. `backend/app/schemas/risk.py`:
   - `AuthorityCategory` enum (`AUTHORITATIVE`, `POLICY_VIOLATION`, `HEURISTIC`, `INFORMATIONAL`, `INCONCLUSIVE`)
   - `RiskClassification` enum (`LOW_RISK`, `SUSPICIOUS`, `HIGH_RISK`, `CONFIRMED_MALICIOUS`, `INCONCLUSIVE`)
   - `ClassifiedIndicator` Pydantic model (`extra="forbid"`) with `is_policy_violation` field
   - `ClassificationPackage` Pydantic model
2. `backend/app/services/risk/severity_classifier.py`:
   - `SEVERITY_BASIS_REGISTRY`: SSRF rules mapped to `POLICY_VIOLATION`; threat intelligence mapped to `AUTHORITATIVE`.
   - `CORRELATION_MAP`: Maps both `RULE-URL-001` and `RULE-SSRF-001` to `CORR-IP-DESTINATION` to prevent double-counting.
   - `SeverityClassifier` class implementing authority classification, coverage, and confidence calculations.
3. `backend/tests/test_part14_severity.py`:
   - 7 unit tests validating SSRF policy violation classification, authoritative threat intelligence classification, heuristic boundaries, AI inference limits, correlation grouping, and coverage/confidence metrics.

---

## 3. Test Evidence

Executed: `.\backend\venv\Scripts\python.exe -m pytest backend/tests/test_part14_severity.py -v`
- `test_authoritative_ssrf_classification`: **PASSED** (verifies `POLICY_VIOLATION`, `is_authoritative=False`, `is_policy_violation=True`)
- `test_authoritative_threat_intel_classification`: **PASSED** (verifies `AUTHORITATIVE`, `is_authoritative=True`, `is_policy_violation=False`)
- `test_heuristic_indicator_classification`: **PASSED**
- `test_ai_inference_authority_is_never_authoritative`: **PASSED**
- `test_unavailable_check_classified_as_inconclusive`: **PASSED**
- `test_correlated_indicators_grouped`: **PASSED**
- `test_coverage_and_confidence_calculation`: **PASSED**
- **Result:** 7 passed in 0.05s.

---

## 4. Definition of Done Checklist

- [x] Every indicator has a documented severity and authority basis.
- [x] Correlated indicators are detected and tagged to prevent blind double-counting.
- [x] Heuristic findings and AI inferences are not represented as authoritative confirmation.
- [x] Evidence provenance and timestamps are preserved.
- [x] Check coverage and confidence metrics are calculated with mandatory safety disclaimers.
- [x] Tests pass (6 passed, 0 failed).
