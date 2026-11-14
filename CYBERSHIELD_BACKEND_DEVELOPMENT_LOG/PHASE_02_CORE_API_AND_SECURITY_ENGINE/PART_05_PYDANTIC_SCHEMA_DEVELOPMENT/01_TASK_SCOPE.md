# PART 05: PYDANTIC SCHEMA DEVELOPMENT — TASK SCOPE

## 1. Goal & Objective
Define and validate robust, type-safe Pydantic V2 data models for CyberShield AI 2.0 analysis APIs (URL, Email, SMS), ensuring consistent request and response structures, field length constraints, defensive validation, and explicit segregation of empirical evidence from heuristic findings.

## 2. In-Scope Tasks
1. Inspect frozen Phase 01 schemas (`common.py`, `health.py`).
2. Design request schemas:
   - `UrlAnalysisRequest` (`backend/app/schemas/url.py`)
   - `EmailAnalysisRequest` (`backend/app/schemas/email.py`)
   - `SmsAnalysisRequest` (`backend/app/schemas/sms.py`)
3. Design response and indicator models (`backend/app/schemas/analysis.py`):
   - `RiskLevel` Enum (`CLEAN`, `LOW_RISK`, `SUSPICIOUS`, `HIGH_RISK`)
   - `SecurityIndicator` (rule ID, category, severity, evidence snippet, explanation, mitigation)
   - `UrlObservedEvidence` (normalized URL, scheme, hostname, port, IP, SSRF safety, homoglyphs)
   - `EmailObservedEvidence` (sender domain, extracted URLs, extracted phone numbers)
   - `SmsObservedEvidence` (extracted URLs, phone numbers, character length)
   - `UrlAnalysisResponse`, `EmailAnalysisResponse`, `SmsAnalysisResponse`
4. Apply field constraints (min/max length, regex, whitespace trimming).
5. Ensure no AI-generated or Blockchain placeholders are marked as completed.
6. Author unit tests covering valid payloads, invalid structures, boundary cases, and edge cases.

## 3. Out-of-Scope Tasks
- Implementing Gemini LLM response fields (reserved for Phase 03).
- Implementing smart contract / Web3 trust verification fields (reserved for Phase 04).
- Creating routes or endpoints (reserved for Part 06).

## 4. Acceptance Criteria
- Valid payloads validate cleanly.
- Invalid, empty, or excessively long payloads are rejected with clear validation messages.
- Evidence structures remain separate from heuristic findings.
- Unit tests verify schema validation and boundary constraints.
