"""System health check schemas for CyberShield AI 2.0."""

from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field


class SubsystemHealth(BaseModel):
    """Health status of an individual subsystem."""

    status: str = Field(..., description="Status of the subsystem: healthy, degraded, or disabled.")
    message: Optional[str] = Field(None, description="Optional diagnostic message.")


class HealthCheckResponse(BaseModel):
    """Overall system health and environment diagnostic payload."""

    status: str = Field("healthy", description="Overall health state (healthy, degraded, unhealthy).")
    version: str = Field(..., description="Application semantic version.")
    environment: str = Field(..., description="Running environment (development, staging, production).")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of the check.")
    subsystems: Dict[str, SubsystemHealth] = Field(
        default_factory=dict, description="Status of individual modular subsystems."
    )
