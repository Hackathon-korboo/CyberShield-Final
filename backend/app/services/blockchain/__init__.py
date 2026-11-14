"""CyberShield AI 2.0 — Enterprise Blockchain & Cryptographic Trust Registry."""

from backend.app.services.blockchain.adapter import (
    BlockchainAdapter,
    BlockchainStatus,
    CONTRACT_ABI,
    ReportVerificationResult,
)
from backend.app.services.blockchain.canonical_hasher import (
    compute_canonical_hash,
    compute_keccak_hash,
    derive_report_id,
    rfc8785_canonical_json,
    to_bytes32_hex,
)
from backend.app.services.blockchain.evidence_hasher import (
    EvidenceHasher,
    IntegrityResult,
    _pure_keccak256,
)

__all__ = [
    "BlockchainAdapter",
    "BlockchainStatus",
    "CONTRACT_ABI",
    "ReportVerificationResult",
    "compute_canonical_hash",
    "compute_keccak_hash",
    "derive_report_id",
    "rfc8785_canonical_json",
    "to_bytes32_hex",
    "EvidenceHasher",
    "IntegrityResult",
    "_pure_keccak256",
]
