"""Standardized Evidence and Finding Models for Part 13.

Defines a common, reusable finding structure and check status lifecycle for all
upstream technical investigations, heuristic engines, and intelligence feeds.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


def get_utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class CheckStatus(str, Enum):
    """Execution state of a technical verification or intelligence check."""

    COMPLETED = "COMPLETED"
    UNAVAILABLE = "UNAVAILABLE"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PARTIAL = "PARTIAL"


class FindingSeverity(str, Enum):
    """Standardized finding severity ratings."""

    INFORMATIONAL = "INFORMATIONAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FindingType(str, Enum):
    """Categorization of standardized technical observations."""

    URL_PATTERN = "URL_PATTERN"
    DNS_INVESTIGATION = "DNS_INVESTIGATION"
    REDIRECT_ANALYSIS = "REDIRECT_ANALYSIS"
    TLS_ANALYSIS = "TLS_ANALYSIS"
    HTTP_HEADERS = "HTTP_HEADERS"
    THREAT_INTELLIGENCE = "THREAT_INTELLIGENCE"
    SSRF_GUARD = "SSRF_GUARD"
    EMAIL_PATTERN = "EMAIL_PATTERN"
    SMS_PATTERN = "SMS_PATTERN"
    AI_INFERENCE = "AI_INFERENCE"


class StandardizedFinding(BaseModel):
    """Standardized finding representing an empirical observation or rule match."""

    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the standardized finding.",
    )
    finding_type: FindingType = Field(
        ...,
        description="Broad category of the technical investigation.",
    )
    severity: FindingSeverity = Field(
        ...,
        description="Standardized severity rating of the finding.",
    )
    title: str = Field(
        ...,
        description="Concise, descriptive title for the observation.",
    )
    description: str = Field(
        ...,
        description="Detailed plain-text explanation of what was observed.",
    )
    observed_evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="Empirical, unmanipulated evidence values or tokens.",
    )
    source: str = Field(
        ...,
        description="Name of the service or component generating the finding.",
    )
    source_status: CheckStatus = Field(
        default=CheckStatus.COMPLETED,
        description="Operational state of the source service during check.",
    )
    timestamp: datetime = Field(
        default_factory=get_utc_now,
        description="Timezone-aware UTC timestamp when observation occurred.",
    )
    related_indicators: List[str] = Field(
        default_factory=list,
        description="Cross-referenced deterministic rule IDs or indicator keys.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Supplementary contextual metadata or correlation keys.",
    )


class EvidencePackage(BaseModel):
    """Aggregated container of standardized findings and check statuses."""

    model_config = ConfigDict(extra="forbid")

    scan_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique correlation ID for the evidence collection session.",
    )
    target: str = Field(
        ...,
        description="Target subject analyzed (sanitized URL, email, or message).",
    )
    target_type: str = Field(
        ...,
        description="Type of submission (url, email, sms).",
    )
    timestamp: datetime = Field(
        default_factory=get_utc_now,
        description="UTC timestamp of evidence collection.",
    )
    findings: List[StandardizedFinding] = Field(
        default_factory=list,
        description="Deduplicated list of standardized technical findings.",
    )
    check_statuses: Dict[str, CheckStatus] = Field(
        default_factory=dict,
        description="Explicit execution status of each upstream investigation module.",
    )
