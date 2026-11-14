# CYBERSHIELD AI 2.0 — RISK SCORING ROOT CAUSE AUDIT & TRACE REPORT

**Project:** CyberShield AI 2.0  
**Phase:** Phase 1 — Root Cause Audit  
**Status:** AUDIT_COMPLETE_AWAITING_APPROVAL  
**Date:** 2026-11-14  
**Primary Engine:** Antigravity Autonomous Integration Engine  
**Workspace:** `D:\Adamas offline Hackathon`  
**Snapshots & Backups:** `Brain/BACKUPS/BACKUP_RISK_AUDIT_20261114/`  

---

## 1. EXECUTIVE SUMMARY & OBSERVED DEFECT

The owner observed that distinct scam messages evaluated through the SMS analysis interface receive identical maximum risk scores and inappropriate threat categories:

### Test Case A — KYC Phishing
- **Input Message:**  
  `"Your KYC verification has expired. Your banking services will be suspended today. Update your KYC immediately using the link provided in this message."`
- **Observed Result:**  
  - Detected Category: `PHISHING_EMAIL` *(Defect: Input source was SMS, but classified as email phishing)*
  - Risk Level: `CRITICAL`
  - Risk Score: **`98.5 / 100`**

### Test Case B — Fake Job Offer
- **Input Message:**  
  `"Congratulations! You have been selected for a work-from-home job with a salary of Rs. 45,000 per month. Pay Rs. 1,500 registration fees to confirm your position immediately."`
- **Observed Result:**  
  - Detected Category: `FAKE_JOB_OFFER`
  - Risk Level: `CRITICAL`
  - Risk Score: **`98.5 / 100`**

### The Core Defect
Different scam categories, disparate indicators, and entirely different communication structures produced the **exact same 98.5 score**. The system failed to provide evidence-calibrated risk differentiation, and misclassified an SMS as an email threat.

---

## 2. CODE-LEVEL EXECUTION TRACE: THE EXACT SOURCE OF `98.5`

Tracing the complete execution flow from input to output:

```
[User Input in Frontend Console]
       │
       ▼
POST /api/v1/analyze/text (payload: { content: "...", source_type: "sms", enable_gemini: true })
       │
       ▼
backend/app/api/routes/member2_routes.py :: analyze_scam_text()
       │
       ▼
backend/app/services/scam_threat_service.py :: ThreatIntelligenceService.analyze()
       │
       ├─ Layer 1: Input Validation
       ├─ Layer 2: Deterministic IOC Extraction
       ├─ Layer 3: VirusTotal Enrichment (no domain in payload -> skipped)
       └─ Layer 4: AI Threat Analysis
               │
               ▼
backend/app/gemini/gemini_client.py :: GeminiClient.analyze_threat()
       │
       ▼
Google Gemini API Request (gemini-3.1-flash-lite)
Prompt asks: "risk_score": float (0.0 to 100.0) with NO scoring rubric or formula.
Gemini generates JSON output:
  {
    "risk_level": "CRITICAL",
    "risk_score": 98.5,
    "primary_category": "PHISHING_EMAIL" (or "FAKE_JOB_OFFER"),
    "confidence_score": 0.99,
    ...
  }
       │
       ▼
backend/app/gemini/gemini_client.py (Line 194):
  "risk_score": float(parsed.get("risk_score", 10.0))  ==> Returns 98.5
       │
       ▼
backend/app/services/scam_threat_service.py (Line 126):
  final_score = analysis_dict.get("risk_score", 5.0)   ==> Passes 98.5 unmodified!
       │
       ▼
backend/app/schemas/threat_models.py :: ScamAnalysisResponse(risk_score=98.5, ...)
       │
       ▼
frontend/main.js (Line 1057):
  riskScoreEl.textContent = v.score.toFixed(1)         ==> Faithfully renders "98.5"
```

### Exact Code References:

1. **`backend/app/gemini/gemini_client.py` Lines 105–109:**
   ```python
   "Respond ONLY with a JSON object adhering to this exact schema:\n"
   "{\n"
   '  "risk_level": "BENIGN" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",\n'
   '  "risk_score": float (0.0 to 100.0),\n'
   '  "primary_category": "CATEGORY_NAME",\n'
   ...
   ```
   *Analysis:* The system prompt directs Gemini to output a float from `0.0 to 100.0` but gives **zero guidance, zero scoring rubric, zero mathematical formula, and zero evidence weighting**.
   LLMs, when prompted without calibration rubrics on urgent fraud lures, habitually emit stereotypical clichéd scores: **`98.5`** or **`99.5`**.

2. **`backend/app/gemini/gemini_client.py` Line 194:**
   ```python
   return {
       "risk_level": RiskLevel(parsed.get("risk_level", "LOW")),
       "risk_score": float(parsed.get("risk_score", 10.0)),
       "primary_category": ThreatCategory(parsed.get("primary_category", "BENIGN")),
       ...
   ```
   *Analysis:* The client naively adopts whatever uncalibrated float the LLM returned.

3. **`backend/app/services/scam_threat_service.py` Lines 126–127:**
   ```python
   final_score = analysis_dict.get("risk_score", 5.0)
   final_level = analysis_dict.get("risk_level", RiskLevel.BENIGN)
   ```
   *Analysis:* `scam_threat_service.py` performs **no deterministic score calculation, no evidence normalization, and no calibration**. It passes the uncalibrated LLM hallucinated score straight through to the response.

---

## 3. CHECKLIST AUDIT OF THE 8 SUSPECTED CAUSES

| # | Suspected Cause | Finding | Evidence & Details |
|---|---|---|---|
| **1** | **Is AI confidence being copied into risk_score?** | **NO** | Evidence: In Test A, `confidence_score` was `0.99`, while `risk_score` was `98.5`. In Test B, `confidence_score` was `1.0`, while `risk_score` was `98.5`. They are separate fields in the JSON, but both are uncalibrated AI outputs. |
| **2** | **Is a fixed fallback score being assigned?** | **NO (in live run)** | Evidence: The engine used in live runs was `gemini (gemini-3.1-flash-lite)`, not the fallback. However, if fallback *did* trigger, it failed completely (see Section 5 below). |
| **3** | **Does every scam category have the same hardcoded score?** | **PARTIALLY (in heuristic fallback)** | Evidence: In `backend/app/ai_engine/heuristics_engine.py` (lines 116-117), any threat matching `high_critical_cats` is hard-floored at `92.0`. In Gemini, the LLM hallucinates `98.5` across different categories due to lack of a scoring rubric. |
| **4** | **Is a maximum score always being returned?** | **NO** | Evidence: Benign messages return `5.0`. OTP theft returned `99.5`. The score is not universally clamped to 98.5; rather, Gemini arbitrarily picked 98.5 for both Test A and Test B. |
| **5** | **Are multiple related indicators being counted repeatedly?** | **YES (in heuristics)** | Evidence: In `backend/app/ai_engine/heuristics_engine.py` (line 105), `breadth_bonus = (len(evidence_list) - 1) * 10.0` arbitrarily adds +10 points for each indicator without correlation deduplication. |
| **6** | **Is risk score being overwritten during report generation?** | **NO** | Evidence: `scam_threat_service.py` sets `final_score = analysis_dict.get("risk_score", 5.0)` and only elevates it if VirusTotal confirms malicious (`max(final_score, 95.0)`) or prompt injection is detected (`max(final_score, 85.0)`). Neither condition triggered in Test A or B. |
| **7** | **Is frontend displaying the wrong response field?** | **NO** | Evidence: `frontend/main.js` correctly reads `data.risk_score` and formats it as `v.score.toFixed(1)`. The backend genuinely sent `98.5`. |
| **8** | **Is CRITICAL risk classification automatically forcing 98.5?** | **NO** | Evidence: `98.5` originated inside Gemini's raw JSON text response candidate. The backend merely parsed it. |

---

## 4. ROOT CAUSE OF CATEGORY MISCLASSIFICATION: WHY KYC SMS BECAME `PHISHING_EMAIL`

In `backend/app/gemini/gemini_client.py` (Lines 93–95) and `backend/app/schemas/threat_models.py` (Lines 12–27), the allowed categories are defined as:
```python
Allowed Threat Categories: [
    PHISHING_EMAIL, SCAM_SMS, FAKE_JOB_OFFER, FAKE_INTERNSHIP, 
    OTP_THEFT, CREDENTIAL_HARVESTING, BANKING_FRAUD, UPI_PAYMENT_FRAUD, 
    IMPERSONATION, SOCIAL_ENGINEERING, SUSPICIOUS_ATTACHMENT, 
    PROMPT_INJECTION_ATTEMPT, BENIGN
]
```

### Why KYC Phishing became `PHISHING_EMAIL`:
1. **Missing Schema Categories:** The taxonomy contains no `KYC_PHISHING`, `ADVANCE_FEE_FRAUD`, `LOTTERY_SCAM`, `INVESTMENT_SCAM`, `DELIVERY_SCAM`, or `ELECTRICITY_BILL_SCAM`.
2. **First-Choice Phishing Bias:** In the allowed category enum, `PHISHING_EMAIL` is the very first entry and the only one containing the word `PHISHING`.
3. **No Channel-Aware Category Enforcement:** The Gemini prompt tells the model `Context: Source format is 'sms'`, but fails to instruct the model that SMS phishing must be classified under an SMS/Communication category (or `KYC_PHISHING`), rather than `PHISHING_EMAIL`. Consequently, Gemini saw "phishing link" and selected `PHISHING_EMAIL`.

---

## 5. AUDIT OF THE HEURISTIC FALLBACK ENGINE: BRITTLE REGEX DEFECTS

When Gemini times out or is disabled (`enable_gemini: false`), `scam_threat_service.py` falls back to `backend/app/ai_engine/heuristics_engine.py`.

Our live audit revealed that **the heuristic fallback engine failed completely on both user test messages**:

```
[KYC Phishing Message]
  -> Heuristic Fallback Evidence Count: 0
  -> Fallback Risk Score: 5.0 (BENIGN / NO THREAT)

[Fake Job Offer Message]
  -> Heuristic Fallback Evidence Count: 0
  -> Fallback Risk Score: 5.0 (BENIGN / NO THREAT)

[Lottery Scam Message]
  -> Heuristic Fallback Evidence Count: 0
  -> Fallback Risk Score: 5.0 (BENIGN / NO THREAT)
```

### Root Cause in Regexes:
1. **`backend/app/ai_engine/sms_scam_detector.py` Line 24:**
   ```python
   (re.compile(r'(?i)\byour\s+(?:sim|pancard|aadhaar|bank\s*a/c|kyc)\s+(?:has\s+expired|will\s+be\s+blocked|suspended)\b'),
   ```
   *Defect:* Only matches if `"kyc"` is immediately followed by `"has expired"`. In Test A, the message was:  
   `"Your KYC verification has expired."`  
   Because of the word `"verification"`, the pattern failed completely.

2. **`backend/app/ai_engine/job_internship_detector.py` Line 20:**
   ```python
   (re.compile(r'(?i)\b(?:pay|deposit|transfer)\s+(?:a\s+)?(?:refundable\s+)?(?:security\s+deposit|registration\s+fee|training\s+fee|kit\s+charge)\b'),
   ```
   *Defect:* Only matches if `"pay"` is immediately followed by `"registration fee"`. In Test B, the message was:  
   `"Pay Rs. 1,500 registration fees..."`  
   Because the fee amount (`"Rs. 1,500"`) was between `"pay"` and `"registration fees"`, the pattern failed completely.

3. **`backend/app/ai_engine/sms_scam_detector.py` Line 26:**
   ```python
   (re.compile(r'(?i)\bcongratulations!?\s+you\s+(?:have\s+)?won\s+(?:a\s+lottery|cash\s+prize|iphone|\$|\u20b9)\b'),
   ```
   *Defect:* Requires the message to start with `"Congratulations!"`. When a lottery scam starts with `"You have won 25,00,000 Rupees..."`, the pattern fails.

---

## 6. ARCHITECTURAL DISCONNECT: WHY MEMBER 1'S RISK ENGINE WAS BYPASSED

The project contains two distinct architectures:

1. **Member 1's Calibrated Deterministic Risk Engine (`backend/app/services/risk/`):**
   - Built in Parts 13, 14, 15, and 16.
   - Contains `evidence_normalizer.py`, `severity_classifier.py`, `deterministic_engine.py`, and `UnifiedRiskPipeline`.
   - Uses calibrated `SEVERITY_WEIGHTS` (Critical: 40, High: 25, Medium: 15, Low: 5), `SEVERITY_FLOORS` (Critical: 70, High: 40, Medium: 15), correlation de-duplication (`CORRELATION_MAP`), and strictly gates AI so that AI alone cannot fabricate critical risk scores.
2. **Member 2's Scam Analysis Service (`backend/app/services/scam_threat_service.py`):**
   - Serviced `/api/v1/analyze/text` (which the frontend SMS and Text tabs call).
   - **Never invoked Member 1's `DeterministicRiskEngine`!**
   - Directly accepted the raw float from Gemini (`parsed.get("risk_score")`) as the final score.

---

## 7. PROPOSED TECHNICAL REMEDIATION PLAN

To eliminate the 98.5 anomaly and produce explainable, differentiated, evidence-based risk scores:

### Phase 2: Calibrated Evidence-Based Scoring Architecture
1. **Disconnect AI output from final risk score:** AI must provide contextual intelligence (threat intent, extracted indicators, tactics, detected sensitive requests, AI confidence), **NOT** the final numerical risk score.
2. **Unify with Deterministic Scoring Engine:** Route evidence extracted by AI and deterministic heuristics through the existing calibrated scoring framework:
   - Base indicator severity weights (Critical: 35–45, High: 20–25, Medium: 10–15, Low: 5).
   - Independent corroboration and correlation de-duplication (prevent double-counting).
   - Calibrated severity floors (Critical floor: 70, High floor: 45, Medium floor: 20).
   - Hard upper bound: Reserve 95–100 exclusively for confirmed external threat intelligence (e.g. VirusTotal positive domain) or verified direct credential/OTP harvesting with zero-trust validation.
   - Phishing without confirmed domain reputation or credential extraction scores in the 65–85 band based on specific tactics.
   - Advance fee / Fake job scams score in the 60–80 band based on presence of upfront fees, unrealistic salary, and unverified contacts.
   - Normal/benign messages score in the 0–10 band.

### Phase 3: Taxonomy & Category Differentiation
1. Expand `ThreatCategory` in `backend/app/schemas/threat_models.py` to natively support:
   - `KYC_PHISHING`
   - `ADVANCE_FEE_FRAUD`
   - `LOTTERY_SCAM`
   - `INVESTMENT_SCAM`
   - `DELIVERY_SCAM`
   - `ELECTRICITY_BILL_SCAM`
2. Update the Gemini system instruction and schema with comprehensive category definitions and channel-aware constraints (e.g., an SMS message must not be categorized as `PHISHING_EMAIL`).
3. Harden regex detectors in `sms_scam_detector.py`, `job_internship_detector.py`, and `phishing_detector.py` to be resilient to flexible word order and amounts.

### Phase 4: Structured AI Calibration
1. Update Gemini prompt in `gemini_client.py` to demand structured evidentiary signals rather than a raw risk score:
   - `threat_intent`
   - `social_engineering_tactics`
   - `demanded_actions` (e.g., `PAYMENT_FEE`, `CREDENTIAL_DISCLOSURE`, `OTP_DISCLOSURE`, `CLICK_LINK`)
   - `indicators` (with specific indicator severity and evidence text)
   - `model_confidence` (0.0 to 1.0)
2. Retain `confidence_score` as purely representing model certainty, completely separate from `risk_score`.

### Phase 5: Frontend Risk Score Explanation
1. Update the frontend result panel to show:
   - **Verdict & Category:** Correct channel-appropriate category (e.g. `KYC_PHISHING`).
   - **Risk Score:** Calibrated evidence score (e.g., KYC Phishing: ~78.0, Fake Job Offer: ~70.0, OTP Theft: ~92.0).
   - **Why This Score:** Clear breakdown of contributing indicators (e.g., Urgency lure + Banking impersonation + Suspicious link lure).
   - **AI Confidence:** Distinctly displayed (e.g., "AI Confidence: 99%").

### Phase 6: Regression Test Suite
1. Build test fixtures in `backend/tests/fixtures/risk_scoring/` covering all 15 scenarios specified in Section 8.
2. Verify score differentiation, monotonicity, duplicate resistance, and false positive controls.
3. Run complete test suite (`pytest backend/tests -v`).

---

## 8. GATE STOP & APPROVAL REQUEST

In strict accordance with Section 11 of the instructions:
> *"Start with PHASE 1 — ROOT CAUSE AUDIT.*  
> *After Phase 1:*  
> *- Show the exact source of the 98.5 score.*  
> *- Show the relevant code paths.*  
> *- Show the evidence of score assignment.*  
> *- Identify the responsible modules.*  
> *- Propose the correction.*  
> *Then STOP and wait for approval.*  
> *Do not change the entire risk architecture before the owner reviews the root cause.*  
> *After approval, continue through Phases 2–6."*

Phase 1 Root Cause Audit is complete and documented. No production code has been altered yet. All files are backed up in `Brain/BACKUPS/BACKUP_RISK_AUDIT_20261114/`.

**Awaiting your explicit approval to proceed to Phase 2 (Rebuild the Risk Scoring Logic) and subsequent phases.**
