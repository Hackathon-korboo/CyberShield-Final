"""Deterministic detection rules for Email targets."""

import re
from typing import Optional

from backend.app.engines.rules.base import BaseSecurityRule
from backend.app.schemas.analysis import (
    EmailObservedEvidence,
    IndicatorCategory,
    IndicatorSeverity,
    SecurityIndicator,
)
from backend.app.schemas.email import EmailAnalysisRequest

URGENCY_PATTERNS = [
    re.compile(r"\b(?:immediate\s+action\s+required|account\s+(?:will\s+be\s+)?suspended|within\s+24\s+hours|urgent\s+security\s+notice)\b", re.IGNORECASE),
    re.compile(r"\b(?:unauthorized\s+transaction|security\s+breach|access\s+terminated|final\s+warning)\b", re.IGNORECASE),
]

PAYMENT_FRAUD_PATTERNS = [
    re.compile(r"\b(?:itunes\s+gift\s+card|google\s+play\s+card|steam\s+card|western\s+union|bitcoin\s+wallet|send\s+crypto)\b", re.IGNORECASE),
]

JOB_SCAM_PATTERNS = [
    re.compile(r"\b(?:earn\s+\$\d{2,4}\s*(?:daily|per\s+day|weekly)|no\s+experience\s+needed.*work\s+from\s+home|package\s+forwarding\s+agent)\b", re.IGNORECASE),
]

CREDENTIAL_HARVEST_PATTERNS = [
    re.compile(r"\b(?:confirm\s+your\s+password|verify\s+your\s+identity\s+now|click\s+here\s+to\s+keep\s+your\s+account\s+active)\b", re.IGNORECASE),
]


class EmailUrgencyRule(BaseSecurityRule):
    """RULE-EML-001: Artificial urgency and social engineering panic lure."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-EML-001",
            category=IndicatorCategory.URGENCY_LURE,
            severity=IndicatorSeverity.HIGH,
            explanation="The email employs high-pressure urgency tactics designed to induce panic and bypass critical scrutiny.",
            mitigation="Do not act under artificial deadlines; independently verify via official customer channels.",
        )

    def evaluate(self, request: EmailAnalysisRequest) -> Optional[SecurityIndicator]:
        content = f"{request.subject or ''} {request.body}"
        for pat in URGENCY_PATTERNS:
            match = pat.search(content)
            if match:
                return SecurityIndicator(
                    rule_id=self.rule_id,
                    category=self.category,
                    severity=self.severity,
                    evidence=f"Urgency trigger phrase: '{match.group(0)}'",
                    explanation=self.explanation,
                    mitigation=self.mitigation,
                )
        return None


class EmailPaymentFraudRule(BaseSecurityRule):
    """RULE-EML-002: Gift card, wire transfer, or cryptocurrency payment request."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-EML-002",
            category=IndicatorCategory.PAYMENT_LURE,
            severity=IndicatorSeverity.CRITICAL,
            explanation="The email requests payment via irreversible instruments (gift cards, money wires, crypto) characteristic of fraud.",
            mitigation="Never pay fines, bills, or taxes using gift cards or anonymous money transfers.",
        )

    def evaluate(self, request: EmailAnalysisRequest) -> Optional[SecurityIndicator]:
        content = f"{request.subject or ''} {request.body}"
        for pat in PAYMENT_FRAUD_PATTERNS:
            match = pat.search(content)
            if match:
                return SecurityIndicator(
                    rule_id=self.rule_id,
                    category=self.category,
                    severity=self.severity,
                    evidence=f"Payment instrument solicitation: '{match.group(0)}'",
                    explanation=self.explanation,
                    mitigation=self.mitigation,
                )
        return None


class EmailJobScamRule(BaseSecurityRule):
    """RULE-EML-003: Unrealistic work-from-home or employment fee scam."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-EML-003",
            category=IndicatorCategory.JOB_SCAM,
            severity=IndicatorSeverity.HIGH,
            explanation="The email advertises implausible compensation for minimal work, typical of recruitment fraud and mule recruitment.",
            mitigation="Legitimate employers never demand upfront fees or promise exorbitant pay for trivial tasks.",
        )

    def evaluate(self, request: EmailAnalysisRequest) -> Optional[SecurityIndicator]:
        content = f"{request.subject or ''} {request.body}"
        for pat in JOB_SCAM_PATTERNS:
            match = pat.search(content)
            if match:
                return SecurityIndicator(
                    rule_id=self.rule_id,
                    category=self.category,
                    severity=self.severity,
                    evidence=f"Suspicious job lure: '{match.group(0)}'",
                    explanation=self.explanation,
                    mitigation=self.mitigation,
                )
        return None


class EmailCredentialHarvestRule(BaseSecurityRule):
    """RULE-EML-004: Direct solicitation of passwords or login confirmation."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-EML-004",
            category=IndicatorCategory.CREDENTIAL_HARVESTING,
            severity=IndicatorSeverity.HIGH,
            explanation="The message solicits password confirmation or identity verification through an email link.",
            mitigation="Authentic security teams never ask you to verify passwords via unsolicited email links.",
        )

    def evaluate(self, request: EmailAnalysisRequest) -> Optional[SecurityIndicator]:
        content = f"{request.subject or ''} {request.body}"
        for pat in CREDENTIAL_HARVEST_PATTERNS:
            match = pat.search(content)
            if match:
                return SecurityIndicator(
                    rule_id=self.rule_id,
                    category=self.category,
                    severity=self.severity,
                    evidence=f"Credential confirmation prompt: '{match.group(0)}'",
                    explanation=self.explanation,
                    mitigation=self.mitigation,
                )
        return None
