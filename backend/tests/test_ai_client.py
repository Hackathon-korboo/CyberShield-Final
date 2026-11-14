"""Unit and mock tests for Part 10: Gemini API Integration.

Verifies client initialization, secret masking, timeout handling, retry behavior,
rate-limit detection, and error translation without requiring live network calls.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from pydantic import SecretStr

from backend.app.engines.ai.client import GeminiProvider
from backend.app.engines.ai.exceptions import (
    AIAuthenticationError,
    AIRateLimitError,
    AIServiceError,
    AITimeoutError,
    AIUnavailableError,
)
from backend.app.engines.ai.mock_provider import MockAIProvider
from backend.app.engines.ai.schemas import AiAnalysisResult


@pytest.mark.asyncio
async def test_gemini_client_init_without_key(monkeypatch):
    """Test client initializes in unconfigured state when no key is supplied."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    provider = GeminiProvider(api_key=None)

    assert provider.is_configured is False
    assert "configured=False" in repr(provider)

    with pytest.raises(AIUnavailableError) as exc_info:
        await provider.generate_text("test")
    assert "unconfigured" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_gemini_client_init_with_key():
    """Test client initializes and properly masks secret key."""
    secret = "AIzaSyFakeKeyForTesting1234567890ABCDEF"
    provider = GeminiProvider(api_key=secret)

    assert provider.is_configured is True
    # Secret must be masked in repr
    repr_str = repr(provider)
    assert secret not in repr_str
    assert "AIza...CDEF" in repr_str or "***" in repr_str


@pytest.mark.asyncio
async def test_gemini_client_init_with_pydantic_secret_str():
    """Test client accepts Pydantic SecretStr without leaking it."""
    raw_key = "AIzaSySuperSecretPydanticKey9876543210"
    secret_str = SecretStr(raw_key)
    provider = GeminiProvider(api_key=secret_str)

    assert provider.is_configured is True
    assert raw_key not in repr(provider)


@pytest.mark.asyncio
async def test_gemini_client_timeout_handling():
    """Test that calls exceeding the configured timeout raise AITimeoutError."""
    provider = GeminiProvider(api_key="AIzaSyTestKey1234567890", timeout=0.05)

    # Mock client.aio.models.generate_content to hang
    async def slow_call(*args, **kwargs):
        await asyncio.sleep(0.2)
        return MagicMock(text="late")

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = slow_call
    provider._client = mock_client

    with pytest.raises(AITimeoutError) as exc_info:
        await provider.generate_text("quick prompt")
    assert "exceeded timeout" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_gemini_client_rate_limit_handling():
    """Test HTTP 429 translation to AIRateLimitError."""
    from google.genai.errors import APIError

    provider = GeminiProvider(api_key="AIzaSyTestKey1234567890")

    mock_client = MagicMock()
    # Create an APIError with code 429
    err = APIError(code=429, response_json={"error": {"code": 429, "message": "Resource has been exhausted (e.g. check quota)."}})
    mock_client.aio.models.generate_content = AsyncMock(side_effect=err)
    provider._client = mock_client

    with pytest.raises(AIRateLimitError) as exc_info:
        await provider.generate_text("test")
    assert "rate limit or quota" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_gemini_client_auth_error_handling():
    """Test HTTP 401/403 translation to AIAuthenticationError."""
    from google.genai.errors import APIError

    provider = GeminiProvider(api_key="AIzaSyInvalidKey123456")

    mock_client = MagicMock()
    err = APIError(code=403, response_json={"error": {"code": 403, "message": "API key not valid."}})
    mock_client.aio.models.generate_content = AsyncMock(side_effect=err)
    provider._client = mock_client

    with pytest.raises(AIAuthenticationError) as exc_info:
        await provider.generate_text("test")
    assert "authorization failure" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_gemini_client_retry_logic_transient_error():
    """Test that transient 503 errors trigger exponential backoff retry."""
    from google.genai.errors import APIError

    provider = GeminiProvider(api_key="AIzaSyTestKey1234567890", max_retries=1)

    mock_client = MagicMock()
    err503 = APIError(code=503, response_json={"error": {"code": 503, "message": "Service Unavailable"}})
    success_resp = MagicMock(text='{"summary": "recovered after retry"}')

    # Fails once with 503, then succeeds on retry
    mock_client.aio.models.generate_content = AsyncMock(side_effect=[err503, success_resp])
    provider._client = mock_client

    result = await provider.generate_text("retry test")
    assert "recovered after retry" in result
    assert mock_client.aio.models.generate_content.call_count == 2


@pytest.mark.asyncio
async def test_mock_provider_basic_generation():
    """Test MockAIProvider returns valid JSON conforming to schema."""
    mock_p = MockAIProvider()
    raw = await mock_p.generate_text("hello")
    parsed = AiAnalysisResult.model_validate_json(raw)

    assert parsed.summary != ""
    assert parsed.provider == "mock-gemini"
    assert parsed.status == "COMPLETED"
    assert len(parsed.supporting_evidence) > 0


@pytest.mark.asyncio
async def test_mock_provider_error_simulations():
    """Test MockAIProvider accurately simulates error modes."""
    # Timeout
    timeout_p = MockAIProvider(simulate_timeout=True)
    with pytest.raises(AITimeoutError):
        await timeout_p.generate_text("test")

    # Rate Limit
    rate_p = MockAIProvider(simulate_rate_limit=True)
    with pytest.raises(AIRateLimitError):
        await rate_p.generate_text("test")

    # Auth Error
    auth_p = MockAIProvider(simulate_auth_error=True)
    with pytest.raises(AIAuthenticationError):
        await auth_p.generate_text("test")

    # Server Error
    srv_p = MockAIProvider(simulate_server_error=True)
    with pytest.raises(AIServiceError):
        await srv_p.generate_text("test")


@pytest.mark.asyncio
async def test_mock_provider_health_check():
    """Test MockAIProvider health check status."""
    mock_p = MockAIProvider()
    health = await mock_p.health_check()

    assert health.status == "healthy"
    assert health.configured is True
    assert health.latency_ms is not None
