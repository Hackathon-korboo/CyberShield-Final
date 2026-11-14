# PHASE 03 ARCHITECTURE: 04 — FAILURE FALLBACK & RESILIENCE SPECIFICATION

**Document Version:** 1.0.0  
**Project:** CyberShield AI 2.0  
**Phase:** 03 — AI Integration  
**Status:** Approved for Planning  

---

## 1. Resilience Philosophy

CyberShield AI 2.0 is fundamentally a **security product**, not a conversational chatbot. Availability of threat analysis is paramount:
- A user submitting a phishing link must receive an immediate, accurate risk score and threat indicators even if the external LLM is completely down, unconfigured, or degraded.
- AI failure must **never** degrade the deterministic security posture.

---

## 2. Failure Modes & Fallback Matrix

| Failure Trigger | Detection Mechanism | Fallback Action | Emitted AI Status | Impact on Heuristic Score |
|---|---|---|---|:---:|
| **Missing API Key** | `settings.gemini_api_key is None` | Bypass remote call; invoke local template generator. | `FALLBACK_HEURISTIC_ONLY` | None (100% Intact) |
| **API Timeout** | `asyncio.wait_for(..., timeout=5.0)` raises `TimeoutError` | Cancel pending request; return synthesized explanation. | `FALLBACK_HEURISTIC_ONLY` | None (100% Intact) |
| **Rate Limit / Quota** | Gemini raises HTTP 429 / `ResourceExhausted` | Open circuit breaker for 60 seconds; serve local fallback. | `FALLBACK_HEURISTIC_ONLY` | None (100% Intact) |
| **Network Loss / DNS** | Socket or connection error | Log sanitized network warning; serve local fallback. | `FALLBACK_HEURISTIC_ONLY` | None (100% Intact) |
| **Malformed Output** | Pydantic `ValidationError` on response | Log schema warning; serve sanitized fallback. | `VALIDATION_FAILED` | None (100% Intact) |
| **Adversarial Injection** | Regex detector flags system prompt tampering in response | Flag injection indicator; serve sanitized fallback. | `PROMPT_INJECTION_DETECTED` | None (100% Intact) |

---

## 3. Circuit Breaker Specification

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_time: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
```
When `state == "OPEN"`, calls to Gemini are skipped entirely, saving compute and network overhead, and immediately resolving with deterministic fallback.
