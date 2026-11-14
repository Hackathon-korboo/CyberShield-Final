"""Unit tests for input validation, sanitization, and normalization utilities."""

import pytest
from backend.app.utils.sanitizer import (
    extract_phone_numbers,
    extract_urls_from_text,
    normalize_target_url,
    parse_email_sender,
    sanitize_input_text,
)


def test_normalize_target_url_basic():
    """Verify standard URL normalization."""
    assert normalize_target_url("http://EXAMPLE.COM/Path/../") == "http://example.com/"
    assert normalize_target_url("https://example.com:443/test") == "https://example.com/test"
    assert normalize_target_url("example.com/login") == "https://example.com/login"


def test_normalize_target_url_punycode():
    """Verify Cyrillic homoglyph domain is converted to Punycode."""
    normalized = normalize_target_url("http://раураl.com/verify")
    assert "xn--" in normalized
    assert "verify" in normalized


def test_normalize_target_url_dot_segments():
    """Verify path traversal resolution."""
    normalized = normalize_target_url("https://example.com/a/b/../../secret")
    assert normalized == "https://example.com/secret"


def test_normalize_target_url_invalid():
    """Verify rejection of empty, whitespace, control chars, and unsupported schemes."""
    with pytest.raises(ValueError):
        normalize_target_url("")

    with pytest.raises(ValueError):
        normalize_target_url("   ")

    with pytest.raises(ValueError):
        normalize_target_url("https://example.com\n/test")

    with pytest.raises(ValueError):
        normalize_target_url("ftp://files.example.com")


def test_extract_urls_from_text():
    """Verify extraction of multiple embedded URLs from mixed message content."""
    text = (
        "Hello user, please check https://legit-site.com/docs and also "
        "visit http://phishing-alert.com/login for verification. Thanks!"
    )
    urls = extract_urls_from_text(text)
    assert len(urls) == 2
    assert "https://legit-site.com/docs" in urls
    assert "http://phishing-alert.com/login" in urls


def test_extract_phone_numbers():
    """Verify phone number extraction."""
    text = "Call us immediately at +1 (800) 555-0199 or 555-123-4567 to resolve your dispute."
    phones = extract_phone_numbers(text)
    assert len(phones) >= 2


def test_parse_email_sender():
    """Verify parsing of sender string."""
    parsed = parse_email_sender("Fraud Alert Team <alerts@secure-bank.com>")
    assert parsed["display_name"] == "Fraud Alert Team"
    assert parsed["email"] == "alerts@secure-bank.com"
    assert parsed["domain"] == "secure-bank.com"


def test_sanitize_input_text():
    """Verify stripping of null bytes and hazardous control characters."""
    raw = "Header line\x00\x01\x02\nBody text\tpreserved."
    cleaned = sanitize_input_text(raw)
    assert "\x00" not in cleaned
    assert "\x01" not in cleaned
    assert "\n" in cleaned
    assert "\t" in cleaned
    assert "Body text" in cleaned
