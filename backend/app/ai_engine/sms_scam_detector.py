"""
CyberShield AI 2.0 - SMS Scam & Smishing Detector
Identifies malicious SMS threats including electricity bill disconnection, fake KYC expiry,
lottery prizes, advance fees, delivery scams, and dangerous shortened link vectors.
"""

import re
from typing import List
from backend.app.schemas.threat_models import ThreatCategory, EvidenceItem


class SMSScamDetector:
    """Specialized detector for SMS scams (Smishing)."""

    SMS_SIGNATURES = [
        # Electricity bill scams
        (re.compile(r'(?i)\belectricity\s+(?:power\s+|bill\s+)?(?:will\s+be\s+)?(?:disconnected|overdue|unpaid|due|pending)\b'),
         "Urgent electricity power disconnection threat", 0.95, ThreatCategory.ELECTRICITY_BILL_SCAM, "CORR-IMPERSONATION", "HIGH"),
        (re.compile(r'(?i)\bprevious\s+month\s+bill\s+was\s+not\s+updated\b'),
         "False un-updated utility bill claim", 0.90, ThreatCategory.ELECTRICITY_BILL_SCAM, "CORR-IMPERSONATION", "MEDIUM"),
        (re.compile(r'(?i)\b(?:contact|call)\s+(?:our\s+)?(?:electricity\s+)?officer\s+at\b'),
         "Rogue officer contact directive", 0.90, ThreatCategory.ELECTRICITY_BILL_SCAM, "CORR-IMPERSONATION", "HIGH"),

        # KYC & Banking impersonation
        (re.compile(r'(?i)\byour\s+(?:[a-z0-9_-]+\s+)?(?:sim|pancard|aadhaar|bank\s*a/c|banking\s*services|kyc)(?:\s+[a-z0-9_-]+)*\s+(?:has\s+expired|will\s+be\s+(?:suspended|blocked)|is\s+(?:suspended|blocked))\b'),
         "Threatened KYC or banking service suspension", 0.95, ThreatCategory.KYC_PHISHING, "CORR-CREDENTIAL-HARVEST", "HIGH"),
        (re.compile(r'(?i)\bbanking\s+services\s+will\s+be\s+suspended\b'),
         "Banking service suspension threat", 0.95, ThreatCategory.KYC_PHISHING, "CORR-IMPERSONATION", "HIGH"),
        (re.compile(r'(?i)\bupdate\s+(?:your\s+)?kyc\s+immediately\b'),
         "Urgent KYC update directive", 0.92, ThreatCategory.KYC_PHISHING, "CORR-URGENCY", "HIGH"),

        # Lottery & Prize Scams
        (re.compile(r'(?i)\b(?:congratulations!?\s+)?(?:you\s+(?:have\s+)?won|won\s+(?:a\s+)?(?:lottery|lucky\s+draw|cash\s+prize|iphone|\$|\u20b9|rs\.?))\b'),
         "Unsolicited lottery or high-value prize claim", 0.95, ThreatCategory.LOTTERY_SCAM, "CORR-UNSOLICITED-OFFER", "MEDIUM"),
        (re.compile(r'(?i)\blucky\s+draw\b'),
         "Unsolicited lucky draw lure", 0.90, ThreatCategory.LOTTERY_SCAM, "CORR-UNSOLICITED-OFFER", "MEDIUM"),

        # Advance Fee Fraud
        (re.compile(r'(?i)\b(?:pay|deposit|transfer)\s+(?:(?:rs\.?|inr|\$|\u20b9)\s*\d+[\d,]*\s+)?(?:a\s+)?(?:refundable\s+)?(?:processing\s+fees?|registration\s+fees?|security\s+deposit|charges?)\b'),
         "Upfront processing or registration fee demand", 0.96, ThreatCategory.ADVANCE_FEE_FRAUD, "CORR-ADVANCE-FEE", "HIGH"),
        (re.compile(r'(?i)\bto\s+claim\s+(?:your\s+)?prize\s+today\b'),
         "Prize claim urgency tactic", 0.90, ThreatCategory.LOTTERY_SCAM, "CORR-URGENCY", "MEDIUM"),

        # Delivery / Courier Scams
        (re.compile(r'(?i)\b(?:package|parcel|courier|delivery)\s+(?:is\s+on\s+hold|cannot\s+be\s+delivered|failed|address\s+confirmation)\b'),
         "Urgent postal courier parcel delivery trap", 0.90, ThreatCategory.DELIVERY_SCAM, "CORR-IMPERSONATION", "MEDIUM"),

        # APK / Download directives
        (re.compile(r'(?i)\bdownload\s+(?:and\s+install\s+)?(?:our\s+app|\.apk|app\s+from\s+link)\b'),
         "Unverified mobile application / APK download directive", 0.92, ThreatCategory.SCAM_SMS, "CORR-MALICIOUS-PAYLOAD", "HIGH"),

        # Shortened URLs
        (re.compile(r'https?://(?:bit\.ly|tinyurl\.com|is\.gd|cutt\.ly|t\.co|rb\.gy)/[a-zA-Z0-9]+'),
         "Shortened URL concealing final destination domain", 0.75, ThreatCategory.SCAM_SMS, "CORR-SUSPICIOUS-LINK", "MEDIUM"),

        # Disconnection callback traps
        (re.compile(r'(?i)\bcall\s+(?:immediately\s+)?at\s+(?:\+?\d{10,12})\s+to\s+stop\s+disconnection\b'),
         "Urgent call-back trap for disconnection prevention", 0.88, ThreatCategory.ELECTRICITY_BILL_SCAM, "CORR-URGENCY", "HIGH"),
    ]

    def scan(self, text: str) -> List[EvidenceItem]:
        evidence = []
        for pattern, desc, confidence, category, corr_group, severity in self.SMS_SIGNATURES:
            match = pattern.search(text)
            if match:
                evidence.append(
                    EvidenceItem(
                        indicator=desc,
                        description=f"Detected SMS threat signature: '{match.group(0)}'",
                        confidence=confidence,
                        category=category,
                        raw_snippet=match.group(0),
                        severity=severity,
                        correlation_group=corr_group
                    )
                )
        return evidence
