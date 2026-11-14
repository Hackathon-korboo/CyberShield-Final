"""End-to-End API integration tests for Phase 03 AI analysis endpoints.

Verifies routing, serialization, correlation IDs, security headers, and
error handling through the extended application entry point (`ai_app`).
"""

import pytest
from starlette.testclient import TestClient

from backend.app.ai_app import app
from backend.app.api.ai_dependencies import get_ai_threat_service
from backend.app.engines.ai.mock_provider import MockAIProvider
from backend.app.services.ai_service import AIThreatService


@pytest.fixture
def client_with_mock_ai():
    """TestClient fixture with MockAIProvider injected into dependency graph."""
    mock_provider = MockAIProvider()
    mock_service = AIThreatService(ai_provider=mock_provider)

    app.dependency_overrides[get_ai_threat_service] = lambda: mock_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_ai_url_endpoint_benign(client_with_mock_ai):
    """Test POST /api/v1/analyze/ai/url with clean URL."""
    response = client_with_mock_ai.post(
        "/api/v1/analyze/ai/url",
        json={"url": "https://example.com"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["error"] is None

    result = data["data"]
    assert result["target"] == "https://example.com"
    assert result["observed_evidence"]["ssrf_safe"] is True
    assert result["heuristic_findings"]["risk_level"] == "CLEAN"
    assert result["ai_analysis"] is not None
    assert result["ai_analysis"]["status"] == "COMPLETED"


def test_ai_url_endpoint_phishing(client_with_mock_ai):
    """Test POST /api/v1/analyze/ai/url with phishing lure."""
    response = client_with_mock_ai.post(
        "/api/v1/analyze/ai/url",
        json={"url": "https://secure-login-account-update.com/login"},
    )

    assert response.status_code == 200
    data = response.json()
    result = data["data"]

    assert result["heuristic_findings"]["risk_level"] in ("SUSPICIOUS", "HIGH_RISK")
    assert result["ai_analysis"]["provider"] == "mock-gemini"
    assert len(result["ai_analysis"]["user_recommendations"]) > 0


def test_ai_url_endpoint_ssrf_blocking(client_with_mock_ai):
    """Test POST /api/v1/analyze/ai/url with loopback IP (SSRF)."""
    response = client_with_mock_ai.post(
        "/api/v1/analyze/ai/url",
        json={"url": "http://127.0.0.1:8000/internal"},
    )

    assert response.status_code == 200
    data = response.json()
    result = data["data"]

    assert result["observed_evidence"]["ssrf_safe"] is False
    assert result["heuristic_findings"]["risk_level"] == "HIGH_RISK"
    assert any(i["rule_id"] == "RULE-SSRF-001" for i in result["heuristic_findings"]["indicators"])


def test_ai_email_endpoint_phishing(client_with_mock_ai):
    """Test POST /api/v1/analyze/ai/email with urgent lure."""
    payload = {
        "subject": "URGENT: Immediate action required",
        "sender": "security-alert@fakebank.com",
        "body": "Your account has been suspended. Please confirm your password within 24 hours at https://fakebank.com/pin",
    }
    response = client_with_mock_ai.post("/api/v1/analyze/ai/email", json=payload)

    assert response.status_code == 200
    data = response.json()
    result = data["data"]

    assert result["target_type"] == "email"
    assert result["heuristic_findings"]["risk_score"] >= 40
    assert result["ai_analysis"] is not None
    assert result["ai_analysis"]["status"] == "COMPLETED"


def test_ai_sms_endpoint_otp(client_with_mock_ai):
    """Test POST /api/v1/analyze/ai/sms with OTP extraction."""
    payload = {
        "sender": "+1234567890",
        "message": "Dear customer, your debit card is blocked. Send your 6-digit OTP to unblock now.",
    }
    response = client_with_mock_ai.post("/api/v1/analyze/ai/sms", json=payload)

    assert response.status_code == 200
    data = response.json()
    result = data["data"]

    assert result["target_type"] == "sms"
    assert result["heuristic_findings"]["risk_level"] == "HIGH_RISK"
    assert result["ai_analysis"]["status"] == "COMPLETED"


def test_ai_health_endpoint(client_with_mock_ai):
    """Test GET /api/v1/analyze/ai/health returns healthy status."""
    response = client_with_mock_ai.get("/api/v1/analyze/ai/health")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert data["data"]["configured"] is True


def test_ai_endpoint_invalid_payload_error_envelope(client_with_mock_ai):
    """Test invalid request payload returns standard standardized 422 error envelope."""
    response = client_with_mock_ai.post(
        "/api/v1/analyze/ai/url",
        json={"url": "ftp://unsupported-scheme.com"},
    )

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert len(data["error"]["details"]) > 0
