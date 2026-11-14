"""
CyberShield AI 2.0 - UPI & Payment Fraud Detector
Detects UPI payment fraud, QR code reversal tricks, enter-PIN-to-receive scams,
and fake payment confirmation deceptions.
"""

import re
from typing import List
from backend.app.schemas.threat_models import ThreatCategory, EvidenceItem


class PaymentFraudDetector:
    """Specialized detector for UPI, QR code, and payment gateway fraud."""

    PAYMENT_SCAM_PATTERNS = [
        (re.compile(r'(?i)\benter\s+(?:your\s+)?(?:upi\s+)?pin\s+(?:to\s+)?(?:receive|claim|get|accept|transfer|pay|approve)\b'),
         "Critical UPI deception: Demanding PIN entry in external communication", 0.99),
        (re.compile(r'(?i)\benter\s+(?:your\s+)?(?:upi\s+)?pin\b'),
         "Solicitation of UPI PIN in untrusted channel", 0.95),
        (re.compile(r'(?i)\bscan\s+(?:this\s+)?(?:qr\s*code|qr)\s+(?:to\s+)?(?:receive|claim|get|accept|pay)\b'),
         "Deceptive QR code scan directive for receiving or transferring money", 0.98),
        (re.compile(r'(?i)\baccept\s+(?:the\s+)?(?:collect|payment)\s+request\s+to\s+(?:get|receive)\s+(?:paid|money|refund)\b'),
         "Collect request exploitation disguised as incoming payment", 0.95),
        (re.compile(r'(?i)\bi\s+have\s+sent\s+(?:extra|by\s+mistake)\s+(?:\u20b9|\$|rs\.?)\s*\d+.*(?:please\s+refund|send\s+back)\b'),
         "Overpayment / accidental transfer refund manipulation", 0.90),
        (re.compile(r'(?i)\bclick\s+(?:on\s+)?link\s+to\s+(?:claim|receive)\s+(?:cashback|scratch\s+card|reward)\b'),
         "Fraudulent cashback / scratch card payment lure", 0.88),
        (re.compile(r'(?i)\bpayment\s+(?:failed|declined|on\s+hold).*approve\s+(?:via|through)\s+(?:link|upi)\b'),
         "Deceptive failed transaction resolution prompt", 0.85),
    ]

    def scan(self, text: str) -> List[EvidenceItem]:
        evidence = []
        for pattern, desc, confidence in self.PAYMENT_SCAM_PATTERNS:
            match = pattern.search(text)
            if match:
                evidence.append(
                    EvidenceItem(
                        indicator=desc,
                        description=f"Detected payment fraud signature: '{match.group(0)}'",
                        confidence=confidence,
                        category=ThreatCategory.UPI_PAYMENT_FRAUD,
                        raw_snippet=match.group(0)
                    )
                )
        return evidence
