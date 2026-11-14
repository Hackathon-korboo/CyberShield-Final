"""Unit tests for Phase 02 Pydantic schemas."""

import pytest
from pydantic import ValidationError

from backend.app.schemas.analysis import (
    HeuristicFindings,
    IndicatorCategory,
    IndicatorSeverity,
    RiskLevel,
    SecurityIndicator,
    SmsAnalysisResponse,
    SmsObservedEvidence,
    UrlAnalysisResponse,
    UrlObservedEvidence,
)
from backend.app.schemas.email import EmailAnalysisRequest
from backend.app.schemas.sms import SmsAnalysisRequest
from backend.app.schemas.url import UrlAnalysisRequest


def test_valid_url_analysis_request():
    """Verify that legitimate URLs parse cleanly."""
    req = UrlAnalysisRequest(url="https://example.com/login?param=1")
    assert req.url == "https://example.com/login?param=1"

    req_no_scheme = UrlAnalysisRequest(url="example.com/verify")
    assert req_no_scheme.url == "example.com/verify"


def test_invalid_url_analysis_request():
    """Verify invalid or forbidden URLs are rejected."""
    # Empty
    with pytest.raises(ValidationError):
        UrlAnalysisRequest(url="")

    # Whitespace only
    with pytest.raises(ValidationError):
        UrlAnalysisRequest(url="   ")

    # Unsupported scheme (ftp)
    with pytest.raises(ValidationError) as exc:
        UrlAnalysisRequest(url="ftp://malicious.com/file")
    assert "Unsupported URL scheme" in str(exc.value)

    # Control characters
    with pytest.raises(ValidationError) as exc:
        UrlAnalysisRequest(url="https://example.com\n/bad")
    assert "illegal control characters" in str(exc.value)

    # Extra fields forbidden
    with pytest.raises(ValidationError):
        UrlAnalysisRequest(url="https://example.com", extra_field="bad")  # type: ignore


def test_valid_email_analysis_request():
    """Verify valid email payload parsing."""
    req = EmailAnalysisRequest(
        subject="Important Account Notice",
        sender="service@bank.com",
        body="Please verify your email credentials.",
    )
    assert req.subject == "Important Account Notice"
    assert req.body == "Please verify your email credentials."


def test_invalid_email_analysis_request():
    """Verify email payload validation errors."""
    # Empty body
    with pytest.raises(ValidationError):
        EmailAnalysisRequest(body="   ")

    # Null byte in body
    with pytest.raises(ValidationError) as exc:
        EmailAnalysisRequest(body="Hello\x00World")
    assert "null bytes" in str(exc.value)


def test_valid_sms_analysis_request():
    """Verify valid SMS payload parsing."""
    req = SmsAnalysisRequest(sender="+1234567890", message="Your OTP is 123456.")
    assert req.message == "Your OTP is 123456."
    assert req.sender == "+1234567890"


def test_invalid_sms_analysis_request():
    """Verify SMS payload validation errors."""
    with pytest.raises(ValidationError):
        SmsAnalysisRequest(message="")


def test_security_indicator_schema():
    """Verify SecurityIndicator schema serialization."""
    ind = SecurityIndicator(
        rule_id="RULE-URL-001",
        category=IndicatorCategory.IP_HOST,
        severity=IndicatorSeverity.HIGH,
        evidence="192.0.2.1",
        explanation="Direct IP used instead of hostname.",
        mitigation="Avoid navigating directly to IP addresses.",
    )
    assert ind.rule_id == "RULE-URL-001"
    assert ind.severity == IndicatorSeverity.HIGH


def test_url_analysis_response_schema():
    """Verify end-to-end UrlAnalysisResponse serialization."""
    evidence = UrlObservedEvidence(
        normalized_url="https://example.com/test",
        scheme="https",
        hostname="example.com",
        port=443,
        path="/test",
        query=None,
        resolved_ips=["93.184.216.34"],
        is_ip_hostname=False,
        ssrf_safe=True,
        has_homoglyphs=False,
    )
    findings = HeuristicFindings(
        risk_level=RiskLevel.CLEAN,
        risk_score=0,
        indicators=[],
    )
    resp = UrlAnalysisResponse(
        target="https://example.com/test",
        observed_evidence=evidence,
        heuristic_findings=findings,
    )
    dumped = resp.model_dump()
    assert dumped["target"] == "https://example.com/test"
    assert dumped["heuristic_findings"]["risk_level"] == "CLEAN"
    assert dumped["status"] == "COMPLETED"


def test_email_body_length_boundary():
    """Verify email body max length is strictly 50,000 characters."""
    # 50,000 characters should pass
    req_valid = EmailAnalysisRequest(body="A" * 50000)
    assert len(req_valid.body) == 50000

    # 50,001 characters should raise ValidationError
    with pytest.raises(ValidationError):
        EmailAnalysisRequest(body="A" * 50001)


def test_sms_message_length_boundary():
    """Verify SMS message max length is strictly 2,000 characters."""
    # 2,000 characters should pass
    req_valid = SmsAnalysisRequest(message="A" * 2000)
    assert len(req_valid.message) == 2000

    # 2,001 characters should raise ValidationError
    with pytest.raises(ValidationError):
        SmsAnalysisRequest(message="A" * 2001)


def test_response_utc_timezone_awareness():
    """Verify response models generate timezone-aware UTC timestamps with explicit Z notation."""
    evidence = UrlObservedEvidence(
        normalized_url="https://example.com",
        scheme="https",
        hostname="example.com",
        port=443,
        path="",
    )
    findings = HeuristicFindings(
        risk_level=RiskLevel.CLEAN,
        risk_score=0,
    )
    resp = UrlAnalysisResponse(
        target="https://example.com",
        observed_evidence=evidence,
        heuristic_findings=findings,
    )
    # 1. Must be timezone-aware (tzinfo is not None)
    assert resp.timestamp.tzinfo is not None

    # 2. JSON serialization must contain ISO 8601 UTC designator (Z)
    json_data = resp.model_dump_json()
    assert '"timestamp":' in json_data
    dumped_dict = resp.model_dump(mode="json")
    assert dumped_dict["timestamp"].endswith("Z") or "+00:00" in dumped_dict["timestamp"]

