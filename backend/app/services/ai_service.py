"""AI Threat Analysis Orchestration Service.

Integrates the frozen Phase 02 deterministic security pipeline with the Phase 03
AI reasoning engine. Enforces prompt injection defenses, circuit breakers, and
guarantees that deterministic risk scores are immutable.
"""

import logging
from typing import Optional

from backend.app.core.config import get_settings
from backend.app.engines.ai.analyzer import AIThreatAnalyzer
from backend.app.engines.ai.base import BaseAIProvider
from backend.app.engines.ai.client import GeminiProvider
from backend.app.engines.ai.exceptions import (
    AIRateLimitError,
    AITimeoutError,
    AIUnavailableError,
    AIValidationError,
)
from backend.app.engines.ai.fallback import CircuitBreaker, FallbackAIProvider
from backend.app.engines.ai.schemas import AiAnalysisResult
from backend.app.engines.ai.security import inspect_and_sanitize_untrusted_content
from backend.app.schemas.composite import (
    CompositeEmailAnalysisResponse,
    CompositeSmsAnalysisResponse,
    CompositeUrlAnalysisResponse,
)
from backend.app.schemas.email import EmailAnalysisRequest
from backend.app.schemas.sms import SmsAnalysisRequest
from backend.app.schemas.url import UrlAnalysisRequest
from backend.app.services.threat_service import ThreatAnalysisService

logger = logging.getLogger("cybershield.services.ai")


class AIThreatService:
    """Composite orchestration service combining deterministic rules with AI explanations."""

    def __init__(
        self,
        deterministic_service: Optional[ThreatAnalysisService] = None,
        ai_provider: Optional[BaseAIProvider] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ):
        settings = get_settings()
        self.settings = settings
        self.deterministic_service = deterministic_service or ThreatAnalysisService()

        # Initialize AI provider if not injected
        if ai_provider is not None:
            self.ai_provider = ai_provider
        else:
            self.ai_provider = GeminiProvider(
                api_key=settings.gemini_api_key,
                model_name=settings.gemini_model_name,
                timeout=5.0,
            )

        self.analyzer = AIThreatAnalyzer(provider=self.ai_provider)
        self.fallback_provider = FallbackAIProvider()
        self.circuit_breaker = circuit_breaker or CircuitBreaker(failure_threshold=3, recovery_time_seconds=60.0)

    async def analyze_url(self, request: UrlAnalysisRequest) -> CompositeUrlAnalysisResponse:
        """Execute deterministic URL analysis followed by AI contextual enrichment."""
        # Step 1: Execute frozen deterministic analysis (Source of Truth)
        base_result = await self.deterministic_service.analyze_url(request)

        # Step 2: Evaluate AI reasoning
        ai_result = await self._enrich_analysis(
            target_type="url",
            untrusted_content=request.url,
            observed_evidence=base_result.observed_evidence.model_dump(),
            heuristic_findings=base_result.heuristic_findings.model_dump(),
        )

        return CompositeUrlAnalysisResponse(
            target=base_result.target,
            target_type=base_result.target_type,
            analysis_id=base_result.analysis_id,
            timestamp=base_result.timestamp,
            observed_evidence=base_result.observed_evidence,
            heuristic_findings=base_result.heuristic_findings,
            prompt_injection_detected=ai_result.prompt_injection_detected if ai_result else False,
            ai_analysis=ai_result,
            status=base_result.status,
        )

    async def analyze_email(self, request: EmailAnalysisRequest) -> CompositeEmailAnalysisResponse:
        """Execute deterministic Email analysis followed by AI contextual enrichment."""
        base_result = await self.deterministic_service.analyze_email(request)

        ai_result = await self._enrich_analysis(
            target_type="email",
            untrusted_content=request.body,
            observed_evidence=base_result.observed_evidence.model_dump(),
            heuristic_findings=base_result.heuristic_findings.model_dump(),
            sender=request.sender,
            subject=request.subject,
        )

        return CompositeEmailAnalysisResponse(
            target=base_result.target,
            target_type=base_result.target_type,
            analysis_id=base_result.analysis_id,
            timestamp=base_result.timestamp,
            observed_evidence=base_result.observed_evidence,
            heuristic_findings=base_result.heuristic_findings,
            prompt_injection_detected=ai_result.prompt_injection_detected if ai_result else False,
            ai_analysis=ai_result,
            status=base_result.status,
        )

    async def analyze_sms(self, request: SmsAnalysisRequest) -> CompositeSmsAnalysisResponse:
        """Execute deterministic SMS analysis followed by AI contextual enrichment."""
        base_result = await self.deterministic_service.analyze_sms(request)

        ai_result = await self._enrich_analysis(
            target_type="sms",
            untrusted_content=request.message,
            observed_evidence=base_result.observed_evidence.model_dump(),
            heuristic_findings=base_result.heuristic_findings.model_dump(),
            sender=request.sender,
        )

        return CompositeSmsAnalysisResponse(
            target=base_result.target,
            target_type=base_result.target_type,
            analysis_id=base_result.analysis_id,
            timestamp=base_result.timestamp,
            observed_evidence=base_result.observed_evidence,
            heuristic_findings=base_result.heuristic_findings,
            prompt_injection_detected=ai_result.prompt_injection_detected if ai_result else False,
            ai_analysis=ai_result,
            status=base_result.status,
        )

    async def _enrich_analysis(
        self,
        target_type: str,
        untrusted_content: str,
        observed_evidence: dict,
        heuristic_findings: dict,
        sender: Optional[str] = None,
        subject: Optional[str] = None,
    ) -> AiAnalysisResult:
        """Execute safe AI analysis with prompt-injection defense and fallback guards."""
        # Step 1: Deterministically inspect untrusted content for prompt injection
        full_text_to_scan = untrusted_content
        if subject:
            full_text_to_scan = f"{subject}\n{untrusted_content}"
        injection_check = inspect_and_sanitize_untrusted_content(full_text_to_scan)
        sanitized_input = inspect_and_sanitize_untrusted_content(untrusted_content).sanitized_content

        # Check global AI toggle
        if not self.settings.ai_analysis_enabled:
            fallback = FallbackAIProvider(reason="DISABLED")
            return await fallback.analyze_threat(
                target_type, untrusted_content, observed_evidence, heuristic_findings, injection_check=injection_check
            )

        # Check circuit breaker
        if self.circuit_breaker.is_open:
            logger.warning("Circuit breaker OPEN. Bypassing external AI provider.")
            fallback = FallbackAIProvider(reason="RATE_LIMITED")
            return await fallback.analyze_threat(
                target_type, untrusted_content, observed_evidence, heuristic_findings, injection_check=injection_check
            )

        try:
            ai_result = await self.analyzer.analyze(
                target_type=target_type,
                untrusted_content=sanitized_input,
                observed_evidence=observed_evidence,
                heuristic_findings=heuristic_findings,
                sender=sender,
                subject=subject,
            )

            # Deterministically enforce prompt injection detection flags and citations
            ai_result.prompt_injection_detected = injection_check.is_suspicious
            ai_result.prompt_injection_details = list(injection_check.detected_patterns)

            if injection_check.is_suspicious:
                if not any("prompt injection" in inf.lower() for inf in ai_result.ai_inferences):
                    ai_result.ai_inferences.append(
                        "Adversarial prompt injection pattern detected in input text; evaluated safely as untrusted data."
                    )
                for pat in injection_check.detected_patterns:
                    citation = f"Prompt injection signature detected: '{pat}'"
                    if citation not in ai_result.supporting_evidence:
                        ai_result.supporting_evidence.append(citation)

            self.circuit_breaker.record_success()
            return ai_result

        except AIRateLimitError as exc:
            logger.warning("AI provider rate limited: %s. Tripping circuit breaker.", exc)
            self.circuit_breaker.trip_quota_lock()
            fallback = FallbackAIProvider(reason="RATE_LIMITED")
            return await fallback.analyze_threat(
                target_type, untrusted_content, observed_evidence, heuristic_findings, injection_check=injection_check
            )

        except AITimeoutError as exc:
            logger.warning("AI provider timed out: %s. Serving deterministic fallback.", exc)
            self.circuit_breaker.record_failure()
            fallback = FallbackAIProvider(reason="TIMEOUT_FALLBACK")
            return await fallback.analyze_threat(
                target_type, untrusted_content, observed_evidence, heuristic_findings, injection_check=injection_check
            )

        except (AIUnavailableError, AIValidationError) as exc:
            logger.info("AI provider unavailable or returned invalid schema (%s). Serving fallback.", exc)
            fallback = FallbackAIProvider(reason="FALLBACK_HEURISTIC_ONLY")
            return await fallback.analyze_threat(
                target_type, untrusted_content, observed_evidence, heuristic_findings, injection_check=injection_check
            )

        except Exception as exc:
            logger.error("Unexpected error in AI enrichment: %s. Serving fallback.", exc)
            self.circuit_breaker.record_failure()
            fallback = FallbackAIProvider(reason="FALLBACK_HEURISTIC_ONLY")
            return await fallback.analyze_threat(
                target_type, untrusted_content, observed_evidence, heuristic_findings, injection_check=injection_check
            )
