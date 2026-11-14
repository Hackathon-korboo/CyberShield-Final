# CYBERSHIELD AI 2.0 — PHASE 03 ARCHITECTURE OVERVIEW

**Document Version:** 1.0.0  
**Project:** CyberShield AI 2.0  
**Workspace:** `D:\Adamas offline Hackathon`  
**Current Date:** 2026-11-14T10:34:00+05:30  
**Phase Status:** **PLANNED (AWAITING HUMAN AUTHORIZATION)**  

---

## 1. High-Level Architectural Vision

Phase 03 establishes a **Hybrid Multi-Tier Threat Defense Architecture** where deterministic rule engines and large language models cooperate without compromising security or predictability.

```text
+---------------------------------------------------------------------------------------+
|                               FASTAPI INGRESS LAYER                                  |
|               POST /api/v1/analyze/url | /email | /sms (Pydantic V2 Validation)      |
+------------------------------------------+--------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                                CORE PIPELINE CONTROLLER                               |
|                  (Pre-sanitization, Defanging, Phone/URL Token Extraction)            |
+------------------------------------------+--------------------------------------------+
                                           |
                    +----------------------+----------------------+
                    |                                             |
                    v                                             v
+---------------------------------------+     +-----------------------------------------+
|     DETERMINISTIC DEFENSE LAYER       |     |          AI ORCHESTRATION LAYER         |
|  (Phase 01 & 02: 100% Frozen)         |     |  (Phase 03: Asynchronous & Decoupled)   |
|                                       |     |                                         |
| 1. SSRF Guard (Zero-Egress Firewall)  |     | 1. Safe Prompt Context Builder          |
| 2. Heuristic Rules Engine (12 Rules)  |     | 2. Untrusted Delimiter Encapsulation    |
| 3. Severity Floor Scoring Model       |     | 3. Google GenAI / Gemini Provider       |
| 4. Factual Observed Evidence Assembly |     | 4. Strict Pydantic JSON Output Schema   |
|                                       |     | 5. Circuit Breaker & Timeout Fallback   |
| OUTPUT:                               |     | OUTPUT:                                 |
| - observed_evidence (Immutable facts) |     | - ai_analysis (Contextual explanation,  |
| - heuristic_findings (Floor scores)   |     |   user advice, uncertainty note)        |
+-------------------+-------------------+     +--------------------+--------------------+
                    |                                              |
                    +----------------------+-----------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                             COMPOSITE RESPONSE SYNTHESIS                              |
|           Strict Invariant: AI NEVER modifies or lowers heuristic findings!           |
|                 StandardResponse[CompositeAnalysisResponse]                           |
+---------------------------------------------------------------------------------------+
```

---

## 2. Core Architectural Principles

### 2.1 Principle of Decoupled Truth (Tri-Partite Data Model)
Every analysis payload enforces a strict categorical separation:
1. `observed_evidence`: Concrete, empirically extracted data (e.g. normalized hostname, IP resolution, message length, embedded links).
2. `heuristic_findings`: Deterministic rule outputs, severity levels, and severity-floor risk scores.
3. `ai_analysis`: Qualitative semantic interpretations, scam intent explanations, social engineering analysis, and layperson recommendations.

### 2.2 Principle of Asymmetric Authority
- The deterministic engine possesses **absolute authority** over risk scoring and blocking.
- The AI engine possesses **zero authority** to reduce, alter, override, or suppress deterministic risk indicators.
- If the deterministic engine flags `HIGH_RISK` (score $\ge 70$), the final classification remains `HIGH_RISK`, regardless of whether the AI perceives the content as benign.

### 2.3 Principle of Zero-Egress AI Isolation
- The AI engine is provided only with sanitized, pre-extracted text strings and factual metadata.
- The AI engine is completely air-gapped from network tools: it cannot perform DNS lookups, curl URLs, follow redirects, or trigger remote webhooks.

### 2.4 Principle of Graceful Deterministic Fallback
- If the Gemini API key is missing, invalid, rate-limited (HTTP 429), or times out ($> 5.0$ seconds), the system does not crash or fail the request.
- The system automatically emits a valid response with `ai_analysis.status = "FALLBACK_HEURISTIC_ONLY"`, preserving 100% of deterministic threat analysis capabilities.

---

## 3. Modular Component Design

```text
backend/app/engines/ai/
  ├── __init__.py               # Package exports
  ├── base.py                   # BaseAIProvider abstract interface
  ├── client.py                 # GeminiProvider concrete implementation (Google GenAI)
  ├── prompts.py                # Hardened prompts with injection boundary delimiters
  ├── schemas.py                # AiAnalysisResult and sub-models (extra="forbid")
  └── fallback.py               # Deterministic fallback response generators
```

### 3.1 Provider Abstraction Layer (`BaseAIProvider`)
To ensure vendor neutrality and avoid vendor lock-in, all AI interactions pass through an abstract interface:
```python
class BaseAIProvider(ABC):
    @abstractmethod
    async def analyze_threat(
        self,
        target_type: str,
        untrusted_content: str,
        observed_evidence: dict,
        heuristic_findings: dict,
    ) -> AiAnalysisResult:
        pass
```
This guarantees that swapping or adding alternate local/cloud providers (e.g., local Ollama or Claude) requires zero changes to core business logic.
