"""Tests for Part 17: Core API Development.

Verifies:
- POST /api/v1/scan-url endpoint validation, execution, and persistence
- GET /api/v1/scans/{scan_id} report retrieval and 404 handling
- GET /api/v1/scans pagination and ordering
- GET /api/v1/health accuracy and database connectivity
- OpenAPI schema documentation
"""

import pytest
from starlette.testclient import TestClient

from backend.app.risk_app import app
from backend.app.schemas.risk import RiskClassification
from backend.app.schemas.unified_report import UnifiedThreatReport


@pytest.fixture
def client():
    return TestClient(app)


def test_scan_url_endpoint_valid_url(client):
    """Verify submitting a valid benign URL produces a 200 response with a persisted UnifiedThreatReport."""
    resp = client.post("/api/v1/scan-url", json={"url": "https://example.com/safe-page"})
    assert resp.status_code == 200
    data = resp.json()

    assert data["success"] is True
    assert data["error"] is None
    report_data = data["data"]

    assert report_data["input_type"] == "url"
    assert "https://example.com/safe-page" in report_data["submitted_input"]
    assert report_data["risk_assessment"]["classification"] in ("LOW_RISK", "CLEAN")
    assert report_data["report_integrity"]["canonical_sha256"] is not None
    assert len(report_data["report_integrity"]["canonical_sha256"]) == 64

    # Verify report was persisted to DB and can be retrieved
    scan_id = report_data["scan_id"]
    get_resp = client.get(f"/api/v1/scans/{scan_id}")
    assert get_resp.status_code == 200
    retrieved = get_resp.json()["data"]
    assert retrieved["scan_id"] == scan_id
    assert retrieved["report_integrity"]["canonical_sha256"] == report_data["report_integrity"]["canonical_sha256"]


def test_scan_url_endpoint_invalid_url_rejected(client):
    """Verify rejection of empty, malformed, or unsupported URL schemes."""
    # 1. Empty URL
    resp1 = client.post("/api/v1/scan-url", json={"url": ""})
    assert resp1.status_code == 422

    # 2. Missing scheme
    resp2 = client.post("/api/v1/scan-url", json={"url": "example.com"})
    assert resp2.status_code == 422

    # 3. Unsupported scheme (ftp://)
    resp3 = client.post("/api/v1/scan-url", json={"url": "ftp://ftp.example.com/file.zip"})
    assert resp3.status_code == 422

    # 4. Dangerous scheme (javascript://)
    resp4 = client.post("/api/v1/scan-url", json={"url": "javascript:alert(1)"})
    assert resp4.status_code == 422

    # 5. Dangerous scheme (file://)
    resp5 = client.post("/api/v1/scan-url", json={"url": "file:///etc/passwd"})
    assert resp5.status_code == 422

    # 6. Exceeds max length
    long_url = "https://example.com/" + ("a" * 2050)
    resp6 = client.post("/api/v1/scan-url", json={"url": long_url})
    assert resp6.status_code == 422


def test_scan_url_ssrf_blocking_and_policy_violation(client):
    """Verify that loopback SSRF targets are blocked, classified as HIGH_RISK, and policy violation tagged."""
    resp = client.post("/api/v1/scan-url", json={"url": "http://127.0.0.1:8000/admin"})
    assert resp.status_code == 200
    data = resp.json()["data"]

    assessment = data["risk_assessment"]
    assert assessment["classification"] == "HIGH_RISK"
    assert assessment["classification"] != "CONFIRMED_MALICIOUS"
    assert assessment["risk_score"] == 70
    assert assessment["has_policy_violation"] is True
    assert assessment["has_authoritative_match"] is False
    assert "policy violation" in assessment["summary"].lower()


def test_get_scan_by_id_not_found(client):
    """Verify that querying a non-existent scan_id returns a 404 with structured error envelope."""
    resp = client.get("/api/v1/scans/non-existent-uuid-999")
    assert resp.status_code == 404
    data = resp.json()

    assert data["success"] is False
    assert data["data"] is None
    assert data["error"]["code"] == "SCAN_NOT_FOUND"


def test_list_scans_pagination(client):
    """Verify paginated listing of scan reports."""
    # Seed a couple of scans
    client.post("/api/v1/scan-url", json={"url": "https://example.com/page1"})
    client.post("/api/v1/scan-url", json={"url": "https://example.com/page2"})

    resp = client.get("/api/v1/scans?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert "reports" in data
    assert "total" in data
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["reports"]) <= 2
    assert data["total"] >= 2


def test_health_endpoint_accuracy(client):
    """Verify GET /api/v1/health returns subsystem statuses including database."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert data["status"] == "healthy"
    subsystems = data["subsystems"]

    assert "heuristic_engine" in subsystems
    assert "ai_engine" in subsystems
    assert "database" in subsystems
    assert subsystems["database"]["status"] == "healthy"
    assert "threat_intel" in subsystems
    assert "blockchain_engine" in subsystems


def test_openapi_documentation_available(client):
    """Verify that OpenAPI documentation includes all core Stage 5 endpoints."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()

    paths = schema.get("paths", {})
    assert "/api/v1/scan-url" in paths
    assert "/api/v1/scans/{scan_id}" in paths
    assert "/api/v1/scans" in paths
    assert "/api/v1/reports/verify" in paths
    assert "/api/v1/health" in paths
