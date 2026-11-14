"""
CyberShield AI 2.0 - Member 2 Threat Models & Pydantic Schemas
Strict typing, evidence separation, risk classification, IOC extraction,
VirusTotal intelligence enrichment, and zero-trust data models.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ThreatCategory(str, Enum):
    """Supported cybersecurity threat and fraud categories."""
    PHISHING_EMAIL = "PHISHING_EMAIL"
    SCAM_SMS = "SCAM_SMS"
    KYC_PHISHING = "KYC_PHISHING"
    FAKE_JOB_OFFER = "FAKE_JOB_OFFER"
    FAKE_INTERNSHIP = "FAKE_INTERNSHIP"
    ADVANCE_FEE_FRAUD = "ADVANCE_FEE_FRAUD"
    LOTTERY_SCAM = "LOTTERY_SCAM"
    OTP_THEFT = "OTP_THEFT"
    CREDENTIAL_HARVESTING = "CREDENTIAL_HARVESTING"
    BANKING_FRAUD = "BANKING_FRAUD"
    UPI_PAYMENT_FRAUD = "UPI_PAYMENT_FRAUD"
    INVESTMENT_SCAM = "INVESTMENT_SCAM"
    DELIVERY_SCAM = "DELIVERY_SCAM"
    ELECTRICITY_BILL_SCAM = "ELECTRICITY_BILL_SCAM"
    IMPERSONATION = "IMPERSONATION"
    SOCIAL_ENGINEERING = "SOCIAL_ENGINEERING"
    SUSPICIOUS_ATTACHMENT = "SUSPICIOUS_ATTACHMENT"
    PROMPT_INJECTION_ATTEMPT = "PROMPT_INJECTION_ATTEMPT"
    SUSPICIOUS_MESSAGE = "SUSPICIOUS_MESSAGE"
    BENIGN_MESSAGE = "BENIGN_MESSAGE"
    BENIGN = "BENIGN"


class RiskLevel(str, Enum):
    """Categorical risk assessment."""
    BENIGN = "BENIGN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class UrgencyLevel(str, Enum):
    """Urgency of recommended mitigation action."""
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    IMMEDIATE = "IMMEDIATE"


class EvidenceItem(BaseModel):
    """Structured observable evidence separated from subjective analysis."""
    indicator: str = Field(..., description="High-level indicator name, e.g., 'Urgent threat of account deactivation'")
    description: str = Field(..., description="Detailed explanation of the observed artifact")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this specific indicator (0.0 - 1.0)")
    category: ThreatCategory = Field(..., description="Category this evidence belongs to")
    raw_snippet: Optional[str] = Field(None, description="Exact or masked text excerpt highlighting the indicator")
    severity: Optional[str] = Field(default=None, description="Indicator severity tier: CRITICAL, HIGH, MEDIUM, LOW")
    correlation_group: Optional[str] = Field(default=None, description="Correlation group identifier to prevent double counting")


class MitigationStep(BaseModel):
    """Actionable advice for the user to safeguard themselves."""
    action: str = Field(..., description="Concise headline of what action to take")
    urgency: UrgencyLevel = Field(..., description="Urgency priority")
    details: str = Field(..., description="Detailed execution instruction for user safety")


class PIIEntity(BaseModel):
    """Entity detected and redacted for privacy protection."""
    entity_type: str = Field(..., description="Type of PII (e.g. PHONE, EMAIL, CARD_NUMBER, UPI_ID, OTP)")
    masked_value: str = Field(..., description="Masked representation of redacted entity")
    occurrences: int = Field(default=1, description="Number of instances found")


class ExtractedIOCs(BaseModel):
    """Extracted network, communication, and financial indicators of compromise."""
    urls: List[str] = Field(default_factory=list, description="Extracted web URLs")
    domains: List[str] = Field(default_factory=list, description="Extracted network domains")
    emails: List[str] = Field(default_factory=list, description="Extracted email addresses")
    phones: List[str] = Field(default_factory=list, description="Extracted phone numbers")
    upi_ids: List[str] = Field(default_factory=list, description="Extracted UPI payment IDs")


# ==============================================================================
# Scam Analysis Schemas
# ==============================================================================

class ScamAnalysisRequest(BaseModel):
    """Incoming request for scam and social engineering analysis."""
    content: str = Field(..., min_length=1, max_length=50000, description="Raw suspicious message, email, SMS or chat")
    source_type: Optional[str] = Field(default="unknown", description="Source format: email, sms, chat, job_offer, payment_request")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata such as sender address, timestamp")
    enable_gemini: bool = Field(default=True, description="Whether to query Gemini API (falls back automatically if offline)")
    enable_virustotal: bool = Field(default=True, description="Whether to query VirusTotal for domain/URL reputation when configured")
    redact_pii: bool = Field(default=True, description="Whether to redact PII prior to AI processing")


class ScamAnalysisResponse(BaseModel):
    """Comprehensive, evidence-based threat assessment response."""
    analysis_id: str = Field(..., description="Unique UUID for this analysis session")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    risk_level: RiskLevel = Field(..., description="Categorical severity rating")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Normalized risk score from 0 (Safe) to 100 (Critical)")
    primary_category: ThreatCategory = Field(..., description="Most dominant threat category identified")
    detected_categories: List[ThreatCategory] = Field(default_factory=list, description="All threat categories detected")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence rating")
    observed_evidence: List[EvidenceItem] = Field(default_factory=list, description="Strictly observed empirical evidence")
    ai_assessment: str = Field(..., description="Synthesized technical assessment of the threat")
    uncertainty_factors: List[str] = Field(default_factory=list, description="Identified unknowns or ambiguity factors")
    mitigation_recommendations: List[MitigationStep] = Field(default_factory=list, description="Actionable countermeasures")
    pii_redacted_content: Optional[str] = Field(None, description="Text sanitized of sensitive PII data")
    pii_entities_found: List[PIIEntity] = Field(default_factory=list, description="Catalog of PII entities identified")
    iocs: Optional[ExtractedIOCs] = Field(None, description="Extracted indicators of compromise (URLs, domains, emails, phones)")
    external_threat_intel: Optional[Dict[str, Any]] = Field(None, description="Enriched threat intelligence (e.g. VirusTotal results)")
    engine_used: str = Field(..., description="Engine utilized: 'gemini-3.8-flash', 'heuristic-fallback-engine', or 'hybrid-ensemble'")
    prompt_injection_detected: bool = Field(default=False, description="Flag indicating whether an instruction override attempt was detected")
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")

    # Compatibility aliases matching various consumer expectations
    classification: Optional[str] = None
    explanation: Optional[str] = None
    security_checks: Optional[Dict[str, Any]] = None
    limitations_and_uncertainty: Optional[List[str]] = None
    has_authoritative_match: bool = False
    verdict: Optional[str] = None
    coverage_score: float = 1.0
    why_flagged: List[str] = Field(default_factory=list)


# ==============================================================================
# File Analysis Schemas
# ==============================================================================

class ArchiveEntryInfo(BaseModel):
    """Metadata regarding an individual file within an archive."""
    filename: str
    size_bytes: int
    compressed_size_bytes: int
    is_suspicious_extension: bool
    is_directory: bool
    flags: List[str] = Field(default_factory=list)


class ArchiveReport(BaseModel):
    """Safe inspection breakdown of compressed archives (ZIP, TAR)."""
    total_files: int
    uncompressed_size_bytes: int
    compression_ratio: float
    is_zip_bomb: bool
    has_traversal_attack: bool
    suspicious_files: List[str] = Field(default_factory=list)
    entries: List[ArchiveEntryInfo] = Field(default_factory=list)


class FileThreatAnalysisResponse(BaseModel):
    """Static safe analysis of submitted file without code execution."""
    analysis_id: str
    filename: str
    file_size_bytes: int
    sha256: str
    md5: str
    mime_type: str
    detected_file_type: str
    magic_bytes_hex: str
    is_executable: bool
    is_archive: bool
    archive_report: Optional[ArchiveReport] = None
    risk_level: RiskLevel
    risk_score: float = Field(..., ge=0.0, le=100.0)
    suspicious_indicators: List[str] = Field(default_factory=list)
    known_malicious_hash: bool = False
    virustotal_report: Optional[Dict[str, Any]] = None
    disclaimer: str = Field(
        default="SAFE STATIC ANALYSIS ONLY: Uploaded file is never executed. "
                "Static signatures and structural indicators do not replace a full kernel-level AV solution."
    )
    processing_time_ms: float
