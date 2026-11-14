"""Deterministic Fallback Engine and Circuit Breaker for AI Subsystem.

Provides local, deterministic explanations and advice when the external LLM provider
is unconfigured, disabled, timed out, rate-limited, or offline.
Ensures zero degradation of the core security posture during external AI outages.
"""

import time
from typing import Any, Dict, List, Optional

from backend.app.engines.ai.base import BaseAIProvider
from backend.app.engines.ai.schemas import AiAnalysisResult, ProviderHealthStatus
from backend.app.engines.ai.security import InjectionCheckResult


class CircuitBreaker:
    """Circuit breaker guarding against external provider cascading failures and quota burn."""

    def __init__(self, failure_threshold: int = 3, recovery_time_seconds: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_time_seconds = recovery_time_seconds
        self.failure_count: int = 0
        self.last_failure_time: float = 0.0
        self.state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def record_success(self) -> None:
        """Reset failure counter upon successful response."""
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self) -> None:
        """Increment failure counter and trip breaker if threshold reached."""
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

    def trip_quota_lock(self) -> None:
        """Immediately trip circuit breaker on HTTP 429 quota exhaustion."""
        self.failure_count = self.failure_threshold
        self.last_failure_time = time.monotonic()
        self.state = "OPEN"

    @property
    def is_open(self) -> bool:
        """Return True if the circuit is open and calls should be bypassed."""
        if self.state == "OPEN":
            if (time.monotonic() - self.last_failure_time) > self.recovery_time_seconds:
                self.state = "HALF_OPEN"
                return False
            return True
        return False


class FallbackAIProvider(BaseAIProvider):
    """Local deterministic fallback provider requiring zero external network connectivity."""

    def __init__(self, reason: str = "FALLBACK_HEURISTIC_ONLY"):
        self.reason = reason

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        """Return synthetic fallback summary."""
        return "Deterministic heuristic fallback response."

    async def analyze_threat(
        self,
        target_type: str,
        untrusted_content: str,
        observed_evidence: Dict[str, Any],
        heuristic_findings: Dict[str, Any],
        injection_check: Optional[InjectionCheckResult] = None,
    ) -> AiAnalysisResult:
        """Synthesize structured, deterministic explanations directly from heuristic findings and injection defenses."""
        raw_level = heuristic_findings.get("risk_level", "CLEAN")
        risk_level = getattr(raw_level, "value", str(raw_level)).replace("RiskLevel.", "")
        risk_score = heuristic_findings.get("risk_score", 0)
        indicators = heuristic_findings.get("indicators", [])

        is_injection = bool(injection_check and injection_check.is_suspicious)
        injection_patterns = list(injection_check.detected_patterns) if is_injection else []

        supporting_evidence: List[str] = []
        if is_injection:
            for pat in injection_patterns:
                supporting_evidence.append(f"Prompt injection pattern detected: '{pat}'")

        for ind in indicators:
            rule_id = ind.get("rule_id", "UNKNOWN")
            evidence_str = ind.get("evidence", "")
            explanation_str = ind.get("explanation", "")
            supporting_evidence.append(f"{rule_id}: {evidence_str} ({explanation_str})")

        if not supporting_evidence:
            supporting_evidence.append("No suspicious heuristic indicators detected.")

        if is_injection:
            summary = (
                f"Adversarial prompt injection attempt detected in input text. "
                f"Deterministic scam evaluation: {risk_level} (Score: {risk_score}/100)."
            )
            explanation = (
                f"Static inspection identified adversarial prompt injection signatures attempting to manipulate "
                f"system instructions or security policies ({', '.join(injection_patterns)}). Untrusted user content was "
                f"strictly quarantined within data boundaries. In accordance with CyberShield AI architecture, prompt "
                f"injection detection is tracked independently from user scam risk scoring. "
                f"Evaluated in local deterministic fallback mode ({self.reason})."
            )
            ai_inferences = [
                "Adversarial attempt to hijack LLM system directives or elicit internal instructions.",
                "Untrusted payload quarantined within non-executable data boundaries.",
            ]
            recommendations = [
                "Do not execute, trust, or act on instructions embedded within untrusted content.",
                "Treat communications attempting instruction overrides or prompt extraction with high suspicion.",
            ]
        elif risk_level in ("HIGH_RISK", "SUSPICIOUS", "CONFIRMED_MALICIOUS"):
            rule_ids = [i.get("rule_id", "") for i in indicators if i.get("rule_id")]
            is_ssrf = any("SSRF" in r for r in rule_ids)
            is_ip = any("URL-001" in r for r in rule_ids)
            is_cred = any("EML-004" in r or "SMS-002" in r for r in rule_ids)
            is_urgency = any("EML-001" in r or "SMS-001" in r for r in rule_ids)
            is_homoglyph = any("URL-002" in r or "EML-003" in r for r in rule_ids)
            is_intel = any("INTEL" in r for r in rule_ids)

            ai_inferences: List[str] = []
            recommendations: List[str] = []

            if is_ssrf:
                summary = (
                    f"Deterministic security policy violation detected: target destination violates egress policy "
                    f"(Score: {risk_score}/100, {risk_level})."
                )
                explanation = (
                    f"Destination address resolves to a restricted internal, loopback, private, or metadata range. "
                    f"Deterministic rules triggered: {', '.join(rule_ids)}. "
                    f"In accordance with security policy separation, SSRF policy violations are blocked and classified "
                    f"as HIGH_RISK without independently establishing external target maliciousness. "
                    f"External AI contextual reasoning is currently operating in local fallback mode ({self.reason})."
                )
                ai_inferences.append("Target destination resolves to prohibited private or loopback network; violates network isolation policy.")
                ai_inferences.append("Egress request blocked by security policy; does not indicate external website compromise.")
                recommendations.append("Do not route traffic or forward outbound requests to internal or loopback IP addresses.")
                recommendations.append("Ensure internal administrative and cloud metadata endpoints are shielded from public user inputs.")
            else:
                summary = (
                    f"Deterministic security rules identified {len(indicators)} significant risk indicator(s) "
                    f"classifying this {target_type} as {risk_level} (Score: {risk_score}/100)."
                )
                explanation = (
                    f"Heuristic pattern analysis detected behavioral traits characteristic of cyber threats. "
                    f"Deterministic rules triggered: {', '.join(rule_ids)}. "
                    f"External AI contextual reasoning is currently operating in local fallback mode ({self.reason})."
                )
                if is_intel:
                    ai_inferences.append("Target destination identified on authoritative threat intelligence blocklists.")
                if is_cred:
                    ai_inferences.append("High probability of credential harvesting or sensitive data collection.")
                if is_homoglyph:
                    ai_inferences.append("Deceptive visual spoofing (homoglyph/lookalike domain) detected.")
                if is_urgency:
                    ai_inferences.append("Urgency or fear-inducing psychological framing detected.")
                if is_ip and not is_ssrf:
                    ai_inferences.append("Raw IP address used in place of domain name, circumventing domain reputation controls.")

                if not ai_inferences:
                    ai_inferences.append("Deceptive intent detected by deterministic pattern matching.")
                    ai_inferences.append("Behavioral indicators deviate from standard legitimate traffic.")

                recommendations.append("Do not interact with, click, or authenticate against this target.")
                recommendations.append("Verify sender identity and domain legitimacy via independent, authoritative channels.")
                recommendations.append("Report this communication to your organization's IT or security operations team.")
        else:
            summary = (
                f"Deterministic security inspection identified 0 threat indicators. "
                f"Target {target_type} evaluated as {risk_level} (Score: {risk_score}/100)."
            )
            explanation = (
                f"Static analysis of URL, sender, and payload content verified standard conventions without "
                f"detecting homoglyphs, SSRF destinations, or deceptive urgency lures. "
                f"Evaluated in local deterministic fallback mode ({self.reason})."
            )
            ai_inferences = ["Content exhibits standard operational patterns."]
            recommendations = ["Exercise standard security precautions."]

        uncertainty_statement = (
            "This analysis was generated by CyberShield AI's local deterministic heuristic fallback engine. "
            "All findings are based strictly on static rule evaluation and empirical observations."
        )

        return AiAnalysisResult(
            summary=summary,
            explanation=explanation,
            supporting_evidence=supporting_evidence,
            ai_inferences=ai_inferences,
            uncertainty_statement=uncertainty_statement,
            user_recommendations=recommendations,
            prompt_injection_detected=is_injection,
            prompt_injection_details=injection_patterns,
            provider="cybershield-deterministic-fallback",
            model="local-rule-synthesizer",
            status=self.reason,
        )

    async def health_check(self) -> ProviderHealthStatus:
        """Return local fallback health status."""
        return ProviderHealthStatus(
            provider="cybershield-deterministic-fallback",
            model="local-rule-synthesizer",
            status="healthy",
            configured=True,
            latency_ms=0.1,
            message="Local fallback engine operational.",
        )
