"""FastAPI dependency injection providers for CyberShield AI 2.0."""

from functools import lru_cache
from typing import Annotated
from fastapi import Depends
from backend.app.core.config import Settings, get_settings
from backend.app.services.threat_service import ThreatAnalysisService


def get_current_settings() -> Settings:
    """Dependency that returns the application configuration singleton."""
    return get_settings()


@lru_cache
def get_threat_service() -> ThreatAnalysisService:
    """Dependency that returns the ThreatAnalysisService singleton."""
    return ThreatAnalysisService()


SettingsDep = Annotated[Settings, Depends(get_current_settings)]
ThreatServiceDep = Annotated[ThreatAnalysisService, Depends(get_threat_service)]
