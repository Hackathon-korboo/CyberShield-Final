"""Unit tests for deterministic security rule catalog and indicator engine."""

import pytest
from backend.app.engines.rules.engine import (
    SecurityRuleEngine,
    aggregate_indicators,
    calculate_risk_level,
)
from backend.app.schemas.analysis import (
    IndicatorCategory,
    IndicatorSeverity,
    RiskLevel,
    SecurityIndicator,
    UrlObservedEvidence,
)
from backend.app.schemas.email import EmailAnalysisRequest
from backend.app.schemas.sms import SmsAnalysisRequest


@pytest.fixture
def rule_engine() -> SecurityRuleEngine:
    return SecurityRuleEngine()


def test_calculate_risk_level_tiers():
    """Verify standard risk score mapping."""
    assert calculate_risk_level(0) == RiskLevel.CLEAN
    assert calculate_risk_level(14) == RiskLevel.CLEAN
    assert calculate_risk_level(15) == RiskLevel.LOW_RISK
    assert calculate_risk_level(39) == RiskLevel.LOW_RISK
    assert calculate_risk_level(40) == RiskLevel.SUSPICIOUS
    assert calculate_risk_level(69) == RiskLevel.SUSPICIOUS
    assert calculate_risk_level(70) == RiskLevel.HIGH_RISK
    assert calculate_risk_level(100) == RiskLevel.HIGH_RISK


def test_url_rule_ip_hostname(rule_engine: SecurityRuleEngine):
    """Verify RULE-URL-001 triggers on direct IP."""
    evidence = UrlObservedEvidence(
        normalized_url="http://198.51.100.5/test",
        scheme="http",
        hostname="198.51.100.5",
        port=80,
        path="/test",
        resolved_ips=["198.51.100.5"],
    )
    findings = rule_engine.evaluate_url(evidence)
    rule_ids = [ind.rule_id for ind in findings.indicators]
    assert "RULE-URL-001" in rule_ids
    assert findings.risk_score >= 25


def test_url_rule_punycode(rule_engine: SecurityRuleEngine):
    """Verify RULE-URL-002 triggers on Punycode domain."""
    evidence = UrlObservedEvidence(
        normalized_url="https://xn--l-7sba6dbr.com/login",
        scheme="https",
        hostname="xn--l-7sba6dbr.com",
        port=443,
        path="/login",
    )
    findings = rule_engine.evaluate_url(evidence)
    rule_ids = [ind.rule_id for ind in findings.indicators]
    assert "RULE-URL-002" in rule_ids


def test_url_rule_suspicious_keywords(rule_engine: SecurityRuleEngine):
    """Verify RULE-URL-003 triggers on credential keywords."""
    evidence = UrlObservedEvidence(
        normalized_url="https://verify-banking-security.com/login",
        scheme="https",
        hostname="verify-banking-security.com",
        port=443,
        path="/login",
    )
    findings = rule_engine.evaluate_url(evidence)
    rule_ids = [ind.rule_id for ind in findings.indicators]
    assert "RULE-URL-003" in rule_ids


def test_email_rules_urgency_and_fraud(rule_engine: SecurityRuleEngine):
    """Verify email urgency and payment fraud detection."""
    req = EmailAnalysisRequest(
        subject="URGENT: Immediate action required",
        body="Your account is suspended. Pay the fine using an iTunes gift card immediately.",
    )
    findings = rule_engine.evaluate_email(req)
    rule_ids = [ind.rule_id for ind in findings.indicators]
    assert "RULE-EML-001" in rule_ids
    assert "RULE-EML-002" in rule_ids
    assert findings.risk_level in (RiskLevel.SUSPICIOUS, RiskLevel.HIGH_RISK)


def test_email_job_scam(rule_engine: SecurityRuleEngine):
    """Verify email job scam lure detection."""
    req = EmailAnalysisRequest(
        body="Congratulations! You can earn $500 per day with no experience needed from home.",
    )
    findings = rule_engine.evaluate_email(req)
    rule_ids = [ind.rule_id for ind in findings.indicators]
    assert "RULE-EML-003" in rule_ids


def test_sms_otp_extraction(rule_engine: SecurityRuleEngine):
    """Verify RULE-SMS-001 triggers on OTP extraction demand."""
    req = SmsAnalysisRequest(
        message="Please share your 6-digit verification code to unfreeze your bank account.",
    )
    findings = rule_engine.evaluate_sms(req)
    rule_ids = [ind.rule_id for ind in findings.indicators]
    assert "RULE-SMS-001" in rule_ids
    assert findings.indicators[0].severity == IndicatorSeverity.CRITICAL


def test_clean_input_returns_zero_score(rule_engine: SecurityRuleEngine):
    """Verify benign inputs produce clean evaluation."""
    evidence = UrlObservedEvidence(
        normalized_url="https://example.com/about",
        scheme="https",
        hostname="example.com",
        port=443,
        path="/about",
    )
    findings = rule_engine.evaluate_url(evidence)
    assert findings.risk_score == 0
    assert findings.risk_level == RiskLevel.CLEAN
    assert len(findings.indicators) == 0


def test_severity_floor_model_individual_tiers():
    """Verify minimum severity floors per Decision A:
    - No indicators -> 0, CLEAN
    - One LOW indicator -> minimum 5, LOW_RISK
    - One MEDIUM indicator -> minimum 15, LOW_RISK
    - One HIGH indicator -> minimum 40, SUSPICIOUS
    - One CRITICAL indicator -> minimum 70, HIGH_RISK
    """
    def _make_ind(rule_id: str, severity: IndicatorSeverity) -> SecurityIndicator:
        return SecurityIndicator(
            rule_id=rule_id,
            category=IndicatorCategory.SUSPICIOUS_KEYWORD,
            severity=severity,
            evidence="test-evidence",
            explanation="test-explanation",
            mitigation="test-mitigation",
        )

    # 1. No indicators
    res_none = aggregate_indicators([])
    assert res_none.risk_score == 0
    assert res_none.risk_level == RiskLevel.CLEAN

    # 2. One LOW indicator
    res_low = aggregate_indicators([_make_ind("RULE-01", IndicatorSeverity.LOW)])
    assert res_low.risk_score == 5
    assert res_low.risk_level == RiskLevel.LOW_RISK

    # 3. One MEDIUM indicator
    res_med = aggregate_indicators([_make_ind("RULE-02", IndicatorSeverity.MEDIUM)])
    assert res_med.risk_score == 15
    assert res_med.risk_level == RiskLevel.LOW_RISK

    # 4. One HIGH indicator
    res_high = aggregate_indicators([_make_ind("RULE-03", IndicatorSeverity.HIGH)])
    assert res_high.risk_score == 40
    assert res_high.risk_level == RiskLevel.SUSPICIOUS

    # 5. One CRITICAL indicator
    res_crit = aggregate_indicators([_make_ind("RULE-04", IndicatorSeverity.CRITICAL)])
    assert res_crit.risk_score == 70
    assert res_crit.risk_level == RiskLevel.HIGH_RISK


def test_severity_floor_model_multi_indicator_interaction():
    """Verify additive score and severity floor interactions:
    - 1 CRITICAL + 1 HIGH: additive 65, floor 70 -> 70, HIGH_RISK
    - 2 HIGH: additive 50, floor 40 -> 50, SUSPICIOUS
    - 3 HIGH: additive 75, floor 40 -> 75, HIGH_RISK
    - 3 CRITICAL: additive 120, capped at 100 -> 100, HIGH_RISK
    - 1 LOW + 1 CRITICAL: additive 45, floor 70 -> 70, HIGH_RISK
    """
    def _make_ind(rule_id: str, severity: IndicatorSeverity) -> SecurityIndicator:
        return SecurityIndicator(
            rule_id=rule_id,
            category=IndicatorCategory.SUSPICIOUS_KEYWORD,
            severity=severity,
            evidence="test-evidence",
            explanation="test-explanation",
            mitigation="test-mitigation",
        )

    # 1 CRITICAL + 1 HIGH
    res1 = aggregate_indicators([
        _make_ind("C1", IndicatorSeverity.CRITICAL),
        _make_ind("H1", IndicatorSeverity.HIGH),
    ])
    assert res1.risk_score == 70
    assert res1.risk_level == RiskLevel.HIGH_RISK

    # 2 HIGH
    res2 = aggregate_indicators([
        _make_ind("H1", IndicatorSeverity.HIGH),
        _make_ind("H2", IndicatorSeverity.HIGH),
    ])
    assert res2.risk_score == 50
    assert res2.risk_level == RiskLevel.SUSPICIOUS

    # 3 HIGH
    res3 = aggregate_indicators([
        _make_ind("H1", IndicatorSeverity.HIGH),
        _make_ind("H2", IndicatorSeverity.HIGH),
        _make_ind("H3", IndicatorSeverity.HIGH),
    ])
    assert res3.risk_score == 75
    assert res3.risk_level == RiskLevel.HIGH_RISK

    # 3 CRITICAL capped at 100
    res4 = aggregate_indicators([
        _make_ind("C1", IndicatorSeverity.CRITICAL),
        _make_ind("C2", IndicatorSeverity.CRITICAL),
        _make_ind("C3", IndicatorSeverity.CRITICAL),
    ])
    assert res4.risk_score == 100
    assert res4.risk_level == RiskLevel.HIGH_RISK

    # 1 LOW + 1 CRITICAL
    res5 = aggregate_indicators([
        _make_ind("L1", IndicatorSeverity.LOW),
        _make_ind("C1", IndicatorSeverity.CRITICAL),
    ])
    assert res5.risk_score == 70
    assert res5.risk_level == RiskLevel.HIGH_RISK


def test_sms_urgency_rule_positive_cases(rule_engine: SecurityRuleEngine):
    """Verify RULE-SMS-004 triggers on compound contextual smishing panic tactics."""
    positive_samples = [
        "URGENT: Verify your bank account immediately.",
        "Urgent: Reply with your OTP to avoid account suspension.",
        "Your account will be blocked unless you confirm your payment now.",
        "Immediate action required: share your verification code.",
        "urgent:   verify your bank account now.",
        "URGENT - Confirm your card now or access will be restricted.",
        "Final notice: Act now to verify your identity.",
        "URGENT: pay your unpaid bill immediately.",
    ]
    for msg in positive_samples:
        req = SmsAnalysisRequest(message=msg)
        findings = rule_engine.evaluate_sms(req)
        rule_ids = [ind.rule_id for ind in findings.indicators]
        assert "RULE-SMS-004" in rule_ids, f"Expected RULE-SMS-004 to trigger on: {msg}"
        ind = next(i for i in findings.indicators if i.rule_id == "RULE-SMS-004")
        assert ind.category == IndicatorCategory.URGENCY_LURE
        assert ind.severity == IndicatorSeverity.HIGH
        assert len(ind.evidence) > 0


def test_sms_urgency_rule_negative_cases(rule_engine: SecurityRuleEngine):
    """Verify RULE-SMS-004 does NOT trigger on legitimate messages or standalone 'urgent'."""
    negative_samples = [
        "Urgent medical appointment reminder.",
        "Urgent delivery notification: your parcel arrives today.",
        "Please read this urgent community announcement.",
        "This is urgent, please call me back.",
        "Just an urgent note about dinner tonight.",
        "Hi doctor, here is an urgent report.",
        "Reminder: tomorrow's meeting at 10 AM.",
    ]
    for msg in negative_samples:
        req = SmsAnalysisRequest(message=msg)
        findings = rule_engine.evaluate_sms(req)
        rule_ids = [ind.rule_id for ind in findings.indicators]
        assert "RULE-SMS-004" not in rule_ids, f"RULE-SMS-004 should NOT have triggered on: {msg}"


def test_sms_dual_trigger_otp_and_urgency(rule_engine: SecurityRuleEngine):
    """Verify SMS with both urgency and OTP triggers both RULE-SMS-001 and RULE-SMS-004."""
    req = SmsAnalysisRequest(
        message="Urgent: Reply with your OTP to avoid account suspension.",
    )
    findings = rule_engine.evaluate_sms(req)
    rule_ids = [ind.rule_id for ind in findings.indicators]
    assert "RULE-SMS-001" in rule_ids
    assert "RULE-SMS-004" in rule_ids
    assert findings.risk_score == 70  # CRITICAL floor applied (40 + 25 = 65 < 70)
    assert findings.risk_level == RiskLevel.HIGH_RISK

