"""AI-Augmented threat analysis API routes for URL, Email, and SMS."""

from fastapi import APIRouter, status

from backend.app.api.ai_dependencies import AIThreatServiceDep
from backend.app.engines.ai.schemas import ProviderHealthStatus
from backend.app.schemas.common import StandardResponse
from backend.app.schemas.composite import (
    CompositeEmailAnalysisResponse,
    CompositeSmsAnalysisResponse,
    CompositeUrlAnalysisResponse,
)
from backend.app.schemas.email import EmailAnalysisRequest
from backend.app.schemas.sms import SmsAnalysisRequest
from backend.app.schemas.url import UrlAnalysisRequest

router = APIRouter(prefix="/analyze/ai", tags=["AI Threat Analysis"])


@router.post(
    "/url",
    response_model=StandardResponse[CompositeUrlAnalysisResponse],
    status_code=status.HTTP_200_OK,
    summary="AI-Augmented URL Threat Analysis",
    description="Validates URL syntax, performs preflight SSRF check, executes deterministic rules, and enriches with Gemini AI contextual reasoning.",
)
async def analyze_url_with_ai(
    request: UrlAnalysisRequest,
    service: AIThreatServiceDep,
) -> StandardResponse[CompositeUrlAnalysisResponse]:
    """Execute AI-augmented URL threat analysis."""
    result = await service.analyze_url(request)
    return StandardResponse(success=True, data=result, error=None)


@router.post(
    "/email",
    response_model=StandardResponse[CompositeEmailAnalysisResponse],
    status_code=status.HTTP_200_OK,
    summary="AI-Augmented Email Phishing Analysis",
    description="Extracts indicators from email, evaluates deterministic phishing rules, and enriches with Gemini AI social engineering explanations.",
)
async def analyze_email_with_ai(
    request: EmailAnalysisRequest,
    service: AIThreatServiceDep,
) -> StandardResponse[CompositeEmailAnalysisResponse]:
    """Execute AI-augmented email threat analysis."""
    result = await service.analyze_email(request)
    return StandardResponse(success=True, data=result, error=None)


@router.post(
    "/sms",
    response_model=StandardResponse[CompositeSmsAnalysisResponse],
    status_code=status.HTTP_200_OK,
    summary="AI-Augmented SMS Fraud Analysis",
    description="Detects OTP harvesting, urgency lures, and malicious URLs, enriches with Gemini AI contextual layperson advice.",
)
async def analyze_sms_with_ai(
    request: SmsAnalysisRequest,
    service: AIThreatServiceDep,
) -> StandardResponse[CompositeSmsAnalysisResponse]:
    """Execute AI-augmented SMS threat analysis."""
    result = await service.analyze_sms(request)
    return StandardResponse(success=True, data=result, error=None)


@router.get(
    "/health",
    response_model=StandardResponse[ProviderHealthStatus],
    status_code=status.HTTP_200_OK,
    summary="AI Engine Diagnostic Health Check",
    description="Returns diagnostic reachability and configuration status of the AI provider.",
)
async def get_ai_health(
    service: AIThreatServiceDep,
) -> StandardResponse[ProviderHealthStatus]:
    """Check AI provider diagnostic reachability."""
    health = await service.ai_provider.health_check()
    return StandardResponse(success=True, data=health, error=None)
