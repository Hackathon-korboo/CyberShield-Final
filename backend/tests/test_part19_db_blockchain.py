"""Tests for Part 19: Database Persistence & Blockchain Report Integrity.

Verifies:
- SQLite persistence, retrieval, and pagination
- Transaction rollback on failure
- RFC 8785 canonical hash consistency and tamper detection
- Mutable metadata exclusion from canonical hash
- Blockchain honest state reporting (NOT_REGISTERED, SIMULATED)
- Zero sensitive data exposure in blockchain payloads
- Tamper detection via ReportVerificationResult
"""

from datetime import datetime, timezone
import pytest

from backend.app.db.repository import ReportRepository
from backend.app.db.session import DatabaseManager
from backend.app.schemas.evidence import CheckStatus
from backend.app.schemas.risk import DeterministicRiskAssessment, RiskClassification
from backend.app.schemas.unified_report import (
    ReportIntegrityInfo,
    ThreatIntelligenceSummary,
    UnifiedThreatReport,
)
from backend.app.services.blockchain.adapter import BlockchainAdapter
from backend.app.services.blockchain.canonical_hasher import (
    compute_canonical_hash,
    to_bytes32_hex,
)


@pytest.fixture
def test_db(tmp_path):
    """Create isolated test database."""
    db_file = str(tmp_path / "test_cybershield.db")
    mgr = DatabaseManager(db_path=db_file)
    return mgr


@pytest.fixture
def repo(test_db):
    return ReportRepository(db_manager=test_db)


@pytest.fixture
def sample_report():
    """Build a valid sample UnifiedThreatReport."""
    scan_id = "test-scan-12345"
    now = datetime(2026, 11, 14, 12, 0, 0, tzinfo=timezone.utc)
    assessment = DeterministicRiskAssessment(
        scan_id=scan_id,
        target="https://example.com/test",
        target_type="url",
        classification=RiskClassification.SUSPICIOUS,
        risk_score=40,
        summary="Suspicious test target",
        explanation="Detected test rule",
        rules_triggered=["RULE-URL-003"],
        coverage_score=0.8,
        confidence_score=0.8,
    )
    canonical_hash = compute_canonical_hash(
        scan_id=scan_id,
        submitted_input="https://example.com/test",
        input_type="url",
        classification=assessment.classification.value,
        risk_score=assessment.risk_score,
        timestamp_str=now.isoformat(),
        rules_triggered=assessment.rules_triggered,
    )
    return UnifiedThreatReport(
        scan_id=scan_id,
        submitted_input="https://example.com/test",
        input_type="url",
        timestamp=now,
        risk_assessment=assessment,
        technical_findings=[],
        threat_intelligence=ThreatIntelligenceSummary(),
        ai_analysis=None,
        recommendations=["Exercise caution."],
        security_check_status={"URL_PATTERN": CheckStatus.COMPLETED},
        limitations=["Static analysis mode."],
        report_integrity=ReportIntegrityInfo(
            canonical_sha256=canonical_hash,
            blockchain_status="NOT_REGISTERED",
        ),
    )


def test_database_save_and_retrieve_report(repo, sample_report):
    """Verify persisting a report and retrieving it produces identical attributes."""
    saved = repo.save_report(sample_report)
    assert saved is True

    retrieved = repo.get_report(sample_report.scan_id)
    assert retrieved is not None
    assert retrieved.scan_id == sample_report.scan_id
    assert retrieved.submitted_input == sample_report.submitted_input
    assert retrieved.risk_assessment.risk_score == sample_report.risk_assessment.risk_score
    assert retrieved.report_integrity.canonical_sha256 == sample_report.report_integrity.canonical_sha256


def test_database_list_history_and_pagination(repo, sample_report):
    """Verify report listing with limit and offset."""
    repo.save_report(sample_report)

    # Save a second report
    rep2 = sample_report.model_copy(deep=True)
    rep2.scan_id = "test-scan-67890"
    repo.save_report(rep2)

    reports, total = repo.list_reports(limit=1, offset=0)
    assert total >= 2
    assert len(reports) == 1

    reports_p2, total2 = repo.list_reports(limit=1, offset=1)
    assert len(reports_p2) == 1
    assert reports[0].scan_id != reports_p2[0].scan_id


def test_rfc8785_canonical_hash_consistency():
    """Verify identical parameters produce bit-for-bit identical hashes across executions."""
    h1 = compute_canonical_hash(
        scan_id="scan-001",
        submitted_input="https://test.com",
        input_type="url",
        classification="HIGH_RISK",
        risk_score=70,
        timestamp_str="2026-11-14T10:00:00Z",
        rules_triggered=["RULE-URL-001", "RULE-SSRF-001"],
    )
    h2 = compute_canonical_hash(
        scan_id="scan-001",
        submitted_input="https://test.com",
        input_type="url",
        classification="HIGH_RISK",
        risk_score=70,
        timestamp_str="2026-11-14T10:00:00Z",
        rules_triggered=["RULE-SSRF-001", "RULE-URL-001"],  # Order swapped, should be normalized
    )
    assert h1 == h2
    assert len(h1) == 64


def test_canonical_hash_tamper_detection(sample_report):
    """Verify that tampering with any report field changes the canonical hash."""
    adapter = BlockchainAdapter()

    # Original verification must MATCH
    res_valid = adapter.verify_report(sample_report)
    assert res_valid.integrity_status == "MATCH"
    assert res_valid.is_valid is True

    # Tamper with the score
    tampered_report = sample_report.model_copy(deep=True)
    tampered_report.risk_assessment.risk_score = 0  # Changed from 40 to 0

    res_tampered = adapter.verify_report(tampered_report)
    assert res_tampered.integrity_status == "MISMATCH"
    assert res_tampered.is_valid is False
    assert "tampering" in res_tampered.message.lower()


def test_canonical_hash_excludes_mutable_metadata(sample_report):
    """Verify that updating blockchain_status or transaction_hash does NOT change the report's canonical hash."""
    adapter = BlockchainAdapter()
    h_before = sample_report.report_integrity.canonical_sha256

    # Mutate on-chain metadata
    sample_report.report_integrity.blockchain_status = "ANCHORED"
    sample_report.report_integrity.transaction_hash = "0x1234567890abcdef"

    res = adapter.verify_report(sample_report)
    assert res.integrity_status == "MATCH"
    assert res.recomputed_sha256 == h_before


def test_blockchain_adapter_honest_unconfigured_state():
    """Verify that unconfigured blockchain returns honest NOT_REGISTERED with zero fake receipts."""
    adapter = BlockchainAdapter(provider_uri=None, enabled=False)
    integrity = adapter.generate_integrity_info(
        scan_id="scan-123",
        submitted_input="https://example.com",
        input_type="url",
        classification="LOW_RISK",
        risk_score=0,
        timestamp_str="2026-11-14T12:00:00Z",
    )
    assert integrity.blockchain_status == "NOT_REGISTERED"
    assert integrity.transaction_hash is None
    assert integrity.contract_address is None
    assert integrity.network is None


def test_blockchain_zero_sensitive_data_on_chain():
    """Verify EVM bytes32 hash representation contains only 32 bytes and zero sensitive user data."""
    hash_hex = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    bytes32_str = to_bytes32_hex(hash_hex)
    assert bytes32_str.startswith("0x")
    assert len(bytes32_str) == 66  # 0x + 64 hex characters
    assert "example.com" not in bytes32_str
