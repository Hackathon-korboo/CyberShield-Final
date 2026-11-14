# PART 10: CORE SECURITY ENGINE INTEGRATION — TASK SCOPE

## 1. Goal & Objective
Unify the API routing layer, Pydantic schemas, normalization helpers, SSRF guard, and rule engine into a coherent, high-performance orchestration service (`backend/app/services/threat_service.py`), establishing end-to-end request-to-response workflows with integration tests.

## 2. In-Scope Tasks
1. Build `ThreatAnalysisService` in `backend/app/services/threat_service.py`:
   - URL Analysis Pipeline: Normalize -> SSRF Guard -> Rule Engine -> Format Response.
   - Email Analysis Pipeline: Parse -> Extract URLs -> Preflight Check Extracted URLs -> Evaluate Email Rules -> Format Response.
   - SMS Analysis Pipeline: Parse -> Extract URLs -> Preflight Check Extracted URLs -> Evaluate SMS Rules -> Format Response.
2. Aggregate risk scores deterministically based on detected indicator severities.
3. Wire service layer to API controllers in `backend/app/api/routes/analysis.py`.
4. Create comprehensive integration test suite (`backend/tests/test_api_analysis.py`).
5. Execute full test suite and verify end-to-end functionality.

## 3. Out-of-Scope Tasks
- Gemini AI integration (Phase 03).
- Blockchain Web3 integration (Phase 04).
- Production deployment or Git operations.

## 4. Acceptance Criteria
- All 3 analysis endpoints function end-to-end.
- SSRF checks trigger properly on malicious URL submissions.
- Extracted URLs in SMS/email are subjected to SSRF validation.
- All integration tests pass with 100% success rate.
