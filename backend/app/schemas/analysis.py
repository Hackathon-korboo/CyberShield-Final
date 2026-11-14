"""Core threat analysis response schemas, enums, and indicator models.

Enforces clear separation between observed factual evidence and heuristic findings.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


def get_utc_now() -> datetime:
    """Return timezone-aware UTC datetime for standardized ISO 8601 serialization."""
    return datetime.now(timezone.utc)


class RiskLevel(str, Enum):
    """Deterministic threat evaluation classification."""

    CLEAN = "CLEAN"
    LOW_RISK = "LOW_RISK"
    SUSPICIOUS = "SUSPICIOUS"
    HIGH_RISK = "HIGH_RISK"


class IndicatorCategory(str, Enum):
    """Categorization of detected threat rules."""

    HOMOGLYPH_SPOOFING = "HOMOGLYPH_SPOOFING"
    SUSPICIOUS_KEYWORD = "SUSPICIOUS_KEYWORD"
    IP_HOST = "IP_HOST"
    CREDENTIAL_HARVESTING = "CREDENTIAL_HARVESTING"
    URGENCY_LURE = "URGENCY_LURE"
    PAYMENT_LURE = "PAYMENT_LURE"
    OTP_HARVESTING = "OTP_HARVESTING"
    JOB_SCAM = "JOB_SCAM"
    SSRF_ATTEMPT = "SSRF_ATTEMPT"
    SUSPICIOUS_TLD = "SUSPICIOUS_TLD"


class IndicatorSeverity(str, Enum):
    """Severity tier for a triggered security rule."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SecurityIndicator(BaseModel):
    """Detailed record of an individual triggered security rule."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(..., description="Unique deterministic rule identifier.")
    category: IndicatorCategory = Field(..., description="Threat category.")
    severity: IndicatorSeverity = Field(..., description="Severity rating of the indicator.")
    evidence: str = Field(..., description="Exact substring or token that triggered the rule.")
    explanation: str = Field(..., description="Human-readable description of why this is an indicator.")
    mitigation: str = Field(..., description="Recommended defensive action for the user.")


class HeuristicFindings(BaseModel):
    """Aggregated heuristic scoring and triggered indicators."""

    model_config = ConfigDict(extra="forbid")

    risk_level: RiskLevel = Field(..., description="Synthesized deterministic risk level.")
    risk_score: int = Field(..., ge=0, le=100, description="Heuristic threat score from 0 (clean) to 100 (critical).")
    indicators: List[SecurityIndicator] = Field(default_factory=list, description="List of triggered indicators.")


class UrlObservedEvidence(BaseModel):
    """Empirical observations extracted from URL inspection."""

    model_config = ConfigDict(extra="forbid")

    normalized_url: str = Field(..., description="Normalized URL string.")
    scheme: str = Field(..., description="URL scheme (http/https).")
    hostname: str = Field(..., description="Extracted hostname.")
    port: int = Field(..., description="Target port.")
    path: str = Field(..., description="URL path component.")
    query: Optional[str] = Field(None, description="URL query string.")
    resolved_ips: List[str] = Field(default_factory=list, description="Resolved IP addresses from safe DNS preflight.")
    is_ip_hostname: bool = Field(False, description="True if hostname is a direct IP literal.")
    ssrf_safe: bool = Field(True, description="True if destination passed SSRF preflight checks.")
    has_homoglyphs: bool = Field(False, description="True if homoglyph or lookalike characters detected.")


class EmailObservedEvidence(BaseModel):
    """Empirical observations extracted from email inspection."""

    model_config = ConfigDict(extra="forbid")

    sender_domain: Optional[str] = Field(None, description="Domain extracted from sender address.")
    extracted_urls: List[str] = Field(default_factory=list, description="URLs extracted from subject or body.")
    extracted_phones: List[str] = Field(default_factory=list, description="Phone numbers extracted from body.")
    body_length: int = Field(..., description="Character count of email body.")


class SmsObservedEvidence(BaseModel):
    """Empirical observations extracted from SMS message inspection."""

    model_config = ConfigDict(extra="forbid")

    extracted_urls: List[str] = Field(default_factory=list, description="URLs extracted from message text.")
    extracted_phones: List[str] = Field(default_factory=list, description="Phone numbers extracted from message text.")
    message_length: int = Field(..., description="Character count of SMS message.")


class UrlAnalysisResponse(BaseModel):
    """Complete URL threat analysis result."""

    model_config = ConfigDict(extra="forbid")

    target: str = Field(..., description="Target URL submitted for analysis.")
    target_type: str = Field("url", description="Type of target analyzed.")
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique analysis correlation ID.")
    timestamp: datetime = Field(default_factory=get_utc_now, description="UTC timestamp of completion.")
    observed_evidence: UrlObservedEvidence = Field(..., description="Empirical, verifiable facts.")
    heuristic_findings: HeuristicFindings = Field(..., description="Rule-based heuristic evaluation.")
    status: str = Field("COMPLETED", description="Analysis completion status.")


class EmailAnalysisResponse(BaseModel):
    """Complete email threat analysis result."""

    model_config = ConfigDict(extra="forbid")

    target: str = Field(..., description="Sender or subject identifier.")
    target_type: str = Field("email", description="Type of target analyzed.")
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique analysis correlation ID.")
    timestamp: datetime = Field(default_factory=get_utc_now, description="UTC timestamp of completion.")
    observed_evidence: EmailObservedEvidence = Field(..., description="Empirical observations from email content.")
    heuristic_findings: HeuristicFindings = Field(..., description="Rule-based heuristic evaluation.")
    status: str = Field("COMPLETED", description="Analysis completion status.")


class SmsAnalysisResponse(BaseModel):
    """Complete SMS / text threat analysis result."""

    model_config = ConfigDict(extra="forbid")

    target: str = Field(..., description="Message snippet or sender identifier.")
    target_type: str = Field("sms", description="Type of target analyzed.")
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique analysis correlation ID.")
    timestamp: datetime = Field(default_factory=get_utc_now, description="UTC timestamp of completion.")
    observed_evidence: SmsObservedEvidence = Field(..., description="Empirical observations from SMS content.")
    heuristic_findings: HeuristicFindings = Field(..., description="Rule-based heuristic evaluation.")
    status: str = Field("COMPLETED", description="Analysis completion status.")
