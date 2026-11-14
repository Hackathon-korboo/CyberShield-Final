"""Mock AI Provider for deterministic testing and CI environments.

Provides controllable responses, simulated error conditions (timeouts, 429 quota,
auth failures, malformed output), and request logging without external network calls.
"""

import asyncio
from typing import Any, Dict, List, Optional

from backend.app.engines.ai.base import BaseAIProvider
from backend.app.engines.ai.exceptions import (
    AIAuthenticationError,
    AIRateLimitError,
    AIServiceError,
    AITimeoutError,
)
from backend.app.engines.ai.schemas import AiAnalysisResult, ProviderHealthStatus


class MockAIProvider(BaseAIProvider):
    """Deterministic mock provider mimicking Gemini API responses for automated test suites."""

    def __init__(
        self,
        default_response: Optional[str] = None,
        simulate_timeout: bool = False,
        simulate_rate_limit: bool = False,
        simulate_auth_error: bool = False,
        simulate_server_error: bool = False,
        simulate_malformed_json: bool = False,
        model_name: str = "mock-gemini-1.5-flash",
    ):
        self.default_response = default_response
        self.simulate_timeout = simulate_timeout
        self.simulate_rate_limit = simulate_rate_limit
        self.simulate_auth_error = simulate_auth_error
        self.simulate_server_error = simulate_server_error
        self.simulate_malformed_json = simulate_malformed_json
        self.model_name = model_name

        self.call_count: int = 0
        self.calls: List[Dict[str, Any]] = []

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        """Simulate text generation based on configured testing flags."""
        self.call_count += 1
        self.calls.append({
            "prompt": prompt,
            "system_instruction": system_instruction,
            "temperature": temperature,
        })

        if self.simulate_timeout:
            await asyncio.sleep(0.01)
            raise AITimeoutError("Simulated Gemini API call timeout.")

        if self.simulate_rate_limit:
            raise AIRateLimitError("Simulated rate limit exceeded (HTTP 429).")

        if self.simulate_auth_error:
            raise AIAuthenticationError("Simulated invalid API key (HTTP 401).")

        if self.simulate_server_error:
            raise AIServiceError("Simulated upstream server error (HTTP 503).")

        if self.simulate_malformed_json:
            return "This is completely invalid non-JSON output from the LLM."

        if self.default_response:
            return self.default_response

        # Default synthetic JSON matching AiAnalysisResult schema
        return """{
            "summary": "Mock threat analysis identifying social engineering pattern.",
            "explanation": "Simulated contextual explanation for unit testing verification.",
            "supporting_evidence": ["Token 'verify' detected", "Urgent action requested"],
            "ai_inferences": ["Potential credential extraction lure"],
            "uncertainty_statement": "Probabilistic assessment for testing purposes.",
            "user_recommendations": ["Do not click links or share credentials."],
            "provider": "mock-gemini",
            "model": "mock-gemini-1.5-flash",
            "status": "COMPLETED"
        }"""

    async def analyze_threat(
        self,
        target_type: str,
        untrusted_content: str,
        observed_evidence: Dict[str, Any],
        heuristic_findings: Dict[str, Any],
    ) -> AiAnalysisResult:
        """Process structured analysis inputs via mock pipeline."""
        raw_text = await self.generate_text(untrusted_content)
        # Parse output into schema
        return AiAnalysisResult.model_validate_json(raw_text)

    async def health_check(self) -> ProviderHealthStatus:
        """Return healthy diagnostic state."""
        return ProviderHealthStatus(
            provider="mock-gemini",
            model=self.model_name,
            status="healthy",
            configured=True,
            latency_ms=1.5,
            message="Mock provider operational.",
        )
