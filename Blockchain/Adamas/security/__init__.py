"""
CyberShield AI — Security Engineering, Cryptography & Blockchain Module (v2.2)
========================================================================
Member 3 Workstream:
- SSRF & URL Preflight Protection (SSRFValidator, PinnedSession, PinnedHTTPAdapter)
- Deterministic Cryptographic Hashing & Tamper Detection (EvidenceHasher, IntegrityResult)
- Blockchain & Off-Chain Fallback Verification (BlockchainAdapter)
"""

__version__ = "2.2.0"

from .ssrf_validator import (
    SSRFValidator,
    SSRFValidationResult,
    PinnedSession,
    PinnedHTTPAdapter,
    SSRFSecurityException,
    SSRFRedirectBlockedException,
)
from .evidence_hasher import EvidenceHasher, IntegrityResult
from .blockchain_adapter import BlockchainAdapter

__all__ = [
    "__version__",
    "SSRFValidator",
    "SSRFValidationResult",
    "PinnedSession",
    "PinnedHTTPAdapter",
    "SSRFSecurityException",
    "SSRFRedirectBlockedException",
    "EvidenceHasher",
    "IntegrityResult",
    "BlockchainAdapter",
]
