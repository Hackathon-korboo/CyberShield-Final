"""Input sanitization, normalization, and indicator extraction utilities for CyberShield AI 2.0."""

from email.utils import parseaddr
import posixpath
import re
from typing import Dict, List, Optional
import urllib.parse
import idna

# Regular expression matching embedded URLs in text
URL_REGEX = re.compile(
    r"""(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))""",
    re.IGNORECASE,
)

# Regular expression for extracting phone numbers
PHONE_REGEX = re.compile(
    r"""(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"""
)

# Hazardous control characters (excluding \t \n \r)
CONTROL_CHAR_REGEX = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def normalize_target_url(raw_url: str) -> str:
    """Clean and normalize an inbound URL string for consistent analysis.
    
    1. Trims whitespace.
    2. Enforces scheme (defaulting to https:// if missing).
    3. Converts internationalized domain names (IDN) to Punycode.
    4. Normalizes scheme and hostname to lowercase.
    5. Resolves path traversal dot segments (./ and ../).
    6. Ensures hostname is non-empty.
    """
    cleaned = raw_url.strip()
    if not cleaned:
        raise ValueError("URL cannot be empty or solely whitespace.")

    # Reject null bytes or line breaks
    if re.search(r"[\r\n\x00]", cleaned):
        raise ValueError("URL contains illegal control characters or line breaks.")

    # Match scheme
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+\-.]*://", cleaned):
        cleaned = f"https://{cleaned}"

    parsed = urllib.parse.urlsplit(cleaned)
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme '{scheme}'. Only http and https are permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL does not contain a valid hostname.")

    # Encode IDN / Unicode hostnames to ASCII Punycode
    try:
        ascii_host = idna.encode(hostname.lower()).decode("ascii")
    except Exception:
        ascii_host = hostname.lower()

    # Format host for netloc (wrap IPv6 literals in square brackets)
    formatted_host = f"[{ascii_host}]" if ":" in ascii_host else ascii_host

    # Reconstruct netloc with port if non-standard
    port = parsed.port
    if port and ((scheme == "http" and port != 80) or (scheme == "https" and port != 443)):
        netloc = f"{formatted_host}:{port}"
    else:
        netloc = formatted_host

    # Normalize path (remove dot segments)
    path = parsed.path
    if not path:
        path = "/"
    else:
        path = posixpath.normpath(path)
        if parsed.path.endswith("/") and not path.endswith("/"):
            path += "/"

    normalized = urllib.parse.urlunsplit((
        scheme,
        netloc,
        path,
        parsed.query,
        parsed.fragment,
    ))
    return normalized


def extract_urls_from_text(text: str) -> List[str]:
    """Extract and normalize all unique URLs embedded in an email or SMS message."""
    if not text:
        return []

    matches = URL_REGEX.findall(text)
    extracted: List[str] = []
    seen = set()

    for match in matches:
        raw_match = match[0].rstrip(".,;!?:")
        try:
            norm = normalize_target_url(raw_match)
            if norm not in seen:
                seen.add(norm)
                extracted.append(norm)
        except ValueError:
            continue

    return extracted


def extract_phone_numbers(text: str) -> List[str]:
    """Extract unique phone numbers from message content."""
    if not text:
        return []

    raw_matches = PHONE_REGEX.findall(text)
    clean_phones = []
    seen = set()

    for p in raw_matches:
        cleaned = re.sub(r"[-.\s()]", "", p)
        if len(cleaned) >= 7 and cleaned not in seen:
            seen.add(cleaned)
            clean_phones.append(p.strip())

    return clean_phones


def parse_email_sender(sender_str: Optional[str]) -> Dict[str, Optional[str]]:
    """Parse a sender header string into display name, local part, and domain."""
    if not sender_str:
        return {"display_name": None, "email": None, "domain": None}

    display_name, email_addr = parseaddr(sender_str.strip())
    domain = None
    if email_addr and "@" in email_addr:
        domain = email_addr.split("@")[-1].lower()

    return {
        "display_name": display_name or None,
        "email": email_addr or None,
        "domain": domain,
    }


def sanitize_input_text(text: str, max_length: int = 50000) -> str:
    """Trim text and strip dangerous control characters while preserving formatting."""
    if not text:
        return ""
    sanitized = CONTROL_CHAR_REGEX.sub("", text)
    return sanitized[:max_length].strip()
