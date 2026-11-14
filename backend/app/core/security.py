"""Security and cryptographic utility primitives.

Includes secret masking, safe hash generation, and defensive token validation.
"""

import hashlib
import hmac
import secrets
from typing import Optional


def mask_secret(secret_val: Optional[str], visible_chars: int = 4) -> str:
    """Safely mask a sensitive token or key string for diagnostic reporting.
    
    Example: 'AIzaSyD-abc123xyz789' -> 'AIza...y789'
    """
    if not secret_val:
        return "[NOT_SET]"
    if len(secret_val) <= visible_chars * 2:
        return "****"
    return f"{secret_val[:visible_chars]}...{secret_val[-visible_chars:]}"


def constant_time_compare(val1: str, val2: str) -> bool:
    """Perform a constant-time string comparison to prevent timing attacks."""
    return hmac.compare_digest(val1.encode("utf-8"), val2.encode("utf-8"))


def generate_secure_token(length_bytes: int = 32) -> str:
    """Generate a cryptographically secure random hexadecimal token."""
    return secrets.token_hex(length_bytes)


def compute_sha256(data: str) -> str:
    """Compute a SHA-256 digest of input text."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()
