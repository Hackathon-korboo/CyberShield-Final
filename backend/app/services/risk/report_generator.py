"""Unified Threat Report Generator for Part 16.

Aggregates submitted input, standardized findings, deterministic risk assessment,
grounded recommendations, explicit limitations, and canonical integrity hashes.
"""

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Optional
import uuid

from backend.app.engines.ai.schemas import AiAnalysisResult
from backend.app.schemas.evidence import CheckStatus, EvidencePackage, StandardizedFinding
from backend.app.schemas.risk import DeterministicRiskAssessment, RiskClassification
from backend.app.schemas.unified_report import (
    ReportIntegrityInfo,
    ThreatIntelligenceSummary,
    UnifiedThreatReport,
)
from backend.app.services.blockchain.adapter import BlockchainAdapter
from backend.app.services.blockchain.canonical_hasher import (
    compute_canonical_hash,
)

# Grounded recommendations catalog keyed by triggered rule ID or finding category
RECOMMENDATION_REGISTRY = {
    "RULE-SSRF-001": "Do not attempt to interact with or route traffic to this destination; it targets internal, restricted infrastructure.",
    "RULE-SSRF-002": "Do not click embedded links referencing loopback or private intranet addresses.",
    "RULE-SSRF-003": "Do not open SMS links pointing to local or non-routable destinations.",
    "RULE-URL-001": "Verify site legitimacy through independent channels; raw IP addresses commonly evade domain reputation lists.",
    "RULE-URL-002": "Do not submit credentials or personal information; hostname contains lookalike characters to mimic legitimate services.",
    "RULE-URL-003": "Do not input authentication details or passwords on this unverified endpoint.",
    "RULE-URL-004": "Exercise caution; unusually deep subdomain structures often indicate domain shadowing or evasion.",
    "RULE-URL-005": "Exercise caution when visiting domains on high-abuse top-level domains.",
    "RULE-EML-001": "Do not act on artificial deadlines or urgent demands; independently verify the sender through official phone numbers.",
    "RULE-EML-002": "Verify invoice or payment instructions via verified out-of-band communication before transferring funds.",
    "RULE-EML-003": "Beware of unsolicited employment offers requiring upfront fees, equipment payments, or sensitive data.",
    "RULE-EML-004": "Do not enter passwords or account credentials; the message exhibits hallmarks of credential harvesting.",
    "RULE-SMS-001": "Never share OTP or 2FA verification codes with anyone; legitimate institutions will never request them by text or phone.",
    "RULE-SMS-002": "Do not call numbers or click links in card blockage alerts; contact your financial institution via their official app or card back.",
    "RULE-SMS-003": "Do not respond to prize or lottery claims requiring fees or personal information to claim winnings.",
    "RULE-SMS-004": "Treat urgent SMS notifications with caution; verify status directly in your official account portal.",
}


def compute_canonical_report_hash(
    scan_id: str,
    target: str,
    input_type: str,
    classification: str,
    risk_score: Optional[int],
    timestamp_str: str,
    rules_triggered: Optional[List[str]] = None,
    has_policy_violation: bool = False,
    has_authoritative_match: bool = False,
) -> str:
    """Compute an RFC 8785 deterministic SHA-256 canonical hash over report parameters."""
    return compute_canonical_hash(
        scan_id=scan_id,
        submitted_input=target,
        input_type=input_type,
        classification=classification,
        risk_score=risk_score,
        timestamp_str=timestamp_str,
        rules_triggered=rules_triggered,
        has_policy_violation=has_policy_violation,
        has_authoritative_match=has_authoritative_match,
    )


class UnifiedReportGenerator:
    """Constructs comprehensive, schema-validated unified threat intelligence reports."""

    def build_report(
        self,
        evidence_pkg: EvidencePackage,
        risk_assessment: DeterministicRiskAssessment,
        ai_analysis: Optional[AiAnalysisResult] = None,
        threat_intel: Optional[ThreatIntelligenceSummary] = None,
    ) -> UnifiedThreatReport:
        """Assemble all modular outputs into a validated UnifiedThreatReport."""
        scan_id = evidence_pkg.scan_id
        target = evidence_pkg.target
        input_type = evidence_pkg.target_type
        timestamp = evidence_pkg.timestamp

        # 1. Grounded Recommendations
        recommendations = self.generate_recommendations(risk_assessment)

        # 2. Limitations Documentation
        limitations = self.generate_limitations(evidence_pkg.check_statuses, ai_analysis)

        # 3. Canonical Report Integrity Hash
        canonical_hash = compute_canonical_report_hash(
            scan_id=scan_id,
            target=target,
            input_type=input_type,
            classification=risk_assessment.classification.value,
            risk_score=risk_assessment.risk_score,
            timestamp_str=timestamp.isoformat(),
            rules_triggered=risk_assessment.rules_triggered,
            has_policy_violation=getattr(risk_assessment, "has_policy_violation", False),
            has_authoritative_match=getattr(risk_assessment, "has_authoritative_match", False),
        )

        # Generate cryptographic integrity info via integrated BlockchainAdapter
        adapter = BlockchainAdapter()
        integrity_info = adapter.generate_integrity_info(
            scan_id=scan_id,
            submitted_input=target,
            input_type=input_type,
            classification=risk_assessment.classification.value,
            risk_score=risk_assessment.risk_score,
            timestamp_str=timestamp.isoformat(),
            rules_triggered=risk_assessment.rules_triggered,
            has_policy_violation=getattr(risk_assessment, "has_policy_violation", False),
            has_authoritative_match=getattr(risk_assessment, "has_authoritative_match", False),
        )

        intel_summary = threat_intel or ThreatIntelligenceSummary(
            provider_name="local_offline_intel",
            status=evidence_pkg.check_statuses.get("THREAT_INTELLIGENCE", CheckStatus.UNAVAILABLE),
            is_malicious=False,
            threat_types=[],
            reputation_score=None,
            details={"message": "Threat intelligence lookup unconfigured in local offline mode."},
        )

        return UnifiedThreatReport(
            scan_id=scan_id,
            submitted_input=target,
            input_type=input_type,
            timestamp=timestamp,
            risk_assessment=risk_assessment,
            technical_findings=evidence_pkg.findings,
            threat_intelligence=intel_summary,
            ai_analysis=ai_analysis,
            recommendations=recommendations,
            security_check_status=evidence_pkg.check_statuses,
            limitations=limitations,
            report_integrity=integrity_info,
        )

    def generate_recommendations(
        self,
        risk_assessment: DeterministicRiskAssessment,
    ) -> List[str]:
        """Produce actionable recommendations strictly grounded in triggered rules and classification."""
        recs: List[str] = []

        # Add rule-specific grounded recommendations
        for rule_id in risk_assessment.rules_triggered:
            if rule_id in RECOMMENDATION_REGISTRY:
                rec_text = RECOMMENDATION_REGISTRY[rule_id]
                if rec_text not in recs:
                    recs.append(rec_text)

        # Classification-level defensive recommendations
        if risk_assessment.classification in (RiskClassification.CONFIRMED_MALICIOUS, RiskClassification.HIGH_RISK):
            recs.append("Immediately terminate interaction with this target and report it to your IT security administrator.")
            recs.append("Do not authenticate, download attachments, or disclose sensitive organizational or financial data.")
        elif risk_assessment.classification == RiskClassification.SUSPICIOUS:
            recs.append("Exercise elevated caution. Independently verify the sender identity or destination via authoritative sources.")
        elif risk_assessment.classification == RiskClassification.INCONCLUSIVE:
            recs.append("Investigation could not be completed. Treat the target with caution until independent verification is performed.")
        else:
            recs.append("Exercise standard security precautions; verify website domain and transport encryption before submitting credentials.")

        return recs

    def generate_limitations(
        self,
        statuses: Dict[str, CheckStatus],
        ai_analysis: Optional[AiAnalysisResult] = None,
    ) -> List[str]:
        """Compile comprehensive operational limitations, missing modules, and caveats."""
        limitations: List[str] = []

        if statuses.get("REDIRECT_ANALYSIS") == CheckStatus.UNAVAILABLE:
            limitations.append("HTTP redirect tracing is disabled under the zero-egress static analysis security policy.")

        if statuses.get("THREAT_INTELLIGENCE") == CheckStatus.UNAVAILABLE:
            limitations.append("External commercial threat intelligence reputation feeds were not configured or offline.")

        if statuses.get("TLS_ANALYSIS") == CheckStatus.UNAVAILABLE:
            limitations.append("Live cryptographic TLS certificate inspection was unavailable in static preflight mode.")

        if statuses.get("HTTP_HEADERS") == CheckStatus.UNAVAILABLE:
            limitations.append("HTTP response security headers could not be examined due to zero-egress static analysis policy.")

        if ai_analysis and "fallback" in (ai_analysis.provider or "").lower():
            limitations.append("AI contextual reasoning was provided by the local deterministic fallback engine.")

        limitations.append("Report integrity hash is recorded locally; Web3 smart contract blockchain anchoring is currently NOT_REGISTERED.")

        return limitations
