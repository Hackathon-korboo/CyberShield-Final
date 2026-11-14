"""Tests for centralized configuration, environment loading, and secret protection."""

import pytest
from pydantic import SecretStr, ValidationError
from backend.app.core.config import Settings
from backend.app.core.security import mask_secret


def test_default_settings_instantiation():
    """Verify Settings initializes with safe default values."""
    settings = Settings()
    assert settings.app_name == "CyberShield AI 2.0"
    assert settings.app_version == "2.0.0"
    assert settings.environment == "development"
    assert settings.debug is False
    assert settings.port == 8000
    assert settings.host == "127.0.0.1"
    assert len(settings.cors_origins) > 0


def test_secret_masking_in_summary():
    """Verify that get_masked_summary() completely obscures raw secret values."""
    raw_secret = "AIzaSySuperSecretKey1234567890abcdef"
    settings = Settings(gemini_api_key=SecretStr(raw_secret))

    summary = settings.get_masked_summary()

    # Raw secret must never appear in diagnostic summary
    assert raw_secret not in str(summary)
    assert summary["gemini_api_key"].startswith("AIza...")
    assert summary["gemini_api_key"].endswith("cdef")


def test_mask_secret_helper_edge_cases():
    """Verify mask_secret helper behaviors on null and short strings."""
    assert mask_secret(None) == "[NOT_SET]"
    assert mask_secret("") == "[NOT_SET]"
    assert mask_secret("short") == "****"
    assert mask_secret("1234567890", visible_chars=2) == "12...90"


def test_environment_validation_valid():
    """Verify accepted environment identifiers."""
    for env in ["development", "testing", "staging", "production"]:
        s = Settings(environment=env)
        assert s.environment == env


def test_environment_validation_invalid():
    """Verify unapproved environment identifiers trigger validation error."""
    with pytest.raises(ValidationError):
        Settings(environment="unapproved_sandbox")


def test_cors_origins_parsing():
    """Verify comma-separated CORS string is automatically parsed into list."""
    s = Settings(cors_origins="https://dashboard.cybershield.io, https://app.cybershield.io")
    assert s.cors_origins == [
        "https://dashboard.cybershield.io",
        "https://app.cybershield.io",
    ]


def test_secret_scrubbing_log_filter():
    """Verify SecretScrubbingFilter redacts Google API keys, Bearer tokens, and secrets."""
    import logging
    from backend.app.core.logging import SecretScrubbingFilter

    log_filter = SecretScrubbingFilter()

    # 1. Google API Key test
    record1 = logging.LogRecord("test", logging.INFO, "", 0, "Connected with key AIzaSyA1234567890123456789012345678901", (), None)
    log_filter.filter(record1)
    assert "AIzaSy" not in record1.msg
    assert "[REDACTED_API_KEY]" in record1.msg

    # 2. Bearer token test
    record2 = logging.LogRecord("test", logging.INFO, "", 0, "Header: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.token", (), None)
    log_filter.filter(record2)
    assert "eyJhbG" not in record2.msg
    assert "Bearer [REDACTED]" in record2.msg

    # 3. Key-value secret test
    record3 = logging.LogRecord("test", logging.INFO, "", 0, "Params: password=\"supersecretpass\" and api_key=plainkey123", (), None)
    log_filter.filter(record3)
    assert "supersecretpass" not in record3.msg
    assert "plainkey123" not in record3.msg
    assert "password=\"[REDACTED]\"" in record3.msg
    assert "api_key=[REDACTED]" in record3.msg
