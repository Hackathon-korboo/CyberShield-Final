# CYBERSHIELD AI 2.0 — PHASE 03 API INTEGRATION CONTRACT SPECIFICATION

**Document Version:** 1.0.0  
**Project:** CyberShield AI 2.0  
**Workspace:** `D:\Adamas offline Hackathon`  
**Current Date:** 2026-11-14T10:34:00+05:30  
**Phase Status:** **PLANNED (AWAITING HUMAN AUTHORIZATION)**  

---

## 1. Compatibility Invariant & Frozen Interface Preservation

The primary design requirement of Phase 03 is **100% backward compatibility** with Phase 02 clients.

Existing endpoints:
- `POST /api/v1/analyze/url`
- `POST /api/v1/analyze/email`
- `POST /api/v1/analyze/sms`

### Request Contracts (100% Unchanged):
All existing request schemas (`UrlAnalysisRequest`, `EmailAnalysisRequest`, `SmsAnalysisRequest`) remain strictly unchanged.

---

## 2. Response Extension Proposal: `AiAnalysisResult`

To provide AI explanations without breaking existing clients or violating frozen Phase 02 schemas, Phase 03 specifies the `AiAnalysisResult` data contract:

### 2.1 The `AiAnalysisResult` Schema

```json
{
  "summary": "High-urgency phishing message attempting bank credential harvesting.",
  "explanation": "The message utilizes coercive language alleging immediate account suspension to compel the recipient to click an unverified authentication link. This pattern matches standard financial credential harvesting lures.",
  "supporting_evidence": [
    "Presence of 'URGENT: Immediate Account Verification' in subject line",
    "Embedded link pointing to an IP address rather than official domain"
  ],
  "ai_inferences": [
    "Sender likely attempting unauthorized account takeover",
    "Domain registration appears deceptive relative to claimed corporate brand"
  ],
  "uncertainty_statement": "AI inference is probabilistic. Official verification via legitimate banking phone channels is strongly recommended.",
  "user_recommendations": [
    "Do not click links or input login credentials.",
    "Report message as phishing to IT / Security team.",
    "Verify account status directly through official bank mobile app."
  ],
  "provider": "google-gemini",
  "model": "gemini-1.5-flash",
  "status": "COMPLETED"
}
```

### 2.2 Extended Response Envelope Design

In Phase 02, the response model is:
```python
class UrlAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target: str
    target_type: str
    analysis_id: str
    timestamp: datetime
    observed_evidence: UrlObservedEvidence
    heuristic_findings: HeuristicFindings
    status: str
```

In Phase 03, we specify an extended response structure:
```python
class ExtendedUrlAnalysisResponse(UrlAnalysisResponse):
    ai_analysis: Optional[AiAnalysisResult] = Field(
        default=None,
        description="Contextual AI-generated explanation and intent inferences (None when disabled or unavailable)."
    )
```

### 2.3 Status Field Values for `ai_analysis.status`

| Status Value | Meaning | System Behavior |
|---|---|---|
| `COMPLETED` | Gemini successfully evaluated the input. | Full AI explanation, inferences, and recommendations populated. |
| `FALLBACK_HEURISTIC_ONLY` | Gemini API key unconfigured, timed out, or quota exceeded. | Deterministic findings preserved; explanation indicates fallback status. |
| `DISABLED` | `AI_ANALYSIS_ENABLED=false` in application configuration. | AI layer bypassed intentionally; deterministic findings returned. |
| `VALIDATION_FAILED` | Gemini returned malformed JSON or invalid schema. | AI result discarded safely; fallback notice generated. |
| `PROMPT_INJECTION_DETECTED` | Adversarial injection pattern detected in input text. | AI flags injection attempt; deterministic indicators preserved. |

---

## 3. Strict Layered Data Guarantees

```text
+---------------------------------------------------------------------------------+
|                                 ANALYSIS PAYLOAD                                |
+---------------------------------------------------------------------------------+
| 1. observed_evidence (Phase 02): Immutable empirical facts measured by backend |
| 2. heuristic_findings (Phase 02): Deterministic rules & severity floor score    |
| 3. ai_analysis (Phase 03): Explainable AI reasoning & layperson recommendations |
+---------------------------------------------------------------------------------+
```
