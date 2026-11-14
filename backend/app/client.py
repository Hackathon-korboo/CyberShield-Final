"""
CyberShield AI 2.0 - Member 1 Integration Client (Python SDK)
Provides direct, zero-overhead in-process or HTTP invocation interfaces
for Member 1 to easily integrate Scam Intelligence and File Threat Analysis.
"""

from typing import Optional, Dict, Any
from backend.app.schemas.threat_models import (
    ScamAnalysisRequest,
    ScamAnalysisResponse,
    FileThreatAnalysisResponse,
)
from backend.app.services.threat_service import threat_service_instance
from backend.app.services.file_service import file_service_instance


class CyberShieldMember2Client:
    """
    Direct Python client for Member 1 backend integration.
    Provides in-memory fast execution without requiring a separate network hop.
    """

    def __init__(self, enable_gemini: bool = True, redact_pii: bool = True):
        self.enable_gemini = enable_gemini
        self.redact_pii = redact_pii

    def analyze_message(
        self,
        content: str,
        source_type: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ScamAnalysisResponse:
        """
        Analyze a suspicious message, email, SMS, or job offer.

        Args:
            content: Raw untrusted message text.
            source_type: Optional context (email, sms, chat, job_offer, payment_request).
            metadata: Optional dictionary with caller context (sender, channel, etc.).

        Returns:
            ScamAnalysisResponse: Fully populated Pydantic response model.
        """
        req = ScamAnalysisRequest(
            content=content,
            source_type=source_type,
            metadata=metadata,
            enable_gemini=self.enable_gemini,
            redact_pii=self.redact_pii
        )
        return threat_service_instance.analyze(req)

    # Convenient alias for analyze_message
    analyze_text = analyze_message

    def analyze_file(self, filename: str, content: bytes) -> FileThreatAnalysisResponse:
        """
        Perform safe static threat analysis on raw file bytes.

        Args:
            filename: Name of the uploaded file.
            content: Raw byte contents of the file.

        Returns:
            FileThreatAnalysisResponse: Comprehensive file risk assessment.
        """
        return file_service_instance.inspect_file(filename=filename, content=content)


# Convenient module-level default client instance
member2_client = CyberShieldMember2Client()
