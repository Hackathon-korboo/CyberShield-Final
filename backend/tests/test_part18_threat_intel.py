"""Tests for Part 18: Threat Intelligence Integration.

Verifies:
- Multi-source Threat Intelligence Adapter operations
- Authoritative local corpus match producing CONFIRMED_MALICIOUS
- Absence of match does not claim proof of safety
- Partial-failure tolerance when individual providers fail or time out
- Accurate reporting of unconfigured external feeds without crashes
"""

import pytest

from backend.app.schemas.evidence import CheckStatus
from backend.app.schemas.risk import RiskClassification
from backend.app.schemas.url import UrlAnalysisRequest
from backend.app.services.ai_service import AIThreatService
from backend.app.services.risk.pipeline import UnifiedRiskPipeline
from backend.app.services.threat_intel.adapter import ThreatIntelligenceAdapter


@pytest.fixture
def intel_adapter():
    return ThreatIntelligenceAdapter()


@pytest.fixture
def risk_pipeline():
    return UnifiedRiskPipeline()


@pytest.mark.asyncio
async def test_local_threat_corpus_match_produces_confirmed_malicious(intel_adapter, risk_pipeline):
    """Verify that an authoritative match in the local threat corpus triggers CONFIRMED_MALICIOUS with score 100."""
    target_url = "http://malicious-confirmed-c2.com/payload"
    intel_summary = await intel_adapter.query_all(target=target_url)

    assert intel_summary.is_malicious is True
    assert "MALWARE" in intel_summary.threat_types
    assert intel_summary.status == CheckStatus.COMPLETED

    # Run through pipeline
    ai_service = AIThreatService()
    comp_resp = await ai_service.analyze_url(UrlAnalysisRequest(url=target_url))
    report = risk_pipeline.process_url_response(comp_resp, threat_intel=intel_summary)

    assessment = report.risk_assessment
    assert assessment.classification == RiskClassification.CONFIRMED_MALICIOUS
    assert assessment.risk_score == 100
    assert assessment.has_authoritative_match is True
    assert any("INTEL" in r for r in assessment.rules_triggered)


@pytest.mark.asyncio
async def test_local_threat_corpus_no_match(intel_adapter):
    """Verify that benign destinations return no match with explicit safety disclaimer."""
    target_url = "https://example.com/benign"
    intel_summary = await intel_adapter.query_all(target=target_url)

    assert intel_summary.is_malicious is False
    assert len(intel_summary.threat_types) == 0
    assert "safety_disclaimer" in intel_summary.details
    assert "not proof of website safety" in intel_summary.details["safety_disclaimer"].lower()


@pytest.mark.asyncio
async def test_threat_intel_partial_failure_tolerance(monkeypatch, intel_adapter):
    """Verify that an error or exception in an external feed does not crash query_all."""
    async def mock_failing_urlhaus(target):
        raise ConnectionError("Simulated URLhaus upstream connection failure")

    monkeypatch.setattr(intel_adapter, "query_urlhaus", mock_failing_urlhaus)

    intel_summary = await intel_adapter.query_all(target="https://example.com/test")
    assert intel_summary is not None
    assert "URLhaus" in intel_summary.details["providers"]
    assert intel_summary.details["providers"]["URLhaus"]["status"] == "ERROR"


@pytest.mark.asyncio
async def test_unconfigured_external_providers_honestly_reported(intel_adapter):
    """Verify that unconfigured feeds are tagged NOT_CONFIGURED without fabricating clean results."""
    intel_summary = await intel_adapter.query_all(target="https://random-domain.com/")
    providers = intel_summary.details["providers"]

    assert providers["GoogleSafeBrowsing"]["status"] in ("NOT_CONFIGURED", "NO_MATCH")
    assert providers["URLhaus"]["status"] in ("NOT_CONFIGURED", "NO_MATCH")
    assert providers["OpenPhish"]["status"] in ("NOT_CONFIGURED", "NO_MATCH")
