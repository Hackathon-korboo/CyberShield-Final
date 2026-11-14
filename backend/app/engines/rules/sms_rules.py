"""Deterministic detection rules for SMS and chat targets."""

import re
from typing import Optional

from backend.app.engines.rules.base import BaseSecurityRule
from backend.app.schemas.analysis import (
    IndicatorCategory,
    IndicatorSeverity,
    SecurityIndicator,
)
from backend.app.schemas.sms import SmsAnalysisRequest

OTP_PATTERNS = [
    re.compile(r"\b(?:share|send|enter|reply\s+with)\s*(?:your\s+)?(?:6-digit|4-digit|one-time|otp|pin|verification\s+code)\b", re.IGNORECASE),
    re.compile(r"\b(?:otp\s*(?:is|code)?\s*[:=]?\s*\d{4,8})\b", re.IGNORECASE),
]

CARD_BLOCKAGE_PATTERNS = [
    re.compile(r"\b(?:debit|credit)?\s*card\s*(?:has\s+been\s+)?(?:blocked|suspended|frozen|restricted)\b", re.IGNORECASE),
    re.compile(r"\b(?:kyc\s+suspended|pan\s+card\s+expired|bank\s+account\s+locked)\b", re.IGNORECASE),
]

LOTTERY_PATTERNS = [
    re.compile(r"\b(?:congratulations|won\s+\$\d+|lottery\s+winner|claim\s+your\s+cash\s+prize|selected\s+for\s+free\s+gift)\b", re.IGNORECASE),
]

COMPOUND_URGENCY_PATTERNS = [
    re.compile(
        r"\b(?:urgent|immediately|immediate\s+action\s+required|final\s+notice|act\s+now)\b.*?\b(?:verify|confirm|validate)\s+(?:your\s+)?(?:bank|account|card|identity|id|billing)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:urgent|immediately|immediate\s+action\s+required|act\s+now)\b.*?\b(?:reply|send|share|enter)\s+(?:with\s+)?(?:your\s+)?(?:\d+-digit\s+)?(?:otp|code|pin|password|verification)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:urgent|immediately|immediate\s+action\s+required)\b.*?\b(?:avoid|prevent)\s+(?:account\s+)?(?:suspension|blockage|termination|closure)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:account|card|service)\s+(?:will\s+be|has\s+been)\s+(?:blocked|suspended|terminated|frozen)\s+unless\s+you\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bimmediate\s+action\s+required\b.*?\b(?:share|verify|send|confirm|update|pay)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:urgent\s*:|\burgent\b).*?\b(?:pay|payment|transfer|fine|bill)\s+(?:now|immediately|within\s+\d+\s+hours)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:pay|confirm)\s+(?:your\s+)?payment\s+now\b",
        re.IGNORECASE,
    ),
]


class SmsOtpExtractionRule(BaseSecurityRule):
    """RULE-SMS-001: Explicit solicitation of One-Time Passwords (OTP) or PINs."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-SMS-001",
            category=IndicatorCategory.OTP_HARVESTING,
            severity=IndicatorSeverity.CRITICAL,
            explanation="The message attempts to extract a one-time verification code or PIN, a hallmark of active account takeover fraud.",
            mitigation="NEVER share OTPs or security codes with anyone under any circumstances.",
        )

    def evaluate(self, request: SmsAnalysisRequest) -> Optional[SecurityIndicator]:
        for pat in OTP_PATTERNS:
            match = pat.search(request.message)
            if match:
                return SecurityIndicator(
                    rule_id=self.rule_id,
                    category=self.category,
                    severity=self.severity,
                    evidence=f"OTP solicitation phrase: '{match.group(0)}'",
                    explanation=self.explanation,
                    mitigation=self.mitigation,
                )
        return None


class SmsCardBlockageRule(BaseSecurityRule):
    """RULE-SMS-002: False debit/credit card or KYC blockage alert."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-SMS-002",
            category=IndicatorCategory.URGENCY_LURE,
            severity=IndicatorSeverity.HIGH,
            explanation="The message creates artificial panic by claiming a banking card or account is locked to lure the user into clicking.",
            mitigation="Contact your bank directly via the phone number printed on the back of your card.",
        )

    def evaluate(self, request: SmsAnalysisRequest) -> Optional[SecurityIndicator]:
        for pat in CARD_BLOCKAGE_PATTERNS:
            match = pat.search(request.message)
            if match:
                return SecurityIndicator(
                    rule_id=self.rule_id,
                    category=self.category,
                    severity=self.severity,
                    evidence=f"Banking panic trigger: '{match.group(0)}'",
                    explanation=self.explanation,
                    mitigation=self.mitigation,
                )
        return None


class SmsLotteryPrizeRule(BaseSecurityRule):
    """RULE-SMS-003: Unsolicited lottery, prize, or cash gift lure."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-SMS-003",
            category=IndicatorCategory.PAYMENT_LURE,
            severity=IndicatorSeverity.HIGH,
            explanation="The message claims the recipient has won an unentered prize, typical of advance-fee fraud.",
            mitigation="Legitimate sweepstakes never require paying a processing fee to claim prizes.",
        )

    def evaluate(self, request: SmsAnalysisRequest) -> Optional[SecurityIndicator]:
        for pat in LOTTERY_PATTERNS:
            match = pat.search(request.message)
            if match:
                return SecurityIndicator(
                    rule_id=self.rule_id,
                    category=self.category,
                    severity=self.severity,
                    evidence=f"Prize lure phrase: '{match.group(0)}'",
                    explanation=self.explanation,
                    mitigation=self.mitigation,
                )
        return None


class SmsUrgencyRule(BaseSecurityRule):
    """RULE-SMS-004: Contextual urgency and panic-based smishing tactics."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-SMS-004",
            category=IndicatorCategory.URGENCY_LURE,
            severity=IndicatorSeverity.HIGH,
            explanation="The message combines high-pressure urgency with account suspension, credential verification, OTP requests, or payment demands to induce panic.",
            mitigation="Do not react immediately to urgent demands via SMS. Verify the claim through an independent, official channel.",
        )

    def evaluate(self, request: SmsAnalysisRequest) -> Optional[SecurityIndicator]:
        for pat in COMPOUND_URGENCY_PATTERNS:
            match = pat.search(request.message)
            if match:
                return SecurityIndicator(
                    rule_id=self.rule_id,
                    category=self.category,
                    severity=self.severity,
                    evidence=f"Contextual urgency trigger: '{match.group(0)}'",
                    explanation=self.explanation,
                    mitigation=self.mitigation,
                )
        return None
