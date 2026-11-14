"""MEMBER 3 ADAPTER — SECURITY & BLOCKCHAIN EVIDENCE INTEGRITY.

Provides live integration with Member 3's BlockchainAdapter,
RFC 8785 canonical JSON serialization, SHA-256 evidence hashing,
and Ethereum Keccak-256 smart contract anchoring.
"""

from typing import Dict, Any, Optional
import hashlib
import json

from backend.app.services.blockchain.adapter import BlockchainAdapter
from backend.app.services.blockchain.canonical_hasher import compute_canonical_hash, rfc8785_canonical_json


class Member3SecurityAdapter:
    """Live adapter for Member 3 cryptographic and blockchain verification."""

    def __init__(self):
        self._blockchain_adapter = BlockchainAdapter()
        self.is_connected = True
        self.status = "CONNECTED"

    def compute_evidence_hash(self, evidence_data: Dict[str, Any]) -> str:
        """Compute RFC 8785 / SHA-256 canonical hash of report/evidence data."""
        canonical_bytes = rfc8785_canonical_json(evidence_data)
        return hashlib.sha256(canonical_bytes).hexdigest()

    def verify_audit_anchor(self, report_id: str, expected_hash: str) -> Dict[str, Any]:
        """Verify on-chain registration anchor for a given report ID and expected hash."""
        verification_result = self._blockchain_adapter.verify_report(report_id, expected_hash)
        return {
            "report_id": report_id,
            "status": "VERIFIED" if verification_result.is_valid else "NOT_REGISTERED",
            "is_valid": verification_result.is_valid,
            "message": verification_result.message,
            "chain_id": self._blockchain_adapter.chain_id,
            "contract_address": self._blockchain_adapter.contract_address,
        }
