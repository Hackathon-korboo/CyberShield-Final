# PART 11: AI-BASED SCAM ANALYSIS & EXPLANATION — TASK SCOPE

**Part Identifier:** PART_11  
**Part Title:** AI-Based Scam Analysis & Explanation  
**Parent Phase:** PHASE 03 — AI Integration  
**Status:** NOT_STARTED (Awaiting Part 10 Approval)  
**Assigned Roles:** AI Prompt Engineer, Cybersecurity Analyst, Backend Developer  

---

## 1. Objectives
Implement prompt generation and reasoning pipelines for URL, Email, and SMS threats that yield structured, explainable findings while maintaining strict tripartite data separation.

## 2. In-Scope Tasks
1. URL Scam Analysis:
   - Explain suspicious hostname patterns and Punycode spoofing.
   - Explain path and query string lures.
   - Interpret detected indicators without making ungrounded accusations.
2. Email Phishing Analysis:
   - Explain urgency lures, authority manipulation, and financial pressure.
   - Analyze suspicious sender domains and embedded links.
   - Interpret credential harvesting attempts.
3. SMS Smishing Analysis:
   - Explain OTP / 2FA extraction lures.
   - Explain compound urgency and delivery/bank imposter tactics.
   - Distinguish benign operational notifications from smishing attacks.
4. Tripartite Output Compliance:
   - Ensure AI strictly references `observed_evidence` and `heuristic_findings`.
   - Ensure AI never fabricates facts or overrides deterministic scores.
