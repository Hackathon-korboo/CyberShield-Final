"""
CyberShield AI — Cryptographic Integrity & Tamper Detection Test Suite
=======================================================================
Verifies:
1. Deterministic canonical serialization (key order independence).
2. Genuine SHA-256 & Keccak-256 cryptographic hashing.
3. Bug 1 Regression: Keccak-256 produces authentic Ethereum digest distinct from SHA-256.
4. Explicit error handling for unsupported algorithms.
5. Original report verification (status: "verified").
6. Tampering & mutation detection (status: "failed", tamper_detected: true).
7. Cross-language schema compatibility with Member 1's UnifiedThreatReport.
8. API contract adherence: {"integrity": {"status": "...", "evidence_hash": "..."}}.
"""

import copy
import sys
from pathlib import Path
import unittest

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from security.evidence_hasher import EvidenceHasher, _keccak256_bytes


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
    "description": (
        "AI detected a phishing campaign using spoofed login pages to harvest "
        "credentials. Multiple users received emails with malicious links."
    ),
    "indicators": [
        {"ioc_type": "domain", "value": "secure-login-verify.example.com"},
        {"ioc_type": "hash", "value": "d41d8cd98f00b204e9800998ecf8427e"},
    ],
    "affected_assets": [
        {"asset_type": "service", "identifier": "corporate-email"},
        {"asset_type": "user", "identifier": "user-group-finance"},
    ],
    "remediation_steps": [
        {"priority": 1, "action": "Block domain secure-login-verify.example.com at DNS level"},
        {"priority": 2, "action": "Force password reset for all users who clicked the link"},
        {"priority": 3, "action": "Enable MFA for all corporate email accounts"},
    ],
    "mitre_techniques": ["T1566", "T1078"],
    "threat_actor": "unknown",
}

# Known baseline values established in blockchain integration v2
EXPECTED_KECCAK_HASH = "0xd5469a33795e145ad89bc2e577d20545f0e5b6e72b49b7419c78ef4f630970f7"
EXPECTED_KECCAK_ID = "0x56ab21e4ee1c49b609e04024f8c9062afb6e1fb126101bac1a64858ade9c6ca9"


class TestCryptographicIntegrity(unittest.TestCase):
    """Cryptographic evidence hashing and tamper verification tests."""

    def test_canonical_serialization_determinism(self):
        """Verify that dictionary key insertion order does not affect the output."""
        dict_a = {"z_key": 1, "a_key": 2, "m_key": {"b": 3, "a": 4}}
        dict_b = {"a_key": 2, "m_key": {"a": 4, "b": 3}, "z_key": 1}

        canon_a = EvidenceHasher.canonicalize(dict_a)
        canon_b = EvidenceHasher.canonicalize(dict_b)

        self.assertEqual(canon_a, canon_b)
        self.assertEqual(canon_a, '{"a_key":2,"m_key":{"a":4,"b":3},"z_key":1}')

    def test_cross_language_keccak_hash_match(self):
        """Verify that Keccak-256 hash matches the baseline from Hardhat & TypeScript."""
        computed_hash = EvidenceHasher.hash_report(SAMPLE_REPORT, algorithm="keccak256")
        computed_id = EvidenceHasher.derive_report_id(computed_hash)

        self.assertEqual(computed_hash.lower(), EXPECTED_KECCAK_HASH.lower())
        self.assertEqual(computed_id.lower(), EXPECTED_KECCAK_ID.lower())

    def test_sha256_evidence_hashing(self):
        """Verify SHA-256 evidence hashing produces a valid 64-char hex string."""
        sha_hash = EvidenceHasher.hash_report(SAMPLE_REPORT, algorithm="sha256")
        self.assertEqual(len(sha_hash), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in sha_hash.lower()))

    # ── REGRESSION TESTS (Bug 1: Genuine Keccak-256 vs SHA-256) ──

    def test_regression_keccak256_distinct_from_sha256(self):
        """Bug 1: Keccak-256 must NEVER be identical to SHA-256 for the same data."""
        sha_hash = EvidenceHasher.hash_report(SAMPLE_REPORT, algorithm="sha256")
        keccak_hash = EvidenceHasher.hash_report(SAMPLE_REPORT, algorithm="keccak256")

        clean_sha = sha_hash.lower().removeprefix("0x")
        clean_keccak = keccak_hash.lower().removeprefix("0x")

        # They MUST NOT be identical!
        self.assertNotEqual(
            clean_sha, clean_keccak,
            "Critical Error: Keccak-256 and SHA-256 returned identical hashes!"
        )

    def test_regression_genuine_keccak_test_vectors(self):
        """Bug 1: Verify standard Ethereum Keccak-256 test vectors."""
        # Empty string Keccak-256
        empty_keccak = _keccak256_bytes(b"").hex()
        self.assertEqual(empty_keccak, "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470")

        # 'hello' Keccak-256
        hello_keccak = _keccak256_bytes(b"hello").hex()
        self.assertEqual(hello_keccak, "1c8aff950685c2ed4bc3174f3472287b56d9517b9c948127319a09a7a36deac8")

    def test_regression_unsupported_algorithm_raises_error(self):
        """Bug 1: Unsupported algorithms must raise an explicit ValueError rather than fallback."""
        with self.assertRaises(ValueError):
            EvidenceHasher.hash_report(SAMPLE_REPORT, algorithm="md5")

        with self.assertRaises(ValueError):
            EvidenceHasher.hash_report(SAMPLE_REPORT, algorithm="sha1")

    # ── INTEGRITY & TAMPERING TESTS ──────────────────────────────

    def test_original_report_verification_passes(self):
        """Verify original report against its own SHA-256 and Keccak-256 hashes."""
        sha_hash = EvidenceHasher.hash_report(SAMPLE_REPORT, algorithm="sha256")
        result = EvidenceHasher.verify_integrity(SAMPLE_REPORT, sha_hash, algorithm="sha256")

        self.assertEqual(result.status, "verified")
        self.assertFalse(result.tamper_detected)
        self.assertEqual(result.evidence_hash, sha_hash)

        # Check API contract structure
        contract = result.to_api_contract()
        self.assertIn("integrity", contract)
        self.assertEqual(contract["integrity"]["status"], "verified")
        self.assertEqual(contract["integrity"]["evidence_hash"], sha_hash)

    def test_tamper_detection_on_severity_mutation(self):
        """Demonstrate that modifying 'severity' from 'high' to 'low' fails verification."""
        original_hash = EvidenceHasher.hash_report(SAMPLE_REPORT, algorithm="sha256")

        tampered_report = copy.deepcopy(SAMPLE_REPORT)
        tampered_report["severity"] = "low"  # Maliciously downplay risk

        result = EvidenceHasher.verify_integrity(tampered_report, original_hash, algorithm="sha256")

        self.assertEqual(result.status, "failed")
        self.assertTrue(result.tamper_detected)
        self.assertNotEqual(result.evidence_hash, original_hash)
        self.assertIn("Tampering detected", result.details)

        # Verify API contract output reflects failure
        contract = result.to_api_contract()
        self.assertEqual(contract["integrity"]["status"], "failed")

    def test_tamper_detection_on_indicator_mutation(self):
        """Demonstrate that tampering with an IOC value fails verification."""
        original_hash = EvidenceHasher.hash_report(SAMPLE_REPORT, algorithm="sha256")

        tampered_report = copy.deepcopy(SAMPLE_REPORT)
        tampered_report["indicators"][0]["value"] = "tampered-domain.example.com"

        result = EvidenceHasher.verify_integrity(tampered_report, original_hash, algorithm="sha256")
        self.assertEqual(result.status, "failed")
        self.assertTrue(result.tamper_detected)

    def test_tamper_detection_on_confidence_mutation(self):
        """Demonstrate that altering confidence score fails verification."""
        original_hash = EvidenceHasher.hash_report(SAMPLE_REPORT, algorithm="sha256")

        tampered_report = copy.deepcopy(SAMPLE_REPORT)
        tampered_report["confidence_score"] = 99

        result = EvidenceHasher.verify_integrity(tampered_report, original_hash, algorithm="sha256")
        self.assertEqual(result.status, "failed")
        self.assertTrue(result.tamper_detected)

    def test_array_sort_insensitivity(self):
        """
        Verify that raw array ordering (e.g. indicators presented in reverse)
        still yields the identical hash due to canonical normalization.
        """
        reordered_report = copy.deepcopy(SAMPLE_REPORT)
        reordered_report["indicators"].reverse()
        reordered_report["mitre_techniques"].reverse()

        hash_original = EvidenceHasher.hash_report(SAMPLE_REPORT, algorithm="sha256")
        hash_reordered = EvidenceHasher.hash_report(reordered_report, algorithm="sha256")

        self.assertEqual(hash_original, hash_reordered)


if __name__ == "__main__":
    unittest.main()
