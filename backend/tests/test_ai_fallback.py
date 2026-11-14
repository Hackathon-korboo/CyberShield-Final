"""Resilience, fallback, and circuit breaker tests for Part 12.

Verifies that timeouts, quota exhaustion, missing credentials, and configuration
toggles cleanly fall back to deterministic findings without crashing.
"""

import time
import pytest

from backend.app.engines.ai.fallback import CircuitBreaker, FallbackAIProvider
from backend.app.engines.ai.mock_provider import MockAIProvider
from backend.app.services.ai_service import AIThreatService
from backend.app.schemas.url import UrlAnalysisRequest
from backend.app.schemas.email import EmailAnalysisRequest
from backend.app.schemas.sms import SmsAnalysisRequest


@pytest.mark.asyncio
async def test_ai_timeout_fallback_to_heuristic():
    """Verify that a provider timeout serves deterministic fallback while preserving score."""
    timeout_mock = MockAIProvider(simulate_timeout=True)
    ai_service = AIThreatService(ai_provider=timeout_mock)

    req = UrlAnalysisRequest(url="https://phishing-update-login.com/login")
    result = await ai_service.analyze_url(req)

    # Heuristic score and risk level must be 100% intact
    assert result.heuristic_findings.risk_score > 0
    assert result.ai_analysis is not None
    assert result.ai_analysis.status == "TIMEOUT_FALLBACK"
    assert "deterministic" in result.ai_analysis.summary.lower()


@pytest.mark.asyncio
async def test_ai_rate_limit_circuit_breaker():
    """Verify that HTTP 429 quota exhaustion immediately trips the circuit breaker."""
    breaker = CircuitBreaker(failure_threshold=2, recovery_time_seconds=1.0)
    rate_limit_mock = MockAIProvider(simulate_rate_limit=True)
    ai_service = AIThreatService(ai_provider=rate_limit_mock, circuit_breaker=breaker)

    req = SmsAnalysisRequest(message="Your card is suspended. Send 6-digit OTP immediately.")
    result1 = await ai_service.analyze_sms(req)

    assert result1.ai_analysis.status == "RATE_LIMITED"
    assert breaker.is_open is True

    # Next call should be intercepted by open circuit breaker without querying provider
    result2 = await ai_service.analyze_sms(req)
    assert result2.ai_analysis.status == "RATE_LIMITED"
    assert result2.heuristic_findings.risk_score >= 70  # OTP rule enforced


def test_circuit_breaker_recovery_half_open():
    """Verify that circuit breaker recovers to HALF_OPEN after recovery window."""
    breaker = CircuitBreaker(failure_threshold=1, recovery_time_seconds=0.1)
    breaker.record_failure()

    assert breaker.is_open is True
    time.sleep(0.15)
    # After recovery period, is_open should evaluate False and transition to HALF_OPEN
    assert breaker.is_open is False
    assert breaker.state == "HALF_OPEN"

    breaker.record_success()
    assert breaker.state == "CLOSED"


@pytest.mark.asyncio
async def test_ai_disabled_toggle(monkeypatch):
    """Verify that disabling AI via settings serves disabled fallback immediately."""
    from backend.app.core.config import get_settings
    settings = get_settings()

    mock_p = MockAIProvider()
    ai_service = AIThreatService(ai_provider=mock_p)
    ai_service.settings.ai_analysis_enabled = False

    req = EmailAnalysisRequest(body="Job offer! Earn $1000/day clicking links. Register at http://job-scam.com")
    result = await ai_service.analyze_email(req)

    assert result.ai_analysis.status == "DISABLED"
    assert mock_p.call_count == 0  # Provider never invoked
    assert result.heuristic_findings.risk_score >= 40  # Deterministic score preserved

    # Restore setting
    ai_service.settings.ai_analysis_enabled = True


@pytest.mark.asyncio
async def test_unconfigured_provider_fallback(monkeypatch):
    """Verify unconfigured Gemini provider returns FALLBACK_HEURISTIC_ONLY."""
    from backend.app.engines.ai.client import GeminiProvider
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    unconfigured_provider = GeminiProvider(api_key=None)
    ai_service = AIThreatService(ai_provider=unconfigured_provider)

    req = UrlAnalysisRequest(url="https://example.com")
    result = await ai_service.analyze_url(req)

    assert result.ai_analysis.status == "FALLBACK_HEURISTIC_ONLY"
    assert result.observed_evidence.ssrf_safe is True
    assert result.heuristic_findings.risk_level == "CLEAN"
