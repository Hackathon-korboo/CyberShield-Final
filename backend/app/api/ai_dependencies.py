"""Dependency injection providers for AI threat services."""

from typing import Annotated
from fastapi import Depends

from backend.app.services.ai_service import AIThreatService

# Shared singleton instance
_ai_service_instance: AIThreatService | None = None


def get_ai_threat_service() -> AIThreatService:
    """Provide singleton AIThreatService instance."""
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIThreatService()
    return _ai_service_instance


AIThreatServiceDep = Annotated[AIThreatService, Depends(get_ai_threat_service)]
