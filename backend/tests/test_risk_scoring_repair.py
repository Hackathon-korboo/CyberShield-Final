"""
CyberShield AI 2.0 - Regression Test Suite for Calibrated Risk Scoring & Scam Differentiation.
Verifies that scam categories receive evidence-calibrated scores, duplicate evidence is suppressed,
channel constraints are enforced, and synthetic scams are not falsely classified as CONFIRMED_MALICIOUS.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.risk_app import app
from backend.app.schemas.threat_models import ThreatCategory, RiskLevel
from backend.app.ai_engine.heuristics_engine import (
    calculate_calibrated_scam_score,
    EvidenceItem,
    heuristic_engine_instance,
)

client = TestClient(app)


def test_different_scams_produce_differentiated_scores():
    """Verify that different scam inputs receive distinct, evidence-calibrated scores rather than a fixed 98.5."""
    lottery_msg = "Congratulations! You have won Rs. 50,00,000 in our lucky draw. Pay Rs. 999 processing fees to claim your prize today."
    job_msg = "Congratulations! You have been selected for a work-from-home job with a salary of Rs. 45,000 per month. Pay Rs. 1,500 registration fees to confirm your position immediately."
    kyc_msg = "Your KYC verification has expired. Your banking services will be suspended today. Update your KYC immediately using the link provided in this message."
    otp_msg = "Your account verification is pending. Share your 6-digit OTP with our support executive immediately."
    normal_msg = "Your appointment is confirmed for tomorrow at 10 AM. Thank you."

    res_lottery = client.post("/api/v1/analyze/text", json={"content": lottery_msg, "source_type": "sms", "enable_gemini": False})
    res_job = client.post("/api/v1/analyze/text", json={"content": job_msg, "source_type": "sms", "enable_gemini": False})
    res_kyc = client.post("/api/v1/analyze/text", json={"content": kyc_msg, "source_type": "sms", "enable_gemini": False})
    res_otp = client.post("/api/v1/analyze/text", json={"content": otp_msg, "source_type": "sms", "enable_gemini": False})
    res_normal = client.post("/api/v1/analyze/text", json={"content": normal_msg, "source_type": "sms", "enable_gemini": False})

    assert res_lottery.status_code == 200
    assert res_job.status_code == 200
    assert res_kyc.status_code == 200
    assert res_otp.status_code == 200
    assert res_normal.status_code == 200

    score_lottery = res_lottery.json()["risk_score"]
    score_job = res_job.json()["risk_score"]
    score_kyc = res_kyc.json()["risk_score"]
    score_otp = res_otp.json()["risk_score"]
    score_normal = res_normal.json()["risk_score"]

    # Verify no fixed 98.5 score
    for s in (score_lottery, score_job, score_kyc, score_otp, score_normal):
        assert s != 98.5, f"Observed fixed 98.5 score!"

    # Verify score calibration bands
    assert score_normal <= 10.0, f"Normal message score should be <= 10.0, got {score_normal}"
    assert 50.0 <= score_lottery <= 70.0, f"Lottery score out of range: {score_lottery}"
    assert 50.0 <= score_job <= 80.0, f"Fake job score out of range: {score_job}"
    assert 55.0 <= score_kyc <= 85.0, f"KYC score out of range: {score_kyc}"
    assert 70.0 <= score_otp <= 92.0, f"OTP theft score out of range: {score_otp}"

    # Verify normal message is BENIGN
    assert res_normal.json()["risk_level"] == "BENIGN"
    assert res_normal.json()["classification"] == "BENIGN"


def test_identical_evidence_produces_identical_scores():
    """Verify deterministic repeatability: identical evidence must yield identical scores."""
    msg = "Your KYC verification has expired. Your banking services will be suspended today. Update your KYC immediately using the link provided in this message."
    res1 = client.post("/api/v1/analyze/text", json={"content": msg, "source_type": "sms", "enable_gemini": False})
    res2 = client.post("/api/v1/analyze/text", json={"content": msg, "source_type": "sms", "enable_gemini": False})

    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res1.json()["risk_score"] == res2.json()["risk_score"]
    assert res1.json()["risk_level"] == res2.json()["risk_level"]
    assert res1.json()["primary_category"] == res2.json()["primary_category"]


def test_duplicate_indicators_do_not_inflate_score():
    """Verify that multiple duplicate indicators in the same correlation group do not artificially inflate the score."""
    single_ev = [
        EvidenceItem(
            indicator="Upfront processing fee demand",
            description="Fee required",
            confidence=0.95,
            category=ThreatCategory.ADVANCE_FEE_FRAUD,
            severity="HIGH",
            correlation_group="CORR-ADVANCE-FEE"
        )
    ]
    duplicate_ev = [
        EvidenceItem(
            indicator="Upfront processing fee demand",
            description="Fee required",
            confidence=0.95,
            category=ThreatCategory.ADVANCE_FEE_FRAUD,
            severity="HIGH",
            correlation_group="CORR-ADVANCE-FEE"
        ),
        EvidenceItem(
            indicator="Second registration fee demand",
            description="Another fee mention",
            confidence=0.95,
            category=ThreatCategory.ADVANCE_FEE_FRAUD,
            severity="HIGH",
            correlation_group="CORR-ADVANCE-FEE"
        ),
        EvidenceItem(
            indicator="Third kit charge demand",
            description="Yet another fee mention",
            confidence=0.95,
            category=ThreatCategory.ADVANCE_FEE_FRAUD,
            severity="HIGH",
            correlation_group="CORR-ADVANCE-FEE"
        )
    ]

    score_single, _, _, _, _ = calculate_calibrated_scam_score(single_ev)
    score_dup, _, _, _, _ = calculate_calibrated_scam_score(duplicate_ev)

    assert score_single == score_dup, f"Duplicate indicators inflated score: {score_single} vs {score_dup}"


def test_sms_channel_constraint_never_phishing_email():
    """Verify that SMS inputs with phishing lures are classified under SMS categories, never PHISHING_EMAIL."""
    kyc_msg = "Your KYC verification has expired. Your banking services will be suspended today. Update your KYC immediately using the link provided in this message."
    res = client.post("/api/v1/analyze/text", json={"content": kyc_msg, "source_type": "sms", "enable_gemini": False})

    assert res.status_code == 200
    cat = res.json()["primary_category"]
    assert cat != "PHISHING_EMAIL", f"SMS input was incorrectly categorized as PHISHING_EMAIL!"
    assert cat in ("KYC_PHISHING", "SCAM_SMS", "BANKING_FRAUD")


def test_synthetic_scam_not_confirmed_malicious():
    """Verify that synthetic text scam inputs are classified as LIKELY_MALICIOUS or SUSPICIOUS, never CONFIRMED_MALICIOUS without authoritative external threat intel."""
    kyc_msg = "Your KYC verification has expired. Your banking services will be suspended today. Update your KYC immediately using the link provided in this message."
    res = client.post("/api/v1/analyze/text", json={"content": kyc_msg, "source_type": "sms", "enable_gemini": False})

    assert res.status_code == 200
    data = res.json()
    assert data["classification"] != "CONFIRMED_MALICIOUS"
    assert data["has_authoritative_match"] is False
    assert data["verdict"] in ("LIKELY_MALICIOUS", "SUSPICIOUS")


def test_authoritative_threat_intel_sets_confirmed_malicious():
    """Verify that authoritative VirusTotal malicious confirmation sets CONFIRMED_MALICIOUS with score 100."""
    vt_ev = [
        EvidenceItem(
            indicator="VirusTotal Malicious Domain Flag",
            description="Confirmed malicious domain",
            confidence=0.99,
            category=ThreatCategory.SCAM_SMS,
            severity="CRITICAL",
            correlation_group="CORR-VT-MALICIOUS"
        )
    ]
    score, level, _, _, _ = calculate_calibrated_scam_score(vt_ev, has_authoritative_match=True)
    assert score == 100.0
    assert level == RiskLevel.CRITICAL
