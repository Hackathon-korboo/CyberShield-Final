"""Pydantic V2 schemas for AI threat analysis outputs.

Enforces strict type validation and structural boundaries on generative AI outputs.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AiAnalysisResult(BaseModel):
    """Structured, validated AI threat explanation and recommendation output."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(
        ...,
        description="Concise 1-2 sentence high-level summary of the threat context.",
    )
    explanation: str = Field(
        ...,
        description="Detailed plain-language explanation of deceptive tactics, urgency lures, or anomalies.",
    )
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="Concrete citations referencing observed evidence tokens or heuristic findings.",
    )
    ai_inferences: List[str] = Field(
        default_factory=list,
        description="Probabilistic deductions regarding attacker intent or impersonation targets.",
    )
    uncertainty_statement: str = Field(
        ...,
        description="Explicit probabilistic disclosure stating this is an assessment, not verified fact.",
    )
    user_recommendations: List[str] = Field(
        default_factory=list,
        description="Prescriptive, safe guidance for laypersons (e.g., do not click, verify via app).",
    )
    prompt_injection_detected: bool = Field(
        default=False,
        description="Explicit deterministic flag indicating whether prompt injection patterns were detected.",
    )
    prompt_injection_details: List[str] = Field(
        default_factory=list,
        description="List of detected prompt injection pattern descriptions or matched tokens.",
    )
    provider: str = Field(
        default="google-gemini",
        description="Identifier of the AI service provider.",
    )
    model: str = Field(
        default="gemini-1.5-flash",
        description="Model name utilized for generation.",
    )
    status: str = Field(
        default="COMPLETED",
        description="Execution status: COMPLETED, FALLBACK_HEURISTIC_ONLY, DISABLED, RATE_LIMITED, etc.",
    )


class ProviderHealthStatus(BaseModel):
    """Diagnostic health payload for an AI provider."""

    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str
    status: str  # healthy, unconfigured, degraded, disabled
    configured: bool
    latency_ms: Optional[float] = None
    message: Optional[str] = None
