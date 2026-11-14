# CYBERSHIELD AI 2.0 — PHASE 03 RISK REGISTER

**Document Version:** 1.0.0  
**Project:** CyberShield AI 2.0  
**Workspace:** `D:\Adamas offline Hackathon`  
**Current Date:** 2026-11-14T10:34:00+05:30  
**Phase Status:** **PLANNED (AWAITING HUMAN AUTHORIZATION)**  

---

## 1. Risk Assessment Matrix

| Risk ID | Risk Category | Risk Description | Severity | Likelihood | Mitigation Strategy | Owner |
|---|---|---|:---:|:---:|---|:---:|
| **RISK-01** | Security | Prompt injection allows adversary to alter AI threat assessment. | **HIGH** | Medium | Strict boundary tagging (`<UNTRUSTED_CONTENT>`), system prompt hardening, and zero authority for AI to modify deterministic scores. | Security Architect |
| **RISK-02** | Reliability | Gemini API latency spikes cause API request timeouts. | **HIGH** | Medium | Enforce 5.0s asynchronous timeout in client; graceful fallback to pure deterministic findings. | Lead Backend Dev |
| **RISK-03** | Operational | Gemini API key missing or unconfigured in production/local environment. | **MEDIUM** | High | System defaults to `FALLBACK_HEURISTIC_ONLY`; never crashes on missing key; clear placeholder documentation. | DevOps / Architect |
| **RISK-04** | Financial / Quota | High request volume exhausts free-tier Gemini API quota (HTTP 429). | **MEDIUM** | Medium | Circuit breaker design: trip for 60s upon first 429 response, immediately falling back to heuristic engine without re-querying. | Lead Backend Dev |
| **RISK-05** | Integrity | Upstream Phase 01 / Phase 02 frozen interfaces inadvertently modified. | **CRITICAL** | Low | Strict freeze boundary enforcement; zero edits to frozen files; new AI capabilities housed in dedicated `backend/app/engines/ai/` package. | Project Owner |
| **RISK-06** | Legal / Defamation | AI claims a legitimate corporate entity is "fraudulent" or "criminal". | **HIGH** | Low | Strictly prohibit defamatory assertions in system prompt; mandate explicit uncertainty statements in every AI payload. | Legal / Architect |
| **RISK-07** | Quality Assurance | Non-deterministic LLM outputs cause flaky or unpredictable test assertions. | **MEDIUM** | High | Use deterministic mocked responses for 100% of standard unit tests; isolate live tests into separate opt-in test module. | QA Lead |
