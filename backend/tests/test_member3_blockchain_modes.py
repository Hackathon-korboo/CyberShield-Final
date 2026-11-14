"""CyberShield AI 2.0 — Member 3 Blockchain Multi-Mode Verification Suite.

Exhaustively verifies the 5 blockchain operational modes:
Mode A: Blockchain not configured (honest unconfigured / NOT_REGISTERED fallback).
Mode B: Local blockchain provider configured (Hardhat / Ganache local devnet).
Mode C: Invalid provider or contract configuration (graceful error containment).
Mode D: Transaction failure (on-chain revert handling).
Mode E: Successful registration and readback verification.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest

from backend.app.schemas.evidence import CheckStatus
from backend.app.schemas.risk import (
    DeterministicRiskAssessment,
    RiskClassification,
)
from backend.app.schemas.unified_report import (
    ReportIntegrityInfo,
    ThreatIntelligenceSummary,
    UnifiedThreatReport,
)
from backend.app.services.blockchain.adapter import (
    BlockchainAdapter,
    BlockchainStatus,
    CONTRACT_ABI,
    ReportVerificationResult,
)
from backend.app.services.blockchain.evidence_hasher import EvidenceHasher


def make_test_report(scan_id="test-scan-001", target="https://example.com/login", score=75):
    """Helper generating a valid UnifiedThreatReport."""
    now = datetime(2026, 11, 14, 10, 0, 0, tzinfo=timezone.utc)
    assessment = DeterministicRiskAssessment(
        scan_id=scan_id,
        target=target,
        target_type="url",
        classification=RiskClassification.HIGH_RISK,
        risk_score=score,
        summary="Test threat assessment",
        explanation="Test explanation",
        rules_triggered=["RULE-URL-001"],
        coverage_score=0.9,
        confidence_score=0.85,
    )
    return UnifiedThreatReport(
        scan_id=scan_id,
        submitted_input=target,
        input_type="url",
        timestamp=now,
        risk_assessment=assessment,
        technical_findings=[],
        threat_intelligence=ThreatIntelligenceSummary(),
        ai_analysis=None,
        recommendations=["Do not visit"],
        security_check_status={"URL_PATTERN": CheckStatus.COMPLETED},
        limitations=["Testing limitation"],
        report_integrity=ReportIntegrityInfo(
            canonical_sha256="dummy",
            blockchain_status="NOT_REGISTERED",
        ),
    )


# ==============================================================================
# MODE A: Blockchain Not Configured
# ==============================================================================
def test_mode_a_blockchain_not_configured():
    """Verify Mode A: unconfigured blockchain returns honest NOT_REGISTERED status."""
    adapter = BlockchainAdapter(enabled=False)
    status = adapter.get_status()

    assert status.is_operational is False
    assert "off-chain" in status.network or "disabled" in status.note.lower()

    report = make_test_report(scan_id="scan-mode-a", target="https://example.com", score=70)
    integrity = adapter.generate_integrity_info(
        scan_id=report.scan_id,
        submitted_input=report.submitted_input,
        input_type=report.input_type,
        classification=report.risk_assessment.classification.value,
        risk_score=report.risk_assessment.risk_score,
        timestamp_str=report.timestamp.isoformat(),
        rules_triggered=report.risk_assessment.rules_triggered,
    )

    assert integrity.blockchain_status == "NOT_REGISTERED"
    assert integrity.transaction_hash is None
    assert len(integrity.canonical_sha256) == 64

    # Verify report
    report.report_integrity = integrity
    ver = adapter.verify_report(report)

    assert ver.is_valid is True
    assert ver.integrity_status == "MATCH"
    assert ver.blockchain_status == "NOT_REGISTERED"
    assert "NOT_REGISTERED" in ver.message


# ==============================================================================
# MODE B: Local Blockchain Provider Configured
# ==============================================================================
def test_mode_b_local_blockchain_provider_configured():
    """Verify Mode B: operational local Hardhat node (Chain ID 31337)."""
    with patch("web3.Web3") as mock_web3_cls:
        mock_w3 = MagicMock()
        mock_w3.is_connected.return_value = True
        mock_w3.eth.chain_id = 31337
        mock_w3.to_checksum_address.side_effect = lambda addr: addr
        mock_w3.eth.get_code.return_value = b"\x60\x80\x60\x40"  # Valid contract bytecode
        mock_contract = MagicMock()
        mock_contract.functions.reportCount().call.return_value = 42
        mock_w3.eth.contract.return_value = mock_contract
        mock_web3_cls.return_value = mock_w3

        adapter = BlockchainAdapter(
            provider_uri="http://127.0.0.1:8545",
            contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
            enabled=True,
        )
        status = adapter.get_status()

        assert status.is_operational is True
        assert status.chain_id == 31337
        assert "Hardhat" in status.network
        assert status.signer_mode == "local_dev_account"
        assert status.report_count == 42


# ==============================================================================
# MODE C: Invalid Provider or Contract Configuration
# ==============================================================================
def test_mode_c_invalid_provider_unreachable():
    """Verify Mode C: unreachable provider transitions cleanly to local fallback."""
    with patch("web3.Web3") as mock_web3_cls:
        mock_w3 = MagicMock()
        mock_w3.is_connected.return_value = False
        mock_web3_cls.return_value = mock_w3

        adapter = BlockchainAdapter(
            provider_uri="http://127.0.0.1:9999",
            contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
            enabled=True,
        )
        status = adapter.get_status()

        assert status.is_operational is False
        assert "offline" in status.note.lower()


def test_mode_c_contract_not_deployed_empty_bytecode():
    """Verify Mode C: valid RPC node but empty contract address bytecode."""
    with patch("web3.Web3") as mock_web3_cls:
        mock_w3 = MagicMock()
        mock_w3.is_connected.return_value = True
        mock_w3.eth.chain_id = 31337
        mock_w3.to_checksum_address.side_effect = lambda addr: addr
        mock_w3.eth.get_code.return_value = b""  # Empty code (not deployed)
        mock_web3_cls.return_value = mock_w3

        adapter = BlockchainAdapter(
            provider_uri="http://127.0.0.1:8545",
            contract_address="0x0000000000000000000000000000000000000000",
            enabled=True,
        )
        status = adapter.get_status()

        assert status.is_operational is False
        assert "no contract bytecode deployed" in status.note.lower()


# ==============================================================================
# MODE D: Transaction Failure
# ==============================================================================
def test_mode_d_transaction_reverted():
    """Verify Mode D: on-chain transaction failure / revert produces FAILED status."""
    with patch("web3.Web3") as mock_web3_cls:
        mock_w3 = MagicMock()
        mock_w3.is_connected.return_value = True
        mock_w3.eth.chain_id = 31337
        mock_w3.to_checksum_address.side_effect = lambda addr: addr
        mock_w3.eth.get_code.return_value = b"\x60\x80"
        mock_w3.eth.accounts = ["0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"]

        mock_contract = MagicMock()
        mock_contract.functions.hashExists().call.return_value = False
        mock_contract.functions.registerReport().transact.return_value = b"\xaa" * 32

        mock_receipt = MagicMock()
        mock_receipt.status = 0  # 0 indicates transaction reverted!
        mock_receipt.transactionHash = b"\xbb" * 32
        mock_w3.eth.wait_for_transaction_receipt.return_value = mock_receipt

        mock_w3.eth.contract.return_value = mock_contract
        mock_web3_cls.return_value = mock_w3

        adapter = BlockchainAdapter(
            provider_uri="http://127.0.0.1:8545",
            contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
            enabled=True,
        )

        integrity = adapter.generate_integrity_info(
            scan_id="scan-mode-d",
            submitted_input="https://example.com/revert",
            input_type="url",
            classification="HIGH_RISK",
            risk_score=70,
            timestamp_str="2026-11-14T10:00:00Z",
        )

        assert integrity.blockchain_status == "FAILED"


# ==============================================================================
# MODE E: Successful Registration & Contract Readback
# ==============================================================================
def test_mode_e_successful_registration_and_readback():
    """Verify Mode E: full on-chain registration, receipt confirmation, and readback."""
    with patch("web3.Web3") as mock_web3_cls:
        mock_w3 = MagicMock()
        mock_w3.is_connected.return_value = True
        mock_w3.eth.chain_id = 31337
        mock_w3.to_checksum_address.side_effect = lambda addr: addr
        mock_w3.eth.get_code.return_value = b"\x60\x80"
        mock_w3.eth.accounts = ["0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"]

        mock_contract = MagicMock()
        # Hash not registered yet
        mock_contract.functions.hashExists().call.return_value = False
        mock_contract.functions.registerReport().transact.return_value = b"\xcc" * 32

        mock_receipt = MagicMock()
        mock_receipt.status = 1  # 1 indicates transaction success!
        mock_receipt.blockNumber = 12345
        mock_receipt.transactionHash.hex.return_value = "0x" + "cc" * 32
        mock_w3.eth.wait_for_transaction_receipt.return_value = mock_receipt

        # Readback verification passes
        mock_contract.functions.verifyReport().call.return_value = True
        mock_contract.functions.getReport().call.return_value = (
            b"\x01" * 32,
            b"\x02" * 32,
            "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            1731578400,
        )

        mock_w3.eth.contract.return_value = mock_contract
        mock_web3_cls.return_value = mock_w3

        adapter = BlockchainAdapter(
            provider_uri="http://127.0.0.1:8545",
            contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
            enabled=True,
        )

        report = make_test_report(scan_id="scan-mode-e", target="https://example.com/anchored", score=70)
        integrity = adapter.generate_integrity_info(
            scan_id=report.scan_id,
            submitted_input=report.submitted_input,
            input_type=report.input_type,
            classification=report.risk_assessment.classification.value,
            risk_score=report.risk_assessment.risk_score,
            timestamp_str=report.timestamp.isoformat(),
            rules_triggered=report.risk_assessment.rules_triggered,
        )

        assert integrity.blockchain_status == "ANCHORED"
        assert integrity.network == "Hardhat Local Devnet"
        assert integrity.contract_address == "0x5FbDB2315678afecb367f032d93F642f64180aa3"
        assert integrity.transaction_hash == "0x" + "cc" * 32

        # Verify report on-chain
        report.report_integrity = integrity
        ver = adapter.verify_report(report)

        assert ver.is_valid is True
        assert ver.integrity_status == "MATCH"
        assert ver.blockchain_status == "ANCHORED"
        assert "anchored on-chain" in ver.message
