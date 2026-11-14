"""
CyberShield AI 2.0 - Impersonation & Social Engineering Detector
Identifies government agency impersonation (CBI, Police, ED, RBI), courier drug parcel scams,
digital arrest intimidation tactics, and telecom authority coercion.
"""

import re
from typing import List
from backend.app.schemas.threat_models import ThreatCategory, EvidenceItem


class ImpersonationDetector:
    """Specialized detector for impersonation fraud and high-pressure social engineering."""

    IMPERSONATION_PATTERNS = [
        (re.compile(r'(?i)\b(?:cbi|crime\s+branch|mumbai\s+police|delhi\s+police|enforcement\s+directorate|ed\s+officer|cyber\s+crime\s+cell)\b'),
         "Law enforcement agency impersonation marker", 0.92, ThreatCategory.IMPERSONATION),
        (re.compile(r'(?i)\bdigital\s+arrest\b|\byou\s+are\s+under\s+digital\s+arrest\b'),
         "Coercive 'Digital Arrest' intimidation scam", 0.99, ThreatCategory.SOCIAL_ENGINEERING),
        (re.compile(r'(?i)\bkeep\s+(?:your\s+)?camera\s+on\s+and\s+do\s+not\s+(?:disconnect|leave\s+the\s+room|inform\s+anyone)\b'),
         "Coercive video confinement / psychological isolation directive", 0.96, ThreatCategory.SOCIAL_ENGINEERING),
        (re.compile(r'(?i)\b(?:fedex|dhl|customs)\s+parcel\s+(?:containing\s+)?(?:drugs|narcotics|passports|contraband|illegal\s+items)\b'),
         "Narcotics courier parcel extortion scheme", 0.98, ThreatCategory.IMPERSONATION),
        (re.compile(r'(?i)\barrest\s+warrant\s+(?:has\s+been\s+issued|issued\s+in\s+your\s+name)\b'),
         "Fabricated arrest warrant legal intimidation", 0.94, ThreatCategory.SOCIAL_ENGINEERING),
        (re.compile(r'(?i)\btrai\s+(?:has\s+blocked|will\s+disconnect)\s+(?:all\s+)?your\s+mobile\s+numbers\s+within\s+\d+\s+hours\b'),
         "TRAI telecom disconnection impersonation threat", 0.95, ThreatCategory.IMPERSONATION),
        (re.compile(r'(?i)\brbi\s+(?:security\s+audit|mandate|guidelines\s+require\s+transfer)\b'),
         "RBI regulatory authority impersonation", 0.90, ThreatCategory.IMPERSONATION),
        (re.compile(r'(?i)\b(?:dad|mom|mum|son|daughter|grandma|grandpa|friend|family).*?(?:emergency|lost\s+my\s+phone|wallet|stranded|hospital|accident).*?(?:transfer|send|money|funds|upi)\b'),
         "Distressed relative impersonation / emergency fund transfer scam", 0.92, ThreatCategory.SOCIAL_ENGINEERING),
        (re.compile(r'(?i)\b(?:urgently|immediately)\s+(?:transfer|send|pay)\s+(?:\d+|money|funds)\s+(?:to\s+)?(?:this\s+account|upi)\b'),
         "High-pressure urgent fund transfer demand", 0.88, ThreatCategory.SOCIAL_ENGINEERING),
    ]

    def scan(self, text: str) -> List[EvidenceItem]:
        evidence = []
        for pattern, desc, confidence, cat in self.IMPERSONATION_PATTERNS:
            match = pattern.search(text)
            if match:
                evidence.append(
                    EvidenceItem(
                        indicator=desc,
                        description=f"Detected impersonation signature: '{match.group(0)}'",
                        confidence=confidence,
                        category=cat,
                        raw_snippet=match.group(0)
                    )
                )
        return evidence
