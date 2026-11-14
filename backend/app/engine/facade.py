"""CyberShield AI 2.0 — Scam & File Analysis Facade.

Provides a unified programmatic facade for Member 2 analysis capabilities,
bridging incoming adapter and gateway requests to the underlying threat services.
"""

from typing import Dict, Any, Optional
from backend.app.schemas.threat_models import ScamAnalysisRequest
from backend.app.services.scam_threat_service import threat_service_instance
from backend.app.services.file_service import file_service_instance


class ScamAnalysisFacade:
    """Unified facade for scam intelligence and file threat inspection."""

    def __init__(self):
        self.threat_service = threat_service_instance
        self.file_service = file_service_instance

    def analyze_message(
        self,
        content: str,
        source_type: str = "unknown",
        enable_gemini: bool = True,
        enable_virustotal: bool = True,
        redact_pii: bool = True,
    ) -> Dict[str, Any]:
        """Analyze message payload with full zero-trust, PII, and heuristic/Gemini pipeline."""
        req = ScamAnalysisRequest(
            content=content,
            source_type=source_type,
            enable_gemini=enable_gemini,
            enable_virustotal=enable_virustotal,
            redact_pii=redact_pii,
        )
        res = self.threat_service.analyze(req)
        return res.model_dump()

    def analyze_file(self, filename: str, content_bytes: bytes) -> Dict[str, Any]:
        """Inspect file content safely without disk execution."""
        res = self.file_service.inspect_file(filename=filename, content=content_bytes)
        return res.model_dump()
