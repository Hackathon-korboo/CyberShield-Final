# PHASE 03 ARCHITECTURE: 02 — DATA FLOW & PROMPT ISOLATION SPECIFICATION

**Document Version:** 1.0.0  
**Project:** CyberShield AI 2.0  
**Phase:** 03 — AI Integration  
**Status:** Approved for Planning  

---

## 1. End-to-End Analysis Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as FastAPI Router (/analyze/url)
    participant SecSvc as ThreatAnalysisService
    participant SSRF as SSRFGuard (Zero Egress)
    participant Rules as SecurityRuleEngine
    participant AIOrch as AIOrchestrator
    participant Gemini as Google Gemini 1.5/2.0 API

    Client->>API: POST /api/v1/analyze/url {url}
    API->>SecSvc: analyze_url(request)
    SecSvc->>SSRF: validate_url(url)
    SSRF-->>SecSvc: ssrf_safe: true, resolved_ips
    SecSvc->>Rules: evaluate_url(observed_evidence)
    Rules-->>SecSvc: heuristic_findings (score: 65, HIGH_RISK)

    alt AI Enabled & Key Configured
        SecSvc->>AIOrch: enrich_analysis(target, evidence, findings)
        AIOrch->>AIOrch: Wrap untrusted content with <UNTRUSTED_CONTENT>
        AIOrch->>Gemini: Async generate_content(prompt) [5.0s timeout]
        alt Gemini Responds within 5.0s
            Gemini-->>AIOrch: Raw JSON Response
            AIOrch->>AIOrch: Pydantic Validation (extra='forbid')
            AIOrch-->>SecSvc: AiAnalysisResult(status='COMPLETED')
        else Timeout (>5.0s) or Quota (429)
            AIOrch-->>SecSvc: AiAnalysisResult(status='FALLBACK_HEURISTIC_ONLY')
        end
    else AI Disabled or Missing Key
        SecSvc->>AIOrch: fallback_enrichment()
        AIOrch-->>SecSvc: AiAnalysisResult(status='FALLBACK_HEURISTIC_ONLY')
    end

    SecSvc->>SecSvc: Enforce Deterministic Floor Score (AI cannot alter score)
    SecSvc-->>API: StandardResponse[ExtendedUrlAnalysisResponse]
    API-->>Client: 200 OK
```
