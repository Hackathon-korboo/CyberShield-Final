"""Unified Risk Pipeline Orchestrator connecting Parts 13, 14, 15, and 16.

Standardized Evidence (Part 13)
       ↓
Severity & Indicator Classification (Part 14)
       ↓
Deterministic Risk Assessment (Part 15)
       ↓
Unified Threat Report (Part 16)
"""

from typing import Optional, Union

from backend.app.engines.ai.schemas import AiAnalysisResult
from backend.app.schemas.analysis import (
    EmailAnalysisResponse,
    SmsAnalysisResponse,
    UrlAnalysisResponse,
)
from backend.app.schemas.composite import (
    CompositeEmailAnalysisResponse,
    CompositeSmsAnalysisResponse,
    CompositeUrlAnalysisResponse,
)
from backend.app.schemas.unified_report import ThreatIntelligenceSummary, UnifiedThreatReport
from backend.app.services.risk.deterministic_engine import DeterministicRiskEngine
from backend.app.services.risk.evidence_normalizer import EvidenceNormalizer
from backend.app.services.risk.report_generator import UnifiedReportGenerator
from backend.app.services.risk.severity_classifier import SeverityClassifier


class UnifiedRiskPipeline:
    """End-to-End risk pipeline coordinating normalization, classification, assessment, and reporting."""

    def __init__(
        self,
        normalizer: Optional[EvidenceNormalizer] = None,
        classifier: Optional[SeverityClassifier] = None,
        risk_engine: Optional[DeterministicRiskEngine] = None,
        report_generator: Optional[UnifiedReportGenerator] = None,
    ):
        self.normalizer = normalizer or EvidenceNormalizer()
        self.classifier = classifier or SeverityClassifier()
        self.risk_engine = risk_engine or DeterministicRiskEngine()
        self.report_generator = report_generator or UnifiedReportGenerator()

    def process_url_response(
        self,
        response: Union[UrlAnalysisResponse, CompositeUrlAnalysisResponse],
        threat_intel: Optional[ThreatIntelligenceSummary] = None,
    ) -> UnifiedThreatReport:
        """Process URL response through the four-part risk pipeline."""
        # Part 13: Normalize evidence
        evidence_pkg = self.normalizer.normalize_url_response(response, threat_intel=threat_intel)

        # Part 14: Classify severity, authority, and correlations
        class_pkg = self.classifier.classify_evidence_package(evidence_pkg)

        # Part 15: Deterministic risk assessment
        risk_assessment = self.risk_engine.evaluate(evidence_pkg, class_pkg)

        # Part 16: Assemble unified threat report
        ai_analysis = getattr(response, "ai_analysis", None)
        return self.report_generator.build_report(
            evidence_pkg=evidence_pkg,
            risk_assessment=risk_assessment,
            ai_analysis=ai_analysis,
            threat_intel=threat_intel,
        )

    def process_email_response(
        self,
        response: Union[EmailAnalysisResponse, CompositeEmailAnalysisResponse],
    ) -> UnifiedThreatReport:
        """Process Email response through the four-part risk pipeline."""
        evidence_pkg = self.normalizer.normalize_email_response(response)
        class_pkg = self.classifier.classify_evidence_package(evidence_pkg)
        risk_assessment = self.risk_engine.evaluate(evidence_pkg, class_pkg)
        ai_analysis = getattr(response, "ai_analysis", None)
        return self.report_generator.build_report(
            evidence_pkg=evidence_pkg,
            risk_assessment=risk_assessment,
            ai_analysis=ai_analysis,
        )

    def process_sms_response(
        self,
        response: Union[SmsAnalysisResponse, CompositeSmsAnalysisResponse],
    ) -> UnifiedThreatReport:
        """Process SMS response through the four-part risk pipeline."""
        evidence_pkg = self.normalizer.normalize_sms_response(response)
        class_pkg = self.classifier.classify_evidence_package(evidence_pkg)
        risk_assessment = self.risk_engine.evaluate(evidence_pkg, class_pkg)
        ai_analysis = getattr(response, "ai_analysis", None)
        return self.report_generator.build_report(
            evidence_pkg=evidence_pkg,
            risk_assessment=risk_assessment,
            ai_analysis=ai_analysis,
        )
