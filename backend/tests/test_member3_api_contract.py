"""
CyberShield AI 2.0 — Member 3 API Contract Integration Tests (Integrated Backend)
=================================================================================
Tests that all integrity responses conform exactly to Member 1's backend contract:
{
    "integrity": {
        "status": "verified" | "failed" | "not_available",
        "evidence_hash": "<hash>"
    }
}
"""

import unittest
from backend.app.services.blockchain.evidence_hasher import IntegrityResult
from backend.app.schemas.unified_report import ReportIntegrityInfo


class TestAPIContractIntegration(unittest.TestCase):
    """Verify JSON contract adherence and Pydantic schema compatibility."""

    def test_verified_contract_structure(self):
        result = IntegrityResult(
            status="verified",
            evidence_hash="a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
            algorithm="sha256",
        )
        payload = result.to_api_contract()

        self.assertIn("integrity", payload)
        self.assertEqual(list(payload["integrity"].keys()), ["status", "evidence_hash"])
        self.assertEqual(payload["integrity"]["status"], "verified")
        self.assertEqual(
            payload["integrity"]["evidence_hash"],
            "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
        )

    def test_failed_contract_structure(self):
        result = IntegrityResult(
            status="failed",
            evidence_hash="b7f1a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
            algorithm="sha256",
            tamper_detected=True,
        )
        payload = result.to_api_contract()

        self.assertEqual(payload["integrity"]["status"], "failed")
        self.assertEqual(
            payload["integrity"]["evidence_hash"],
            "b7f1a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
        )

    def test_not_available_contract_structure(self):
        result = IntegrityResult(
            status="not_available",
            evidence_hash="",
            algorithm="sha256",
        )
        payload = result.to_api_contract()

        self.assertEqual(payload["integrity"]["status"], "not_available")
        self.assertEqual(payload["integrity"]["evidence_hash"], "")

    def test_valid_statuses_only(self):
        allowed_statuses = {"verified", "failed", "not_available"}
        for st in allowed_statuses:
            res = IntegrityResult(status=st, evidence_hash="dummy")
            self.assertIn(res.to_api_contract()["integrity"]["status"], allowed_statuses)

    def test_pydantic_v2_schema_compliance(self):
        result = IntegrityResult(
            status="verified",
            evidence_hash="a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
            algorithm="sha256",
        )
        # Should initialize ReportIntegrityInfo smoothly
        info = ReportIntegrityInfo(
            canonical_sha256=result.evidence_hash,
            blockchain_status="ANCHORED",
            network="Hardhat Local Devnet",
            contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
            transaction_hash="0x" + "11" * 32,
        )
        self.assertEqual(info.canonical_sha256, result.evidence_hash)
        self.assertEqual(info.blockchain_status, "ANCHORED")


if __name__ == "__main__":
    unittest.main()
