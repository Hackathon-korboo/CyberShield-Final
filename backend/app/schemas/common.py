"""Common Pydantic data schemas for CyberShield AI 2.0.

Provides standard response wrappers, error details, and metadata containers.
"""

from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Specific field or contextual error detail."""

    model_config = ConfigDict(extra="forbid")

    field: Optional[str] = Field(None, description="Field path causing the error if applicable.")
    message: str = Field(..., description="Specific error explanation.")
    error_code: Optional[str] = Field(None, description="Granular application error code.")


class ErrorEnvelope(BaseModel):
    """Standardized error envelope payload."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., description="High-level category code (e.g. VALIDATION_ERROR, NOT_FOUND).")
    message: str = Field(..., description="Human-readable summary of the error.")
    correlation_id: Optional[str] = Field(None, description="Unique request tracing correlation ID.")
    details: List[ErrorDetail] = Field(default_factory=list, description="List of granular error details.")


class StandardResponse(BaseModel, Generic[T]):
    """Standardized top-level response envelope for CyberShield AI 2.0 API."""

    model_config = ConfigDict(extra="forbid")

    success: bool = Field(True, description="Indicates whether the request completed successfully.")
    data: Optional[T] = Field(None, description="Response payload data.")
    error: Optional[ErrorEnvelope] = Field(None, description="Error details if success is false.")
