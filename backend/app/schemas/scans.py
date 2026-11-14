"""Request and response schemas for Core API Scans (Part 17).

Provides strict Pydantic validation, boundary checks, and scheme validation
for URL scanning, scan retrieval, and cryptographic report verification.
"""

import re
from typing import Any, List, Optional
import urllib.parse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.schemas.unified_report import UnifiedThreatReport
from backend.app.services.blockchain.adapter import ReportVerificationResult

SUPPORTED_SCHEMES = {"http", "https"}


class ScanUrlRequest(BaseModel):
    """Request payload for submitting a URL for deep threat inspection."""

    model_config = ConfigDict(extra="forbid")

    url: str = Field(
        ...,
        min_length=3,
        max_length=2048,
        description="Target web URL to submit for security inspection.",
        examples=["https://example.com/login", "http://192.168.1.1/admin"],
    )

    @field_validator("url")
    @classmethod
    def validate_url_syntax(cls, v: str) -> str:
        """Validate URL scheme and syntax, rejecting unsupported or dangerous protocols."""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("URL cannot be empty or whitespace.")

        # Check for scheme prefix
        if "://" not in cleaned:
            raise ValueError("Invalid URL: Missing scheme (e.g., 'https://' or 'http://').")

        parsed = urllib.parse.urlsplit(cleaned)
        scheme = parsed.scheme.lower()
        if scheme not in SUPPORTED_SCHEMES:
            raise ValueError(
                f"Unsupported URL scheme '{scheme}'. Only HTTP and HTTPS are permitted."
            )

        if not parsed.netloc:
            raise ValueError("Invalid URL: Hostname cannot be empty.")

        return cleaned


class ScanHistoryResponse(BaseModel):
    """Paginated scan report history response."""

    model_config = ConfigDict(extra="forbid")

    reports: List[UnifiedThreatReport] = Field(default_factory=list)
    total: int = Field(..., ge=0)
    limit: int = Field(..., ge=1, le=100)
    offset: int = Field(..., ge=0)


class VerifyReportRequest(BaseModel):
    """Request for verifying cryptographic report integrity."""

    model_config = ConfigDict(extra="forbid")

    scan_id: Optional[str] = Field(None, description="Unique scan identifier to verify from database.")
    report: Optional[UnifiedThreatReport] = Field(None, description="Direct report payload to verify.")
