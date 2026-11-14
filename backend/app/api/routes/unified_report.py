"""Unified Threat Report API Endpoints for Stage 4 (Part 16).

Exposes endpoints for generating unified, schema-validated threat reports
integrating evidence normalization, classification, deterministic risk assessment, and report formatting.
"""

from fastapi import APIRouter, Depends, status

from backend.app.api.ai_dependencies import get_ai_threat_service
from backend.app.db.repository import ReportRepository
from backend.app.schemas.common import StandardResponse
from backend.app.schemas.email import EmailAnalysisRequest
from backend.app.schemas.sms import SmsAnalysisRequest
from backend.app.schemas.unified_report import UnifiedThreatReport
from backend.app.schemas.url import UrlAnalysisRequest
from backend.app.services.ai_service import AIThreatService
from backend.app.services.risk.pipeline import UnifiedRiskPipeline
from backend.app.services.threat_intel.adapter import ThreatIntelligenceAdapter

router = APIRouter(prefix="/analyze/report", tags=["Unified Threat Reports"])

_pipeline = UnifiedRiskPipeline()
_repository = ReportRepository()
_threat_intel = ThreatIntelligenceAdapter()


@router.post(
    "/url",
    response_model=StandardResponse[UnifiedThreatReport],
    status_code=status.HTTP_200_OK,
    summary="Generate Unified Threat Report for URL",
)
async def generate_url_threat_report(
    request: UrlAnalysisRequest,
    ai_service: AIThreatService = Depends(get_ai_threat_service),
) -> StandardResponse[UnifiedThreatReport]:
    """Execute end-to-end URL threat analysis and generate unified report."""
    intel_summary = await _threat_intel.query_all(target=request.url, target_type="url")
    comp_resp = await ai_service.analyze_url(request)
    report = _pipeline.process_url_response(comp_resp, threat_intel=intel_summary)
    _repository.save_report(report)
    return StandardResponse(success=True, data=report)


@router.post(
    "/email",
    response_model=StandardResponse[UnifiedThreatReport],
    status_code=status.HTTP_200_OK,
    summary="Generate Unified Threat Report for Email",
)
async def generate_email_threat_report(
    request: EmailAnalysisRequest,
    ai_service: AIThreatService = Depends(get_ai_threat_service),
) -> StandardResponse[UnifiedThreatReport]:
    """Execute end-to-end Email threat analysis and generate unified report."""
    comp_resp = await ai_service.analyze_email(request)
    report = _pipeline.process_email_response(comp_resp)
    _repository.save_report(report)
    return StandardResponse(success=True, data=report)


@router.post(
    "/sms",
    response_model=StandardResponse[UnifiedThreatReport],
    status_code=status.HTTP_200_OK,
    summary="Generate Unified Threat Report for SMS",
)
async def generate_sms_threat_report(
    request: SmsAnalysisRequest,
    ai_service: AIThreatService = Depends(get_ai_threat_service),
) -> StandardResponse[UnifiedThreatReport]:
    """Execute end-to-end SMS threat analysis and generate unified report."""
    comp_resp = await ai_service.analyze_sms(request)
    report = _pipeline.process_sms_response(comp_resp)
    _repository.save_report(report)
    return StandardResponse(success=True, data=report)
