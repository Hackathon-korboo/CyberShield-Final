"""SMS / Text message threat analysis request schemas."""

import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SmsAnalysisRequest(BaseModel):
    """Payload for submitting an SMS or chat message for fraud and scam analysis."""

    model_config = ConfigDict(extra="forbid")

    sender: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Optional sender phone number, shortcode, or display header.",
        examples=["+18005550199"],
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Text content of the SMS or message.",
        examples=["URGENT: Your account has been suspended. Send OTP 4492 to verify."],
    )

    @field_validator("message")
    @classmethod
    def validate_message_not_empty(cls, v: str) -> str:
        """Ensure message is not empty or composed solely of whitespace."""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Message cannot be empty or solely whitespace.")
        if "\x00" in cleaned:
            raise ValueError("Message contains illegal null bytes.")
        return cleaned
