"""
CyberShield AI 2.0 - Phishing Email & Deceptive Domain Detector
Detects phishing, deceptive credential harvesting, urgent account suspension threats,
and brand spoofing.
"""

import re
from typing import List
from backend.app.schemas.threat_models import ThreatCategory, EvidenceItem


class PhishingDetector:
    """Specialized detector for phishing emails and brand credential harvesting."""

    SUSPICIOUS_PHRASES = [
        (re.compile(r'(?i)\baccount\s+(?:has\s+been|is)\s+(?:suspended|locked|disabled|compromised|flagged)\b'),
         "Urgent claim of account suspension or compromise", 0.85),
        (re.compile(r'(?i)\bverify\s+(?:your\s+identity|account|credentials|password|information)\s+immediately\b'),
         "Immediate credential verification demand", 0.90),
        (re.compile(r'(?i)\baction\s+required\s*:\s*(?:unauthorized\s+activity|unusual\s+sign-in|security\s+alert)\b'),
         "Deceptive security alert requiring urgent action", 0.80),
        (re.compile(r'(?i)\bfailure\s+to\s+(?:verify|respond|update)\s+will\s+result\s+in\s+permanent\s+(?:closure|termination|deletion)\b'),
         "Coercive deadline threatening service termination", 0.90),
        (re.compile(r'(?i)\bclick\s+here\s+to\s+(?:restore|reactivate|verify|unlock)\s+(?:your\s+account|access)\b'),
         "Deceptive hyperlink prompt for account restoration", 0.85),
        (re.compile(r'(?i)\b(?:update|confirm)\s+your\s+(?:billing|payment|credit\s*card)\s+details\b'),
         "Billing/payment credential harvesting attempt", 0.85),
        (re.compile(r'(?i)\breset\s+your\s+password\s+now\b'),
         "Unsolicited password reset directive", 0.75),
        (re.compile(r'(?i)https?://[^\s]*\.(?:xyz|top|work|click|cfd|rest|monster|support-account)[^\s]*'),
         "Suspicious low-reputation top-level domain hyperlink", 0.80),
        (re.compile(r'(?i)https?://[^\s]*(?:paypal|netflix|google|microsoft|apple|amazon|chase|wellsfargo)[^\s]*\.(?:xyz|top|live|info|online)'),
         "Typosquatting/brand lookalike domain detected", 0.95),
    ]

    def scan(self, text: str) -> List[EvidenceItem]:
        evidence = []
        for pattern, desc, confidence in self.SUSPICIOUS_PHRASES:
            match = pattern.search(text)
            if match:
                evidence.append(
                    EvidenceItem(
                        indicator=desc,
                        description=f"Detected phishing signature: '{match.group(0)}'",
                        confidence=confidence,
                        category=ThreatCategory.PHISHING_EMAIL,
                        raw_snippet=match.group(0)
                    )
                )
        return evidence
