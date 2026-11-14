"""Analysis API routes for URL, Email, and SMS threat detection."""

from fastapi import APIRouter, status

from backend.app.api.dependencies import ThreatServiceDep
from backend.app.schemas.analysis import (
    EmailAnalysisResponse,
    SmsAnalysisResponse,
    UrlAnalysisResponse,
)
from backend.app.schemas.common import StandardResponse
from backend.app.schemas.email import EmailAnalysisRequest
from backend.app.schemas.sms import SmsAnalysisRequest
from backend.app.schemas.url import UrlAnalysisRequest

router = APIRouter(prefix="/analyze", tags=["Threat Analysis"])


@router.post(
    "/url",
    response_model=StandardResponse[UrlAnalysisResponse],
    status_code=status.HTTP_200_OK,
    summary="Analyze URL for Threats and SSRF Risks",
    description="Validates URL syntax, performs preflight SSRF safety verification, and evaluates heuristic threat rules.",
)
async def analyze_url_endpoint(
    request: UrlAnalysisRequest,
    service: ThreatServiceDep,
) -> StandardResponse[UrlAnalysisResponse]:
    """Execute URL threat analysis."""
    result = await service.analyze_url(request)
    return StandardResponse(success=True, data=result, error=None)


@router.post(
    "/email",
    response_model=StandardResponse[EmailAnalysisResponse],
    status_code=status.HTTP_200_OK,
    summary="Analyze Email for Phishing and Social Engineering",
    description="Extracts indicators from email subject, sender, and body, evaluating heuristic phishing and scam rules.",
)
async def analyze_email_endpoint(
    request: EmailAnalysisRequest,
    service: ThreatServiceDep,
) -> StandardResponse[EmailAnalysisResponse]:
    """Execute email threat analysis."""
    result = await service.analyze_email(request)
    return StandardResponse(success=True, data=result, error=None)


@router.post(
    "/sms",
    response_model=StandardResponse[SmsAnalysisResponse],
    status_code=status.HTTP_200_OK,
    summary="Analyze SMS/Chat Message for Fraud",
    description="Detects OTP harvesting, urgency panic lures, and malicious URLs in SMS and chat communications.",
)
async def analyze_sms_endpoint(
    request: SmsAnalysisRequest,
    service: ThreatServiceDep,
) -> StandardResponse[SmsAnalysisResponse]:
    """Execute SMS threat analysis."""
    result = await service.analyze_sms(request)
    return StandardResponse(success=True, data=result, error=None)
