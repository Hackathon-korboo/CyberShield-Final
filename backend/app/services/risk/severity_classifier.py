"""Severity and Indicator Classifier for Part 14.

Assigns consistent severity levels, evidence authority metadata, and correlation groups
to standardized findings. Computes check coverage and calibrated confidence metrics.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

from backend.app.schemas.evidence import (
    CheckStatus,
    EvidencePackage,
    FindingSeverity,
    FindingType,
    StandardizedFinding,
)
from backend.app.schemas.risk import (
    AuthorityCategory,
    ClassificationPackage,
    ClassifiedIndicator,
)

# Documented rationale basis per rule/finding category
SEVERITY_BASIS_REGISTRY = {
    "RULE-SSRF-001": (
        AuthorityCategory.POLICY_VIOLATION,
        FindingSeverity.CRITICAL,
        "Security policy violation: destination resolves to a prohibited loopback, private, link-local, or cloud metadata network.",
    ),
    "RULE-SSRF-002": (
        AuthorityCategory.POLICY_VIOLATION,
        FindingSeverity.HIGH,
        "Security policy violation: embedded email link references a prohibited private or loopback network.",
    ),
    "RULE-SSRF-003": (
        AuthorityCategory.POLICY_VIOLATION,
        FindingSeverity.HIGH,
        "Security policy violation: embedded SMS link references a prohibited private or loopback network.",
    ),
    "RULE-INTEL-001": (
        AuthorityCategory.AUTHORITATIVE,
        FindingSeverity.CRITICAL,
        "Authoritative threat intelligence match: destination confirmed malicious on verified threat intelligence blocklist.",
    ),
    "RULE-URL-001": (
        AuthorityCategory.HEURISTIC,
        FindingSeverity.HIGH,
        "Heuristic detection: direct IP literal host is commonly abused to evade domain reputation filters.",
    ),
    "RULE-URL-002": (
        AuthorityCategory.HEURISTIC,
        FindingSeverity.HIGH,
        "Heuristic detection: Punycode ('xn--') homoglyph structure indicates visual brand spoofing.",
    ),
    "RULE-URL-003": (
        AuthorityCategory.HEURISTIC,
        FindingSeverity.MEDIUM,
        "Heuristic detection: suspicious authentication keywords found in unauthenticated URL path/query.",
    ),
    "RULE-URL-004": (
        AuthorityCategory.HEURISTIC,
        FindingSeverity.MEDIUM,
        "Heuristic detection: excessive subdomain depth indicates domain shadowing or evasion.",
    ),
    "RULE-URL-005": (
        AuthorityCategory.HEURISTIC,
        FindingSeverity.LOW,
        "Heuristic detection: target uses a high-abuse top-level domain.",
    ),
    "RULE-EML-001": (
        AuthorityCategory.HEURISTIC,
        FindingSeverity.HIGH,
        "Heuristic pattern matching detected artificial urgency designed to bypass critical thinking.",
    ),
    "RULE-EML-002": (
        AuthorityCategory.HEURISTIC,
        FindingSeverity.HIGH,
        "Heuristic pattern matching detected unauthorized payment or wire transfer lure.",
    ),
    "RULE-EML-003": (
        AuthorityCategory.HEURISTIC,
        FindingSeverity.MEDIUM,
        "Heuristic pattern matching detected fraudulent employment lure.",
    ),
    "RULE-EML-004": (
        AuthorityCategory.HEURISTIC,
        FindingSeverity.HIGH,
        "Heuristic pattern matching detected explicit credential harvesting form or lure.",
    ),
    "RULE-SMS-001": (
        AuthorityCategory.HEURISTIC,
        FindingSeverity.CRITICAL,
        "Heuristic pattern matching detected OTP or 2FA verification code extraction attempt.",
    ),
    "RULE-SMS-002": (
        AuthorityCategory.HEURISTIC,
        FindingSeverity.HIGH,
        "Heuristic pattern matching detected deceptive banking card blockage notification.",
    ),
    "RULE-SMS-003": (
        AuthorityCategory.HEURISTIC,
        FindingSeverity.MEDIUM,
        "Heuristic pattern matching detected fake lottery or reward scam lure.",
    ),
    "RULE-SMS-004": (
        AuthorityCategory.HEURISTIC,
        FindingSeverity.HIGH,
        "Heuristic pattern matching detected artificial urgency in SMS message.",
    ),
}

# Correlation group mapping to prevent double-counting across overlapping indicators
CORRELATION_MAP = {
    "RULE-URL-001": "CORR-IP-DESTINATION",
    "RULE-SSRF-001": "CORR-IP-DESTINATION",
    "RULE-URL-004": "CORR-SUBDOMAIN-DEPTH",
    "RULE-EML-001": "CORR-URGENCY",
    "RULE-SMS-004": "CORR-URGENCY",
    "RULE-SMS-001": "CORR-OTP-HARVEST",
    "RULE-EML-004": "CORR-CREDENTIAL-HARVEST",
    "RULE-EML-002": "CORR-PAYMENT-FRAUD",
}


class SeverityClassifier:
    """Classifies standardized findings with authority, documented rationale, and correlation tracking."""

    def classify_evidence_package(self, package: EvidencePackage) -> ClassificationPackage:
        """Process an EvidencePackage into an enriched ClassificationPackage."""
        classified_list: List[ClassifiedIndicator] = []
        active_correlation_groups: Set[str] = set()

        for finding in package.findings:
            classified = self.classify_finding(finding)
            classified_list.append(classified)
            if classified.correlation_group:
                active_correlation_groups.add(classified.correlation_group)

        # Compute coverage and calibrated confidence
        coverage = self.calculate_coverage(package.check_statuses)
        confidence = self.calculate_confidence(coverage, classified_list, package.check_statuses)

        return ClassificationPackage(
            scan_id=package.scan_id,
            total_findings_processed=len(classified_list),
            classified_indicators=classified_list,
            coverage_score=coverage,
            confidence_score=confidence,
            correlation_groups_detected=sorted(list(active_correlation_groups)),
        )

    def classify_finding(self, finding: StandardizedFinding) -> ClassifiedIndicator:
        """Classify a single StandardizedFinding with authority and severity basis."""
        # 1. Check if an explicit rule ID is recorded
        rule_id = finding.related_indicators[0] if finding.related_indicators else None

        if rule_id and rule_id in SEVERITY_BASIS_REGISTRY:
            authority, default_sev, basis = SEVERITY_BASIS_REGISTRY[rule_id]
            corr_group = CORRELATION_MAP.get(rule_id)
            is_policy_viol = (authority == AuthorityCategory.POLICY_VIOLATION)
            is_auth_malicious = (authority == AuthorityCategory.AUTHORITATIVE)
            return ClassifiedIndicator(
                finding_id=finding.finding_id,
                title=finding.title,
                severity=finding.severity or default_sev,
                authority=authority,
                severity_basis=basis,
                correlation_group=corr_group,
                is_authoritative=is_auth_malicious,
                is_policy_violation=is_policy_viol,
                source=finding.source,
                source_status=finding.source_status,
                provenance={
                    "finding_type": finding.finding_type.value,
                    "rule_id": rule_id,
                    "timestamp": finding.timestamp.isoformat(),
                },
            )

        # 2. Categorize by FindingType when rule ID is not in registry
        if finding.source_status in (CheckStatus.UNAVAILABLE, CheckStatus.FAILED, CheckStatus.PARTIAL):
            return ClassifiedIndicator(
                finding_id=finding.finding_id,
                title=finding.title,
                severity=FindingSeverity.INFORMATIONAL,
                authority=AuthorityCategory.INCONCLUSIVE,
                severity_basis=f"Check {finding.finding_type.value} reported {finding.source_status.value}; not proof of safety.",
                correlation_group=None,
                is_authoritative=False,
                is_policy_violation=False,
                source=finding.source,
                source_status=finding.source_status,
                provenance={"finding_type": finding.finding_type.value},
            )

        if finding.finding_type == FindingType.SSRF_GUARD:
            return ClassifiedIndicator(
                finding_id=finding.finding_id,
                title=finding.title,
                severity=FindingSeverity.CRITICAL,
                authority=AuthorityCategory.POLICY_VIOLATION,
                severity_basis="SSRF validation deterministically confirmed prohibited network destination; blocked by egress policy (not proof of target maliciousness).",
                correlation_group="CORR-IP-DESTINATION",
                is_authoritative=False,
                is_policy_violation=True,
                source=finding.source,
                source_status=finding.source_status,
                provenance={"finding_type": finding.finding_type.value},
            )

        if finding.finding_type == FindingType.THREAT_INTELLIGENCE:
            is_intel_malicious = finding.observed_evidence.get("is_malicious") is True
            if is_intel_malicious:
                return ClassifiedIndicator(
                    finding_id=finding.finding_id,
                    title=finding.title,
                    severity=FindingSeverity.CRITICAL,
                    authority=AuthorityCategory.AUTHORITATIVE,
                    severity_basis="Authoritative threat intelligence feed confirmed destination malicious on active reputation blocklist.",
                    correlation_group="CORR-THREAT-INTEL",
                    is_authoritative=True,
                    is_policy_violation=False,
                    source=finding.source,
                    source_status=finding.source_status,
                    provenance={"finding_type": finding.finding_type.value},
                )

        if finding.finding_type == FindingType.AI_INFERENCE:
            return ClassifiedIndicator(
                finding_id=finding.finding_id,
                title=finding.title,
                severity=finding.severity,
                authority=AuthorityCategory.HEURISTIC,
                severity_basis="AI qualitative contextual reasoning; probabilistic interpretation only, not authoritative evidence.",
                correlation_group="CORR-AI-REASONING",
                is_authoritative=False,
                source=finding.source,
                source_status=finding.source_status,
                provenance={"finding_type": finding.finding_type.value, "is_ai": True},
            )

        if finding.finding_type == FindingType.DNS_INVESTIGATION:
            return ClassifiedIndicator(
                finding_id=finding.finding_id,
                title=finding.title,
                severity=finding.severity,
                authority=AuthorityCategory.INFORMATIONAL,
                severity_basis="Empirical DNS resolution preflight observation.",
                correlation_group="CORR-DNS",
                is_authoritative=False,
                source=finding.source,
                source_status=finding.source_status,
                provenance={"finding_type": finding.finding_type.value},
            )

        # Default fallback classification
        return ClassifiedIndicator(
            finding_id=finding.finding_id,
            title=finding.title,
            severity=finding.severity,
            authority=AuthorityCategory.HEURISTIC,
            severity_basis=f"Heuristic observation in {finding.finding_type.value}.",
            correlation_group=None,
            is_authoritative=False,
            source=finding.source,
            source_status=finding.source_status,
            provenance={"finding_type": finding.finding_type.value},
        )

    def calculate_coverage(self, statuses: Dict[str, CheckStatus]) -> float:
        """Calculate the proportion of applicable security checks that were completed."""
        applicable = [s for s in statuses.values() if s != CheckStatus.NOT_APPLICABLE]
        if not applicable:
            return 1.0

        completed = sum(1 for s in applicable if s == CheckStatus.COMPLETED)
        return round(completed / len(applicable), 2)

    def calculate_confidence(
        self,
        coverage: float,
        indicators: List[ClassifiedIndicator],
        statuses: Dict[str, CheckStatus],
    ) -> float:
        """Calculate confidence based on check coverage, authority of findings, and provider completeness."""
        # Baseline confidence heavily weighted by coverage
        score = coverage * 0.70

        # Enforce coverage penalties for failed or unavailable core checks
        failed_count = sum(1 for s in statuses.values() if s == CheckStatus.FAILED)
        unavailable_count = sum(1 for s in statuses.values() if s == CheckStatus.UNAVAILABLE)

        # Evidence quality boost
        has_authoritative = any(i.is_authoritative for i in indicators)
        has_heuristic = any(i.authority == AuthorityCategory.HEURISTIC for i in indicators)

        if has_authoritative:
            score += 0.30
        elif has_heuristic:
            score += 0.15

        # Penalties for inconclusive state
        penalty = (failed_count * 0.10) + (unavailable_count * 0.05)
        score = max(0.10, min(1.0, score - penalty))

        return round(score, 2)
