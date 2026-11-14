"""
CyberShield AI 2.0 - OTP & Credential Harvesting Detector
Detects illicit attempts to steal OTPs, bank credentials, ATM PINs, CVVs,
and installations of remote desktop access tools (AnyDesk, TeamViewer).
"""

import re
from typing import List
from backend.app.schemas.threat_models import ThreatCategory, EvidenceItem


class OTPCredentialDetector:
    """Specialized detector for OTP theft, credential extortion, and remote access abuse."""

    CREDENTIAL_SCAM_PATTERNS = [
        (re.compile(r'(?i)\b(?:share|tell|send|disclose|provide|give)\s+(?:the|your)?\s*(?:\d+[- ]digit\s+)?(?:otp|one[- ]time\s+password|verification\s+code)\b'),
         "Direct OTP disclosure solicitation", 0.98, ThreatCategory.OTP_THEFT, "CORR-OTP-THEFT", "CRITICAL"),
        (re.compile(r'(?i)\bshare\s+otp\b|\btell\s+otp\b|\bverify\s+with\s+otp\b'),
         "OTP request trigger in untrusted communication", 0.95, ThreatCategory.OTP_THEFT, "CORR-OTP-THEFT", "CRITICAL"),
        (re.compile(r'(?i)\baccount\s+verification\s+is\s+pending\b'),
         "Deceptive pending account verification lure", 0.90, ThreatCategory.OTP_THEFT, "CORR-URGENCY", "HIGH"),
        (re.compile(r'(?i)\b(?:with\s+our\s+)?support\s+executive\b'),
         "Rogue support executive impersonation", 0.90, ThreatCategory.IMPERSONATION, "CORR-IMPERSONATION", "HIGH"),
        (re.compile(r'(?i)\benter\s+(?:your\s+)?(?:atm\s+pin|netbanking\s+password|cvv|expiry\s+date)\b'),
         "Sensory financial credential request (PIN/CVV/Password)", 0.98, ThreatCategory.CREDENTIAL_HARVESTING, "CORR-CREDENTIAL-HARVEST", "CRITICAL"),
        (re.compile(r'(?i)\binstall\s+(?:anydesk|teamviewer|rustdesk|quicksupport|screen\s*share)\b'),
         "Remote desktop / screen-sharing tool installation directive", 0.97, ThreatCategory.BANKING_FRAUD, "CORR-REMOTE-ACCESS", "CRITICAL"),
        (re.compile(r'(?i)\bgive\s+(?:me\s+)?the\s+9[- ]digit\s+(?:code|address)\s+from\s+anydesk\b'),
         "AnyDesk connection code harvesting attempt", 0.99, ThreatCategory.BANKING_FRAUD, "CORR-REMOTE-ACCESS", "CRITICAL"),
        (re.compile(r'(?i)\bshare\s+(?:the\s+)?sms\s+you\s+(?:just\s+)?received\b'),
         "Indirect OTP / SMS forwarding harvesting tactic", 0.92, ThreatCategory.OTP_THEFT, "CORR-OTP-THEFT", "HIGH"),
    ]

    def scan(self, text: str) -> List[EvidenceItem]:
        evidence = []
        for pattern, desc, confidence, cat, corr_group, severity in self.CREDENTIAL_SCAM_PATTERNS:
            match = pattern.search(text)
            if match:
                evidence.append(
                    EvidenceItem(
                        indicator=desc,
                        description=f"Detected credential harvesting signature: '{match.group(0)}'",
                        confidence=confidence,
                        category=cat,
                        raw_snippet=match.group(0),
                        severity=severity,
                        correlation_group=corr_group
                    )
                )
        return evidence
