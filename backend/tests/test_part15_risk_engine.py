"""Tests for Part 15: Deterministic Risk Engine.

Covers all 12 required test scenarios specified in the Stage 4 roadmap.
"""

import pytest

from backend.app.schemas.evidence import (
    CheckStatus,
    EvidencePackage,
    FindingSeverity,
    FindingType,
    StandardizedFinding,
)
from backend.app.schemas.risk import (
    AuthorityCategory,
    ClassificationPackage,
    ClassifiedIndicator,
    RiskClassification,
)
from backend.app.services.risk.deterministic_engine import DeterministicRiskEngine
from backend.app.services.risk.severity_classifier import SeverityClassifier


@pytest.fixture
def classifier():
    return SeverityClassifier()


@pytest.fixture
def risk_engine():
    return DeterministicRiskEngine()


def test_scenario_01_benign_input_completed_checks(classifier, risk_engine):
    """Scenario 1: Benign input with completed checks yields LOW_RISK with 0 score."""
    pkg = EvidencePackage(
        target="https://example.com/",
        target_type="url",
        findings=[],
        check_statuses={"URL_PATTERN": CheckStatus.COMPLETED, "DNS_INVESTIGATION": CheckStatus.COMPLETED},
    )
    class_pkg = classifier.classify_evidence_package(pkg)
    assessment = risk_engine.evaluate(pkg, class_pkg)

    assert assessment.classification == RiskClassification.LOW_RISK
    assert assessment.risk_score == 0
    assert "No significant malicious indicators" in assessment.summary


def test_scenario_02_suspicious_url_indicators(classifier, risk_engine):
    """Scenario 2: Single suspicious URL indicator yields SUSPICIOUS tier."""
    f = StandardizedFinding(
        finding_type=FindingType.URL_PATTERN,
        severity=FindingSeverity.MEDIUM,
        title="Suspicious Auth Keyword",
        description="Path contains /login",
        source="url_rules",
        related_indicators=["RULE-URL-003"],
    )
    pkg = EvidencePackage(
        target="https://example.com/login",
        target_type="url",
        findings=[f],
        check_statuses={"URL_PATTERN": CheckStatus.COMPLETED},
    )
    class_pkg = classifier.classify_evidence_package(pkg)
    assessment = risk_engine.evaluate(pkg, class_pkg)

    assert assessment.classification == RiskClassification.SUSPICIOUS
    assert assessment.risk_score >= 15


def test_scenario_03_multiple_significant_indicators(classifier, risk_engine):
    """Scenario 3: Multiple significant indicators yield HIGH_RISK."""
    f1 = StandardizedFinding(
        finding_type=FindingType.URL_PATTERN,
        severity=FindingSeverity.HIGH,
        title="Direct IP Literal",
        description="Raw IP host.",
        source="url_rules",
        related_indicators=["RULE-URL-001"],
    )
    f2 = StandardizedFinding(
        finding_type=FindingType.URL_PATTERN,
        severity=FindingSeverity.HIGH,
        title="Punycode Homoglyph",
        description="xn-- brand spoofing.",
        source="url_rules",
        related_indicators=["RULE-URL-002"],
    )
    pkg = EvidencePackage(
        target="http://192.168.1.1/xn--apple.com",
        target_type="url",
        findings=[f1, f2],
        check_statuses={"URL_PATTERN": CheckStatus.COMPLETED},
    )
    class_pkg = classifier.classify_evidence_package(pkg)
    assessment = risk_engine.evaluate(pkg, class_pkg)

    assert assessment.classification == RiskClassification.HIGH_RISK
    assert assessment.risk_score >= 70


def test_scenario_04_authoritative_malicious_match(classifier, risk_engine):
    """Scenario 4: Authoritative threat intel match yields CONFIRMED_MALICIOUS with 100 score."""
    f = StandardizedFinding(
        finding_type=FindingType.THREAT_INTELLIGENCE,
        severity=FindingSeverity.CRITICAL,
        title="Authoritative Threat Intelligence Match",
        description="Target destination confirmed malicious on threat intelligence blocklist.",
        source="threat_intel_service",
        related_indicators=["RULE-INTEL-001"],
        metadata={"is_malicious": True},
    )
    pkg = EvidencePackage(
        target="http://malicious-confirmed-c2.com/",
        target_type="url",
        findings=[f],
        check_statuses={"THREAT_INTELLIGENCE": CheckStatus.COMPLETED},
    )
    class_pkg = classifier.classify_evidence_package(pkg)
    assessment = risk_engine.evaluate(pkg, class_pkg)

    assert assessment.classification == RiskClassification.CONFIRMED_MALICIOUS
    assert assessment.risk_score == 100
    assert assessment.has_authoritative_match is True
    assert assessment.has_policy_violation is False


def test_scenario_ssrf_policy_violation_yields_high_risk_not_confirmed_malicious(classifier, risk_engine):
    """Verify that SSRF policy violation yields HIGH_RISK (score 70) and never CONFIRMED_MALICIOUS."""
    f = StandardizedFinding(
        finding_type=FindingType.SSRF_GUARD,
        severity=FindingSeverity.CRITICAL,
        title="SSRF Violation: Restricted Destination",
        description="Destination resolves to loopback.",
        source="ssrf_guard",
        related_indicators=["RULE-SSRF-001"],
    )
    pkg = EvidencePackage(
        target="http://127.0.0.1:8000/admin",
        target_type="url",
        findings=[f],
        check_statuses={"SSRF_GUARD": CheckStatus.COMPLETED},
    )
    class_pkg = classifier.classify_evidence_package(pkg)
    assessment = risk_engine.evaluate(pkg, class_pkg)

    assert assessment.classification == RiskClassification.HIGH_RISK
    assert assessment.classification != RiskClassification.CONFIRMED_MALICIOUS
    assert assessment.risk_score == 70
    assert assessment.has_policy_violation is True
    assert assessment.has_authoritative_match is False
    assert "policy violation" in assessment.summary.lower()


def test_scenario_05_missing_or_unavailable_checks(classifier, risk_engine):
    """Scenario 5: Missing or unavailable checks are recorded in coverage and do not crash."""
    pkg = EvidencePackage(
        target="https://example.com/",
        target_type="url",
        findings=[],
        check_statuses={
            "URL_PATTERN": CheckStatus.COMPLETED,
            "REDIRECT_ANALYSIS": CheckStatus.UNAVAILABLE,
            "THREAT_INTELLIGENCE": CheckStatus.UNAVAILABLE,
        },
    )
    class_pkg = classifier.classify_evidence_package(pkg)
    assessment = risk_engine.evaluate(pkg, class_pkg)

    assert assessment.classification == RiskClassification.LOW_RISK
    assert assessment.coverage_score < 1.0


def test_scenario_06_dns_failure_returns_inconclusive(classifier, risk_engine):
    """Scenario 6: DNS resolution failure returns INCONCLUSIVE with null risk_score."""
    f = StandardizedFinding(
        finding_type=FindingType.DNS_INVESTIGATION,
        severity=FindingSeverity.LOW,
        title="Unresolved Hostname",
        description="DNS failed.",
        source="dns_resolver",
        source_status=CheckStatus.FAILED,
    )
    pkg = EvidencePackage(
        target="https://non-existent-domain-xyz987123.com/",
        target_type="url",
        findings=[f],
        check_statuses={"DNS_INVESTIGATION": CheckStatus.FAILED},
    )
    class_pkg = classifier.classify_evidence_package(pkg)
    assessment = risk_engine.evaluate(pkg, class_pkg)

    assert assessment.classification == RiskClassification.INCONCLUSIVE
    assert assessment.risk_score is None
    assert "DNS" in assessment.summary


def test_scenario_07_conflicting_evidence_handled_conservatively(classifier, risk_engine):
    """Scenario 7: Conflicting evidence is tagged and handled conservatively."""
    f1 = StandardizedFinding(
        finding_type=FindingType.DNS_INVESTIGATION,
        severity=FindingSeverity.INFORMATIONAL,
        title="DNS Preflight Resolution",
        description="Clean IP resolved.",
        source="dns_resolver",
        source_status=CheckStatus.COMPLETED,
        metadata={"has_conflicting_evidence": True},
    )
    f2 = StandardizedFinding(
        finding_type=FindingType.URL_PATTERN,
        severity=FindingSeverity.HIGH,
        title="Punycode Spoofing",
        description="Homoglyph detected.",
        source="url_rules",
        related_indicators=["RULE-URL-002"],
        metadata={"has_conflicting_evidence": True},
    )
    pkg = EvidencePackage(
        target="https://xn--appl-43d.com/",
        target_type="url",
        findings=[f1, f2],
        check_statuses={"URL_PATTERN": CheckStatus.COMPLETED, "DNS_INVESTIGATION": CheckStatus.COMPLETED},
    )
    class_pkg = classifier.classify_evidence_package(pkg)
    assessment = risk_engine.evaluate(pkg, class_pkg)

    assert assessment.has_conflicting_evidence is True
    assert assessment.risk_score >= 40
    assert "Conflicting" in assessment.explanation


def test_scenario_08_duplicate_indicators_do_not_inflate_score(classifier, risk_engine):
    """Scenario 8: Duplicate indicators are merged and do not inflate score."""
    f = StandardizedFinding(
        finding_type=FindingType.URL_PATTERN,
        severity=FindingSeverity.HIGH,
        title="Direct IP Literal",
        description="Raw IP host.",
        source="url_rules",
        related_indicators=["RULE-URL-001"],
    )
    pkg = EvidencePackage(
        target="http://192.168.1.1/",
        target_type="url",
        findings=[f],
        check_statuses={"URL_PATTERN": CheckStatus.COMPLETED},
    )
    class_pkg = classifier.classify_evidence_package(pkg)
    assessment = risk_engine.evaluate(pkg, class_pkg)

    assert assessment.risk_score == 40  # Single HIGH indicator floor


def test_scenario_09_correlated_evidence_prevents_double_counting(classifier, risk_engine):
    """Scenario 9: Multiple correlated urgency indicators contribute once to score."""
    f1 = StandardizedFinding(
        finding_type=FindingType.EMAIL_PATTERN,
        severity=FindingSeverity.HIGH,
        title="Urgent Lure",
        description="Action required.",
        source="email_rules",
        related_indicators=["RULE-EML-001"],
    )
    f2 = StandardizedFinding(
        finding_type=FindingType.SMS_PATTERN,
        severity=FindingSeverity.HIGH,
        title="Urgent Alert",
        description="Urgent account alert.",
        source="sms_rules",
        related_indicators=["RULE-SMS-004"],
    )
    pkg = EvidencePackage(
        target="Alert Message",
        target_type="email",
        findings=[f1, f2],
        check_statuses={"EMAIL_PATTERN": CheckStatus.COMPLETED, "SMS_PATTERN": CheckStatus.COMPLETED},
    )
    class_pkg = classifier.classify_evidence_package(pkg)
    assessment = risk_engine.evaluate(pkg, class_pkg)

    # Both share CORR-URGENCY. Instead of 25 + 25 = 50, the group contributes 25 -> floor 40
    assert assessment.risk_score == 40
    assert "CORR-URGENCY" in assessment.correlation_groups


def test_scenario_10_ai_only_prediction_never_confirmed_malicious(classifier, risk_engine):
    """Scenario 10: AI-only prediction cannot produce CONFIRMED_MALICIOUS (caps at SUSPICIOUS)."""
    f = StandardizedFinding(
        finding_type=FindingType.AI_INFERENCE,
        severity=FindingSeverity.HIGH,
        title="AI Threat Inference",
        description="AI model predicts dangerous phishing.",
        source="ai_provider_gemini",
        metadata={"is_ai": True},
    )
    pkg = EvidencePackage(
        target="https://example.com/test",
        target_type="url",
        findings=[f],
        check_statuses={"AI_INFERENCE": CheckStatus.COMPLETED},
    )
    class_pkg = classifier.classify_evidence_package(pkg)
    assessment = risk_engine.evaluate(pkg, class_pkg)

    assert assessment.classification != RiskClassification.CONFIRMED_MALICIOUS
    assert assessment.classification == RiskClassification.SUSPICIOUS
    assert assessment.risk_score <= 40


def test_scenario_11_valid_https_does_not_override_suspicious_indicators(classifier, risk_engine):
    """Scenario 11: Valid HTTPS transport does not neutralize suspicious indicators."""
    f1 = StandardizedFinding(
        finding_type=FindingType.URL_PATTERN,
        severity=FindingSeverity.INFORMATIONAL,
        title="HTTPS Scheme",
        description="Target uses HTTPS.",
        source="url_rules",
    )
    f2 = StandardizedFinding(
        finding_type=FindingType.URL_PATTERN,
        severity=FindingSeverity.HIGH,
        title="Punycode Homoglyph",
        description="Homoglyph brand spoofing.",
        source="url_rules",
        related_indicators=["RULE-URL-002"],
    )
    pkg = EvidencePackage(
        target="https://xn--paypal-94a.com/",
        target_type="url",
        findings=[f1, f2],
        check_statuses={"URL_PATTERN": CheckStatus.COMPLETED},
    )
    class_pkg = classifier.classify_evidence_package(pkg)
    assessment = risk_engine.evaluate(pkg, class_pkg)

    assert assessment.classification in (RiskClassification.SUSPICIOUS, RiskClassification.HIGH_RISK)
    assert assessment.risk_score >= 40


def test_scenario_12_no_threat_intel_match_with_incomplete_checks(classifier, risk_engine):
    """Scenario 12: Threat intelligence offline/no-match does not claim proof of safety."""
    f = StandardizedFinding(
        finding_type=FindingType.THREAT_INTELLIGENCE,
        severity=FindingSeverity.INFORMATIONAL,
        title="Threat Intel Unavailable",
        description="No threat intel available.",
        source="threat_intel_service",
        source_status=CheckStatus.UNAVAILABLE,
    )
    pkg = EvidencePackage(
        target="https://example.com/",
        target_type="url",
        findings=[f],
        check_statuses={"URL_PATTERN": CheckStatus.COMPLETED, "THREAT_INTELLIGENCE": CheckStatus.UNAVAILABLE},
    )
    class_pkg = classifier.classify_evidence_package(pkg)
    assessment = risk_engine.evaluate(pkg, class_pkg)

    assert assessment.classification == RiskClassification.LOW_RISK
    assert "does not prove the website is safe" in assessment.explanation
