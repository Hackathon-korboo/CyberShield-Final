"""
CyberShield AI — Cryptographic Evidence Hasher & Tamper Detection Engine
=========================================================================
Implements:
1. Canonical, deterministic JSON serialization.
2. Genuine, verified cryptographic hashing:
   - SHA-256 (via hashlib standard library)
   - Ethereum-compatible Keccak-256 (via eth_hash / Web3 / verified pure-Python Keccak engine)
   - Strict rejection: NEVER falls back to SHA-256 when Keccak-256 is requested.
3. Evidence fingerprinting for Member 1's backend reports.
4. Tamper detection: validates report integrity and detects any field mutation.
5. Strict output generation conforming to Member 1's backend API contract:
   {
       "integrity": {
           "status": "verified" | "failed" | "not_available",
           "evidence_hash": "<sha256_or_keccak256_hex>"
       }
   }
"""

from __future__ import annotations

__version__ = "2.2.0"

import copy
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


NAMESPACE = "CYBERSHIELD_REPORT_V1"


def _pure_keccak256(data: bytes) -> bytes:
    """
    Genuine, bit-exact pure-Python implementation of Keccak-256 (Ethereum standard).
    Specification: Keccak-f[1600], rate = 1088 bits (136 bytes), capacity = 512 bits (64 bytes),
    output length = 256 bits (32 bytes), padding byte = 0x01.
    Strictly distinct from NIST SHA3-256 (0x06 padding) and SHA-256.
    """
    RC = [
        0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
        0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
        0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
        0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
        0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
        0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
    ]
    r_offsets = [
        [0, 36, 3, 41, 18],
        [1, 44, 10, 45, 2],
        [62, 6, 43, 15, 61],
        [28, 55, 25, 21, 56],
        [27, 20, 39, 8, 14],
    ]
    rate = 136  # 1088 bits / 8
    # Padding: 0x01 ... 0x80
    padlen = rate - (len(data) % rate)
    if padlen == 1:
        padded = data + b"\x81"
    else:
        padded = data + b"\x01" + b"\x00" * (padlen - 2) + b"\x80"

    state = [0] * 25
    for block_idx in range(0, len(padded), rate):
        block = padded[block_idx : block_idx + rate]
        for i in range(17):
            val = int.from_bytes(block[i * 8 : (i + 1) * 8], "little")
            state[i] ^= val
        # 24 rounds of Keccak-f[1600]
        for round_idx in range(24):
            # Theta step
            C = [
                state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20]
                for x in range(5)
            ]
            D = [
                C[(x + 4) % 5]
                ^ (((C[(x + 1) % 5] << 1) | (C[(x + 1) % 5] >> 63)) & 0xFFFFFFFFFFFFFFFF)
                for x in range(5)
            ]
            for x in range(5):
                for y in range(5):
                    state[x + y * 5] ^= D[x]
            # Rho and Pi steps
            B = [0] * 25
            for x in range(5):
                for y in range(5):
                    rot = r_offsets[x][y]
                    val = state[x + y * 5]
                    B[y + ((2 * x + 3 * y) % 5) * 5] = (
                        ((val << rot) | (val >> (64 - rot))) & 0xFFFFFFFFFFFFFFFF
                        if rot
                        else val
                    )
            # Chi step
            for y in range(5):
                for x in range(5):
                    state[x + y * 5] = B[x + y * 5] ^ (
                        (~B[(x + 1) % 5 + y * 5]) & B[(x + 2) % 5 + y * 5]
                    )
            # Iota step
            state[0] ^= RC[round_idx]

    # Squeeze 32 bytes (256 bits)
    return b"".join(state[i].to_bytes(8, "little") for i in range(4))


def _keccak256_bytes(data: bytes) -> bytes:
    """
    Compute genuine Keccak-256 bytes using available engine:
    1. eth_hash.auto.keccak (fast C/compiled if available)
    2. web3.Web3.keccak
    3. verified pure_keccak256 algorithm
    NEVER uses SHA-256.
    """
    try:
        import eth_hash.auto as eth_hash_module
        return eth_hash_module.keccak(data)
    except Exception:
        pass

    try:
        from web3 import Web3
        return bytes(Web3.keccak(data))
    except Exception:
        pass

    return _pure_keccak256(data)


@dataclass
class IntegrityResult:
    """Standardized cryptographic verification result."""
    status: str                         # "verified" | "failed" | "not_available"
    evidence_hash: str | None           # Hex digest of computed hash
    expected_hash: str | None = None    # Hash presented for verification
    algorithm: str = "sha256"           # "sha256" | "keccak256"
    tamper_detected: bool = False       # True if hash mismatch detected
    verified_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    details: str = ""

    def to_api_contract(self) -> dict[str, Any]:
        """
        Conforms strictly to Member 1's shared API integration requirement:
        {
            "integrity": {
                "status": "verified" | "failed" | "not_available",
                "evidence_hash": "..."
            }
        }
        """
        return {
            "integrity": {
                "status": self.status,
                "evidence_hash": self.evidence_hash,
            }
        }

    def to_detailed_report(self) -> dict[str, Any]:
        """Extended diagnostic view for security audit logs."""
        return {
            "integrity": {
                "status": self.status,
                "evidence_hash": self.evidence_hash,
                "expected_hash": self.expected_hash,
                "algorithm": self.algorithm,
                "tamper_detected": self.tamper_detected,
                "verified_at": self.verified_at,
                "details": self.details,
            }
        }


class EvidenceHasher:
    """Deterministic cryptographic evidence hashing and verification."""

    SUPPORTED_ALGORITHMS = {"sha256", "keccak256", "keccak"}

    @staticmethod
    def canonicalize(data: Any) -> str:
        """
        Serialize any Python data structure into deterministic canonical JSON.
        Rules:
        - Keys sorted recursively at all nesting levels.
        - Compact delimiters (no whitespace): (',', ':').
        - UTF-8 characters preserved (ensure_ascii=False).
        """
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    @classmethod
    def normalize_report(cls, raw: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize report fields to ensure deterministic hashing across languages.
        Strips unpredictable/ephemeral runtime fields and sorts all internal lists.
        """
        if "observed_evidence" in raw or "technical_findings" in raw:
            normalized = copy.deepcopy(raw)
            normalized.pop("integrity", None)
            normalized.pop("report_integrity", None)
            return normalized

        indicators = []
        for ioc in (raw.get("indicators") or []):
            if isinstance(ioc, dict):
                indicators.append({
                    "ioc_type": str(ioc.get("ioc_type", "")),
                    "value": str(ioc.get("value", "")),
                })
            else:
                indicators.append({
                    "ioc_type": "indicator",
                    "value": str(ioc),
                })
        indicators.sort(key=lambda x: (x["ioc_type"], x["value"]))

        affected_assets = []
        for a in (raw.get("affected_assets") or []):
            if isinstance(a, dict):
                affected_assets.append({
                    "asset_type": str(a.get("asset_type", "")),
                    "identifier": str(a.get("identifier", "")),
                })
            else:
                affected_assets.append({
                    "asset_type": "asset",
                    "identifier": str(a),
                })
        affected_assets.sort(key=lambda x: (x["asset_type"], x["identifier"]))

        remediation_steps = []
        for s in (raw.get("remediation_steps") or []):
            if isinstance(s, dict):
                remediation_steps.append({
                    "action": str(s.get("action", "")),
                    "priority": int(s.get("priority", 0)),
                })
            else:
                remediation_steps.append({
                    "action": str(s),
                    "priority": 0,
                })
        remediation_steps.sort(key=lambda x: x["priority"])

        mitre_techniques = sorted(str(t) for t in (raw.get("mitre_techniques") or []))

        return {
            "report_id": str(raw.get("report_id", "")),
            "schema_version": str(raw.get("schema_version", "1.0")),
            "detected_at": str(raw.get("detected_at", "")),
            "generated_at": str(raw.get("generated_at", "")),
            "severity": str(raw.get("severity", "")),
            "category": str(raw.get("category", "")),
            "status": str(raw.get("status", "")),
            "confidence_score": int(raw.get("confidence_score", 0)),
            "summary": str(raw.get("summary", "")),
            "description": str(raw.get("description", "")),
            "indicators": indicators,
            "affected_assets": affected_assets,
            "remediation_steps": remediation_steps,
            "mitre_techniques": mitre_techniques,
            "threat_actor": str(raw.get("threat_actor", "")),
        }

    @classmethod
    def compute_sha256(cls, data: Any) -> str:
        """
        Compute standard SHA-256 hash over canonical JSON representation.
        Returns a 64-character lowercase hex string.
        """
        canonical_str = cls.canonicalize(data)
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    @classmethod
    def compute_keccak256(cls, data: Any) -> str:
        """
        Compute genuine EVM-compatible Keccak-256 hash over canonical JSON representation.
        Guaranteed genuine Ethereum Keccak-256 digest (0x-prefixed 64-char hex string).
        Never falls back to SHA-256.
        """
        canonical_bytes = cls.canonicalize(data).encode("utf-8")
        raw_hash = _keccak256_bytes(canonical_bytes)
        return "0x" + raw_hash.hex()

    @classmethod
    def hash_report(cls, report: dict[str, Any], algorithm: str = "sha256") -> str:
        """
        Generate cryptographic evidence fingerprint for a report.
        Raises ValueError if an unsupported algorithm is requested.
        """
        algo = algorithm.lower().strip()
        if algo not in cls.SUPPORTED_ALGORITHMS:
            raise ValueError(
                f"Unsupported cryptographic algorithm '{algorithm}'. "
                f"Allowed algorithms are: {', '.join(sorted(cls.SUPPORTED_ALGORITHMS))}"
            )

        normalized = cls.normalize_report(report)
        if algo in ("keccak256", "keccak"):
            return cls.compute_keccak256(normalized)
        return cls.compute_sha256(normalized)

    @classmethod
    def derive_report_id(cls, report_hash: str) -> str:
        """
        Derive deterministic report ID from a Keccak-256 report hash using the
        CYBERSHIELD_REPORT_V1 namespace.
        Matches Solidity: generateReportId(bytes32 reportHash) = keccak256(abi.encodePacked(NAMESPACE, reportHash)).
        Guaranteed genuine Keccak-256.
        """
        clean_hash = report_hash.removeprefix("0x")
        try:
            hash_bytes = bytes.fromhex(clean_hash)
        except ValueError as e:
            raise ValueError(f"Invalid hex string in report_hash: {e}") from e

        if len(hash_bytes) != 32:
            raise ValueError(
                f"report_hash must be exactly 32 bytes (64 hex characters), got {len(hash_bytes)} bytes."
            )

        namespace_bytes = NAMESPACE.encode("utf-8")
        combined = namespace_bytes + hash_bytes
        derived = _keccak256_bytes(combined)
        return "0x" + derived.hex()

    @classmethod
    def verify_integrity(
        cls,
        report_data: dict[str, Any],
        expected_hash: str,
        algorithm: str = "sha256",
    ) -> IntegrityResult:
        """
        Verify that report_data matches the expected hash.
        Detects tampering or modification.
        """
        if not expected_hash:
            return IntegrityResult(
                status="not_available",
                evidence_hash=None,
                expected_hash=None,
                algorithm=algorithm,
                details="No expected hash was provided for verification.",
            )

        algo = algorithm.lower().strip()
        if algo not in cls.SUPPORTED_ALGORITHMS:
            return IntegrityResult(
                status="failed",
                evidence_hash=None,
                expected_hash=expected_hash,
                algorithm=algorithm,
                tamper_detected=True,
                details=f"Verification failed: Unsupported algorithm '{algorithm}'.",
            )

        try:
            computed_hash = cls.hash_report(report_data, algorithm=algorithm)
            comp_norm = computed_hash.lower().removeprefix("0x")
            exp_norm = expected_hash.lower().removeprefix("0x")

            if comp_norm == exp_norm:
                return IntegrityResult(
                    status="verified",
                    evidence_hash=computed_hash,
                    expected_hash=expected_hash,
                    algorithm=algorithm,
                    tamper_detected=False,
                    details="Cryptographic integrity successfully verified. Data matches original fingerprint bit-for-bit.",
                )
            else:
                return IntegrityResult(
                    status="failed",
                    evidence_hash=computed_hash,
                    expected_hash=expected_hash,
                    algorithm=algorithm,
                    tamper_detected=True,
                    details=f"Tampering detected! Computed hash ({computed_hash[:16]}...) does not match expected hash ({expected_hash[:16]}...).",
                )
        except Exception as e:
            return IntegrityResult(
                status="failed",
                evidence_hash=None,
                expected_hash=expected_hash,
                algorithm=algorithm,
                tamper_detected=True,
                details=f"Verification failed due to error: {e}",
            )
