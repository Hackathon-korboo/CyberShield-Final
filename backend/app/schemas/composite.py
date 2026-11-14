"""Composite response schemas integrating deterministic findings with AI reasoning.

Preserves complete backward compatibility by cleanly embedding the frozen Phase 02
observed evidence and heuristic findings alongside the new AiAnalysisResult.
"""

from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

from backend.app.engines.ai.schemas import AiAnalysisResult
from backend.app.schemas.analysis import (
    EmailObservedEvidence,
    HeuristicFindings,
    SmsObservedEvidence,
    UrlObservedEvidence,
    get_utc_now,
)


class CompositeUrlAnalysisResponse(BaseModel):
    """Integrated URL threat analysis payload with deterministic evidence and AI reasoning."""

    model_config = ConfigDict(extra="forbid")

    target: str = Field(..., description="Target URL analyzed.")
    target_type: str = Field("url", description="Type of target analyzed.")
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique analysis correlation ID.")
    timestamp: datetime = Field(default_factory=get_utc_now, description="UTC timestamp of completion.")
    observed_evidence: UrlObservedEvidence = Field(..., description="Empirical, verifiable facts.")
    heuristic_findings: HeuristicFindings = Field(..., description="Deterministic rule-based evaluation.")
    prompt_injection_detected: bool = Field(default=False, description="Top-level flag indicating whether prompt injection patterns were detected.")
    ai_analysis: Optional[AiAnalysisResult] = Field(None, description="Contextual AI-generated explanation and guidance.")
    status: str = Field("COMPLETED", description="Analysis completion status.")


class CompositeEmailAnalysisResponse(BaseModel):
    """Integrated Email threat analysis payload with deterministic evidence and AI reasoning."""

    model_config = ConfigDict(extra="forbid")

    target: str = Field(..., description="Sender or subject identifier.")
    target_type: str = Field("email", description="Type of target analyzed.")
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique analysis correlation ID.")
    timestamp: datetime = Field(default_factory=get_utc_now, description="UTC timestamp of completion.")
    observed_evidence: EmailObservedEvidence = Field(..., description="Empirical observations from email content.")
    heuristic_findings: HeuristicFindings = Field(..., description="Deterministic rule-based evaluation.")
    prompt_injection_detected: bool = Field(default=False, description="Top-level flag indicating whether prompt injection patterns were detected.")
    ai_analysis: Optional[AiAnalysisResult] = Field(None, description="Contextual AI-generated explanation and guidance.")
    status: str = Field("COMPLETED", description="Analysis completion status.")


class CompositeSmsAnalysisResponse(BaseModel):
    """Integrated SMS threat analysis payload with deterministic evidence and AI reasoning."""

    model_config = ConfigDict(extra="forbid")

    target: str = Field(..., description="Message snippet or sender identifier.")
    target_type: str = Field("sms", description="Type of target analyzed.")
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique analysis correlation ID.")
    timestamp: datetime = Field(default_factory=get_utc_now, description="UTC timestamp of completion.")
    observed_evidence: SmsObservedEvidence = Field(..., description="Empirical observations from SMS content.")
    heuristic_findings: HeuristicFindings = Field(..., description="Deterministic rule-based evaluation.")
    prompt_injection_detected: bool = Field(default=False, description="Top-level flag indicating whether prompt injection patterns were detected.")
    ai_analysis: Optional[AiAnalysisResult] = Field(None, description="Contextual AI-generated explanation and guidance.")
    status: str = Field("COMPLETED", description="Analysis completion status.")
