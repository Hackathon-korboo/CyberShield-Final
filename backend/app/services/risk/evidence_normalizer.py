"""Evidence Normalizer and Standardization Service for Part 13.

Normalizes empirical observations and heuristic rule triggers from existing URL,
DNS, SSRF, Email, SMS, and AI modules into standardized finding objects.
Handles sensitive data redaction, deduplication, conflict preservation, and check status.
"""

from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional, Tuple, Union
import urllib.parse
import uuid

from backend.app.schemas.analysis import (
    EmailAnalysisResponse,
    HeuristicFindings,
    IndicatorSeverity,
    SecurityIndicator,
    SmsAnalysisResponse,
    UrlAnalysisResponse,
    UrlObservedEvidence,
)
from backend.app.schemas.composite import (
    CompositeEmailAnalysisResponse,
    CompositeSmsAnalysisResponse,
    CompositeUrlAnalysisResponse,
)
from backend.app.schemas.evidence import (
    CheckStatus,
    EvidencePackage,
    FindingSeverity,
    FindingType,
    StandardizedFinding,
)
from backend.app.schemas.unified_report import ThreatIntelligenceSummary

# Sensitive query parameter keys subject to redaction
SENSITIVE_PARAM_NAMES = {
    "token", "password", "pass", "pwd", "secret", "api_key", "apikey",
    "auth", "access_token", "refresh_token", "session", "bearer", "signature",
    "pin", "otp", "code", "credential", "private_key"
}


def redact_sensitive_query_string(url_or_query: str) -> str:
    """Redact sensitive parameter values from a URL or query string."""
    if not url_or_query:
        return url_or_query

    # If it's a full URL, split and parse query
    if "://" in url_or_query or url_or_query.startswith("/"):
        parsed = urllib.parse.urlsplit(url_or_query)
        if not parsed.query:
            return url_or_query

        query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        redacted_params = []
        for k, v in query_params:
            if k.lower() in SENSITIVE_PARAM_NAMES:
                redacted_params.append((k, "[REDACTED]"))
            else:
                redacted_params.append((k, v))

        new_query = urllib.parse.urlencode(redacted_params)
        return urllib.parse.urlunsplit((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            new_query,
            parsed.fragment,
        ))

    # Standalone query string
    query_params = urllib.parse.parse_qsl(url_or_query, keep_blank_values=True)
    if not query_params:
        return url_or_query

    redacted_params = []
    for k, v in query_params:
        if k.lower() in SENSITIVE_PARAM_NAMES:
            redacted_params.append((k, "[REDACTED]"))
        else:
            redacted_params.append((k, v))
    return urllib.parse.urlencode(redacted_params)


def map_legacy_severity(severity: Union[str, IndicatorSeverity]) -> FindingSeverity:
    """Map legacy IndicatorSeverity enum to Standardized FindingSeverity."""
    val = getattr(severity, "value", str(severity)).upper()
    mapping = {
        "CRITICAL": FindingSeverity.CRITICAL,
        "HIGH": FindingSeverity.HIGH,
        "MEDIUM": FindingSeverity.MEDIUM,
        "LOW": FindingSeverity.LOW,
    }
    return mapping.get(val, FindingSeverity.INFORMATIONAL)


class EvidenceNormalizer:
    """Converts multi-source threat investigation data into standardized finding packages."""

    def normalize_url_response(
        self,
        response: Union[UrlAnalysisResponse, CompositeUrlAnalysisResponse],
        threat_intel: Optional[ThreatIntelligenceSummary] = None,
    ) -> EvidencePackage:
        """Normalize URL analysis into an EvidencePackage."""
        observed = response.observed_evidence
        heuristic = response.heuristic_findings
        redacted_target = redact_sensitive_query_string(response.target)
        redacted_norm_url = redact_sensitive_query_string(observed.normalized_url)

        findings: List[StandardizedFinding] = []
        statuses: Dict[str, CheckStatus] = {
            "URL_PATTERN": CheckStatus.COMPLETED,
            "DNS_INVESTIGATION": CheckStatus.COMPLETED if observed.resolved_ips else CheckStatus.PARTIAL,
            "SSRF_GUARD": CheckStatus.COMPLETED,
            "REDIRECT_ANALYSIS": CheckStatus.UNAVAILABLE,
            "TLS_ANALYSIS": CheckStatus.UNAVAILABLE if observed.scheme == "https" else CheckStatus.NOT_APPLICABLE,
            "HTTP_HEADERS": CheckStatus.UNAVAILABLE,
            "THREAT_INTELLIGENCE": threat_intel.status if threat_intel else CheckStatus.UNAVAILABLE,
        }

        # 1. Structural URL findings
        if observed.is_ip_hostname:
            findings.append(StandardizedFinding(
                finding_type=FindingType.URL_PATTERN,
                severity=FindingSeverity.HIGH,
                title="Direct IP Address Hostname",
                description="The target URL uses a raw IP address instead of a registered domain name.",
                observed_evidence={"hostname": observed.hostname, "is_ip_hostname": True},
                source="url_structure_inspector",
                source_status=CheckStatus.COMPLETED,
                related_indicators=["RULE-URL-001"],
            ))

        if observed.has_homoglyphs:
            findings.append(StandardizedFinding(
                finding_type=FindingType.URL_PATTERN,
                severity=FindingSeverity.HIGH,
                title="Punycode / Homoglyph Detected",
                description="The target hostname contains Punycode ('xn--') indicating potential Internationalized Domain Name spoofing.",
                observed_evidence={"hostname": observed.hostname, "has_homoglyphs": True},
                source="url_structure_inspector",
                source_status=CheckStatus.COMPLETED,
                related_indicators=["RULE-URL-002"],
            ))

        # 2. DNS Investigation findings
        if observed.resolved_ips:
            findings.append(StandardizedFinding(
                finding_type=FindingType.DNS_INVESTIGATION,
                severity=FindingSeverity.INFORMATIONAL,
                title="DNS Preflight Resolution",
                description=f"Destination resolved to {len(observed.resolved_ips)} IP address(es).",
                observed_evidence={"resolved_ips": observed.resolved_ips, "hostname": observed.hostname},
                source="dns_resolver",
                source_status=CheckStatus.COMPLETED,
            ))
        else:
            findings.append(StandardizedFinding(
                finding_type=FindingType.DNS_INVESTIGATION,
                severity=FindingSeverity.LOW,
                title="Unresolved Hostname",
                description="The target hostname did not resolve to any public IP addresses during preflight checks.",
                observed_evidence={"hostname": observed.hostname, "resolved_ips": []},
                source="dns_resolver",
                source_status=CheckStatus.PARTIAL,
            ))

        # 3. SSRF Preflight findings
        if not observed.ssrf_safe:
            findings.append(StandardizedFinding(
                finding_type=FindingType.SSRF_GUARD,
                severity=FindingSeverity.CRITICAL,
                title="SSRF Violation: Restricted Destination",
                description="Target destination resolves to loopback, private, link-local, or cloud metadata network prohibited by security policy.",
                observed_evidence={"resolved_ips": observed.resolved_ips, "ssrf_safe": False},
                source="ssrf_guard",
                source_status=CheckStatus.COMPLETED,
                related_indicators=["RULE-SSRF-001"],
            ))

        # 4. Map heuristic indicators
        for ind in heuristic.indicators:
            finding_sev = map_legacy_severity(ind.severity)
            findings.append(StandardizedFinding(
                finding_type=FindingType.URL_PATTERN,
                severity=finding_sev,
                title=f"Rule Match: {ind.rule_id}",
                description=ind.explanation,
                observed_evidence={"evidence_token": ind.evidence, "mitigation": ind.mitigation},
                source="heuristic_rule_engine",
                source_status=CheckStatus.COMPLETED,
                related_indicators=[ind.rule_id],
                metadata={"category": ind.category.value if hasattr(ind.category, "value") else str(ind.category)},
            ))

        # 5. Unavailable check records
        findings.append(StandardizedFinding(
            finding_type=FindingType.REDIRECT_ANALYSIS,
            severity=FindingSeverity.INFORMATIONAL,
            title="Redirect Analysis Unavailable",
            description="HTTP redirect tracing is disabled in zero-egress static analysis mode to prevent outbound connections.",
            observed_evidence={"configured": False, "mode": "zero_egress"},
            source="redirect_tracer",
            source_status=CheckStatus.UNAVAILABLE,
        ))

        if threat_intel and threat_intel.status != CheckStatus.UNAVAILABLE:
            if threat_intel.is_malicious:
                findings.append(StandardizedFinding(
                    finding_type=FindingType.THREAT_INTELLIGENCE,
                    severity=FindingSeverity.CRITICAL,
                    title="Authoritative Threat Intelligence Match",
                    description=f"Destination confirmed malicious on {threat_intel.provider_name}: {', '.join(threat_intel.threat_types)}",
                    observed_evidence={"threat_types": threat_intel.threat_types, "provider": threat_intel.provider_name},
                    source="threat_intel_service",
                    source_status=threat_intel.status,
                    related_indicators=["RULE-INTEL-001"],
                    metadata={"is_malicious": True},
                ))
            else:
                findings.append(StandardizedFinding(
                    finding_type=FindingType.THREAT_INTELLIGENCE,
                    severity=FindingSeverity.INFORMATIONAL,
                    title="Threat Intelligence Check: Clean / No Match",
                    description="No malicious record found on queried threat feeds. Note: absence of record is not proof of safety.",
                    observed_evidence={"status": "NO_MATCH"},
                    source="threat_intel_service",
                    source_status=threat_intel.status,
                    metadata={"is_malicious": False},
                ))
        else:
            findings.append(StandardizedFinding(
                finding_type=FindingType.THREAT_INTELLIGENCE,
                severity=FindingSeverity.INFORMATIONAL,
                title="Threat Intelligence Feed Offline",
                description="External threat intelligence reputation feeds are not configured in local offline mode.",
                observed_evidence={"configured": False, "feed": "none"},
                source="threat_intel_service",
                source_status=CheckStatus.UNAVAILABLE,
            ))

        # 6. Normalize AI inferences if present
        ai_analysis = getattr(response, "ai_analysis", None)
        if ai_analysis:
            statuses["AI_INFERENCE"] = CheckStatus.COMPLETED
            findings.append(StandardizedFinding(
                finding_type=FindingType.AI_INFERENCE,
                severity=FindingSeverity.INFORMATIONAL,
                title="AI Contextual Explanation",
                description=ai_analysis.summary,
                observed_evidence={
                    "explanation": ai_analysis.explanation,
                    "inferences": ai_analysis.ai_inferences,
                    "recommendations": ai_analysis.user_recommendations,
                    "prompt_injection_detected": getattr(ai_analysis, "prompt_injection_detected", False),
                },
                source=f"ai_provider_{ai_analysis.provider}",
                source_status=CheckStatus.COMPLETED,
                metadata={
                    "model": ai_analysis.model,
                    "status": ai_analysis.status,
                    "is_probabilistic": True,
                },
            ))

        # Deduplicate and tag conflicting evidence
        deduped = self.deduplicate_findings(findings)
        tagged_findings = self.identify_conflicting_evidence(deduped)

        return EvidencePackage(
            scan_id=response.analysis_id,
            target=redacted_target,
            target_type="url",
            timestamp=response.timestamp,
            findings=tagged_findings,
            check_statuses=statuses,
        )

    def normalize_email_response(
        self,
        response: Union[EmailAnalysisResponse, CompositeEmailAnalysisResponse],
    ) -> EvidencePackage:
        """Normalize Email analysis into an EvidencePackage."""
        observed = response.observed_evidence
        heuristic = response.heuristic_findings
        findings: List[StandardizedFinding] = []

        statuses: Dict[str, CheckStatus] = {
            "EMAIL_PATTERN": CheckStatus.COMPLETED,
            "URL_PATTERN": CheckStatus.COMPLETED if observed.extracted_urls else CheckStatus.NOT_APPLICABLE,
            "THREAT_INTELLIGENCE": CheckStatus.UNAVAILABLE,
        }

        # Indicators
        for ind in heuristic.indicators:
            finding_sev = map_legacy_severity(ind.severity)
            f_type = FindingType.SSRF_GUARD if "SSRF" in ind.rule_id else FindingType.EMAIL_PATTERN
            findings.append(StandardizedFinding(
                finding_type=f_type,
                severity=finding_sev,
                title=f"Email Security Indicator: {ind.rule_id}",
                description=ind.explanation,
                observed_evidence={"evidence": ind.evidence, "mitigation": ind.mitigation},
                source="email_security_inspector",
                source_status=CheckStatus.COMPLETED,
                related_indicators=[ind.rule_id],
                metadata={"category": ind.category.value if hasattr(ind.category, "value") else str(ind.category)},
            ))

        # AI analysis if present
        ai_analysis = getattr(response, "ai_analysis", None)
        if ai_analysis:
            statuses["AI_INFERENCE"] = CheckStatus.COMPLETED
            findings.append(StandardizedFinding(
                finding_type=FindingType.AI_INFERENCE,
                severity=FindingSeverity.INFORMATIONAL,
                title="AI Threat Explanation",
                description=ai_analysis.summary,
                observed_evidence={
                    "explanation": ai_analysis.explanation,
                    "inferences": ai_analysis.ai_inferences,
                },
                source=f"ai_provider_{ai_analysis.provider}",
                source_status=CheckStatus.COMPLETED,
                metadata={"is_probabilistic": True},
            ))

        deduped = self.deduplicate_findings(findings)
        return EvidencePackage(
            scan_id=response.analysis_id,
            target=response.target,
            target_type="email",
            timestamp=response.timestamp,
            findings=deduped,
            check_statuses=statuses,
        )

    def normalize_sms_response(
        self,
        response: Union[SmsAnalysisResponse, CompositeSmsAnalysisResponse],
    ) -> EvidencePackage:
        """Normalize SMS analysis into an EvidencePackage."""
        observed = response.observed_evidence
        heuristic = response.heuristic_findings
        findings: List[StandardizedFinding] = []

        statuses: Dict[str, CheckStatus] = {
            "SMS_PATTERN": CheckStatus.COMPLETED,
            "URL_PATTERN": CheckStatus.COMPLETED if observed.extracted_urls else CheckStatus.NOT_APPLICABLE,
            "THREAT_INTELLIGENCE": CheckStatus.UNAVAILABLE,
        }

        for ind in heuristic.indicators:
            finding_sev = map_legacy_severity(ind.severity)
            findings.append(StandardizedFinding(
                finding_type=FindingType.SMS_PATTERN,
                severity=finding_sev,
                title=f"SMS Indicator: {ind.rule_id}",
                description=ind.explanation,
                observed_evidence={"evidence": ind.evidence, "mitigation": ind.mitigation},
                source="sms_security_inspector",
                source_status=CheckStatus.COMPLETED,
                related_indicators=[ind.rule_id],
            ))

        ai_analysis = getattr(response, "ai_analysis", None)
        if ai_analysis:
            statuses["AI_INFERENCE"] = CheckStatus.COMPLETED
            findings.append(StandardizedFinding(
                finding_type=FindingType.AI_INFERENCE,
                severity=FindingSeverity.INFORMATIONAL,
                title="AI Scam Analysis",
                description=ai_analysis.summary,
                observed_evidence={
                    "explanation": ai_analysis.explanation,
                    "inferences": ai_analysis.ai_inferences,
                    "prompt_injection_detected": getattr(ai_analysis, "prompt_injection_detected", False),
                },
                source=f"ai_provider_{ai_analysis.provider}",
                source_status=CheckStatus.COMPLETED,
                metadata={"is_probabilistic": True},
            ))

        deduped = self.deduplicate_findings(findings)
        return EvidencePackage(
            scan_id=response.analysis_id,
            target=response.target,
            target_type="sms",
            timestamp=response.timestamp,
            findings=deduped,
            check_statuses=statuses,
        )

    def deduplicate_findings(self, findings: List[StandardizedFinding]) -> List[StandardizedFinding]:
        """Deduplicate findings representing identical observations while merging sources."""
        seen: Dict[str, StandardizedFinding] = {}

        for finding in findings:
            # Generate deduplication key based on type, title, and related indicators
            indicator_key = "-".join(sorted(finding.related_indicators))
            dedup_key = f"{finding.finding_type}:{finding.title}:{indicator_key}"

            if dedup_key in seen:
                existing = seen[dedup_key]
                # Merge sources in metadata
                merged_sources = list(existing.metadata.get("merged_sources", [existing.source]))
                if finding.source not in merged_sources:
                    merged_sources.append(finding.source)
                existing.metadata["merged_sources"] = merged_sources
            else:
                seen[dedup_key] = finding

        return list(seen.values())

    def identify_conflicting_evidence(
        self,
        findings: List[StandardizedFinding],
    ) -> List[StandardizedFinding]:
        """Preserve and tag conflicting observations (e.g. Clean indicators vs High Risk)."""
        has_severe_findings = any(
            f.severity in (FindingSeverity.HIGH, FindingSeverity.CRITICAL)
            for f in findings
        )
        has_informational_or_clean = any(
            f.severity in (FindingSeverity.INFORMATIONAL, FindingSeverity.LOW)
            and f.source_status == CheckStatus.COMPLETED
            for f in findings
        )

        # If findings contain both critical threats and clean observations on the same target, tag them
        if has_severe_findings and has_informational_or_clean:
            for f in findings:
                f.metadata["has_conflicting_evidence"] = True

        return findings
