"""Abstract provider interface for the CyberShield AI reasoning layer.

Decouples high-level threat reasoning from specific LLM vendors (Google Gemini,
local Ollama, etc.) to ensure complete provider neutrality.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from backend.app.engines.ai.schemas import AiAnalysisResult, ProviderHealthStatus


class BaseAIProvider(ABC):
    """Abstract contract governing all external and mock AI providers."""

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        """Asynchronously query the model with raw prompt text."""
        pass

    @abstractmethod
    async def analyze_threat(
        self,
        target_type: str,
        untrusted_content: str,
        observed_evidence: Dict[str, Any],
        heuristic_findings: Dict[str, Any],
    ) -> AiAnalysisResult:
        """Process structured analysis inputs into a validated AiAnalysisResult."""
        pass

    @abstractmethod
    async def health_check(self) -> ProviderHealthStatus:
        """Check provider configuration and diagnostic reachability."""
        pass
