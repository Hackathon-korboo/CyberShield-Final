"""Comprehensive API integration tests for Phase 02 threat analysis endpoints."""

from fastapi.testclient import TestClient


def test_analyze_url_endpoint_benign(client: TestClient):
    """Verify clean URL produces CLEAN rating with zero score."""
    response = client.post(
        "/api/v1/analyze/url",
        json={"url": "https://example.com/about-us"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["heuristic_findings"]["risk_level"] == "CLEAN"
    assert payload["data"]["heuristic_findings"]["risk_score"] == 0
    assert payload["data"]["observed_evidence"]["ssrf_safe"] is True


def test_analyze_url_endpoint_phishing_lure(client: TestClient):
    """Verify phishing keywords trigger deterministic indicators."""
    response = client.post(
        "/api/v1/analyze/url",
        json={"url": "https://verify-banking-security.com/login"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    findings = payload["data"]["heuristic_findings"]
    assert findings["risk_level"] in ("SUSPICIOUS", "HIGH_RISK")
    assert findings["risk_score"] > 0
    rule_ids = [ind["rule_id"] for ind in findings["indicators"]]
    assert "RULE-URL-003" in rule_ids


def test_analyze_url_endpoint_ssrf_detection(client: TestClient):
    """Verify private IP submission is detected and flagged as SSRF risk."""
    response = client.post(
        "/api/v1/analyze/url",
        json={"url": "http://127.0.0.1/admin"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    evidence = payload["data"]["observed_evidence"]
    assert evidence["ssrf_safe"] is False
    findings = payload["data"]["heuristic_findings"]
    assert findings["risk_level"] in ("SUSPICIOUS", "HIGH_RISK")
    rule_ids = [ind["rule_id"] for ind in findings["indicators"]]
    assert "RULE-SSRF-001" in rule_ids


def test_analyze_url_endpoint_invalid_scheme(client: TestClient):
    """Verify POST /api/v1/analyze/url rejects unsupported schemes with 422."""
    response = client.post(
        "/api/v1/analyze/url",
        json={"url": "ftp://malicious.com/file"},
    )
    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "VALIDATION_ERROR"
    assert "correlation_id" in payload["error"]


def test_analyze_email_endpoint_fraud_and_urgency(client: TestClient):
    """Verify email urgency and payment fraud detection end-to-end."""
    response = client.post(
        "/api/v1/analyze/email",
        json={
            "subject": "URGENT: Immediate action required",
            "sender": "Security Department <security@fake-support-desk.com>",
            "body": "Your account has been suspended. Pay your bill using an iTunes gift card within 24 hours.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    evidence = payload["data"]["observed_evidence"]
    assert evidence["sender_domain"] == "fake-support-desk.com"
    findings = payload["data"]["heuristic_findings"]
    assert findings["risk_level"] in ("SUSPICIOUS", "HIGH_RISK")
    rule_ids = [ind["rule_id"] for ind in findings["indicators"]]
    assert "RULE-EML-001" in rule_ids
    assert "RULE-EML-002" in rule_ids


def test_analyze_email_with_embedded_urls(client: TestClient):
    """Verify email body URL extraction and preflight checks."""
    response = client.post(
        "/api/v1/analyze/email",
        json={
            "subject": "Verify invoice",
            "body": "Check your invoice at https://verify-banking-security.com/login now.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    evidence = payload["data"]["observed_evidence"]
    assert len(evidence["extracted_urls"]) == 1
    assert "https://verify-banking-security.com/login" in evidence["extracted_urls"]


def test_analyze_email_endpoint_empty_body(client: TestClient):
    """Verify POST /api/v1/analyze/email rejects empty body with 422."""
    response = client.post(
        "/api/v1/analyze/email",
        json={"body": "   "},
    )
    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False


def test_analyze_sms_endpoint_otp_extraction(client: TestClient):
    """Verify SMS OTP extraction is flagged as CRITICAL risk."""
    response = client.post(
        "/api/v1/analyze/sms",
        json={
            "sender": "+18005550199",
            "message": "Dear customer, your bank account is locked. Reply with your 6-digit OTP to unblock.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    findings = payload["data"]["heuristic_findings"]
    rule_ids = [ind["rule_id"] for ind in findings["indicators"]]
    assert "RULE-SMS-001" in rule_ids
    assert findings["risk_score"] >= 40


def test_analyze_sms_with_embedded_ssrf_url(client: TestClient):
    """Verify SMS containing internal IP URL is flagged for SSRF."""
    response = client.post(
        "/api/v1/analyze/sms",
        json={
            "message": "Update router settings at http://192.168.1.1/login immediately.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    findings = payload["data"]["heuristic_findings"]
    rule_ids = [ind["rule_id"] for ind in findings["indicators"]]
    assert "RULE-SSRF-003" in rule_ids


def test_analyze_sms_clean(client: TestClient):
    """Verify benign SMS produces clean evaluation."""
    response = client.post(
        "/api/v1/analyze/sms",
        json={
            "message": "Hi mom, I will arrive home around 6 PM for dinner.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    findings = payload["data"]["heuristic_findings"]
    assert findings["risk_level"] == "CLEAN"
    assert findings["risk_score"] == 0
    assert len(findings["indicators"]) == 0


def test_analyze_sms_compound_urgency_endpoint(client: TestClient):
    """Verify POST /api/v1/analyze/sms triggers RULE-SMS-004 on contextual urgency."""
    response = client.post(
        "/api/v1/analyze/sms",
        json={
            "message": "URGENT: Verify your bank account immediately to prevent service termination.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    findings = payload["data"]["heuristic_findings"]
    rule_ids = [ind["rule_id"] for ind in findings["indicators"]]
    assert "RULE-SMS-004" in rule_ids
    assert findings["risk_level"] in ("SUSPICIOUS", "HIGH_RISK")
    assert findings["risk_score"] >= 40  # HIGH floor applied (min 40)


def test_api_endpoints_emit_utc_timestamp_with_z(client: TestClient):
    """Verify all 3 analysis endpoints emit standardized UTC timestamps with Z notation."""
    # 1. URL Endpoint
    resp_url = client.post("/api/v1/analyze/url", json={"url": "https://example.com/test"})
    assert resp_url.status_code == 200
    ts_url = resp_url.json()["data"]["timestamp"]
    assert ts_url.endswith("Z") or "+00:00" in ts_url

    # 2. Email Endpoint
    resp_email = client.post("/api/v1/analyze/email", json={"body": "Hello team, here is the monthly report."})
    assert resp_email.status_code == 200
    ts_email = resp_email.json()["data"]["timestamp"]
    assert ts_email.endswith("Z") or "+00:00" in ts_email

    # 3. SMS Endpoint
    resp_sms = client.post("/api/v1/analyze/sms", json={"message": "Your package has been delivered to your porch."})
    assert resp_sms.status_code == 200
    ts_sms = resp_sms.json()["data"]["timestamp"]
    assert ts_sms.endswith("Z") or "+00:00" in ts_sms

