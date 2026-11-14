"""CyberShield AI 2.0 Schemas Package.

Exports common response wrappers, health models, threat analysis requests,
and deterministic indicator models.
"""

from backend.app.schemas.common import ErrorDetail, ErrorEnvelope, StandardResponse
from backend.app.schemas.health import HealthCheckResponse, SubsystemHealth
from backend.app.schemas.url import UrlAnalysisRequest
from backend.app.schemas.email import EmailAnalysisRequest
from backend.app.schemas.sms import SmsAnalysisRequest
from backend.app.schemas.analysis import (
    RiskLevel,
    IndicatorCategory,
    IndicatorSeverity,
    SecurityIndicator,
    HeuristicFindings,
    UrlObservedEvidence,
    EmailObservedEvidence,
    SmsObservedEvidence,
    UrlAnalysisResponse,
    EmailAnalysisResponse,
    SmsAnalysisResponse,
)

__all__ = [
    # Phase 01 Base & Health
    "ErrorDetail",
    "ErrorEnvelope",
    "StandardResponse",
    "HealthCheckResponse",
    "SubsystemHealth",
    # Phase 02 Requests
    "UrlAnalysisRequest",
    "EmailAnalysisRequest",
    "SmsAnalysisRequest",
    # Phase 02 Response Enums & Models
    "RiskLevel",
    "IndicatorCategory",
    "IndicatorSeverity",
    "SecurityIndicator",
    "HeuristicFindings",
    "UrlObservedEvidence",
    "EmailObservedEvidence",
    "SmsObservedEvidence",
    "UrlAnalysisResponse",
    "EmailAnalysisResponse",
    "SmsAnalysisResponse",
]
