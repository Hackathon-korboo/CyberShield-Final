"""Tests for system health endpoints, root info, security headers, and error handling."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Verify root / endpoint returns standard response with application identity."""
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["name"] == "CyberShield AI 2.0"
    assert payload["data"]["version"] == "2.0.0"
    assert payload["data"]["status"] == "online"
    assert "X-Correlation-ID" in response.headers


def test_api_v1_health_endpoint(client: TestClient):
    """Verify /api/v1/health endpoint returns health status and subsystem details."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "healthy"
    assert payload["data"]["version"] == "2.0.0"
    assert "subsystems" in payload["data"]
    assert "heuristic_engine" in payload["data"]["subsystems"]
    assert "ai_engine" in payload["data"]["subsystems"]
    assert "blockchain_engine" in payload["data"]["subsystems"]


def test_root_health_alias(client: TestClient):
    """Verify /health alias endpoint responds identically."""
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "healthy"


def test_security_headers_present(client: TestClient):
    """Verify custom security headers are attached to all HTTP responses."""
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "X-Correlation-ID" in response.headers


def test_custom_correlation_id_preserved(client: TestClient):
    """Verify client-supplied X-Correlation-ID is preserved throughout the pipeline."""
    custom_id = "test-correlation-uuid-9999"
    response = client.get("/", headers={"X-Correlation-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == custom_id


def test_standardized_404_error_envelope(client: TestClient):
    """Verify non-existent routes return standardized error envelope with correlation ID."""
    response = client.get("/non-existent-endpoint-404")
    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["data"] is None
    assert payload["error"]["code"] == "NOT_FOUND"
    assert "correlation_id" in payload["error"]
    assert payload["error"]["correlation_id"] is not None
