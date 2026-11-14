"""Email threat analysis request schemas."""

import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class EmailAnalysisRequest(BaseModel):
    """Payload for submitting an email message for phishing and threat indicator analysis."""

    model_config = ConfigDict(extra="forbid")

    subject: Optional[str] = Field(
        default=None,
        max_length=256,
        description="Optional subject line of the email.",
        examples=["Immediate action required: Verify your billing info"],
    )
    sender: Optional[str] = Field(
        default=None,
        max_length=256,
        description="Optional sender email address or display name.",
        examples=["Security Alert <support@billing-update-center.com>"],
    )
    body: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Full text or content body of the email.",
        examples=["Dear user, click https://verify-bank.com/login to restore access."],
    )

    @field_validator("body")
    @classmethod
    def validate_body_not_empty(cls, v: str) -> str:
        """Ensure body has readable non-whitespace text."""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Email body cannot be empty or solely whitespace.")
        if "\x00" in cleaned:
            raise ValueError("Email body contains illegal null bytes.")
        return cleaned
