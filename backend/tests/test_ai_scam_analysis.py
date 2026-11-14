"""Unit and integration tests for Part 11: AI-Based Scam Analysis & Explanation.

Tests URL, Email, and SMS reasoning prompts, structured output extraction,
markdown fence stripping, and tripartite evidence separation.
"""

import json
import pytest

from backend.app.engines.ai.analyzer import AIThreatAnalyzer, clean_llm_json_response
from backend.app.engines.ai.exceptions import AIValidationError
from backend.app.engines.ai.mock_provider import MockAIProvider
from backend.app.engines.ai.schemas import AiAnalysisResult


@pytest.mark.asyncio
async def test_url_scam_analysis_phishing():
    """Test URL threat reasoning with suspicious credential harvesting path."""
    expected_response = {
        "summary": "Suspicious URL mimicking a bank authentication page with suspicious path tokens.",
        "explanation": "The URL path '/login-verify' combined with an unverified domain pattern strongly suggests a credential harvesting portal.",
        "supporting_evidence": ["Rule RULE-URL-002 triggered", "Path component contains 'login-verify'"],
        "ai_inferences": ["Possible spoofing of financial institution login"],
        "uncertainty_statement": "Automated AI assessment; verify official domain registry independently.",
        "user_recommendations": ["Do not submit credentials", "Check SSL certificate owner"],
        "provider": "mock-gemini",
        "model": "mock-gemini-1.5-flash",
        "status": "COMPLETED",
    }

    mock_p = MockAIProvider(default_response=json.dumps(expected_response))
    analyzer = AIThreatAnalyzer(provider=mock_p)

    evidence = {
        "normalized_url": "https://secure-login-bank-verify.com/login-verify",
        "hostname": "secure-login-bank-verify.com",
        "scheme": "https",
        "path": "/login-verify",
        "is_ip_hostname": False,
        "has_homoglyphs": False,
        "ssrf_safe": True,
    }
    findings = {
        "risk_level": "HIGH_RISK",
        "risk_score": 70,
        "indicators": [{"rule_id": "RULE-URL-002", "category": "CREDENTIAL_HARVESTING"}],
    }

    result = await analyzer.analyze(
        target_type="url",
        untrusted_content="https://secure-login-bank-verify.com/login-verify",
        observed_evidence=evidence,
        heuristic_findings=findings,
    )

    assert isinstance(result, AiAnalysisResult)
    assert "credential harvesting" in result.explanation.lower() or "suspicious" in result.summary.lower()
    assert len(result.supporting_evidence) == 2
    assert "RULE-URL-002" in result.supporting_evidence[0]
    assert result.status == "COMPLETED"


@pytest.mark.asyncio
async def test_url_scam_analysis_benign():
    """Test URL threat reasoning on benign site."""
    benign_response = {
        "summary": "Benign standard web resource with no detected security anomalies.",
        "explanation": "The domain adheres to standard conventions with no homoglyph indicators, IP routing, or deceptive credential paths.",
        "supporting_evidence": ["No security indicators triggered", "Standard HTTPS port 443"],
        "ai_inferences": ["Legitimate informational or corporate web property"],
        "uncertainty_statement": "Assessment is probabilistic and reflects current observable attributes.",
        "user_recommendations": ["Safe to access normally under standard browsing hygiene"],
        "provider": "mock-gemini",
        "model": "mock-gemini-1.5-flash",
        "status": "COMPLETED",
    }

    mock_p = MockAIProvider(default_response=json.dumps(benign_response))
    analyzer = AIThreatAnalyzer(provider=mock_p)

    evidence = {
        "normalized_url": "https://example.com/",
        "hostname": "example.com",
        "scheme": "https",
        "path": "/",
        "is_ip_hostname": False,
        "has_homoglyphs": False,
        "ssrf_safe": True,
    }
    findings = {"risk_level": "CLEAN", "risk_score": 0, "indicators": []}

    result = await analyzer.analyze(
        target_type="url",
        untrusted_content="https://example.com/",
        observed_evidence=evidence,
        heuristic_findings=findings,
    )

    assert result.summary.startswith("Benign")
    assert "no detected security anomalies" in result.summary.lower()


@pytest.mark.asyncio
async def test_email_phishing_analysis():
    """Test Email threat reasoning with urgency and credential harvesting lure."""
    email_response = {
        "summary": "Urgent coercive email attempting unauthorized password reset verification.",
        "explanation": "The sender employs psychological urgency alleging immediate account suspension to force the recipient to click an embedded credential harvesting link.",
        "supporting_evidence": ["Rule RULE-EML-001 (Urgency)", "Rule RULE-EML-002 (Credential Fraud)"],
        "ai_inferences": ["Coercive social engineering attempt"],
        "uncertainty_statement": "Probabilistic assessment based on text cues and detected indicators.",
        "user_recommendations": ["Do not click embedded links", "Report to security team"],
        "provider": "mock-gemini",
        "model": "gemini-1.5-flash",
        "status": "COMPLETED",
    }

    mock_p = MockAIProvider(default_response=json.dumps(email_response))
    analyzer = AIThreatAnalyzer(provider=mock_p)

    evidence = {
        "sender_domain": "scam-verify.com",
        "extracted_urls": ["https://scam-verify.com/login"],
        "extracted_phones": [],
        "body_length": 250,
    }
    findings = {
        "risk_level": "HIGH_RISK",
        "risk_score": 70,
        "indicators": [
            {"rule_id": "RULE-EML-001", "category": "URGENCY_LURE"},
            {"rule_id": "RULE-EML-002", "category": "CREDENTIAL_HARVESTING"},
        ],
    }

    result = await analyzer.analyze(
        target_type="email",
        untrusted_content="Your account is suspended. Click immediately to restore access: https://scam-verify.com/login",
        observed_evidence=evidence,
        heuristic_findings=findings,
        sender="security@scam-verify.com",
        subject="URGENT: Immediate Account Suspension",
    )

    assert isinstance(result, AiAnalysisResult)
    assert "coercive" in result.explanation.lower() or "urgent" in result.summary.lower()


@pytest.mark.asyncio
async def test_sms_smishing_analysis():
    """Test SMS threat reasoning with OTP lure."""
    sms_response = {
        "summary": "Financial smishing attempt targeting one-time authorization code.",
        "explanation": "Message impersonates bank card fraud alert demanding user share a 6-digit OTP code.",
        "supporting_evidence": ["Rule RULE-SMS-001 (OTP Harvesting)"],
        "ai_inferences": ["Attackers attempting two-factor authentication bypass"],
        "uncertainty_statement": "Automated analysis of SMS message content.",
        "user_recommendations": ["Never share OTP or PIN with anyone, including bank representatives."],
        "provider": "mock-gemini",
        "model": "gemini-1.5-flash",
        "status": "COMPLETED",
    }

    mock_p = MockAIProvider(default_response=json.dumps(sms_response))
    analyzer = AIThreatAnalyzer(provider=mock_p)

    evidence = {"extracted_urls": [], "extracted_phones": [], "message_length": 90}
    findings = {
        "risk_level": "HIGH_RISK",
        "risk_score": 70,
        "indicators": [{"rule_id": "RULE-SMS-001", "category": "OTP_HARVESTING"}],
    }

    result = await analyzer.analyze(
        target_type="sms",
        untrusted_content="Your card is blocked. Send your 6-digit OTP code to unblock immediately.",
        observed_evidence=evidence,
        heuristic_findings=findings,
        sender="+1999888777",
    )

    assert "OTP" in result.summary or "smishing" in result.summary.lower()
    assert len(result.user_recommendations) > 0


@pytest.mark.asyncio
async def test_analyzer_markdown_fence_stripping():
    """Test that Markdown fences (```json ... ```) are cleanly stripped."""
    fenced = """```json
    {
        "summary": "Clean fenced output test.",
        "explanation": "Testing clean JSON extraction from markdown backticks.",
        "supporting_evidence": ["Evidence 1"],
        "ai_inferences": ["Inference 1"],
        "uncertainty_statement": "Standard disclaimer.",
        "user_recommendations": ["Recommendation 1"],
        "provider": "mock-gemini",
        "model": "gemini-1.5-flash",
        "status": "COMPLETED"
    }
    ```"""

    mock_p = MockAIProvider(default_response=fenced)
    analyzer = AIThreatAnalyzer(provider=mock_p)

    result = await analyzer.analyze(
        target_type="url",
        untrusted_content="https://example.org",
        observed_evidence={},
        heuristic_findings={},
    )

    assert result.summary == "Clean fenced output test."


@pytest.mark.asyncio
async def test_analyzer_rejects_non_json():
    """Test AIValidationError raised on malformed non-JSON output."""
    mock_p = MockAIProvider(simulate_malformed_json=True)
    analyzer = AIThreatAnalyzer(provider=mock_p)

    with pytest.raises(AIValidationError) as exc_info:
        await analyzer.analyze(
            target_type="url",
            untrusted_content="https://example.org",
            observed_evidence={},
            heuristic_findings={},
        )
    assert "not valid json" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_analyzer_rejects_missing_required_fields():
    """Test validation failure when a required field like uncertainty_statement is missing."""
    incomplete = json.dumps({
        "summary": "Incomplete output",
        "explanation": "Missing uncertainty statement and recommendations",
    })

    mock_p = MockAIProvider(default_response=incomplete)
    analyzer = AIThreatAnalyzer(provider=mock_p)

    with pytest.raises(AIValidationError) as exc_info:
        await analyzer.analyze(
            target_type="url",
            untrusted_content="https://example.org",
            observed_evidence={},
            heuristic_findings={},
        )
    assert "schema contract" in str(exc_info.value).lower()
