"""
CyberShield AI 2.0 - File Threat Analysis Service
High-level service interface for safe static file verification, archive inspection,
and optional VirusTotal file hash reputation lookup (zero file upload).
"""

import time
import uuid
from backend.app.schemas.threat_models import FileThreatAnalysisResponse, RiskLevel
from backend.app.file_analysis.safe_analyzer import safe_file_analyzer_instance
from backend.app.threat_intel.virustotal_client import virustotal_client_instance


class FileThreatService:
    """Service coordinator for safe static file analysis and hash intelligence."""

    def inspect_file(self, filename: str, content: bytes) -> FileThreatAnalysisResponse:
        start_time = time.perf_counter()
        analysis = safe_file_analyzer_instance.analyze(filename=filename, content=content)

        # Optional VirusTotal Hash Lookup (zero file upload)
        vt_report = None
        suspicious_indicators = list(analysis["suspicious_indicators"])
        risk_score = analysis["risk_score"]
        risk_level = analysis["risk_level"]
        known_malicious = analysis["known_malicious_hash"]

        if virustotal_client_instance.is_configured and analysis["sha256"]:
            vt_res = virustotal_client_instance.check_file_hash(analysis["sha256"])
            vt_report = vt_res
            if vt_res.get("status") == "MALICIOUS":
                known_malicious = True
                risk_level = RiskLevel.CRITICAL
                risk_score = 100.0
                suspicious_indicators.append(
                    f"VirusTotal Hash Match: {vt_res.get('malicious_count', 0)} security vendors flagged this hash as MALICIOUS."
                )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return FileThreatAnalysisResponse(
            analysis_id=str(uuid.uuid4()),
            filename=analysis["filename"],
            file_size_bytes=analysis["file_size_bytes"],
            sha256=analysis["sha256"],
            md5=analysis["md5"],
            mime_type=analysis["mime_type"],
            detected_file_type=analysis["detected_file_type"],
            magic_bytes_hex=analysis["magic_bytes_hex"],
            is_executable=analysis["is_executable"],
            is_archive=analysis["is_archive"],
            archive_report=analysis.get("archive_report"),
            risk_level=risk_level,
            risk_score=risk_score,
            suspicious_indicators=suspicious_indicators,
            known_malicious_hash=known_malicious,
            virustotal_report=vt_report,
            processing_time_ms=round(elapsed_ms, 2)
        )


file_service_instance = FileThreatService()
