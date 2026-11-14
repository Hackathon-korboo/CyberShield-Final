"""CyberShield AI 2.0 — Member 2 AI Scam Intelligence & Security Routes.

Provides endpoints for text scam detection, safe static file inspection,
PII redaction, prompt injection defense, external provider configuration,
and live multi-member integration telemetry.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request, status
from pydantic import BaseModel, Field

from backend.app.schemas.threat_models import (
    ScamAnalysisRequest,
    ScamAnalysisResponse,
    FileThreatAnalysisResponse,
    ThreatCategory,
    PIIEntity,
)
from backend.app.services.scam_threat_service import threat_service_instance
from backend.app.services.file_service import file_service_instance
from backend.app.services.config_service import (
    config_service_instance,
    PROVIDER_METADATA,
)
from backend.app.privacy.pii_redactor import redact_pii
from backend.app.security.prompt_guard import inspect_prompt_injection

router = APIRouter()


# ==============================================================================
# Security Dependencies
# ==============================================================================

def verify_localhost_client(request: Request) -> None:
    """Restrict administrative configuration endpoints to localhost clients."""
    client_host = request.client.host if request.client else None
    allowed_hosts = {"127.0.0.1", "::1", "localhost", "testclient"}
    if client_host and client_host not in allowed_hosts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative configuration restricted to localhost clients only."
        )


# ==============================================================================
# Request / Response Schemas
# ==============================================================================

class StandaloneRedactRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000, description="Text to redact PII from")


class StandaloneRedactResponse(BaseModel):
    redacted_text: str
    entities: List[PIIEntity]
    total_entities: int


class InjectionCheckRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000, description="Text to check for prompt injection")


class InjectionCheckResponse(BaseModel):
    is_injection_detected: bool
    risk_score: float
    signatures_detected: List[str]


class ProviderTestRequest(BaseModel):
    provider_id: str = Field(..., description="Provider identifier: 'gemini', 'virustotal', or 'safebrowsing'")
    api_key: Optional[str] = Field(None, description="Optional raw key to test without saving. Uses saved key if omitted.")


class ProviderTestResponse(BaseModel):
    provider_id: str
    status: str
    connected: bool
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class SaveConfigRequest(BaseModel):
    gemini_api_key: Optional[str] = Field(None, description="Google Gemini API key")
    virustotal_api_key: Optional[str] = Field(None, description="VirusTotal API key")
    google_safebrowsing_api_key: Optional[str] = Field(None, description="Google Safe Browsing API key")


class SaveConfigResponse(BaseModel):
    success: bool
    message: str
    updated_providers: List[str]


# ==============================================================================
# Scam & Threat Intelligence Endpoints
# ==============================================================================

@router.post(
    "/analyze/text",
    response_model=ScamAnalysisResponse,
    status_code=status.HTTP_200_OK,
    tags=["Threat Intelligence"]
)
def analyze_scam_text(request: ScamAnalysisRequest) -> ScamAnalysisResponse:
    """
    Execute complete evidence-based scam and threat analysis on text content.
    Automatically handles PII minimization, prompt injection defense, and Gemini fallback.
    """
    if not request.content or not request.content.strip():
        raise HTTPException(
            status_code=422,
            detail="Content must not be empty or whitespace only."
        )
    try:
        response = threat_service_instance.analyze(request)
        return response
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis pipeline error: {str(exc)}"
        )


@router.post(
    "/analyze/file",
    response_model=FileThreatAnalysisResponse,
    status_code=status.HTTP_200_OK,
    tags=["File Threat Analysis"]
)
async def analyze_file(file: UploadFile = File(...)) -> FileThreatAnalysisResponse:
    """
    Perform safe, non-execution static inspection on an uploaded file.
    Validates MIME type, magic bytes, SHA-256 hash, disguised executables, and archive safety.
    """
    try:
        content = await file.read()
        filename = file.filename or "unknown_file"
        response = file_service_instance.inspect_file(filename=filename, content=content)
        return response
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File inspection error: {str(exc)}"
        )


@router.post(
    "/privacy/redact",
    response_model=StandaloneRedactResponse,
    tags=["Privacy & Security"]
)
def standalone_redact_pii(request: StandaloneRedactRequest) -> StandaloneRedactResponse:
    """Standalone utility to detect and redact sensitive PII (PAN, Aadhaar, Cards, UPI, Phones, Emails)."""
    sanitized, entities = redact_pii(request.text)
    return StandaloneRedactResponse(
        redacted_text=sanitized,
        entities=entities,
        total_entities=len(entities)
    )


@router.post(
    "/security/check-injection",
    response_model=InjectionCheckResponse,
    tags=["Privacy & Security"]
)
def standalone_check_injection(request: InjectionCheckRequest) -> InjectionCheckResponse:
    """Standalone utility to detect prompt injection, jailbreaks, or instruction overrides."""
    is_inj, score, sigs = inspect_prompt_injection(request.text)
    return InjectionCheckResponse(
        is_injection_detected=is_inj,
        risk_score=score,
        signatures_detected=sigs
    )


# ==============================================================================
# Credential Configuration & Live Testing Endpoints
# ==============================================================================

@router.get("/config/providers", tags=["Configuration Wizard"])
def get_providers_config_status() -> Dict[str, Any]:
    """Retrieve current configuration status and masked credential states."""
    return config_service_instance.get_all_providers_status()


@router.post(
    "/config/test",
    response_model=ProviderTestResponse,
    tags=["Configuration Wizard"],
    dependencies=[Depends(verify_localhost_client)]
)
def test_provider_connection(request: ProviderTestRequest) -> ProviderTestResponse:
    """
    Perform a live backend connection test against an external cybersecurity provider.
    Protected to localhost requests only.
    """
    if request.provider_id not in PROVIDER_METADATA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider_id '{request.provider_id}'. Supported: {list(PROVIDER_METADATA.keys())}"
        )
    res = config_service_instance.test_connection(
        provider_id=request.provider_id,
        api_key=request.api_key
    )
    return ProviderTestResponse(**res)


@router.post(
    "/config/save",
    response_model=SaveConfigResponse,
    tags=["Configuration Wizard"],
    dependencies=[Depends(verify_localhost_client)]
)
def save_provider_credentials(request: SaveConfigRequest) -> SaveConfigResponse:
    """
    Persist verified credentials securely into local .env.
    Protected to localhost requests only.
    """
    res = config_service_instance.save_credentials(
        gemini_api_key=request.gemini_api_key,
        virustotal_api_key=request.virustotal_api_key,
        google_safebrowsing_api_key=request.google_safebrowsing_api_key
    )
    return SaveConfigResponse(**res)


# ==============================================================================
# Metadata & Integrations Endpoints
# ==============================================================================

@router.get("/meta/categories", tags=["System"])
def list_threat_categories() -> Dict[str, List[str]]:
    """List all supported threat categories recognized by CyberShield AI 2.0."""
    return {
        "categories": [c.value for c in ThreatCategory]
    }


@router.get("/integrations", tags=["System"])
def get_integrations_status() -> Dict[str, Any]:
    """Return live status of the 4-member integration architecture."""
    from integrations.registry import registry
    return registry.get_all_statuses()
