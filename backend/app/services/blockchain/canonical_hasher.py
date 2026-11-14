"""RFC 8785 Canonical JSON Hashing Engine for Part 19.

Provides deterministic SHA-256 fingerprinting over canonical report attributes.
Ensures that changing any report-integrity-covered field alters the hash,
while excluded mutable metadata (blockchain transaction hash, anchoring status)
does not alter the fingerprint.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional


def rfc8785_canonical_json(data: Any) -> bytes:
    """Serialize data into deterministic canonical JSON bytes conforming to RFC 8785."""
    if isinstance(data, dict):
        # Sort keys lexicographically by Unicode code point
        sorted_dict = {
            k: json.loads(rfc8785_canonical_json(v).decode("utf-8"))
            for k, v in sorted(data.items())
        }
        return json.dumps(sorted_dict, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    elif isinstance(data, list):
        encoded_list = [
            json.loads(rfc8785_canonical_json(item).decode("utf-8"))
            for item in data
        ]
        return json.dumps(encoded_list, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    elif isinstance(data, (str, int, bool)) or data is None:
        return json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    elif isinstance(data, float):
        # Canonical float formatting (remove trailing zeros if exact)
        formatted = f"{data:.8f}".rstrip("0").rstrip(".")
        return formatted.encode("utf-8")
    else:
        # Fallback to string representation
        return json.dumps(str(data), separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def build_canonical_report_payload(
    scan_id: str,
    submitted_input: str,
    input_type: str,
    classification: str,
    risk_score: Optional[int],
    timestamp_str: str,
    rules_triggered: Optional[List[str]] = None,
    has_policy_violation: bool = False,
    has_authoritative_match: bool = False,
) -> Dict[str, Any]:
    """Assemble the exact dictionary of attributes covered by the cryptographic hash.

    Mutable blockchain metadata (blockchain_status, transaction_hash, network, contract_address)
    and volatile runtime limits are explicitly excluded.
    """
    return {
        "scan_id": scan_id,
        "submitted_input": submitted_input,
        "input_type": input_type,
        "classification": classification,
        "risk_score": risk_score,
        "timestamp": timestamp_str,
        "rules_triggered": sorted(rules_triggered or []),
        "has_policy_violation": has_policy_violation,
        "has_authoritative_match": has_authoritative_match,
    }


def compute_canonical_hash(
    scan_id: str,
    submitted_input: str,
    input_type: str,
    classification: str,
    risk_score: Optional[int],
    timestamp_str: str,
    rules_triggered: Optional[List[str]] = None,
    has_policy_violation: bool = False,
    has_authoritative_match: bool = False,
) -> str:
    """Compute the deterministic 64-character hex SHA-256 hash over canonical report contents."""
    payload = build_canonical_report_payload(
        scan_id=scan_id,
        submitted_input=submitted_input,
        input_type=input_type,
        classification=classification,
        risk_score=risk_score,
        timestamp_str=timestamp_str,
        rules_triggered=rules_triggered,
        has_policy_violation=has_policy_violation,
        has_authoritative_match=has_authoritative_match,
    )
    canonical_bytes = rfc8785_canonical_json(payload)
    return hashlib.sha256(canonical_bytes).hexdigest()


def to_bytes32_hex(sha256_hex: str) -> str:
    """Convert 64-character SHA-256 hex string to EVM 0x-prefixed bytes32."""
    clean = sha256_hex.replace("0x", "").strip().lower()
    if len(clean) != 64:
        raise ValueError(f"Expected 64-char hex string, got {len(clean)}")
    return f"0x{clean}"


def compute_keccak_hash(
    scan_id: str,
    submitted_input: str,
    input_type: str,
    classification: str,
    risk_score: Optional[int],
    timestamp_str: str,
    rules_triggered: Optional[List[str]] = None,
    has_policy_violation: bool = False,
    has_authoritative_match: bool = False,
) -> str:
    """Compute the deterministic 0x-prefixed 64-character hex Keccak-256 hash."""
    payload = build_canonical_report_payload(
        scan_id=scan_id,
        submitted_input=submitted_input,
        input_type=input_type,
        classification=classification,
        risk_score=risk_score,
        timestamp_str=timestamp_str,
        rules_triggered=rules_triggered,
        has_policy_violation=has_policy_violation,
        has_authoritative_match=has_authoritative_match,
    )
    canonical_bytes = rfc8785_canonical_json(payload)
    from backend.app.services.blockchain.evidence_hasher import _keccak256
    return "0x" + _keccak256(canonical_bytes).hex()


def derive_report_id(report_hash: str) -> str:
    """Derive deterministic bytes32 report ID matching Solidity generateReportId()."""
    from backend.app.services.blockchain.evidence_hasher import EvidenceHasher
    return EvidenceHasher.derive_report_id(report_hash)
