# PART 11: AI-BASED SCAM ANALYSIS & EXPLANATION — IMPLEMENTATION DETAILS

**Part Identifier:** PART_11  
**Parent Phase:** PHASE 03 — AI Integration  
**Status:** IMPLEMENTATION_COMPLETED  

---

## 1. Technical Implementation Summary

Part 11 implements the prompt engineering, contextual threat reasoning, and schema parsing engine across URL, Email, and SMS attack surfaces:

1. **System Directives & Role (`backend/app/engines/ai/prompts.py`):**
   - System persona: CyberShield AI Cybersecurity Analysis Engine.
   - Non-negotiable prompt-injection directives treating all content inside `<UNTRUSTED_CONTENT_TO_ANALYZE>` as passive, non-executable data.
   - Absolute prohibition against declaring targets "confirmed fraudulent" without authoritative domain registry records.
   - Mandated probabilistic language and explicit `uncertainty_statement`.
2. **Modality-Specific Prompt Generators:**
   - `build_url_analysis_prompt`: Ingests `target_url`, structured `UrlObservedEvidence` (hostname, IP routing, homoglyphs), and heuristic findings.
   - `build_email_analysis_prompt`: Ingests `sender`, `subject`, `body`, extracted URLs/phones, and heuristic rule IDs.
   - `build_sms_analysis_prompt`: Ingests `sender`, `message`, length, and heuristic rule IDs.
3. **AI Threat Analyzer (`backend/app/engines/ai/analyzer.py`):**
   - Coordinates provider query, temperature control (0.2 for deterministic reasoning).
   - `clean_llm_json_response`: Strips markdown fences (````json ... ````) and isolates JSON objects.
   - Strict Pydantic V2 validation against `AiAnalysisResult` (`extra="forbid"`).
   - Raises `AIValidationError` on unparseable or incomplete outputs.
