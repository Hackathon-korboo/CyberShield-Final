"""Rule engine orchestrator for deterministic security indicator evaluation."""

from typing import List, Optional

from backend.app.engines.rules.base import BaseSecurityRule
from backend.app.engines.rules.email_rules import (
    EmailCredentialHarvestRule,
    EmailJobScamRule,
    EmailPaymentFraudRule,
    EmailUrgencyRule,
)
from backend.app.engines.rules.sms_rules import (
    SmsCardBlockageRule,
    SmsLotteryPrizeRule,
    SmsOtpExtractionRule,
    SmsUrgencyRule,
)
from backend.app.engines.rules.url_rules import (
    ExcessiveSubdomainRule,
    IpHyphenRule,
    PunycodeHomoglyphRule,
    SuspiciousAuthKeywordsRule,
    SuspiciousTldRule,
)
from backend.app.schemas.analysis import (
    HeuristicFindings,
    IndicatorSeverity,
    RiskLevel,
    SecurityIndicator,
    UrlObservedEvidence,
)
from backend.app.schemas.email import EmailAnalysisRequest
from backend.app.schemas.sms import SmsAnalysisRequest

# Severity rank order for floor comparison
SEVERITY_RANK = {
    IndicatorSeverity.CRITICAL: 4,
    IndicatorSeverity.HIGH: 3,
    IndicatorSeverity.MEDIUM: 2,
    IndicatorSeverity.LOW: 1,
}

# Standard additive scoring weights per indicator severity tier
SEVERITY_WEIGHTS = {
    IndicatorSeverity.CRITICAL: 40,
    IndicatorSeverity.HIGH: 25,
    IndicatorSeverity.MEDIUM: 15,
    IndicatorSeverity.LOW: 5,
}

# Minimum score and tier floors per highest indicator severity (Approved Decision A)
SEVERITY_FLOORS = {
    IndicatorSeverity.CRITICAL: (70, RiskLevel.HIGH_RISK),
    IndicatorSeverity.HIGH: (40, RiskLevel.SUSPICIOUS),
    IndicatorSeverity.MEDIUM: (15, RiskLevel.LOW_RISK),
    IndicatorSeverity.LOW: (5, RiskLevel.LOW_RISK),
}

RISK_TIER_ORDER = {
    RiskLevel.CLEAN: 0,
    RiskLevel.LOW_RISK: 1,
    RiskLevel.SUSPICIOUS: 2,
    RiskLevel.HIGH_RISK: 3,
}


def calculate_risk_level(score: int, min_risk_level: Optional[RiskLevel] = None) -> RiskLevel:
    """Map composite score (0-100) to standard RiskLevel tier, respecting minimum tier floor."""
    if score >= 70:
        tier = RiskLevel.HIGH_RISK
    elif score >= 40:
        tier = RiskLevel.SUSPICIOUS
    elif score >= 15:
        tier = RiskLevel.LOW_RISK
    else:
        tier = RiskLevel.CLEAN

    if min_risk_level is not None:
        if RISK_TIER_ORDER[min_risk_level] > RISK_TIER_ORDER[tier]:
            tier = min_risk_level
    return tier


def aggregate_indicators(indicators: List[SecurityIndicator]) -> HeuristicFindings:
    """Compute composite score using the approved Severity Floor Model.

    1. Calculate normal additive score using severity weights.
    2. Determine the highest severity among all triggered indicators.
    3. Apply the corresponding minimum score floor.
    4. Final score is max(additive_score, severity_floor) capped at 100.
    5. Derive final risk level from final score respecting the minimum risk tier.
    """
    if not indicators:
        return HeuristicFindings(
            risk_level=RiskLevel.CLEAN,
            risk_score=0,
            indicators=[],
        )

    # 1. Normal additive score
    additive_score = sum(SEVERITY_WEIGHTS.get(ind.severity, 10) for ind in indicators)

    # 2. Determine highest severity among all triggered indicators
    highest_severity = max(indicators, key=lambda ind: SEVERITY_RANK.get(ind.severity, 0)).severity
    score_floor, tier_floor = SEVERITY_FLOORS.get(highest_severity, (0, RiskLevel.CLEAN))

    # 3. Final score is max(additive_score, score_floor), capped at 100
    final_score = min(100, max(additive_score, score_floor))

    # 4. Derive final risk level from final score using existing risk tiers + tier floor
    final_tier = calculate_risk_level(final_score, min_risk_level=tier_floor)

    return HeuristicFindings(
        risk_level=final_tier,
        risk_score=final_score,
        indicators=indicators,
    )


class SecurityRuleEngine:
    """Executes catalog of deterministic rules across targets and computes risk score."""

    def __init__(self):
        self.url_rules: List[BaseSecurityRule] = [
            IpHyphenRule(),
            PunycodeHomoglyphRule(),
            SuspiciousAuthKeywordsRule(),
            ExcessiveSubdomainRule(),
            SuspiciousTldRule(),
        ]
        self.email_rules: List[BaseSecurityRule] = [
            EmailUrgencyRule(),
            EmailPaymentFraudRule(),
            EmailJobScamRule(),
            EmailCredentialHarvestRule(),
        ]
        self.sms_rules: List[BaseSecurityRule] = [
            SmsOtpExtractionRule(),
            SmsCardBlockageRule(),
            SmsLotteryPrizeRule(),
            SmsUrgencyRule(),
        ]

    def aggregate_indicators(self, indicators: List[SecurityIndicator]) -> HeuristicFindings:
        """Public interface for indicator aggregation using Severity Floor Model."""
        return aggregate_indicators(indicators)

    def _aggregate_indicators(self, indicators: List[SecurityIndicator]) -> HeuristicFindings:
        """Internal alias for indicator aggregation."""
        return aggregate_indicators(indicators)

    def evaluate_url(self, evidence: UrlObservedEvidence) -> HeuristicFindings:
        """Evaluate a URL target against all URL detection rules."""
        indicators: List[SecurityIndicator] = []
        for rule in self.url_rules:
            match = rule.evaluate(evidence)
            if match:
                indicators.append(match)

        return aggregate_indicators(indicators)

    def evaluate_email(self, request: EmailAnalysisRequest) -> HeuristicFindings:
        """Evaluate an Email message against email rules."""
        indicators: List[SecurityIndicator] = []
        for rule in self.email_rules:
            match = rule.evaluate(request)
            if match:
                indicators.append(match)

        return aggregate_indicators(indicators)

    def evaluate_sms(self, request: SmsAnalysisRequest) -> HeuristicFindings:
        """Evaluate an SMS message against SMS rules."""
        indicators: List[SecurityIndicator] = []
        for rule in self.sms_rules:
            match = rule.evaluate(request)
            if match:
                indicators.append(match)

        return aggregate_indicators(indicators)
