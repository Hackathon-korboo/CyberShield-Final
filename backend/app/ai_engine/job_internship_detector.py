"""
CyberShield AI 2.0 - Fake Job & Internship Scam Detector
Detects recruitment fraud, fake internships, task-based Telegram scams,
upfront registration fees, and pay-to-work schemes.
"""

import re
from typing import List
from backend.app.schemas.threat_models import ThreatCategory, EvidenceItem


class JobInternshipDetector:
    """Specialized detector for fake job offers, recruitment scams, and fraudulent internships."""

    JOB_SCAM_PATTERNS = [
        (re.compile(r'(?i)\bearn\s+(?:\u20b9|\$|rs\.?)\s*\d{3,6}\s*(?:daily|per\s+day|every\s+day|hourly)\b'),
         "Unrealistic daily earnings guarantee", 0.90, ThreatCategory.FAKE_JOB_OFFER, "CORR-UNSOLICITED-OFFER", "MEDIUM"),
        (re.compile(r'(?i)\b(?:selected\s+for\s+(?:a\s+)?work[- ]from[- ]home\s+job|salary\s+of\s+(?:rs\.?|inr|\$|\u20b9)\s*\d+[\d,]*)\b'),
         "Unsolicited job selection with high salary", 0.92, ThreatCategory.FAKE_JOB_OFFER, "CORR-UNSOLICITED-OFFER", "HIGH"),
        (re.compile(r'(?i)\b(?:part[- ]time|work\s+from\s+home)\s+job.*(?:like|subscribe|review|rate)\s+(?:youtube|google|hotel|products)\b'),
         "Task-based review/like social media work scam", 0.95, ThreatCategory.FAKE_JOB_OFFER, "CORR-JOB-SCAM", "HIGH"),
        (re.compile(r'(?i)\b(?:pay|deposit|transfer)\s+(?:(?:rs\.?|inr|\$|\u20b9)\s*\d+[\d,]*\s+)?(?:a\s+)?(?:refundable\s+)?(?:security\s+deposit|registration\s+fees?|training\s+fees?|kit\s+charges?)\b'),
         "Upfront registration or security fee demand", 0.96, ThreatCategory.ADVANCE_FEE_FRAUD, "CORR-ADVANCE-FEE", "HIGH"),
        (re.compile(r'(?i)\bconfirm\s+your\s+position\s+immediately\b'),
         "Job offer urgency pressure tactic", 0.88, ThreatCategory.FAKE_JOB_OFFER, "CORR-URGENCY", "MEDIUM"),
        (re.compile(r'(?i)\b(?:selected\s+for|offered)\s+(?:an?\s+)?internship\s+without\s+(?:any\s+)?interview\b'),
         "Guaranteed internship without screening or interview", 0.92, ThreatCategory.FAKE_INTERNSHIP, "CORR-UNSOLICITED-OFFER", "MEDIUM"),
        (re.compile(r'(?i)\b(?:internship|offer\s+letter).*(?:pay|fee|charge|deposit)\s*(?:of\s*)?(?:\u20b9|\$|rs\.?)\s*\d+\b'),
         "Paid internship certificate / fee requirement", 0.95, ThreatCategory.FAKE_INTERNSHIP, "CORR-ADVANCE-FEE", "HIGH"),
        (re.compile(r'(?i)\bjoin\s+(?:our\s+)?telegram\s+(?:channel|group)\s+to\s+receive\s+(?:tasks|payment|salary)\b'),
         "Telegram task assignment redirection", 0.92, ThreatCategory.FAKE_JOB_OFFER, "CORR-JOB-SCAM", "HIGH"),
        (re.compile(r'(?i)\bcontact\s+(?:our\s+)?hr\s+manager\s+on\s+whatsapp\b'),
         "WhatsApp recruitment bypassing official corporate career portals", 0.82, ThreatCategory.FAKE_JOB_OFFER, "CORR-IMPERSONATION", "MEDIUM"),
        (re.compile(r'(?i)\bno\s+experience\s+required.*guaranteed\s+(?:income|salary|stipend)\s+of\b'),
         "No experience required with guaranteed high stipend", 0.85, ThreatCategory.FAKE_INTERNSHIP, "CORR-UNSOLICITED-OFFER", "MEDIUM"),
    ]

    def scan(self, text: str) -> List[EvidenceItem]:
        evidence = []
        for pattern, desc, confidence, cat, corr_group, severity in self.JOB_SCAM_PATTERNS:
            match = pattern.search(text)
            if match:
                evidence.append(
                    EvidenceItem(
                        indicator=desc,
                        description=f"Detected job/internship scam signature: '{match.group(0)}'",
                        confidence=confidence,
                        category=cat,
                        raw_snippet=match.group(0),
                        severity=severity,
                        correlation_group=corr_group
                    )
                )
        return evidence
