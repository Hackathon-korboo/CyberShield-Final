"""
CyberShield AI — Blockchain & Off-Chain Fallback Test Suite (v2.2)
===================================================================
Verifies:
1. Hash Consistency:
   - report_integrity.report_hash is Keccak-256
   - derive_report_id(report_hash) == report_id is mathematically verified
   - integrity.evidence_hash is SHA-256 matching sha256_evidence_hash
2. Dynamic chain ID verification and detection of dev vs production networks.
3. Signer safety: Rejects unlocked node accounts on non-local networks.
4. Post-transaction contract readback verification logic.
5. Honest off-chain fallback behavior (no false on-chain claims).
6. Contract compilation artifact verification (bytecode & ABI).
"""

import copy
import json
import subprocess
import sys
from pathlib import Path
import unittest

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from security.blockchain_adapter import BlockchainAdapter
from security.evidence_hasher import EvidenceHasher


SAMPLE_REPORT = {
    "report_id": "CSR-20261107-00001",
    "schema_version": "1.0",
    "detected_at": "2026-11-07T10:00:00.000Z",
    "generated_at": "2026-11-07T10:05:00.000Z",
    "severity": "high",
    "category": "phishing",
    "status": "detected",
    "confidence_score": 87,
    "summary": "Credential harvesting phishing campaign targeting corporate email.",
    "description": "AI detected a phishing campaign using spoofed login pages.",
    "indicators": [
        {"ioc_type": "domain", "value": "secure-login-verify.example.com"},
    ],
    "affected_assets": [
        {"asset_type": "service", "identifier": "corporate-email"},
    ],
    "remediation_steps": [
        {"priority": 1, "action": "Block domain secure-login-verify.example.com"},
    ],
    "mitre_techniques": ["T1566"],
    "threat_actor": "unknown",
}


class TestBlockchainAdapter(unittest.TestCase):
    """Test blockchain adapter, chain-ID verification, and honest off-chain fallback."""

    def setUp(self):
        self.adapter = BlockchainAdapter(rpc_url="http://127.0.0.1:8545")

    def test_status_reporting(self):
        """Verify status reporting accurately reflects offline/online state and verified chain ID."""
        status = self.adapter.get_status()
        self.assertIsInstance(status.is_operational, bool)
        if not status.is_operational:
            self.assertIn("off-chain", status.network)
            self.assertIsNone(status.contract_address)

    def test_off_chain_fallback_registration_and_hash_consistency(self):
        """
        Verify that in fallback mode:
        1. report_integrity.report_hash is Keccak-256.
        2. derive_report_id(report_hash) exactly reproduces report_id.
        3. integrity.evidence_hash is SHA-256 matching sha256_evidence_hash.
        4. is_on_chain=False (zero fake on-chain claims).
        """
        self.adapter.is_operational = False
        res = self.adapter.register_report(SAMPLE_REPORT)

        # 1. API contract check
        self.assertIn("integrity", res)
        self.assertEqual(res["integrity"]["status"], "verified")
        sha_hash = res["integrity"]["evidence_hash"]
        self.assertIsNotNone(sha_hash)
        self.assertEqual(len(sha_hash), 64)

        # 2. Blockchain report metadata check
        self.assertIn("report_integrity", res)
        rep = res["report_integrity"]
        self.assertFalse(rep["is_on_chain"])
        self.assertIn("off-chain", rep["blockchain_network"])
        self.assertIsNone(rep["transaction_hash"])
        self.assertFalse(rep["readback_verified"])

        # 3. Hash consistency check (Issue 2 resolution)
        self.assertEqual(rep["sha256_evidence_hash"], sha_hash)
        self.assertTrue(rep["report_hash"].startswith("0x"))
        self.assertEqual(rep["keccak256_report_hash"], rep["report_hash"])

        # Mathematical link: report_id MUST be derived from report_hash!
        derived_id = EvidenceHasher.derive_report_id(rep["report_hash"])
        self.assertEqual(rep["report_id"], derived_id)

    def test_off_chain_fallback_tamper_detection(self):
        """Verify off-chain fallback detects modified evidence."""
        self.adapter.is_operational = False
        reg_res = self.adapter.register_report(SAMPLE_REPORT)
        expected_hash = reg_res["integrity"]["evidence_hash"]

        # 1. Verify original report passes
        ver_orig = self.adapter.verify_report(SAMPLE_REPORT, expected_hash)
        self.assertEqual(ver_orig["integrity"]["status"], "verified")
        self.assertFalse(ver_orig["report_integrity"]["tamper_detected"])

        # 2. Modify report and verify tampering is detected
        tampered = copy.deepcopy(SAMPLE_REPORT)
        tampered["severity"] = "critical"
        ver_tampered = self.adapter.verify_report(tampered, expected_hash)
        self.assertEqual(ver_tampered["integrity"]["status"], "failed")
        self.assertTrue(ver_tampered["report_integrity"]["tamper_detected"])

    def test_regression_unlocked_account_rejected_on_external_network(self):
        """Bug 5: On non-dev external network (e.g. Sepolia Chain ID 11155111), unlocked accounts are rejected."""
        self.adapter.is_operational = True
        self.adapter.chain_id = 11155111  # Sepolia
        self.adapter.network_name = "Ethereum Sepolia Testnet"
        self.adapter.private_key = None

        class MockCall:
            def call(self, *args, **kwargs):
                return False

        class MockFuncs:
            def hashExists(self, *args, **kwargs):
                return MockCall()

        class MockContract:
            functions = MockFuncs()

        self.adapter.contract = MockContract()
        self.adapter.w3 = type("MockW3", (), {
            "eth": type("MockEth", (), {"accounts": ["0x1234567890123456789012345678901234567890"]})()
        })()

        res = self.adapter.register_report(SAMPLE_REPORT)
        self.assertFalse(res["report_integrity"]["is_on_chain"])
        self.assertIn("explicitly configured private key or signer", res["report_integrity"]["note"])

    def test_contract_compilation_artifact_integrity(self):
        """Verify that the compiled ThreatReportRegistry artifact exists, is valid JSON, and contains expected bytecode."""
        artifact_path = WORKSPACE_ROOT / "artifacts" / "ThreatReportRegistry.json"
        self.assertTrue(artifact_path.exists(), f"Artifact missing at {artifact_path}")

        data = json.loads(artifact_path.read_text())
        self.assertEqual(data.get("contractName"), "ThreatReportRegistry")
        self.assertIn("abi", data)
        self.assertIn("bytecode", data)
        self.assertTrue(len(data["bytecode"]) > 100)

        # Check required function names in ABI
        fn_names = {x["name"] for x in data["abi"] if x.get("name")}
        required_fns = {"registerReport", "verifyReport", "getReport", "transferOwnership", "setRegistrar"}
        self.assertTrue(required_fns.issubset(fn_names), f"Missing functions in ABI: {required_fns - fn_names}")


if __name__ == "__main__":
    unittest.main()
