# CYBERSHIELD AI 2.0 — PHASE 1: API RESPONSE TO FRONTEND MAPPING SPECIFICATION

**Project:** CyberShield AI 2.0  
**Phase:** Phase 1 — Frontend-First Audit, Verdict Display & Result Experience  
**Status:** FULLY RECONCILED  
**Report Date:** 2026-11-14  
**Authoritative Backend Schema:** `backend/app/schemas/threat_models.py` (`ScamAnalysisResponse`, `FileThreatAnalysisResponse`)  
**Authoritative Frontend Target:** `frontend/main.js`, `frontend/index.html`  

---

## 1. PRIMARY CONTRACT MAPPING: `POST /api/v1/analyze/text`

The table below defines how each field of the Pydantic `ScamAnalysisResponse` model maps directly into the CyberShield AI 2.0 user interface:

| Backend Field | Python Type | Frontend Element ID / Class | Formatting / Transform Applied | Fallback Behavior |
|---|---|---|---|---|
| `risk_level` | `RiskLevel` (Enum: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `SAFE`) | `#res-risk-level`, `#res-risk-level-badge` | Uppercase string; determines badge color class. | Defaults to `"UNKNOWN"`. |
| `risk_score` | `float` (0.0 to 100.0) | `#res-risk-score`, `#res-risk-score-badge` | Formatted to 1 decimal place (`score.toFixed(1)`). | Defaults to `0.0`. |
| *Derived Verdict* | *Derived* (String) | `#res-verdict-title` | Synthesizes plain-English verdict (e.g. `MALICIOUS WEBSITE DETECTED` or `CONFIRMED MALICIOUS THREAT`). | Defaults to `"ANALYSIS COMPLETE"`. |
| *Derived Subtitle* | *Derived* (String) | `#res-verdict-subtitle` | Human-readable explanation of why this verdict applies. | Defaults to category description. |
| *Derived Type* | *Derived* (String) | `#res-verdict-type-pill` | `"URL / WEB THREAT"`, `"COMMUNICATION THREAT"`, or `"FILE STATIC AUDIT"`. | Defaults to `"THREAT EVALUATION"`. |
| *Derived Action* | *Derived* (String) | `#res-primary-action-text` | Plain-English immediate recommendation (e.g. "Do NOT enter credentials..."). | Defaults to standard caution. |
| *Why Flagged List* | *Derived* (List) | `#res-why-flagged-list` | Dynamic `<li>` bullets extracted from `observed_evidence` or clean status. | Shows baseline security check summary. |
| `primary_category` | `ThreatCategory` (Enum) | `#res-primary-category` | Uppercase string with underscores replaced by spaces where needed. | Falls back to `classification` or `"GENERAL"`. |
| `engine_used` | `str` | `#res-engine-used` | Displays active engine (e.g., `hybrid-ensemble`, `gemini-3.1-flash-lite`, `heuristic-floor`). | Defaults to `"hybrid-ensemble"`. |
| `prompt_injection_detected` | `bool` | `#res-injection-alert` | If `true`, removes `hidden` attribute to show amber/red quarantine alert. | Stays hidden if `false`. |
| `observed_evidence` | `List[EvidenceItem]` | `#res-evidence-list`, `#evidence-count` | Maps each item to `.evidence-item` with badge, indicator name, confidence %, description, and code snippet. | If empty, renders clean check: "No Malicious Heuristic Signatures Detected". |
| `ai_assessment` | `str` | `#res-ai-assessment` | Rendered under Tab 2 below `[ AI-GENERATED EXPLANATION — CONTEXTUAL INTERPRETATION ONLY ]` banner. | Falls back to `explanation` or "No narrative provided." |
| `uncertainty_factors` | `List[str]` | `#res-uncertainty-list` | Rendered as `<li>` elements under Limitations & Uncertainty section. | If empty, displays "No significant uncertainty detected; evidence thresholds decisively crossed." |
| `iocs.urls` | `List[str]` | `#ioc-urls-list`, `#ioc-urls-count` | Dynamic `<li><code>url</code></li>`. | If empty, renders `<li>None detected</li>`. |
| `iocs.domains` | `List[str]` | `#ioc-domains-list`, `#ioc-domains-count` | Dynamic `<li><code>domain</code></li>`. | If empty, renders `<li>None detected</li>`. |
| `iocs.emails` | `List[str]` | `#ioc-emails-list`, `#ioc-emails-count` | Dynamic `<li><code>email</code></li>`. | If empty, renders `<li>None detected</li>`. |
| `iocs.phones` | `List[str]` | `#ioc-phones-list`, `#ioc-phones-count` | Dynamic `<li><code>phone</code></li>`. | Falls back to `iocs.phone_numbers` or "None detected". |
| `iocs.upi_handles` | `List[str]` | `#ioc-upi-list`, `#ioc-upi-count` | Dynamic `<li><code>upi_id</code></li>`. | Falls back to `iocs.upi_ids` or "None detected". |
| `mitigation_recommendations` | `List[MitigationStep]` | `#res-mitigation-list` | Maps to indexed cards with title, description, and `.priority-{low\|medium\|high}` chips. | Falls back to `recommended_actions` or "No immediate actions required." |
| `pii_redacted_content` | `Optional[str]` | `#res-pii-text` | Preformatted text display in Tab 5. | Falls back to `sanitized_content` or raw payload. |
| `pii_entities_found` | `List[PIIEntity]` | `#pii-entities-count` | Count displayed in badge (`"${count} Entities Redacted"`). | Falls back to `pii_redacted_count`. |
| *Full Response* | `dict` | `#res-raw-json` | `JSON.stringify(data, null, 2)` inside `<pre>` with 1-click clipboard copy. | Validates complete Member 1 schema contract. |

---

## 2. URL THREAT VERDICT DERIVATION MATRIX

When incoming content contains a URL or the user selects `source_type="url"`, `deriveVerdict()` applies the following deterministic mapping:

```
+----------------------------------------------------------------------------------------------------+
| EVALUATION CONDITIONS                           | VERDICT TITLE                | BADGE CLASS       |
+----------------------------------------------------------------------------------------------------+
| Prompt Injection detected in URL parameters     | MALICIOUS WEBSITE / INJECTION| verdict-malicious |
| Risk Score >= 75 OR Risk Level == CRITICAL      | MALICIOUS WEBSITE DETECTED   | verdict-malicious |
| Risk Score 50 - 74 OR Risk Level == HIGH        | LIKELY MALICIOUS WEBSITE     | verdict-likely-mal|
| Risk Score 25 - 49 OR Risk Level == MEDIUM      | SUSPICIOUS WEBSITE           | verdict-suspicious|
| Risk Score 6 - 24 OR Risk Level == LOW          | LIKELY SAFE WEBSITE          | verdict-likely-saf|
| Risk Score <= 5 AND Risk Level == SAFE          | VERIFIED SAFE WEBSITE        | verdict-safe      |
| Ambiguous heuristics / conflicting signals      | INCONCLUSIVE — MORE VERIF... | verdict-inconclus |
| Network timeout / Server connection failure     | ANALYSIS SERVICE UNAVAILABLE | verdict-unavail   |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. SECONDARY CONTRACT MAPPING: `POST /api/v1/analyze/file`

The static file analysis response (`FileThreatAnalysisResponse`) maps seamlessly into the same unified verdict container:

| Backend Field | Target UI Element | Visual Representation |
|---|---|---|
| `filename` | `#res-verdict-subtitle`, Tab 5 | `[File: ${filename}] (${size_kb} KB)` |
| `is_executable` | Evidence List, `#res-why-flagged-list` | Flagged as high-risk disguised executable if extension mismatched. |
| `archive_report.is_zip_bomb` | Evidence List, Why Flagged | High compression ratio flagged as Decompression Bomb Vector. |
| `archive_report.has_traversal_attack` | Evidence List, Why Flagged | Path traversal sequence `../` flagged as directory escape attack. |
| `sha256` / `md5` | IOC Tab / Raw JSON | Cryptographic digest cataloged. |
| `risk_level` & `risk_score` | `#res-risk-level`, `#res-risk-score` | Scaled 0–100 risk rating. |
| `disclaimer` | Tab 2 (Assessment) | Explains non-execution safe static analysis boundaries. |

---

## 4. ERROR CODE & TIMEOUT MAPPINGS

| Scenario | HTTP / Exception Code | UI State Triggered | User Action Available |
|---|---|---|---|
| Timeout (> 15 seconds) | `DOMException: AbortError` | `#lab-error-state` (Title: "Analysis Execution Timed Out (15s Bounded Limit)") | Suggests toggling off upstream APIs for local heuristics; 1-click retry. |
| User Cancellation | `DOMException: AbortError` | `#lab-error-state` (Title: "Analysis Cancelled by User") | 1-click input reset or sample selection. |
| Validation Error | HTTP 422 Unprocessable | `#lab-error-state` (Title: "Invalid Request Payload", details from `detail`) | Edit content and resubmit. |
| Backend Offline / Down | Network Error (Failed to fetch) | `#lab-error-state` (Title: "Backend Connection Error") | `RETRY HEALTH CHECK` and `RESET INPUT` buttons. |
| Server Internal Error | HTTP 500 Internal Error | `#lab-error-state` (Title: "Analysis Execution Failed", details from server) | Displays detailed error trace message; allows clean retry. |

---

## 5. CONTRACT COMPLIANCE SUMMARY

- All backend fields from Member 1, Member 2, and Member 3 are mapped and displayed without schema drift.
- Backward compatibility with legacy tests (`res-risk-level`, `res-risk-score`, `res-primary-category`, `res-engine-used`) is 100% preserved.
- The UI eliminates all ambiguity: URLs, SMS coercion, UPI fraud, and benign chats each receive unambiguous, human-readable verdicts.
