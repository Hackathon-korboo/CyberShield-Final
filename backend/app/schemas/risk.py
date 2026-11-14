"""Risk Assessment and Classification Schemas for Parts 14 and 15.

Defines authority levels, risk classifications, classified indicators, and assessment containers.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.evidence import CheckStatus, FindingSeverity


class AuthorityCategory(str, Enum):
    """Authority tier of an observed indicator."""

    AUTHORITATIVE = "AUTHORITATIVE"        # Authoritative external threat intelligence or verified malicious signature
    POLICY_VIOLATION = "POLICY_VIOLATION"  # Deterministic security policy violation (e.g. SSRF prohibited network)
    HEURISTIC = "HEURISTIC"                # Pattern matching, lexical regex, structural heuristics
    INFORMATIONAL = "INFORMATIONAL"        # Neutral factual observations
    INCONCLUSIVE = "INCONCLUSIVE"          # Incomplete, ambiguous, or failed checks


class RiskClassification(str, Enum):
    """Deterministic threat classifications for the unified risk engine."""

    LOW_RISK = "LOW_RISK"                    # No significant malicious indicators in checks performed
    SUSPICIOUS = "SUSPICIOUS"                # One or more indicators requiring further investigation
    HIGH_RISK = "HIGH_RISK"                  # Multiple significant indicators suggesting substantial threat
    CONFIRMED_MALICIOUS = "CONFIRMED_MALICIOUS" # Authoritative intelligence match or verified severe compromise
    INCONCLUSIVE = "INCONCLUSIVE"            # Insufficient information or critical checks failed/unavailable


class ClassifiedIndicator(BaseModel):
    """An individual security indicator enriched with authority and correlation metadata."""

    model_config = ConfigDict(extra="forbid")

    indicator_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the classified indicator.",
    )
    finding_id: str = Field(
        ...,
        description="ID of the upstream StandardizedFinding.",
    )
    title: str = Field(..., description="Short title of the indicator.")
    severity: FindingSeverity = Field(..., description="Assigned severity rating.")
    authority: AuthorityCategory = Field(..., description="Authority level of the evidence.")
    severity_basis: str = Field(..., description="Documented rationale for assigned severity and authority.")
    correlation_group: Optional[str] = Field(
        None,
        description="Group key for correlated indicators representing the same root cause.",
    )
    is_authoritative: bool = Field(False, description="True if evidence is authoritative confirmation of external maliciousness.")
    is_policy_violation: bool = Field(False, description="True if evidence represents an internal security policy violation (e.g. SSRF).")
    source: str = Field(..., description="Source module producing the indicator.")
    source_status: CheckStatus = Field(CheckStatus.COMPLETED, description="Status of the source check.")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Traceability and source provenance metadata.")


class ClassificationPackage(BaseModel):
    """Aggregated classification summary across all indicators in an EvidencePackage."""

    model_config = ConfigDict(extra="forbid")

    scan_id: str = Field(..., description="Correlation ID matching the scan session.")
    total_findings_processed: int = Field(..., ge=0)
    classified_indicators: List[ClassifiedIndicator] = Field(default_factory=list)
    coverage_score: float = Field(..., ge=0.0, le=1.0, description="Proportion of applicable checks completed.")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in assessment coverage and authority.")
    confidence_disclaimer: str = Field(
        default="Confidence score indicates verification completeness and evidence quality; it does not constitute proof of safety.",
        description="Mandatory disclaimer qualifying the confidence score.",
    )
    correlation_groups_detected: List[str] = Field(default_factory=list)


class DeterministicRiskAssessment(BaseModel):
    """Output of the deterministic risk evaluation engine."""

    model_config = ConfigDict(extra="forbid")

    scan_id: str = Field(..., description="Scan correlation ID.")
    target: str = Field(..., description="Target evaluated.")
    target_type: str = Field(..., description="url, email, sms.")
    classification: RiskClassification = Field(..., description="Deterministic threat classification.")
    risk_score: Optional[int] = Field(None, ge=0, le=100, description="Quantitative risk score (0-100) or null if inconclusive.")
    method: str = Field(
        default="CYBERSHIELD_SEVERITY_FLOOR_AUTHORITY_V2",
        description="Deterministic calculation methodology.",
    )
    summary: str = Field(..., description="1-2 sentence high-level summary of risk determination.")
    explanation: str = Field(..., description="Detailed explanation grounded in empirical observations.")
    supporting_evidence: List[str] = Field(default_factory=list, description="Concrete citations from findings.")
    correlation_groups: List[str] = Field(default_factory=list, description="Triggered correlation groups.")
    has_conflicting_evidence: bool = Field(False, description="True if conflicting findings were detected.")
    has_policy_violation: bool = Field(False, description="True if target triggered a security policy violation (e.g. SSRF).")
    has_authoritative_match: bool = Field(False, description="True if determination is backed by authoritative threat intelligence.")
    coverage_score: float = Field(..., ge=0.0, le=1.0, description="Check execution coverage.")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Calibrated confidence score.")
    rules_triggered: List[str] = Field(default_factory=list, description="List of rule IDs triggered.")
