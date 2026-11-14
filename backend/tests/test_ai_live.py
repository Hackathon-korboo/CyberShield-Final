"""Optional live Gemini API integration tests.

These tests execute actual network queries to the Google Gemini API.
They are executed ONLY when a valid GEMINI_API_KEY is configured in the environment.
In CI or unconfigured local environments, they are safely skipped.
"""

import os
import pytest

from backend.app.engines.ai.client import GeminiProvider

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()


@pytest.mark.skipif(
    not GEMINI_API_KEY,
    reason="Live Gemini API test skipped: GEMINI_API_KEY environment variable is not configured."
)
@pytest.mark.asyncio
async def test_live_gemini_api_connectivity():
    """Verify live asynchronous generation with genuine Google GenAI API."""
    provider = GeminiProvider(api_key=GEMINI_API_KEY, timeout=20.0)
    assert provider.is_configured is True

    prompt = "Respond with the single word: OK"
    response = await provider.generate_text(prompt, temperature=0.0)

    assert "OK" in response.upper()


@pytest.mark.skipif(
    not GEMINI_API_KEY,
    reason="Live Gemini API test skipped: GEMINI_API_KEY environment variable is not configured."
)
@pytest.mark.asyncio
async def test_live_gemini_health_check():
    """Verify live health check returns healthy status."""
    provider = GeminiProvider(api_key=GEMINI_API_KEY, timeout=20.0)
    health = await provider.health_check()

    assert health.status == "healthy"
    assert health.configured is True
    assert health.latency_ms is not None
