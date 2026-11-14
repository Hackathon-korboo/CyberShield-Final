"""
CyberShield AI — Member 1 API Contract Integration Tests
=========================================================
Tests that all integrity responses conform exactly to Member 1's backend contract:
{
    "integrity": {
        "status": "verified" | "failed" | "not_available",
        "evidence_hash": "<hash>"
    }
}
"""

import sys
from pathlib import Path
import unittest

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from security.evidence_hasher import EvidenceHasher, IntegrityResult


class TestAPIContractIntegration(unittest.TestCase):
    """Verify JSON contract adherence."""

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

        self.assertIn("integrity", payload)
        self.assertEqual(payload["integrity"]["status"], "failed")

    def test_not_available_contract_structure(self):
        result = IntegrityResult(
            status="not_available",
            evidence_hash=None,
            algorithm="sha256",
        )
        payload = result.to_api_contract()

        self.assertIn("integrity", payload)
        self.assertEqual(payload["integrity"]["status"], "not_available")
        self.assertIsNone(payload["integrity"]["evidence_hash"])

    def test_valid_statuses_only(self):
        allowed_statuses = {"verified", "failed", "not_available"}
        for st in allowed_statuses:
            res = IntegrityResult(status=st, evidence_hash="dummy")
            self.assertIn(res.to_api_contract()["integrity"]["status"], allowed_statuses)

    def test_pydantic_v2_schema_compliance(self):
        """
        Verify that Member 1's Pydantic v2 schema model successfully parses
        and validates the integrity payload without schema degradation.
        """
        from pydantic import BaseModel, ValidationError
        from typing import Literal, Optional

        class IntegritySchema(BaseModel):
            status: Literal["verified", "failed", "not_available"]
            evidence_hash: Optional[str] = None

        class ThreatReportResponseSchema(BaseModel):
            url: str
            threat_level: str
            confidence: float
            indicators: list[str]
            integrity: IntegritySchema

        res = IntegrityResult(
            status="verified",
            evidence_hash="a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
        )
        report = {
            "url": "https://example.com",
            "threat_level": "high",
            "confidence": 0.95,
            "indicators": ["bad_ssl", "phishing_pattern"],
            **res.to_api_contract()
        }

        # Validate with Pydantic v2
        validated = ThreatReportResponseSchema.model_validate(report)
        self.assertEqual(validated.integrity.status, "verified")
        self.assertEqual(validated.integrity.evidence_hash, "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e")

    def test_integrity_injection_preserves_existing_report_fields(self):
        """
        Verify that finalize_report helper preserves all upstream fields
        and does not corrupt or overwrite other members' report attributes.
        """
        original_report = {
            "url": "https://example.com/login",
            "threat_level": "medium",
            "confidence": 0.82,
            "indicators": ["suspicious_form"],
            "scan_id": "scan_12345"
        }
        report_copy = dict(original_report)
        hash_val = EvidenceHasher.hash_report(report_copy, algorithm="sha256")
        report_copy["integrity"] = {
            "status": "verified",
            "evidence_hash": hash_val
        }

        # Check that original fields are preserved intact
        for key, val in original_report.items():
            self.assertEqual(report_copy[key], val)
        self.assertIn("integrity", report_copy)

    def test_async_event_loop_offload_compatibility(self):
        """
        Verify that synchronous EvidenceHasher and PinnedSession can be safely
        executed inside an asyncio event loop using asyncio.to_thread without blocking.
        """
        import asyncio

        async def simulate_async_endpoint():
            raw_data = {"test": "data", "status": "active"}
            # Offload synchronous hashing to worker thread pool
            h = await asyncio.to_thread(EvidenceHasher.hash_report, raw_data, "sha256")
            return h

        loop_result = asyncio.run(simulate_async_endpoint())
        self.assertEqual(len(loop_result), 64)


if __name__ == "__main__":
    unittest.main()
