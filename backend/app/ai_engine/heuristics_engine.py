"""
CyberShield AI 2.0 - Master Heuristics & Deterministic Evidence Engine
Aggregates specialized detection modules, computes calibrated composite risk scores,
evaluates empirical evidence, applies correlation deduplication, and generates mitigation advice.
Functions as the core fallback engine when Gemini API is offline or unconfigured, and provides
authoritative deterministic scoring logic.
"""

from typing import List, Dict, Any, Tuple
from backend.app.schemas.threat_models import (
    ThreatCategory,
    RiskLevel,
    UrgencyLevel,
    EvidenceItem,
    MitigationStep,
)
from backend.app.ai_engine.phishing_detector import PhishingDetector
from backend.app.ai_engine.sms_scam_detector import SMSScamDetector
from backend.app.ai_engine.job_internship_detector import JobInternshipDetector
from backend.app.ai_engine.payment_fraud_detector import PaymentFraudDetector
from backend.app.ai_engine.otp_credential_detector import OTPCredentialDetector
from backend.app.ai_engine.impersonation_detector import ImpersonationDetector

# Documented correlation groups, weights, and severity floors
CORRELATION_CONFIG: Dict[str, Dict[str, Any]] = {
    # CRITICAL (Weight: 40-45, Floor: 75)
    "CORR-OTP-THEFT": {"weight": 45.0, "floor": 75.0, "severity": "CRITICAL"},
    "CORR-REMOTE-ACCESS": {"weight": 40.0, "floor": 70.0, "severity": "CRITICAL"},
    "CORR-VT-MALICIOUS": {"weight": 45.0, "floor": 95.0, "severity": "CRITICAL"},

    # HIGH (Weight: 25-30, Floor: 50)
    "CORR-CREDENTIAL-HARVEST": {"weight": 30.0, "floor": 55.0, "severity": "HIGH"},
    "CORR-ADVANCE-FEE": {"weight": 25.0, "floor": 50.0, "severity": "HIGH"},
    "CORR-PAYMENT-FRAUD": {"weight": 25.0, "floor": 50.0, "severity": "HIGH"},
    "CORR-JOB-SCAM": {"weight": 25.0, "floor": 45.0, "severity": "HIGH"},
    "CORR-PROMPT-INJECTION": {"weight": 35.0, "floor": 65.0, "severity": "HIGH"},
    "CORR-MALICIOUS-PAYLOAD": {"weight": 30.0, "floor": 55.0, "severity": "HIGH"},

    # MEDIUM (Weight: 15-20, Floor: 25)
    "CORR-UNSOLICITED-OFFER": {"weight": 20.0, "floor": 35.0, "severity": "MEDIUM"},
    "CORR-IMPERSONATION": {"weight": 20.0, "floor": 30.0, "severity": "MEDIUM"},
    "CORR-URGENCY": {"weight": 15.0, "floor": 20.0, "severity": "MEDIUM"},
    "CORR-SUSPICIOUS-LINK": {"weight": 15.0, "floor": 25.0, "severity": "MEDIUM"},

    # DEFAULT
    "CORR-GENERAL-THREAT": {"weight": 15.0, "floor": 20.0, "severity": "MEDIUM"},
}


def infer_correlation_group(indicator: str, category: ThreatCategory) -> str:
    """Infer correlation group to prevent double-counting across overlapping indicators."""
    ind_lower = indicator.lower()

    if any(k in ind_lower for k in ("otp", "verification code", "one-time password", "2fa")):
        return "CORR-OTP-THEFT"
    if any(k in ind_lower for k in ("anydesk", "teamviewer", "remote desktop", "quicksupport")):
        return "CORR-REMOTE-ACCESS"
    if "virustotal malicious" in ind_lower:
        return "CORR-VT-MALICIOUS"
    if any(k in ind_lower for k in ("credential", "password", "pin", "cvv", "kyc")):
        return "CORR-CREDENTIAL-HARVEST"
    if any(k in ind_lower for k in ("registration fee", "processing fee", "security deposit", "advance fee", "upfront")):
        return "CORR-ADVANCE-FEE"
    if any(k in ind_lower for k in ("work-from-home", "work from home", "task", "job", "internship", "recruitment")):
        return "CORR-JOB-SCAM"
    if any(k in ind_lower for k in ("lottery", "lucky draw", "prize", "won", "earnings guarantee")):
        return "CORR-UNSOLICITED-OFFER"
    if any(k in ind_lower for k in ("electricity", "officer", "police", "cbi", "bank", "impersonat", "support executive")):
        return "CORR-IMPERSONATION"
    if any(k in ind_lower for k in ("upi", "qr code", "refund", "wire transfer")):
        return "CORR-PAYMENT-FRAUD"
    if any(k in ind_lower for k in ("urgency", "urgent", "immediate", "suspended", "arrest", "deadline", "today")):
        return "CORR-URGENCY"
    if any(k in ind_lower for k in ("shortened", "url", "link", "domain", "typosquatting")):
        return "CORR-SUSPICIOUS-LINK"
    if any(k in ind_lower for k in ("prompt injection", "override", "jailbreak")):
        return "CORR-PROMPT-INJECTION"

    # Category fallbacks
    cat_mapping = {
        ThreatCategory.OTP_THEFT: "CORR-OTP-THEFT",
        ThreatCategory.CREDENTIAL_HARVESTING: "CORR-CREDENTIAL-HARVEST",
        ThreatCategory.KYC_PHISHING: "CORR-CREDENTIAL-HARVEST",
        ThreatCategory.ADVANCE_FEE_FRAUD: "CORR-ADVANCE-FEE",
        ThreatCategory.LOTTERY_SCAM: "CORR-UNSOLICITED-OFFER",
        ThreatCategory.FAKE_JOB_OFFER: "CORR-JOB-SCAM",
        ThreatCategory.FAKE_INTERNSHIP: "CORR-JOB-SCAM",
        ThreatCategory.IMPERSONATION: "CORR-IMPERSONATION",
        ThreatCategory.ELECTRICITY_BILL_SCAM: "CORR-IMPERSONATION",
        ThreatCategory.UPI_PAYMENT_FRAUD: "CORR-PAYMENT-FRAUD",
        ThreatCategory.PROMPT_INJECTION_ATTEMPT: "CORR-PROMPT-INJECTION",
    }
    return cat_mapping.get(category, "CORR-GENERAL-THREAT")


def calculate_calibrated_scam_score(
    evidence_list: List[EvidenceItem],
    has_authoritative_match: bool = False,
    prompt_injection_flag: bool = False,
    source_type: str = "unknown"
) -> Tuple[float, RiskLevel, ThreatCategory, List[ThreatCategory], Dict[str, float]]:
    """
    Evidence-based deterministic scoring model with correlation deduplication.
    Prevents artificial inflation and ensures explainable risk differentiation.
    """
    if not evidence_list:
        return 5.0, RiskLevel.BENIGN, ThreatCategory.BENIGN, [ThreatCategory.BENIGN], {}

    # Filter out benign/clean evidence items that do not represent active threats
    threat_evidence = [
        ev for ev in evidence_list
        if ev.category not in (ThreatCategory.BENIGN, ThreatCategory.BENIGN_MESSAGE)
        and not any(k in ev.indicator.lower() for k in ("benign", "clean", "routine communication", "safe", "appointment confirmation"))
    ]
    if not threat_evidence:
        return 5.0, RiskLevel.BENIGN, ThreatCategory.BENIGN, [ThreatCategory.BENIGN], {}

    grouped_scores: Dict[str, float] = {}
    highest_floor: float = 0.0
    category_weights: Dict[ThreatCategory, float] = {}

    for ev in threat_evidence:
        # Resolve correlation group
        group = ev.correlation_group or infer_correlation_group(ev.indicator, ev.category)
        cfg = CORRELATION_CONFIG.get(group, CORRELATION_CONFIG["CORR-GENERAL-THREAT"])

        weight = cfg["weight"]
        floor = cfg["floor"]

        # Track correlation group max (prevents double counting)
        item_score = weight * ev.confidence
        if item_score > grouped_scores.get(group, 0.0):
            grouped_scores[group] = item_score

        if floor > highest_floor:
            highest_floor = floor

        # Category dominance tracking
        current_cat_w = category_weights.get(ev.category, 0.0)
        category_weights[ev.category] = current_cat_w + (ev.confidence * weight)

    additive_score = sum(grouped_scores.values())
    raw_calculated = max(additive_score, highest_floor)

    if has_authoritative_match:
        final_score = 100.0
        risk_level = RiskLevel.CRITICAL
    elif prompt_injection_flag:
        final_score = max(raw_calculated, 85.0)
        final_score = min(final_score, 95.0)
        risk_level = RiskLevel.CRITICAL if final_score >= 90.0 else RiskLevel.HIGH
    else:
        # Non-authoritative heuristic/AI scores cap at 92.0
        final_score = min(92.0, max(5.0, raw_calculated))
        if final_score >= 80.0:
            risk_level = RiskLevel.CRITICAL
        elif final_score >= 50.0:
            risk_level = RiskLevel.HIGH
        elif final_score >= 25.0:
            risk_level = RiskLevel.MEDIUM
        elif final_score >= 10.0:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.BENIGN

    # Determine dominant primary category
    primary_category = max(category_weights, key=category_weights.get) if category_weights else ThreatCategory.BENIGN

    # Channel-aware normalization (SMS input must not show email phishing)
    if source_type in ("sms", "chat"):
        if primary_category == ThreatCategory.PHISHING_EMAIL:
            # Check if KYC or generic SMS
            if any(ev.category == ThreatCategory.KYC_PHISHING for ev in evidence_list):
                primary_category = ThreatCategory.KYC_PHISHING
            else:
                primary_category = ThreatCategory.SCAM_SMS

    detected_categories = list(category_weights.keys())
    if primary_category not in detected_categories:
        detected_categories.insert(0, primary_category)

    return round(final_score, 1), risk_level, primary_category, detected_categories, grouped_scores


class HeuristicScamEngine:
    """Master rule-based scam analysis engine with deterministic evidence extraction."""

    def __init__(self):
        self.phishing = PhishingDetector()
        self.sms = SMSScamDetector()
        self.jobs = JobInternshipDetector()
        self.payments = PaymentFraudDetector()
        self.credentials = OTPCredentialDetector()
        self.impersonation = ImpersonationDetector()

    def analyze(
        self,
        text: str,
        prompt_injection_detected: bool = False,
        source_type: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Execute full heuristic analysis across all threat vectors with calibrated scoring.
        """
        evidence_list: List[EvidenceItem] = []

        # 1. Run all domain-specific sub-detectors
        evidence_list.extend(self.phishing.scan(text))
        evidence_list.extend(self.sms.scan(text))
        evidence_list.extend(self.jobs.scan(text))
        evidence_list.extend(self.payments.scan(text))
        evidence_list.extend(self.credentials.scan(text))
        evidence_list.extend(self.impersonation.scan(text))

        # 2. Factor in prompt injection flag if present
        if prompt_injection_detected:
            evidence_list.append(
                EvidenceItem(
                    indicator="Adversarial Prompt Injection Attempt",
                    description="Input contains explicit system override, delimiter evasion, or jailbreak directives.",
                    confidence=0.98,
                    category=ThreatCategory.PROMPT_INJECTION_ATTEMPT,
                    severity="HIGH",
                    correlation_group="CORR-PROMPT-INJECTION",
                    raw_snippet="Instruction override sequence detected"
                )
            )

        # 3. Categorize & Score via deterministic model
        if not evidence_list:
            # Benign / Safe
            return {
                "risk_level": RiskLevel.BENIGN,
                "risk_score": 5.0,
                "primary_category": ThreatCategory.BENIGN,
                "detected_categories": [ThreatCategory.BENIGN],
                "confidence_score": 0.95,
                "observed_evidence": [],
                "ai_assessment": (
                    "No malicious indicators, social engineering coercion, financial fraud requests, "
                    "or phishing signatures were detected in the analyzed message. Content appears benign."
                ),
                "uncertainty_factors": [
                    "Static text analysis does not account for out-of-band context or sender address spoofing.",
                    "If this message asks you to open unfamiliar attachments, perform file threat analysis."
                ],
                "mitigation_recommendations": [
                    MitigationStep(
                        action="Standard Vigilance",
                        urgency=UrgencyLevel.INFO,
                        details="No immediate threats identified. Continue standard digital security practices."
                    )
                ]
            }

        final_score, risk_level, primary_category, detected_categories, _ = calculate_calibrated_scam_score(
            evidence_list=evidence_list,
            has_authoritative_match=False,
            prompt_injection_flag=prompt_injection_detected,
            source_type=source_type
        )

        # Average confidence
        avg_confidence = sum(ev.confidence for ev in evidence_list) / len(evidence_list)

        # Evidence summary
        evidence_summary = "; ".join([ev.indicator for ev in evidence_list[:3]])
        ai_assessment = (
            f"Deterministic threat signals detected matching {primary_category.value}. "
            f"Key indicators observed: {evidence_summary}. "
            f"Evaluation produced a calibrated risk score of {final_score}/100 ({risk_level.value})."
        )

        uncertainty_factors = [
            "Analysis conducted via local deterministic heuristic threat signature engine.",
            "Evaluation is based strictly on observable syntactic and semantic threat patterns in submitted text."
        ]
        if len(text.strip()) < 40:
            uncertainty_factors.append("Input text is brief; brevity limits broader behavioral pattern detection.")

        mitigations = self._generate_mitigations(primary_category, detected_categories)

        return {
            "risk_level": risk_level,
            "risk_score": final_score,
            "primary_category": primary_category,
            "detected_categories": detected_categories,
            "confidence_score": round(avg_confidence, 2),
            "observed_evidence": evidence_list,
            "ai_assessment": ai_assessment,
            "uncertainty_factors": uncertainty_factors,
            "mitigation_recommendations": mitigations,
        }

    def _generate_mitigations(
        self, primary: ThreatCategory, all_cats: List[ThreatCategory]
    ) -> List[MitigationStep]:
        mitigations: List[MitigationStep] = []

        if ThreatCategory.OTP_THEFT in all_cats or primary == ThreatCategory.OTP_THEFT:
            mitigations.append(
                MitigationStep(
                    action="NEVER Share Your OTP or Security Code",
                    urgency=UrgencyLevel.IMMEDIATE,
                    details="Banks, legitimate companies, and government entities will NEVER ask for your OTP. Do not disclose it to anyone."
                )
            )

        if ThreatCategory.UPI_PAYMENT_FRAUD in all_cats or primary == ThreatCategory.UPI_PAYMENT_FRAUD:
            mitigations.append(
                MitigationStep(
                    action="Do NOT Enter Your UPI PIN",
                    urgency=UrgencyLevel.IMMEDIATE,
                    details="Entering your UPI PIN or scanning a QR code is ONLY required to SEND money, NEVER to receive funds or cashback."
                )
            )

        if ThreatCategory.KYC_PHISHING in all_cats or primary == ThreatCategory.KYC_PHISHING or ThreatCategory.PHISHING_EMAIL in all_cats:
            mitigations.append(
                MitigationStep(
                    action="Avoid Clicking Links & Verify Directly With Bank",
                    urgency=UrgencyLevel.HIGH,
                    details="Do not click embedded links claiming your KYC or bank services have expired. Visit your official bank branch or official app directly."
                )
            )

        if ThreatCategory.ADVANCE_FEE_FRAUD in all_cats or ThreatCategory.LOTTERY_SCAM in all_cats:
            mitigations.append(
                MitigationStep(
                    action="Do Not Pay Advance Fees or Processing Charges",
                    urgency=UrgencyLevel.HIGH,
                    details="Legitimate lotteries and contests do not require upfront processing fees to claim prizes. Any request to pay money to receive money is fraud."
                )
            )

        if ThreatCategory.FAKE_JOB_OFFER in all_cats or ThreatCategory.FAKE_INTERNSHIP in all_cats:
            mitigations.append(
                MitigationStep(
                    action="Do Not Pay Registration or Security Fees",
                    urgency=UrgencyLevel.HIGH,
                    details="Legitimate corporate employers and internship programs never demand upfront payments or task-based fees. Verify via official career portals."
                )
            )

        if ThreatCategory.BANKING_FRAUD in all_cats or primary == ThreatCategory.BANKING_FRAUD:
            mitigations.append(
                MitigationStep(
                    action="Reject Remote Desktop Software Installation",
                    urgency=UrgencyLevel.IMMEDIATE,
                    details="Never install AnyDesk, TeamViewer, or QuickSupport at the request of an unverified caller. This grants full remote control over your bank accounts."
                )
            )

        if ThreatCategory.SOCIAL_ENGINEERING in all_cats or ThreatCategory.IMPERSONATION in all_cats:
            mitigations.append(
                MitigationStep(
                    action="Reject 'Digital Arrest' & Law Enforcement Calls",
                    urgency=UrgencyLevel.IMMEDIATE,
                    details="Law enforcement agencies (CBI, Police, ED) do NOT conduct arrests via video calls (Skype/WhatsApp) nor demand funds for clearing charges. Report to 1930 / cybercrime.gov.in."
                )
            )

        if ThreatCategory.PROMPT_INJECTION_ATTEMPT in all_cats:
            mitigations.append(
                MitigationStep(
                    action="Isolate Adversarial Input",
                    urgency=UrgencyLevel.HIGH,
                    details="Submitted text contains active prompt injection vectors designed to manipulate security guardrails. Content should be quarantined."
                )
            )

        if not mitigations:
            mitigations.append(
                MitigationStep(
                    action="Verify Through Official Channels",
                    urgency=UrgencyLevel.HIGH,
                    details="Do not act upon the instructions in this message without independent verification through recognized official contact numbers."
                )
            )

        return mitigations


# Module singleton
heuristic_engine_instance = HeuristicScamEngine()
