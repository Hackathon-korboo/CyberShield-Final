# PART 09: SECURITY RULES AND THREAT INDICATOR ENGINE — TASK SCOPE

## 1. Goal & Objective
Design and implement a deterministic, rule-based security indicator engine in `backend/app/engines/rules/` that evaluates URLs, emails, and SMS messages against curated threat catalogs, extracting concrete evidence snippets and mitigations.

## 2. In-Scope Tasks
1. Construct rule catalog and detection engine:
   - URL Rules (`RULE-URL-001` through `RULE-URL-006`): Direct IP hostnames, Punycode/homoglyph lookalikes, suspicious auth keywords, excessive subdomains, brand typo-squatting, suspicious TLDs.
   - Email Rules (`RULE-EML-001` through `RULE-EML-006`): Extreme urgency lures, sender impersonation mismatch, credential harvesting links, fake invoice/payment demands, fake job/internship offers.
   - SMS Rules (`RULE-SMS-001` through `RULE-SMS-005`): OTP/PIN extraction requests, card blockage panic lures, lottery/prize scams, suspicious shortened links.
2. Extract embedded indicators:
   - Extract URLs from email bodies and SMS text.
   - Extract phone numbers and monetary amounts.
3. Attach transparent metadata to each finding: Rule ID, severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), evidence string, explanation, mitigation advice.
4. Unit tests verifying each detection rule independently.

## 3. Out-of-Scope Tasks
- Applying blackbox ML or LLM classifications (reserved for Phase 03).
- Claiming definitive legal fraud classification without human review.

## 4. Acceptance Criteria
- Rules execute deterministically with linear-time complexity.
- Triggered rules report the exact evidence substring.
- Clean inputs return clean verdicts with zero false positives.
