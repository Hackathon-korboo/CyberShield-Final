# PART 05: PYDANTIC SCHEMA DEVELOPMENT — IMPLEMENTATION DETAILS

## 1. Work Performed
1. Reviewed existing Phase 01 schemas (`backend/app/schemas/common.py`, `backend/app/schemas/health.py`).
2. Implemented request schemas:
   - `UrlAnalysisRequest` (`backend/app/schemas/url.py`): URL validation, string length limits (3 to 2048 chars), scheme check.
   - `EmailAnalysisRequest` (`backend/app/schemas/email.py`): Body length (1 to 50,000 chars), subject/sender constraints.
   - `SmsAnalysisRequest` (`backend/app/schemas/sms.py`): Message length (1 to 2,000 chars), sender constraint.
3. Implemented response schemas and models (`backend/app/schemas/analysis.py`):
   - `RiskLevel` Enum: `CLEAN`, `LOW_RISK`, `SUSPICIOUS`, `HIGH_RISK`.
   - `SecurityIndicator`: Rule ID, Category, Severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), Evidence substring, Explanation, Mitigation.
   - `UrlObservedEvidence`, `EmailObservedEvidence`, `SmsObservedEvidence`: Detailed empirical observations cleanly separated from heuristic scores.
   - `UrlAnalysisResponse`, `EmailAnalysisResponse`, `SmsAnalysisResponse`: Full response structures wrapping evidence, heuristic findings, and analysis metadata.
4. Exported all schemas in `backend/app/schemas/__init__.py`.
5. Created unit tests in `backend/tests/test_schemas.py` asserting validation on valid/invalid inputs.

## 2. Technical Decisions
- **Decision 1: Strict Input Constraints:** Input strings are bounded with `min_length` and `max_length` to prevent payload inflation or memory exhaustion.
- **Decision 2: Separation of Evidence and Heuristics:** In compliance with Rule 14, `observed_evidence` contains verifiable facts (scheme, hostname, port, IP, character length) while `heuristic_findings` contains rule IDs, severities, and risk scores.
- **Decision 3: Zero AI Placeholders in Phase 2 Responses:** Kept Phase 2 response models clean of premature Phase 3/4 mock fields.
