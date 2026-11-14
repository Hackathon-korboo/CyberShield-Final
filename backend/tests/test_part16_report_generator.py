"""Fixture-based tests for Part 16: Final Risk Report Generator.

Covers all 10 required report fixtures specified in the Stage 4 roadmap.
"""

from datetime import datetime, timezone
import pytest

from backend.app.engines.ai.schemas import AiAnalysisResult
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
    DeterministicRiskAssessment,
    RiskClassification,
)
from backend.app.schemas.unified_report import ThreatIntelligenceSummary, UnifiedThreatReport
from backend.app.services.risk.report_generator import UnifiedReportGenerator


@pytest.fixture
def generator():
    return UnifiedReportGenerator()


def test_fixture_01_low_risk_report(generator):
    """Fixture 1: Low Risk unified threat report."""
    evidence_pkg = EvidencePackage(
        target="https://example.com/",
        target_type="url",
        findings=[],
        check_statuses={"URL_PATTERN": CheckStatus.COMPLETED, "DNS_INVESTIGATION": CheckStatus.COMPLETED},
    )
    assessment = DeterministicRiskAssessment(
        scan_id=evidence_pkg.scan_id,
        target=evidence_pkg.target,
        target_type=evidence_pkg.target_type,
        classification=RiskClassification.LOW_RISK,
        risk_score=0,
        summary="No significant threat indicators found.",
        explanation="Standard static analysis verified clean input.",
        supporting_evidence=["0 indicators found."],
        coverage_score=1.0,
        confidence_score=0.7,
    )

    report = generator.build_report(evidence_pkg, assessment)

    assert isinstance(report, UnifiedThreatReport)
    assert report.risk_assessment.classification == RiskClassification.LOW_RISK
    assert report.risk_assessment.risk_score == 0
    assert len(report.recommendations) > 0
    assert report.report_integrity.blockchain_status == "NOT_REGISTERED"
    assert len(report.report_integrity.canonical_sha256) == 64


def test_fixture_02_suspicious_report(generator):
    """Fixture 2: Suspicious unified threat report."""
    f = StandardizedFinding(
        finding_type=FindingType.URL_PATTERN,
        severity=FindingSeverity.MEDIUM,
        title="Suspicious Auth Keyword",
        description="Path contains /login",
        source="url_rules",
        related_indicators=["RULE-URL-003"],
    )
    evidence_pkg = EvidencePackage(
        target="https://example.com/login",
        target_type="url",
        findings=[f],
        check_statuses={"URL_PATTERN": CheckStatus.COMPLETED},
    )
    assessment = DeterministicRiskAssessment(
        scan_id=evidence_pkg.scan_id,
        target=evidence_pkg.target,
        target_type=evidence_pkg.target_type,
        classification=RiskClassification.SUSPICIOUS,
        risk_score=25,
        summary="Suspicious keywords detected in URL path.",
        explanation="Authentication keyword found.",
        supporting_evidence=["RULE-URL-003 triggered."],
        rules_triggered=["RULE-URL-003"],
        coverage_score=1.0,
        confidence_score=0.85,
    )

    report = generator.build_report(evidence_pkg, assessment)

    assert report.risk_assessment.classification == RiskClassification.SUSPICIOUS
    assert any("authentication details" in r.lower() for r in report.recommendations)


def test_fixture_03_high_risk_report(generator):
    """Fixture 3: High Risk unified threat report."""
    evidence_pkg = EvidencePackage(
        target="http://192.168.1.1/xn--apple.com",
        target_type="url",
        findings=[],
        check_statuses={"URL_PATTERN": CheckStatus.COMPLETED},
    )
    assessment = DeterministicRiskAssessment(
        scan_id=evidence_pkg.scan_id,
        target=evidence_pkg.target,
        target_type=evidence_pkg.target_type,
        classification=RiskClassification.HIGH_RISK,
        risk_score=70,
        summary="Multiple significant threat indicators detected.",
        explanation="IP literal hostname and punycode spoofing.",
        supporting_evidence=["RULE-URL-001", "RULE-URL-002"],
        rules_triggered=["RULE-URL-001", "RULE-URL-002"],
        coverage_score=1.0,
        confidence_score=0.85,
    )

    report = generator.build_report(evidence_pkg, assessment)

    assert report.risk_assessment.classification == RiskClassification.HIGH_RISK
    assert report.risk_assessment.risk_score >= 70
    assert any("terminate interaction" in r.lower() for r in report.recommendations)


def test_fixture_04_confirmed_malicious_authoritative(generator):
    """Fixture 4: Confirmed Malicious with authoritative threat intelligence validation."""
    evidence_pkg = EvidencePackage(
        target="http://confirmed-c2-malware.com/payload",
        target_type="url",
        findings=[],
        check_statuses={"THREAT_INTELLIGENCE": CheckStatus.COMPLETED},
    )
    assessment = DeterministicRiskAssessment(
        scan_id=evidence_pkg.scan_id,
        target=evidence_pkg.target,
        target_type=evidence_pkg.target_type,
        classification=RiskClassification.CONFIRMED_MALICIOUS,
        risk_score=100,
        summary="Authoritative threat intelligence match confirmed malicious target.",
        explanation="Target destination is confirmed malicious on authoritative threat intelligence blocklists.",
        supporting_evidence=["RULE-INTEL-001: Verified malware repository"],
        has_authoritative_match=True,
        has_policy_violation=False,
        rules_triggered=["RULE-INTEL-001"],
        coverage_score=1.0,
        confidence_score=1.0,
    )

    report = generator.build_report(evidence_pkg, assessment)

    assert report.risk_assessment.classification == RiskClassification.CONFIRMED_MALICIOUS
    assert report.risk_assessment.risk_score == 100
    assert report.risk_assessment.has_authoritative_match is True
    assert report.risk_assessment.has_policy_violation is False


def test_fixture_ssrf_policy_violation_report(generator):
    """Fixture for SSRF policy violation: HIGH_RISK, score 70, not CONFIRMED_MALICIOUS."""
    evidence_pkg = EvidencePackage(
        target="http://127.0.0.1:8000/internal",
        target_type="url",
        findings=[],
        check_statuses={"SSRF_GUARD": CheckStatus.COMPLETED},
    )
    assessment = DeterministicRiskAssessment(
        scan_id=evidence_pkg.scan_id,
        target=evidence_pkg.target,
        target_type=evidence_pkg.target_type,
        classification=RiskClassification.HIGH_RISK,
        risk_score=70,
        summary="Security policy violation detected: target destination is restricted by egress policy (Score: 70/100, HIGH_RISK).",
        explanation="Security inspection triggered rules: RULE-SSRF-001. Destination resolves to a prohibited loopback address. In accordance with security policy separation, an SSRF policy violation is classified as HIGH_RISK and does not independently establish external target maliciousness.",
        supporting_evidence=["RULE-SSRF-001: Loopback blocked"],
        has_policy_violation=True,
        has_authoritative_match=False,
        rules_triggered=["RULE-SSRF-001"],
        coverage_score=1.0,
        confidence_score=0.9,
    )

    report = generator.build_report(evidence_pkg, assessment)

    assert report.risk_assessment.classification == RiskClassification.HIGH_RISK
    assert report.risk_assessment.risk_score == 70
    assert report.risk_assessment.has_policy_violation is True
    assert report.risk_assessment.has_authoritative_match is False


def test_fixture_05_inconclusive_report(generator):
    """Fixture 5: Inconclusive threat report due to missing/failed checks."""
    evidence_pkg = EvidencePackage(
        target="https://unknown-host-fail.com/",
        target_type="url",
        findings=[],
        check_statuses={"DNS_INVESTIGATION": CheckStatus.FAILED},
    )
    assessment = DeterministicRiskAssessment(
        scan_id=evidence_pkg.scan_id,
        target=evidence_pkg.target,
        target_type=evidence_pkg.target_type,
        classification=RiskClassification.INCONCLUSIVE,
        risk_score=None,
        summary="Investigation inconclusive due to DNS failure.",
        explanation="DNS lookup failed; destination not reachable.",
        supporting_evidence=["DNS failure."],
        coverage_score=0.2,
        confidence_score=0.2,
    )

    report = generator.build_report(evidence_pkg, assessment)

    assert report.risk_assessment.classification == RiskClassification.INCONCLUSIVE
    assert report.risk_assessment.risk_score is None


def test_fixture_06_conflicting_evidence_report(generator):
    """Fixture 6: Conflicting evidence handling in report."""
    evidence_pkg = EvidencePackage(
        target="https://target-with-conflicts.com/",
        target_type="url",
        findings=[],
        check_statuses={"URL_PATTERN": CheckStatus.COMPLETED},
    )
    assessment = DeterministicRiskAssessment(
        scan_id=evidence_pkg.scan_id,
        target=evidence_pkg.target,
        target_type=evidence_pkg.target_type,
        classification=RiskClassification.SUSPICIOUS,
        risk_score=40,
        summary="Suspicious indicators detected despite benign structural profile.",
        explanation="Conflicting findings detected.",
        supporting_evidence=["Punycode detected alongside valid HTTPS."],
        has_conflicting_evidence=True,
        coverage_score=0.8,
        confidence_score=0.7,
    )

    report = generator.build_report(evidence_pkg, assessment)

    assert report.risk_assessment.has_conflicting_evidence is True


def test_fixture_07_partial_scan_report(generator):
    """Fixture 7: Partial scan report with explicit limitations."""
    evidence_pkg = EvidencePackage(
        target="https://example.com/",
        target_type="url",
        findings=[],
        check_statuses={
            "URL_PATTERN": CheckStatus.COMPLETED,
            "DNS_INVESTIGATION": CheckStatus.PARTIAL,
            "REDIRECT_ANALYSIS": CheckStatus.UNAVAILABLE,
        },
    )
    assessment = DeterministicRiskAssessment(
        scan_id=evidence_pkg.scan_id,
        target=evidence_pkg.target,
        target_type=evidence_pkg.target_type,
        classification=RiskClassification.LOW_RISK,
        risk_score=0,
        summary="Clean static check.",
        explanation="Completed available checks.",
        coverage_score=0.5,
        confidence_score=0.4,
    )

    report = generator.build_report(evidence_pkg, assessment)

    assert any("redirect tracing is disabled" in lim.lower() for lim in report.limitations)


def test_fixture_08_ai_provider_unavailable_report(generator):
    """Fixture 8: AI provider fallback report limitation."""
    evidence_pkg = EvidencePackage(
        target="https://example.com/",
        target_type="url",
        findings=[],
        check_statuses={"URL_PATTERN": CheckStatus.COMPLETED},
    )
    assessment = DeterministicRiskAssessment(
        scan_id=evidence_pkg.scan_id,
        target=evidence_pkg.target,
        target_type=evidence_pkg.target_type,
        classification=RiskClassification.LOW_RISK,
        risk_score=0,
        summary="Clean.",
        explanation="Clean.",
        coverage_score=1.0,
        confidence_score=0.7,
    )
    fallback_ai = AiAnalysisResult(
        summary="Fallback summary",
        explanation="Evaluated in local deterministic fallback mode.",
        supporting_evidence=[],
        ai_inferences=[],
        uncertainty_statement="Disclaimer",
        user_recommendations=[],
        provider="cybershield-deterministic-fallback",
        model="local-rule-synthesizer",
        status="FALLBACK_HEURISTIC_ONLY",
    )

    report = generator.build_report(evidence_pkg, assessment, ai_analysis=fallback_ai)

    assert any("fallback engine" in lim.lower() for lim in report.limitations)
    assert report.ai_analysis.provider == "cybershield-deterministic-fallback"


def test_fixture_09_threat_intelligence_unavailable_report(generator):
    """Fixture 9: Threat intelligence offline report."""
    evidence_pkg = EvidencePackage(
        target="https://example.com/",
        target_type="url",
        findings=[],
        check_statuses={"THREAT_INTELLIGENCE": CheckStatus.UNAVAILABLE},
    )
    assessment = DeterministicRiskAssessment(
        scan_id=evidence_pkg.scan_id,
        target=evidence_pkg.target,
        target_type=evidence_pkg.target_type,
        classification=RiskClassification.LOW_RISK,
        risk_score=0,
        summary="Clean.",
        explanation="Clean.",
        coverage_score=0.8,
        confidence_score=0.6,
    )

    intel = ThreatIntelligenceSummary(
        provider_name="offline_feed",
        status=CheckStatus.UNAVAILABLE,
        is_malicious=None,
        threat_types=[],
    )

    report = generator.build_report(evidence_pkg, assessment, threat_intel=intel)

    assert report.threat_intelligence.status == CheckStatus.UNAVAILABLE
    assert any("threat intelligence reputation feeds" in lim.lower() for lim in report.limitations)


def test_fixture_10_blockchain_not_configured_report(generator):
    """Fixture 10: Blockchain unconfigured report."""
    evidence_pkg = EvidencePackage(
        target="https://example.com/",
        target_type="url",
        findings=[],
        check_statuses={"URL_PATTERN": CheckStatus.COMPLETED},
    )
    assessment = DeterministicRiskAssessment(
        scan_id=evidence_pkg.scan_id,
        target=evidence_pkg.target,
        target_type=evidence_pkg.target_type,
        classification=RiskClassification.LOW_RISK,
        risk_score=0,
        summary="Clean.",
        explanation="Clean.",
        coverage_score=1.0,
        confidence_score=0.7,
    )

    report = generator.build_report(evidence_pkg, assessment)

    assert report.report_integrity.blockchain_status == "NOT_REGISTERED"
    assert report.report_integrity.contract_address is None
    assert report.report_integrity.transaction_hash is None
    assert any("blockchain anchoring is currently not_registered" in lim.lower() for lim in report.limitations)
