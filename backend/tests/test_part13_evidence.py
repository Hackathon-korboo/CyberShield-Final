"""Tests for Part 13: Evidence Collection & Standardization."""

from datetime import datetime, timezone
import pytest

from backend.app.schemas.analysis import (
    HeuristicFindings,
    IndicatorCategory,
    IndicatorSeverity,
    RiskLevel,
    SecurityIndicator,
    UrlAnalysisResponse,
    UrlObservedEvidence,
)
from backend.app.schemas.composite import CompositeUrlAnalysisResponse
from backend.app.engines.ai.schemas import AiAnalysisResult
from backend.app.schemas.evidence import (
    CheckStatus,
    FindingSeverity,
    FindingType,
    StandardizedFinding,
)
from backend.app.services.risk.evidence_normalizer import (
    EvidenceNormalizer,
    redact_sensitive_query_string,
)


def test_sensitive_value_redaction_in_url():
    """Verify that credentials, tokens, and api_keys in URLs are redacted."""
    raw_url = "https://example.com/api?token=secret12345&user=alice&api_key=XYZ987"
    redacted = redact_sensitive_query_string(raw_url)

    assert "secret12345" not in redacted
    assert "XYZ987" not in redacted
    assert "token=%5BREDACTED%5D" in redacted or "token=[REDACTED]" in redacted
    assert "api_key=%5BREDACTED%5D" in redacted or "api_key=[REDACTED]" in redacted
    assert "user=alice" in redacted


def test_sensitive_value_redaction_standalone_query():
    """Verify that credentials in standalone query strings are redacted."""
    raw_query = "password=SuperSecretPassword&session=sess_999&mode=fast"
    redacted = redact_sensitive_query_string(raw_query)

    assert "SuperSecretPassword" not in redacted
    assert "password=%5BREDACTED%5D" in redacted or "password=[REDACTED]" in redacted
    assert "session=%5BREDACTED%5D" in redacted or "session=[REDACTED]" in redacted
    assert "mode=fast" in redacted


def test_url_finding_normalization_benign():
    """Verify normalization of benign URL analysis output."""
    normalizer = EvidenceNormalizer()

    observed = UrlObservedEvidence(
        normalized_url="https://example.com/",
        scheme="https",
        hostname="example.com",
        port=443,
        path="/",
        resolved_ips=["93.184.216.34"],
        is_ip_hostname=False,
        ssrf_safe=True,
        has_homoglyphs=False,
    )
    heuristic = HeuristicFindings(
        risk_level=RiskLevel.CLEAN,
        risk_score=0,
        indicators=[],
    )
    url_resp = UrlAnalysisResponse(
        target="https://example.com/",
        observed_evidence=observed,
        heuristic_findings=heuristic,
    )

    package = normalizer.normalize_url_response(url_resp)

    assert package.target == "https://example.com/"
    assert package.target_type == "url"
    assert package.check_statuses["URL_PATTERN"] == CheckStatus.COMPLETED
    assert package.check_statuses["DNS_INVESTIGATION"] == CheckStatus.COMPLETED
    assert package.check_statuses["REDIRECT_ANALYSIS"] == CheckStatus.UNAVAILABLE
    assert package.check_statuses["THREAT_INTELLIGENCE"] == CheckStatus.UNAVAILABLE

    # DNS finding should be present
    dns_findings = [f for f in package.findings if f.finding_type == FindingType.DNS_INVESTIGATION]
    assert len(dns_findings) == 1
    assert "93.184.216.34" in dns_findings[0].observed_evidence["resolved_ips"]


def test_url_finding_normalization_threats_and_ssrf():
    """Verify normalization of malicious/SSRF indicators."""
    normalizer = EvidenceNormalizer()

    observed = UrlObservedEvidence(
        normalized_url="http://127.0.0.1:8000/admin",
        scheme="http",
        hostname="127.0.0.1",
        port=8000,
        path="/admin",
        resolved_ips=["127.0.0.1"],
        is_ip_hostname=True,
        ssrf_safe=False,
        has_homoglyphs=False,
    )
    indicator = SecurityIndicator(
        rule_id="RULE-SSRF-001",
        category=IndicatorCategory.SSRF_ATTEMPT,
        severity=IndicatorSeverity.CRITICAL,
        evidence="Blocked destination: 127.0.0.1",
        explanation="Loopback IP prohibited.",
        mitigation="Do not access loopback.",
    )
    heuristic = HeuristicFindings(
        risk_level=RiskLevel.HIGH_RISK,
        risk_score=70,
        indicators=[indicator],
    )
    url_resp = UrlAnalysisResponse(
        target="http://127.0.0.1:8000/admin",
        observed_evidence=observed,
        heuristic_findings=heuristic,
    )

    package = normalizer.normalize_url_response(url_resp)

    ssrf_findings = [f for f in package.findings if f.finding_type == FindingType.SSRF_GUARD]
    assert len(ssrf_findings) >= 1
    assert ssrf_findings[0].severity == FindingSeverity.CRITICAL

    ip_findings = [f for f in package.findings if f.title == "Direct IP Address Hostname"]
    assert len(ip_findings) == 1
    assert ip_findings[0].severity == FindingSeverity.HIGH


def test_ai_inference_separation():
    """Verify that AI analysis is normalized strictly as AI_INFERENCE finding."""
    normalizer = EvidenceNormalizer()

    observed = UrlObservedEvidence(
        normalized_url="https://secure-login.com/",
        scheme="https",
        hostname="secure-login.com",
        port=443,
        path="/",
        resolved_ips=["1.2.3.4"],
    )
    heuristic = HeuristicFindings(risk_level=RiskLevel.CLEAN, risk_score=0, indicators=[])
    ai_result = AiAnalysisResult(
        summary="Potential phishing site imitating financial portal.",
        explanation="Detailed AI analysis indicating suspicious domain naming.",
        supporting_evidence=["Suspicious keywords in domain"],
        ai_inferences=["Deceptive intent likely"],
        uncertainty_statement="Probabilistic assessment.",
        user_recommendations=["Verify independently"],
        provider="google-gemini",
        model="gemini-1.5-flash",
        status="COMPLETED",
    )
    composite_resp = CompositeUrlAnalysisResponse(
        target="https://secure-login.com/",
        observed_evidence=observed,
        heuristic_findings=heuristic,
        ai_analysis=ai_result,
    )

    package = normalizer.normalize_url_response(composite_resp)

    ai_findings = [f for f in package.findings if f.finding_type == FindingType.AI_INFERENCE]
    assert len(ai_findings) == 1
    assert ai_findings[0].metadata["is_probabilistic"] is True
    assert ai_findings[0].source == "ai_provider_google-gemini"
    assert "Potential phishing" in ai_findings[0].description


def test_deduplication_and_merging_of_findings():
    """Verify that duplicate findings are deduplicated with merged sources in metadata."""
    normalizer = EvidenceNormalizer()

    f1 = StandardizedFinding(
        finding_type=FindingType.URL_PATTERN,
        severity=FindingSeverity.HIGH,
        title="Direct IP Literal",
        description="Raw IP host.",
        source="engine_a",
        related_indicators=["RULE-URL-001"],
    )
    f2 = StandardizedFinding(
        finding_type=FindingType.URL_PATTERN,
        severity=FindingSeverity.HIGH,
        title="Direct IP Literal",
        description="Raw IP host.",
        source="engine_b",
        related_indicators=["RULE-URL-001"],
    )

    deduped = normalizer.deduplicate_findings([f1, f2])
    assert len(deduped) == 1
    assert "engine_a" in deduped[0].metadata["merged_sources"]
    assert "engine_b" in deduped[0].metadata["merged_sources"]


def test_conflicting_evidence_tagging():
    """Verify that conflicting evidence is preserved and explicitly tagged."""
    normalizer = EvidenceNormalizer()

    f_good = StandardizedFinding(
        finding_type=FindingType.DNS_INVESTIGATION,
        severity=FindingSeverity.INFORMATIONAL,
        title="DNS Preflight Resolution",
        description="Resolved cleanly.",
        source="dns_resolver",
        source_status=CheckStatus.COMPLETED,
    )
    f_bad = StandardizedFinding(
        finding_type=FindingType.SSRF_GUARD,
        severity=FindingSeverity.CRITICAL,
        title="SSRF Violation",
        description="Loopback detected.",
        source="ssrf_guard",
        source_status=CheckStatus.COMPLETED,
    )

    tagged = normalizer.identify_conflicting_evidence([f_good, f_bad])
    assert len(tagged) == 2
    assert tagged[0].metadata.get("has_conflicting_evidence") is True
    assert tagged[1].metadata.get("has_conflicting_evidence") is True
