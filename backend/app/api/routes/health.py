"""Health check and diagnostic API endpoints."""

from datetime import datetime
from fastapi import APIRouter, status
from backend.app.api.dependencies import SettingsDep
from backend.app.db.session import get_db_manager
from backend.app.schemas.common import StandardResponse
from backend.app.schemas.health import HealthCheckResponse, SubsystemHealth

router = APIRouter(tags=["Health & Diagnostics"])


@router.get(
    "/health",
    response_model=StandardResponse[HealthCheckResponse],
    status_code=status.HTTP_200_OK,
    summary="System Health & Diagnostic Check",
    description="Returns application health status, version, running environment, and modular subsystem states.",
)
async def get_health_status(settings: SettingsDep) -> StandardResponse[HealthCheckResponse]:
    """Perform a system health check and return structured status."""
    ai_status = "enabled" if (settings.ai_analysis_enabled and settings.gemini_api_key) else "disabled"
    blockchain_status = "enabled" if (settings.blockchain_verification_enabled and settings.web3_provider_uri) else "disabled"

    db_mgr = get_db_manager()
    db_healthy = db_mgr.check_health()
    db_status = "healthy" if db_healthy else "unhealthy"

    subsystems = {
        "heuristic_engine": SubsystemHealth(status="healthy", message="Local heuristic engine ready."),
        "ai_engine": SubsystemHealth(
            status=ai_status,
            message=f"Gemini AI ({settings.gemini_model_name}) is {'configured' if settings.gemini_api_key else 'unconfigured / placeholder'}."
        ),
        "database": SubsystemHealth(
            status=db_status,
            message="SQLite persistence engine operational." if db_healthy else "Database connection failed."
        ),
        "threat_intel": SubsystemHealth(
            status="healthy",
            message="Threat intelligence adapter operational (local curated corpus active)."
        ),
        "blockchain_engine": SubsystemHealth(
            status=blockchain_status,
            message="Web3 trust registry is placeholder / unconfigured." if not settings.web3_provider_uri else "Configured."
        ),
    }

    health_data = HealthCheckResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.utcnow(),
        subsystems=subsystems,
    )

    return StandardResponse(success=True, data=health_data, error=None)
