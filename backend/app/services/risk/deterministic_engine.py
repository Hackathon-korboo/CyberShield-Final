"""Deterministic Risk Assessment Engine for Part 15.

Aggregates classified findings into explainable risk classifications and quantitative scores
using deterministic rules, correlation de-duplication, severity floors, and authority gates.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

from backend.app.schemas.evidence import (
    CheckStatus,
    EvidencePackage,
    FindingSeverity,
    FindingType,
)
from backend.app.schemas.risk import (
    AuthorityCategory,
    ClassificationPackage,
    ClassifiedIndicator,
    DeterministicRiskAssessment,
    RiskClassification,
)

SEVERITY_WEIGHTS = {
    FindingSeverity.CRITICAL: 40,
    FindingSeverity.HIGH: 25,
    FindingSeverity.MEDIUM: 15,
    FindingSeverity.LOW: 5,
    FindingSeverity.INFORMATIONAL: 0,
}

SEVERITY_FLOORS = {
    FindingSeverity.CRITICAL: 70,
    FindingSeverity.HIGH: 40,
    FindingSeverity.MEDIUM: 15,
    FindingSeverity.LOW: 5,
    FindingSeverity.INFORMATIONAL: 0,
}


class DeterministicRiskEngine:
    """Deterministic, explainable risk assessment engine implementing roadmap governance."""

    def evaluate(
        self,
        evidence_pkg: EvidencePackage,
        class_pkg: ClassificationPackage,
    ) -> DeterministicRiskAssessment:
        """Evaluate evidence package and classification package into a deterministic risk assessment."""
        scan_id = evidence_pkg.scan_id
        target = evidence_pkg.target
        target_type = evidence_pkg.target_type
        indicators = class_pkg.classified_indicators
        statuses = evidence_pkg.check_statuses

        # Filter active threat indicators (exclude informational and inconclusive notes)
        threat_indicators = [
            ind for ind in indicators
            if ind.severity in (FindingSeverity.LOW, FindingSeverity.MEDIUM, FindingSeverity.HIGH, FindingSeverity.CRITICAL)
            and ind.authority in (AuthorityCategory.AUTHORITATIVE, AuthorityCategory.POLICY_VIOLATION, AuthorityCategory.HEURISTIC)
        ]

        has_authoritative_malicious = any(
            i.is_authoritative and i.authority == AuthorityCategory.AUTHORITATIVE
            for i in threat_indicators
        )
        has_policy_violation = any(
            getattr(i, "is_policy_violation", False) or i.authority == AuthorityCategory.POLICY_VIOLATION
            for i in threat_indicators
        )
        has_conflicts = any(
            f.metadata.get("has_conflicting_evidence", False)
            for f in evidence_pkg.findings
        )
        rules_triggered = list(
            dict.fromkeys(
                i.provenance.get("rule_id") for i in threat_indicators
                if i.provenance.get("rule_id")
            )
        )

        # -------------------------------------------------------------
        # 1. Check Inconclusive criteria
        # -------------------------------------------------------------
        dns_status = statuses.get("DNS_INVESTIGATION")
        if dns_status == CheckStatus.FAILED and not has_authoritative_malicious and not has_policy_violation:
            return DeterministicRiskAssessment(
                scan_id=scan_id,
                target=target,
                target_type=target_type,
                classification=RiskClassification.INCONCLUSIVE,
                risk_score=None,
                summary="Investigation inconclusive due to DNS resolution failure.",
                explanation="DNS preflight check failed to resolve the destination host. In accordance with security policy, failed checks cannot be evaluated as clean.",
                supporting_evidence=["DNS preflight query failed or returned SERVFAIL/NXDOMAIN."],
                correlation_groups=[],
                has_conflicting_evidence=has_conflicts,
                has_policy_violation=False,
                has_authoritative_match=False,
                coverage_score=class_pkg.coverage_score,
                confidence_score=class_pkg.confidence_score,
                rules_triggered=[],
            )

        # -------------------------------------------------------------
        # 2. Check Authoritative Confirmed Malicious criteria
        # -------------------------------------------------------------
        if has_authoritative_malicious:
            auth_indicators = [i for i in threat_indicators if i.is_authoritative and i.authority == AuthorityCategory.AUTHORITATIVE]
            evidence_citations = [f"{i.title}: {i.severity_basis}" for i in auth_indicators]
            return DeterministicRiskAssessment(
                scan_id=scan_id,
                target=target,
                target_type=target_type,
                classification=RiskClassification.CONFIRMED_MALICIOUS,
                risk_score=100,
                summary="Authoritative threat intelligence match confirmed malicious target.",
                explanation="Target destination is confirmed malicious on authoritative threat intelligence blocklists with verified threat reputation.",
                supporting_evidence=evidence_citations,
                correlation_groups=class_pkg.correlation_groups_detected,
                has_conflicting_evidence=has_conflicts,
                has_policy_violation=has_policy_violation,
                has_authoritative_match=True,
                coverage_score=class_pkg.coverage_score,
                confidence_score=class_pkg.confidence_score,
                rules_triggered=rules_triggered,
            )

        # -------------------------------------------------------------
        # 3. Handle Empty Indicators (Clean / Low Risk)
        # -------------------------------------------------------------
        if not threat_indicators:
            summary = "No significant malicious indicators were found within the checks performed."
            explanation = (
                "Static analysis of target structure and payload verified standard conventions. "
                "This evaluation reflects only the static checks executed and does not prove the website is safe."
            )
            return DeterministicRiskAssessment(
                scan_id=scan_id,
                target=target,
                target_type=target_type,
                classification=RiskClassification.LOW_RISK,
                risk_score=0,
                summary=summary,
                explanation=explanation,
                supporting_evidence=["0 malicious indicators detected in static inspection."],
                correlation_groups=[],
                has_conflicting_evidence=has_conflicts,
                has_policy_violation=False,
                has_authoritative_match=False,
                coverage_score=class_pkg.coverage_score,
                confidence_score=class_pkg.confidence_score,
                rules_triggered=[],
            )

        # -------------------------------------------------------------
        # 4. Correlated Deduplication and Severity Floor Aggregation
        # -------------------------------------------------------------
        # Group indicators by correlation_group to prevent double-counting
        grouped_scores: Dict[str, int] = {}
        highest_severity = FindingSeverity.LOW

        for ind in threat_indicators:
            # Track highest severity for floor calculation
            if SEVERITY_WEIGHTS[ind.severity] > SEVERITY_WEIGHTS[highest_severity]:
                highest_severity = ind.severity

            # Correlated contribution
            group_key = ind.correlation_group or ind.indicator_id
            curr_val = grouped_scores.get(group_key, 0)
            weight = SEVERITY_WEIGHTS.get(ind.severity, 10)
            if weight > curr_val:
                grouped_scores[group_key] = weight

        additive_score = sum(grouped_scores.values())
        floor_score = SEVERITY_FLOORS.get(highest_severity, 0)
        final_score = min(100, max(additive_score, floor_score))

        # -------------------------------------------------------------
        # 5. Classify Threat Level
        # -------------------------------------------------------------
        # Check if only AI inference predicted threat without deterministic indicators
        is_only_ai = all(i.provenance.get("is_ai") for i in threat_indicators)
        high_or_crit_groups = sum(1 for score in grouped_scores.values() if score >= 25)
        independent_group_count = len(grouped_scores)

        if is_only_ai:
            classification = RiskClassification.SUSPICIOUS
            final_score = min(final_score, 40)
        elif has_policy_violation:
            classification = RiskClassification.HIGH_RISK
            final_score = max(final_score, 70)
        elif final_score >= 70 or high_or_crit_groups >= 2 or independent_group_count >= 3:
            classification = RiskClassification.HIGH_RISK
            final_score = max(final_score, 70)
        elif final_score >= 15:
            classification = RiskClassification.SUSPICIOUS
        else:
            classification = RiskClassification.LOW_RISK

        # -------------------------------------------------------------
        # 6. Generate Contextual Explanation
        # -------------------------------------------------------------
        citations = [f"{i.title} ({i.severity.value}): {i.severity_basis}" for i in threat_indicators]
        if has_policy_violation:
            summary = (
                f"Security policy violation detected: target destination is restricted by egress policy "
                f"(Score: {final_score}/100, {classification.value})."
            )
            explanation = (
                f"Security inspection triggered rules: {', '.join(rules_triggered or ['Policy Rules'])}. "
                f"Destination resolves to a prohibited loopback, private, link-local, or metadata address. "
                f"In accordance with security policy separation, an SSRF policy violation is classified as HIGH_RISK "
                f"and does not independently establish external target maliciousness."
            )
        else:
            summary = (
                f"Deterministic evaluation classified target as {classification.value} (Score: {final_score}/100) "
                f"based on {len(threat_indicators)} indicator(s) across {len(grouped_scores)} independent evidence group(s)."
            )
            explanation = (
                f"Security inspection triggered rules: {', '.join(rules_triggered or ['Heuristic Findings'])}. "
                f"Scoring applied the Severity Floor Model (Floor: {floor_score}) with correlated indicator de-duplication."
            )

        if has_conflicts:
            explanation += " Note: Conflicting findings were observed between structural observations and threat indicators; evaluated conservatively."

        return DeterministicRiskAssessment(
            scan_id=scan_id,
            target=target,
            target_type=target_type,
            classification=classification,
            risk_score=final_score,
            summary=summary,
            explanation=explanation,
            supporting_evidence=citations,
            correlation_groups=class_pkg.correlation_groups_detected,
            has_conflicting_evidence=has_conflicts,
            has_policy_violation=has_policy_violation,
            has_authoritative_match=False,
            coverage_score=class_pkg.coverage_score,
            confidence_score=class_pkg.confidence_score,
            rules_triggered=rules_triggered,
        )
