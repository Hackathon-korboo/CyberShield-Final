"""URL threat analysis request schemas."""

import re
from pydantic import BaseModel, ConfigDict, Field, field_validator


class UrlAnalysisRequest(BaseModel):
    """Payload for submitting a URL for threat and SSRF analysis."""

    model_config = ConfigDict(extra="forbid")

    url: str = Field(
        ...,
        min_length=3,
        max_length=2048,
        description="Target URL to analyze (e.g. https://example.com/path).",
        examples=["https://example.com/verify-account"],
    )

    @field_validator("url")
    @classmethod
    def validate_url_syntax(cls, v: str) -> str:
        """Validate URL string and ensure safe basic structure."""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("URL cannot be empty or solely whitespace.")
        
        # Check for control characters or line breaks
        if re.search(r"[\r\n\t\x00]", cleaned):
            raise ValueError("URL contains illegal control characters or line breaks.")
        
        # If scheme is present, must be http or https
        scheme_match = re.match(r"^([a-zA-Z][a-zA-Z0-9+\-.]*):", cleaned)
        if scheme_match:
            scheme = scheme_match.group(1).lower()
            if scheme not in ("http", "https"):
                raise ValueError(f"Unsupported URL scheme '{scheme}'. Only http and https are permitted.")
        
        return cleaned
