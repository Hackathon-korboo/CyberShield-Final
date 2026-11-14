# PART 09: AI ARCHITECTURE & INTEGRATION PLANNING — ISSUES AND FIXES

**Part Identifier:** PART_09  
**Parent Phase:** PHASE 03 — AI Integration  

---

## 1. Technical Invariant Reconciliation

### Issue 1: Ensuring 100% Backward Compatibility with Frozen Phase 02 Schemas
- **Challenge:** Phase 02 response schemas (`UrlAnalysisResponse`, `EmailAnalysisResponse`, `SmsAnalysisResponse`) have `model_config = ConfigDict(extra="forbid")`. Adding rogue fields directly breaks Phase 02 validation tests.
- **Resolution:** Designed an explicit response extension model (`ExtendedUrlAnalysisResponse`, `ExtendedEmailAnalysisResponse`, `ExtendedSmsAnalysisResponse`) that cleanly inherits from the frozen schemas and attaches `ai_analysis: Optional[AiAnalysisResult] = None`. This preserves 100% backward compatibility when AI is absent or disabled.

### Issue 2: Preventing LLM Hallucinations from Fabricating Deterministic Evidence
- **Challenge:** LLMs often assert ungrounded claims (e.g. claiming a website is "confirmed phishing" without proof).
- **Resolution:** Hardened system prompts strictly separate `observed_evidence` and `heuristic_findings` from `ai_inferences`. Required every AI analysis output to include an explicit `uncertainty_statement`.
