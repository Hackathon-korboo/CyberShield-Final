"""Core Scans & Report Management API Router for Part 17.

Exposes endpoints for submitting URLs for investigation, retrieving persisted scan reports,
listing scan history with pagination, and verifying report cryptographic integrity.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse

from backend.app.api.ai_dependencies import get_ai_threat_service
from backend.app.db.repository import ReportRepository
from backend.app.schemas.common import ErrorEnvelope, StandardResponse
from backend.app.schemas.scans import (
    ScanHistoryResponse,
    ScanUrlRequest,
    VerifyReportRequest,
)
from backend.app.schemas.unified_report import UnifiedThreatReport
from backend.app.schemas.url import UrlAnalysisRequest
from backend.app.services.ai_service import AIThreatService
from backend.app.services.blockchain.adapter import (
    BlockchainAdapter,
    ReportVerificationResult,
)
from backend.app.services.risk.pipeline import UnifiedRiskPipeline
from backend.app.services.threat_intel.adapter import ThreatIntelligenceAdapter

logger = logging.getLogger("cybershield.api.scans")

router = APIRouter(tags=["Scan & Verification Operations"])

_pipeline = UnifiedRiskPipeline()
_threat_intel = ThreatIntelligenceAdapter()
_repository = ReportRepository()
_blockchain = BlockchainAdapter()


@router.post(
    "/scan-url",
    response_model=StandardResponse[UnifiedThreatReport],
    status_code=status.HTTP_200_OK,
    summary="Submit URL for Comprehensive Threat Investigation",
    description=(
        "Submits a target web URL through zero-egress SSRF validation, structural pattern analysis, "
        "AI contextual intent analysis, and multi-source threat intelligence aggregation. "
        "Persists the resulting report and generates an RFC 8785 canonical integrity fingerprint."
    ),
)
async def scan_url_endpoint(
    request: ScanUrlRequest,
    ai_service: AIThreatService = Depends(get_ai_threat_service),
) -> StandardResponse[UnifiedThreatReport]:
    """Execute end-to-end URL threat scan, normalize findings, and persist report."""
    logger.info("Initiating URL scan for target: %s", request.url)

    # 1. Query Threat Intelligence (partial failure tolerant)
    intel_summary = await _threat_intel.query_all(target=request.url, target_type="url")

    # 2. Execute URL Analysis (SSRF validation + Rules + AI Reasoning)
    url_req = UrlAnalysisRequest(url=request.url)
    composite_resp = await ai_service.analyze_url(url_req)

    # 3. Process through Unified Risk Assessment Pipeline (Parts 13–16)
    report = _pipeline.process_url_response(composite_resp, threat_intel=intel_summary)

    # 4. Persist Report to SQLite Database (Part 19)
    save_ok = _repository.save_report(report)
    if not save_ok:
        logger.warning("Database persistence failed for scan %s; returning in-memory report", report.scan_id)

    return StandardResponse(success=True, data=report, error=None)


@router.get(
    "/scans/{scan_id}",
    response_model=StandardResponse[UnifiedThreatReport],
    status_code=status.HTTP_200_OK,
    summary="Retrieve Persisted Scan Report by Scan ID",
    description="Retrieves a previously generated Unified Threat Report by its unique scan identifier.",
)
async def get_scan_by_id(scan_id: str) -> StandardResponse[UnifiedThreatReport]:
    """Retrieve a stored threat report by scan_id."""
    clean_id = scan_id.strip()
    report = _repository.get_report(clean_id)
    if not report:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=StandardResponse(
                success=False,
                data=None,
                error=ErrorEnvelope(
                    code="SCAN_NOT_FOUND",
                    message=f"Threat scan report with ID '{clean_id}' was not found.",
                ),
            ).model_dump(mode="json"),
        )
    return StandardResponse(success=True, data=report, error=None)


@router.get(
    "/scans",
    response_model=StandardResponse[ScanHistoryResponse],
    status_code=status.HTTP_200_OK,
    summary="List Scan Report History",
    description="Retrieves a paginated list of previously generated threat reports ordered by creation time descending.",
)
async def list_scans_endpoint(
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of reports to return"),
    offset: int = Query(default=0, ge=0, description="Offset index for pagination"),
) -> StandardResponse[ScanHistoryResponse]:
    """List stored threat reports with pagination."""
    reports, total = _repository.list_reports(limit=limit, offset=offset)
    return StandardResponse(
        success=True,
        data=ScanHistoryResponse(reports=reports, total=total, limit=limit, offset=offset),
        error=None,
    )


@router.post(
    "/reports/verify",
    response_model=StandardResponse[ReportVerificationResult],
    status_code=status.HTTP_200_OK,
    summary="Cryptographically Verify Report Integrity",
    description=(
        "Recomputes the RFC 8785 canonical SHA-256 fingerprint from report contents and compares it "
        "against the stored hash to detect unauthorized data modification or report tampering."
    ),
)
async def verify_report_endpoint(
    request: VerifyReportRequest,
) -> StandardResponse[ReportVerificationResult]:
    """Verify cryptographic integrity of a scan report."""
    target_report: Optional[UnifiedThreatReport] = None

    if request.scan_id:
        target_report = _repository.get_report(request.scan_id.strip())
        if not target_report:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=StandardResponse(
                    success=False,
                    data=None,
                    error=ErrorEnvelope(
                        code="SCAN_NOT_FOUND",
                        message=f"Scan report with ID '{request.scan_id}' was not found for verification.",
                    ),
                ).model_dump(mode="json"),
            )
    elif request.report:
        target_report = request.report
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=StandardResponse(
                success=False,
                data=None,
                error=ErrorEnvelope(
                    code="INVALID_VERIFICATION_REQUEST",
                    message="Either 'scan_id' or a full 'report' payload must be provided for verification.",
                ),
            ).model_dump(mode="json"),
        )

    verification_result = _blockchain.verify_report(target_report)
    return StandardResponse(success=True, data=verification_result, error=None)
