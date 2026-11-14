"""Threat Analysis Orchestration Service.

Integrates input sanitization, SSRF preflight protection, and deterministic
security indicator rules across URL, Email, and SMS endpoints.
"""

from datetime import datetime, timezone
import ipaddress
import urllib.parse
import uuid
from typing import List, Optional

from backend.app.engines.rules.engine import SecurityRuleEngine, calculate_risk_level
from backend.app.engines.ssrf_guard import SSRFGuard
from backend.app.schemas.analysis import (
    EmailAnalysisResponse,
    EmailObservedEvidence,
    HeuristicFindings,
    IndicatorCategory,
    IndicatorSeverity,
    RiskLevel,
    SecurityIndicator,
    SmsAnalysisResponse,
    SmsObservedEvidence,
    UrlAnalysisResponse,
    UrlObservedEvidence,
)
from backend.app.schemas.email import EmailAnalysisRequest
from backend.app.schemas.sms import SmsAnalysisRequest
from backend.app.schemas.url import UrlAnalysisRequest
from backend.app.utils.sanitizer import (
    extract_phone_numbers,
    extract_urls_from_text,
    normalize_target_url,
    parse_email_sender,
    sanitize_input_text,
)

# Severity weights matching rule engine
SEVERITY_WEIGHTS = {
    IndicatorSeverity.CRITICAL: 40,
    IndicatorSeverity.HIGH: 25,
    IndicatorSeverity.MEDIUM: 15,
    IndicatorSeverity.LOW: 5,
}


class ThreatAnalysisService:
    """Core orchestration service integrating detection engines with business flows."""

    def __init__(self):
        self.ssrf_guard = SSRFGuard()
        self.rule_engine = SecurityRuleEngine()

    async def analyze_url(self, request: UrlAnalysisRequest) -> UrlAnalysisResponse:
        """Process URL submission through normalization, SSRF preflight, and heuristics."""
        normalized = normalize_target_url(request.url)
        parsed = urllib.parse.urlsplit(normalized)
        scheme = parsed.scheme.lower()
        hostname = parsed.hostname or ""
        port = parsed.port or (443 if scheme == "https" else 80)
        path = parsed.path or "/"

        # Check if hostname is direct IP literal
        is_ip = False
        try:
            ipaddress.ip_address(hostname)
            is_ip = True
        except ValueError:
            is_ip = False

        # Run SSRF Preflight Verification
        ssrf_result = self.ssrf_guard.validate_url(normalized, raise_exception=False)
        has_homoglyphs = "xn--" in hostname.lower()

        evidence = UrlObservedEvidence(
            normalized_url=normalized,
            scheme=scheme,
            hostname=hostname,
            port=port,
            path=path,
            query=parsed.query or None,
            resolved_ips=ssrf_result.resolved_ips,
            is_ip_hostname=is_ip,
            ssrf_safe=ssrf_result.is_safe,
            has_homoglyphs=has_homoglyphs,
        )

        # Run deterministic URL security rules
        findings = self.rule_engine.evaluate_url(evidence)
        indicators: List[SecurityIndicator] = list(findings.indicators)

        # If SSRF preflight failed, attach SSRF finding with CRITICAL severity
        if not ssrf_result.is_safe:
            indicators.append(
                SecurityIndicator(
                    rule_id="RULE-SSRF-001",
                    category=IndicatorCategory.SSRF_ATTEMPT,
                    severity=IndicatorSeverity.CRITICAL,
                    evidence=f"Blocked destination: {ssrf_result.blocked_reason}",
                    explanation="Destination resolves to private, loopback, link-local, or cloud metadata network prohibited by security policy.",
                    mitigation="Target points to internal or restricted network infrastructure and cannot be accessed.",
                )
            )

        # Re-aggregate score using Severity Floor Model
        composite_findings = self.rule_engine.aggregate_indicators(indicators)

        return UrlAnalysisResponse(
            target=request.url,
            target_type="url",
            analysis_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            observed_evidence=evidence,
            heuristic_findings=composite_findings,
            status="COMPLETED",
        )

    async def analyze_email(self, request: EmailAnalysisRequest) -> EmailAnalysisResponse:
        """Process email submission through normalization, indicator extraction, and heuristics."""
        clean_body = sanitize_input_text(request.body)
        target_name = request.subject or request.sender or "Email Message"

        # Sender parsing
        sender_info = parse_email_sender(request.sender)
        sender_domain = sender_info.get("domain")

        # Extract embedded URLs and phone numbers
        extracted_urls = extract_urls_from_text(f"{request.subject or ''} {clean_body}")
        extracted_phones = extract_phone_numbers(clean_body)

        evidence = EmailObservedEvidence(
            sender_domain=sender_domain,
            extracted_urls=extracted_urls,
            extracted_phones=extracted_phones,
            body_length=len(clean_body),
        )

        # Run email detection rules
        email_findings = self.rule_engine.evaluate_email(request)
        indicators: List[SecurityIndicator] = list(email_findings.indicators)

        # Preflight and analyze all extracted URLs
        for url in extracted_urls:
            ssrf_res = self.ssrf_guard.validate_url(url, raise_exception=False)
            if not ssrf_res.is_safe:
                indicators.append(
                    SecurityIndicator(
                        rule_id="RULE-SSRF-002",
                        category=IndicatorCategory.SSRF_ATTEMPT,
                        severity=IndicatorSeverity.HIGH,
                        evidence=f"Embedded URL '{url}' points to restricted target: {ssrf_res.blocked_reason}",
                        explanation="Embedded link in email references a private network or loopback address.",
                        mitigation="Do not click links pointing to internal or loopback IP addresses.",
                    )
                )
            else:
                # Also evaluate URL rules on embedded URLs
                parsed_u = urllib.parse.urlsplit(url)
                u_evidence = UrlObservedEvidence(
                    normalized_url=url,
                    scheme=parsed_u.scheme,
                    hostname=parsed_u.hostname or "",
                    port=parsed_u.port or 443,
                    path=parsed_u.path or "/",
                    resolved_ips=ssrf_res.resolved_ips,
                    has_homoglyphs="xn--" in (parsed_u.hostname or ""),
                )
                u_findings = self.rule_engine.evaluate_url(u_evidence)
                for u_ind in u_findings.indicators:
                    # Avoid duplicate rule matches
                    if u_ind.rule_id not in [i.rule_id for i in indicators]:
                        indicators.append(u_ind)

        # Calculate composite score using Severity Floor Model
        composite_findings = self.rule_engine.aggregate_indicators(indicators)

        return EmailAnalysisResponse(
            target=target_name,
            target_type="email",
            analysis_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            observed_evidence=evidence,
            heuristic_findings=composite_findings,
            status="COMPLETED",
        )

    async def analyze_sms(self, request: SmsAnalysisRequest) -> SmsAnalysisResponse:
        """Process SMS submission through normalization, indicator extraction, and heuristics."""
        clean_message = sanitize_input_text(request.message)
        target_name = request.sender or "SMS Message"

        # Extract embedded URLs and phone numbers
        extracted_urls = extract_urls_from_text(clean_message)
        extracted_phones = extract_phone_numbers(clean_message)

        evidence = SmsObservedEvidence(
            extracted_urls=extracted_urls,
            extracted_phones=extracted_phones,
            message_length=len(clean_message),
        )

        # Run SMS detection rules
        sms_findings = self.rule_engine.evaluate_sms(request)
        indicators: List[SecurityIndicator] = list(sms_findings.indicators)

        # Preflight and analyze all extracted URLs
        for url in extracted_urls:
            ssrf_res = self.ssrf_guard.validate_url(url, raise_exception=False)
            if not ssrf_res.is_safe:
                indicators.append(
                    SecurityIndicator(
                        rule_id="RULE-SSRF-003",
                        category=IndicatorCategory.SSRF_ATTEMPT,
                        severity=IndicatorSeverity.HIGH,
                        evidence=f"Embedded SMS link '{url}' points to restricted destination: {ssrf_res.blocked_reason}",
                        explanation="Embedded link in text message targets private or loopback resources.",
                        mitigation="Do not click links referencing loopback or intranet IPs.",
                    )
                )
            else:
                parsed_u = urllib.parse.urlsplit(url)
                u_evidence = UrlObservedEvidence(
                    normalized_url=url,
                    scheme=parsed_u.scheme,
                    hostname=parsed_u.hostname or "",
                    port=parsed_u.port or 443,
                    path=parsed_u.path or "/",
                    resolved_ips=ssrf_res.resolved_ips,
                    has_homoglyphs="xn--" in (parsed_u.hostname or ""),
                )
                u_findings = self.rule_engine.evaluate_url(u_evidence)
                for u_ind in u_findings.indicators:
                    if u_ind.rule_id not in [i.rule_id for i in indicators]:
                        indicators.append(u_ind)

        # Calculate composite score using Severity Floor Model
        composite_findings = self.rule_engine.aggregate_indicators(indicators)

        return SmsAnalysisResponse(
            target=target_name,
            target_type="sms",
            analysis_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            observed_evidence=evidence,
            heuristic_findings=composite_findings,
            status="COMPLETED",
        )


# Member 2 Scam Intelligence Re-exports for unified architecture compatibility
try:
    from backend.app.services.scam_threat_service import (
        ThreatIntelligenceService,
        threat_service_instance,
    )
except ImportError:
    pass

