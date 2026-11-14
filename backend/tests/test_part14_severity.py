"""Tests for Part 14: Severity & Indicator Classification."""

import pytest

from backend.app.schemas.evidence import (
    CheckStatus,
    EvidencePackage,
    FindingSeverity,
    FindingType,
    StandardizedFinding,
)
from backend.app.schemas.risk import AuthorityCategory
from backend.app.services.risk.severity_classifier import SeverityClassifier


def test_authoritative_ssrf_classification():
    """Verify that SSRF violations are classified as POLICY_VIOLATION and CRITICAL."""
    classifier = SeverityClassifier()
    finding = StandardizedFinding(
        finding_type=FindingType.SSRF_GUARD,
        severity=FindingSeverity.CRITICAL,
        title="SSRF Violation: Restricted Destination",
        description="Loopback blocked.",
        source="ssrf_guard",
        source_status=CheckStatus.COMPLETED,
        related_indicators=["RULE-SSRF-001"],
    )

    classified = classifier.classify_finding(finding)

    assert classified.authority == AuthorityCategory.POLICY_VIOLATION
    assert classified.is_authoritative is False
    assert classified.is_policy_violation is True
    assert classified.severity == FindingSeverity.CRITICAL
    assert "policy violation" in classified.severity_basis.lower()


def test_authoritative_threat_intel_classification():
    """Verify that confirmed threat intelligence matches are classified as AUTHORITATIVE and CRITICAL."""
    classifier = SeverityClassifier()
    finding = StandardizedFinding(
        finding_type=FindingType.THREAT_INTELLIGENCE,
        severity=FindingSeverity.CRITICAL,
        title="Authoritative Malicious Intelligence Match",
        description="Target listed on known malware blocklist.",
        source="threat_intel_blocklist",
        source_status=CheckStatus.COMPLETED,
        related_indicators=["RULE-INTEL-001"],
        metadata={"is_malicious": True},
    )

    classified = classifier.classify_finding(finding)

    assert classified.authority == AuthorityCategory.AUTHORITATIVE
    assert classified.is_authoritative is True
    assert classified.is_policy_violation is False
    assert classified.severity == FindingSeverity.CRITICAL
    assert "authoritative" in classified.severity_basis.lower()


def test_heuristic_indicator_classification():
    """Verify that heuristic rules are classified as HEURISTIC and not authoritative."""
    classifier = SeverityClassifier()
    finding = StandardizedFinding(
        finding_type=FindingType.URL_PATTERN,
        severity=FindingSeverity.HIGH,
        title="Direct IP Address Hostname",
        description="Raw IP host.",
        source="url_structure_inspector",
        source_status=CheckStatus.COMPLETED,
        related_indicators=["RULE-URL-001"],
    )

    classified = classifier.classify_finding(finding)

    assert classified.authority == AuthorityCategory.HEURISTIC
    assert classified.is_authoritative is False
    assert classified.correlation_group == "CORR-IP-DESTINATION"


def test_ai_inference_authority_is_never_authoritative():
    """Verify that AI analysis is strictly classified as HEURISTIC/probabilistic, never authoritative."""
    classifier = SeverityClassifier()
    finding = StandardizedFinding(
        finding_type=FindingType.AI_INFERENCE,
        severity=FindingSeverity.INFORMATIONAL,
        title="AI Phishing Analysis",
        description="Model predicts high likelihood of fraud.",
        source="ai_provider_gemini",
        source_status=CheckStatus.COMPLETED,
    )

    classified = classifier.classify_finding(finding)

    assert classified.authority == AuthorityCategory.HEURISTIC
    assert classified.is_authoritative is False
    assert "probabilistic" in classified.severity_basis.lower()


def test_unavailable_check_classified_as_inconclusive():
    """Verify that an unavailable check is marked INCONCLUSIVE and never as clean/proof of safety."""
    classifier = SeverityClassifier()
    finding = StandardizedFinding(
        finding_type=FindingType.REDIRECT_ANALYSIS,
        severity=FindingSeverity.INFORMATIONAL,
        title="Redirect Analysis Unavailable",
        description="Redirect tracking disabled in static mode.",
        source="redirect_tracer",
        source_status=CheckStatus.UNAVAILABLE,
    )

    classified = classifier.classify_finding(finding)

    assert classified.authority == AuthorityCategory.INCONCLUSIVE
    assert classified.is_authoritative is False
    assert "not proof of safety" in classified.severity_basis.lower()


def test_correlated_indicators_grouped():
    """Verify that multiple indicators sharing a root cause are assigned correlation groups."""
    classifier = SeverityClassifier()

    f1 = StandardizedFinding(
        finding_type=FindingType.EMAIL_PATTERN,
        severity=FindingSeverity.HIGH,
        title="Urgency Pattern 1",
        description="Immediate action requested.",
        source="email_inspector",
        related_indicators=["RULE-EML-001"],
    )
    f2 = StandardizedFinding(
        finding_type=FindingType.SMS_PATTERN,
        severity=FindingSeverity.HIGH,
        title="Urgency Pattern 2",
        description="Urgent account alert.",
        source="sms_inspector",
        related_indicators=["RULE-SMS-004"],
    )

    pkg = EvidencePackage(
        target="test-subject",
        target_type="email",
        findings=[f1, f2],
        check_statuses={"EMAIL_PATTERN": CheckStatus.COMPLETED, "SMS_PATTERN": CheckStatus.COMPLETED},
    )

    res = classifier.classify_evidence_package(pkg)
    assert "CORR-URGENCY" in res.correlation_groups_detected
    assert res.classified_indicators[0].correlation_group == "CORR-URGENCY"
    assert res.classified_indicators[1].correlation_group == "CORR-URGENCY"


def test_coverage_and_confidence_calculation():
    """Verify that coverage and confidence accurately penalize unavailable/failed checks."""
    classifier = SeverityClassifier()

    statuses = {
        "URL_PATTERN": CheckStatus.COMPLETED,
        "DNS_INVESTIGATION": CheckStatus.COMPLETED,
        "SSRF_GUARD": CheckStatus.COMPLETED,
        "REDIRECT_ANALYSIS": CheckStatus.UNAVAILABLE,
        "THREAT_INTELLIGENCE": CheckStatus.UNAVAILABLE,
    }

    coverage = classifier.calculate_coverage(statuses)
    # 3 completed out of 5 applicable = 0.60
    assert coverage == 0.60

    confidence = classifier.calculate_confidence(coverage, [], statuses)
    # Coverage 0.60 * 0.70 = 0.42, minus unavailable penalty (2 * 0.05 = 0.10) = 0.32
    assert 0.20 <= confidence <= 0.50
