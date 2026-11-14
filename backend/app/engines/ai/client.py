"""Google Gemini API Provider Client.

Implements BaseAIProvider using the official Google GenAI Python SDK (`google-genai`).
Features asynchronous execution, timeout guards, exponential backoff retries,
rate-limit detection, and secret masking.
"""

import asyncio
import logging
import os
import time
from typing import Any, Dict, Optional, Union

from pydantic import SecretStr

from backend.app.core.security import mask_secret
from backend.app.engines.ai.base import BaseAIProvider
from backend.app.engines.ai.exceptions import (
    AIAuthenticationError,
    AIRateLimitError,
    AIServiceError,
    AITimeoutError,
    AIUnavailableError,
)
from backend.app.engines.ai.schemas import AiAnalysisResult, ProviderHealthStatus

logger = logging.getLogger("cybershield.ai.client")


_UNSPECIFIED = object()


class GeminiProvider(BaseAIProvider):
    """Production provider integrating Google's Gemini models via official SDK."""

    def __init__(
        self,
        api_key: Any = _UNSPECIFIED,
        model_name: Optional[str] = None,
        timeout: float = 5.0,
        max_retries: int = 2,
    ):
        raw_key: Optional[str] = None
        if api_key is not _UNSPECIFIED:
            if isinstance(api_key, SecretStr):
                raw_key = api_key.get_secret_value()
            elif isinstance(api_key, str) and api_key.strip():
                raw_key = api_key.strip()
            else:
                raw_key = None
        else:
            env_key = os.environ.get("GEMINI_API_KEY", "").strip()
            raw_key = env_key if env_key else None

        if model_name is None:
            model_name = (
                os.environ.get("GEMINI_MODEL")
                or os.environ.get("GEMINI_MODEL_NAME")
                or "gemini-3.1-flash-lite"
            )

        self._api_key = raw_key
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Any = None

        if self._api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self._api_key)
                logger.info(
                    "GeminiProvider initialized with model '%s' and key %s",
                    self.model_name,
                    mask_secret(self._api_key),
                )
            except Exception as exc:
                logger.warning("Failed to initialize Google GenAI client: %s", exc)
                self._client = None
        else:
            logger.info("GeminiProvider initialized in UNCONFIGURED mode (no API key provided).")

    @property
    def is_configured(self) -> bool:
        """Return True if a valid client and API key are available."""
        return self._client is not None and bool(self._api_key)

    def __repr__(self) -> str:
        masked = mask_secret(self._api_key) if self._api_key else "None"
        return f"<GeminiProvider model='{self.model_name}' configured={self.is_configured} key={masked}>"

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        """Asynchronously query the Gemini model with timeout and retry controls."""
        if not self.is_configured:
            raise AIUnavailableError(
                "Gemini API key is unconfigured. Set GEMINI_API_KEY in environment to enable live AI reasoning."
            )

        from google.genai import errors, types

        config_args: Dict[str, Any] = {"temperature": temperature}
        if system_instruction:
            config_args["system_instruction"] = system_instruction

        config = types.GenerateContentConfig(**config_args)

        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                # Wrap asynchronous call in timeout
                call_coro = self._client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config,
                )
                response = await asyncio.wait_for(call_coro, timeout=self.timeout)

                if response and hasattr(response, "text") and response.text:
                    return response.text
                elif response and hasattr(response, "candidates") and response.candidates:
                    first_cand = response.candidates[0]
                    if hasattr(first_cand, "content") and first_cand.content:
                        parts = first_cand.content.parts or []
                        text_parts = [p.text for p in parts if hasattr(p, "text") and p.text]
                        return "".join(text_parts)
                return ""

            except asyncio.TimeoutError as exc:
                logger.warning("Gemini API call timed out after %.1fs (attempt %d/%d)", self.timeout, attempt + 1, self.max_retries + 1)
                last_error = AITimeoutError(f"Gemini API call exceeded timeout threshold of {self.timeout}s.")
                # Do not retry timeouts
                break

            except errors.APIError as exc:
                status_code = getattr(exc, "code", None) or 500
                message = getattr(exc, "message", str(exc))

                if status_code == 429:
                    logger.warning("Gemini API rate limit exceeded (HTTP 429): %s", message)
                    raise AIRateLimitError("Gemini API rate limit or quota exceeded.", details=message)

                if status_code in (400, 401, 403):
                    logger.warning("Gemini API authentication/permission error (%d): %s", status_code, message)
                    raise AIAuthenticationError(f"Gemini API authorization failure ({status_code}).", details=message)

                if 500 <= status_code < 600:
                    logger.warning("Gemini API server error (%d): %s (attempt %d/%d)", status_code, message, attempt + 1, self.max_retries + 1)
                    last_error = AIServiceError(f"Gemini server error ({status_code})", details=message)
                    if attempt < self.max_retries:
                        backoff = 0.5 * (2 ** attempt)
                        await asyncio.sleep(backoff)
                        continue
                raise AIServiceError(f"Gemini API error ({status_code})", details=message)

            except Exception as exc:
                logger.error("Unexpected error during Gemini API query: %s", exc)
                last_error = AIServiceError("Unexpected error during AI generation.", details=str(exc))
                break

        if isinstance(last_error, AIServiceError):
            raise last_error
        raise AIServiceError("Failed to generate AI response.", details=str(last_error))

    async def analyze_threat(
        self,
        target_type: str,
        untrusted_content: str,
        observed_evidence: Dict[str, Any],
        heuristic_findings: Dict[str, Any],
    ) -> AiAnalysisResult:
        """High-level threat analysis: delegates to analyzer pipeline in Part 11."""
        from backend.app.engines.ai.analyzer import AIThreatAnalyzer
        analyzer = AIThreatAnalyzer(provider=self)
        return await analyzer.analyze(
            target_type=target_type,
            untrusted_content=untrusted_content,
            observed_evidence=observed_evidence,
            heuristic_findings=heuristic_findings,
        )

    async def health_check(self) -> ProviderHealthStatus:
        """Diagnostic check of provider reachability and configuration."""
        if not self.is_configured:
            return ProviderHealthStatus(
                provider="google-gemini",
                model=self.model_name,
                status="unconfigured",
                configured=False,
                message="GEMINI_API_KEY is not configured.",
            )

        start_time = time.monotonic()
        try:
            # Lightweight health ping
            await self.generate_text("ping", temperature=0.0)
            latency = (time.monotonic() - start_time) * 1000.0
            return ProviderHealthStatus(
                provider="google-gemini",
                model=self.model_name,
                status="healthy",
                configured=True,
                latency_ms=round(latency, 2),
                message="Connected to Google GenAI API.",
            )
        except Exception as exc:
            latency = (time.monotonic() - start_time) * 1000.0
            return ProviderHealthStatus(
                provider="google-gemini",
                model=self.model_name,
                status="degraded",
                configured=True,
                latency_ms=round(latency, 2),
                message=f"Health probe failed: {exc}",
            )
