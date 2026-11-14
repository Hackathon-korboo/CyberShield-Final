"""
CyberShield AI 2.0 - Scam & Threat Intelligence Service
Orchestrates Layer 1 Input Validation, Layer 2 Deterministic IOC extraction & link analysis,
Layer 3 VirusTotal external threat enrichment, Layer 4 Gemini analysis / Heuristic fallback,
Layer 5 Calibrated deterministic risk scoring & evidence integration, and Layer 6 Actionable mitigation recommendations.
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List

from backend.app.schemas.threat_models import (
    ScamAnalysisRequest,
    ScamAnalysisResponse,
    ExtractedIOCs,
    EvidenceItem,
    ThreatCategory,
    RiskLevel,
)
from backend.app.privacy.pii_redactor import redact_pii
from backend.app.security.prompt_guard import inspect_prompt_injection
from backend.app.gemini.gemini_client import gemini_client_instance
from backend.app.ai_engine.heuristics_engine import (
    heuristic_engine_instance,
    calculate_calibrated_scam_score,
)
from backend.app.ai_engine.ioc_extractor import ioc_extractor_instance
from backend.app.threat_intel.virustotal_client import virustotal_client_instance


class ThreatIntelligenceService:
    """End-to-end 6-layer orchestrator for scam detection, IOC extraction, and threat intelligence."""

    def analyze(self, request: ScamAnalysisRequest) -> ScamAnalysisResponse:
        start_time = time.perf_counter()
        raw_content = request.content.strip()

        # ----------------------------------------------------------------------
        # Layer 1: Input Validation & Sanitization
        # ----------------------------------------------------------------------
        if len(raw_content) > 50000:
            raise ValueError("Payload size exceeds maximum allowed boundary of 50,000 characters.")

        # ----------------------------------------------------------------------
        # Layer 2: Deterministic Security Analysis & IOC Extraction
        # ----------------------------------------------------------------------
        # A. Prompt Injection Inspection
        is_injection, injection_score, injection_signatures = inspect_prompt_injection(raw_content)

        # B. Structured IOC Extraction (URLs, Domains, Emails, Phones, UPI IDs)
        extracted_dict = ioc_extractor_instance.extract_iocs(raw_content)
        iocs_model = ExtractedIOCs(**extracted_dict)

        # C. Deterministic Link & Domain Anomalies
        url_evidence = ioc_extractor_instance.analyze_urls_and_domains(raw_content)

        # D. Privacy & PII Redaction
        pii_entities = []
        sanitized_content = raw_content
        if request.redact_pii:
            sanitized_content, pii_entities = redact_pii(raw_content)

        # ----------------------------------------------------------------------
        # Layer 3: External Threat Intelligence (VirusTotal)
        # ----------------------------------------------------------------------
        vt_intel: Dict[str, Any] = {}
        vt_evidence: List[EvidenceItem] = []

        if request.enable_virustotal and virustotal_client_instance.is_configured:
            domains_to_check = extracted_dict.get("domains", [])[:3]
            for domain in domains_to_check:
                vt_res = virustotal_client_instance.check_domain(domain)
                vt_intel[domain] = vt_res
                if vt_res.get("status") == "MALICIOUS":
                    vt_evidence.append(
                        EvidenceItem(
                            indicator="VirusTotal Malicious Domain Flag",
                            description=f"External threat intelligence confirmed '{domain}' is malicious ({vt_res.get('malicious_count', 0)} security vendors).",
                            confidence=0.99,
                            category=ThreatCategory.PHISHING_EMAIL,
                            raw_snippet=domain,
                            severity="CRITICAL",
                            correlation_group="CORR-VT-MALICIOUS"
                        )
                    )
                elif vt_res.get("status") == "SUSPICIOUS":
                    vt_evidence.append(
                        EvidenceItem(
                            indicator="VirusTotal Suspicious Domain Flag",
                            description=f"Domain '{domain}' flagged as suspicious by external threat intel vendors.",
                            confidence=0.85,
                            category=ThreatCategory.PHISHING_EMAIL,
                            raw_snippet=domain,
                            severity="HIGH",
                            correlation_group="CORR-SUSPICIOUS-LINK"
                        )
                    )

        # ----------------------------------------------------------------------
        # Layer 4: AI Analysis / Deterministic Heuristic Engine
        # ----------------------------------------------------------------------
        # Also run local heuristic detectors to guarantee empirical indicators are present
        local_heuristic_dict = heuristic_engine_instance.analyze(
            text=sanitized_content,
            prompt_injection_detected=is_injection,
            source_type=request.source_type or "unknown"
        )
        local_evidence = local_heuristic_dict.get("observed_evidence", [])

        if request.enable_gemini:
            analysis_dict = gemini_client_instance.analyze_threat(
                sanitized_content=sanitized_content,
                source_type=request.source_type or "unknown",
                prompt_injection_flag=is_injection
            )
        else:
            analysis_dict = local_heuristic_dict
            analysis_dict["engine_used"] = "heuristic-local-engine"

        # ----------------------------------------------------------------------
        # Layer 5: Calibrated Deterministic Risk Synthesis & Evidence Integration
        # ----------------------------------------------------------------------
        combined_evidence: List[EvidenceItem] = list(analysis_dict.get("observed_evidence", []))
        combined_evidence.extend(local_evidence)
        combined_evidence.extend(url_evidence)
        combined_evidence.extend(vt_evidence)

        # Deduplicate evidence by indicator + raw_snippet
        seen_indicators = set()
        deduped_evidence: List[EvidenceItem] = []
        for ev in combined_evidence:
            key = (ev.indicator.strip().lower(), (ev.raw_snippet or "").strip().lower())
            if key not in seen_indicators:
                seen_indicators.add(key)
                deduped_evidence.append(ev)

        has_authoritative_match = any(
            ev.indicator.startswith("VirusTotal Malicious") for ev in vt_evidence
        )

        # Calculate calibrated deterministic score from deduplicated empirical evidence
        det_score, det_level, det_primary, det_cats, grouped_scores = calculate_calibrated_scam_score(
            evidence_list=deduped_evidence,
            has_authoritative_match=has_authoritative_match,
            prompt_injection_flag=is_injection,
            source_type=request.source_type or "unknown"
        )

        # Adopt AI primary category if Gemini successfully differentiated and is channel-consistent
        ai_primary = analysis_dict.get("primary_category")
        primary_category = det_primary
        if ai_primary and ai_primary != ThreatCategory.BENIGN and det_primary == ThreatCategory.BENIGN and not deduped_evidence:
            primary_category = ai_primary
        elif ai_primary and ai_primary != ThreatCategory.BENIGN:
            # Enforce channel constraints
            if request.source_type in ("sms", "chat") and ai_primary == ThreatCategory.PHISHING_EMAIL:
                primary_category = ThreatCategory.KYC_PHISHING if "kyc" in raw_content.lower() else ThreatCategory.SCAM_SMS
            else:
                primary_category = ai_primary

        detected_categories = list(set([primary_category] + det_cats + analysis_dict.get("detected_categories", [])))

        # Determine classification
        if has_authoritative_match:
            classification = "CONFIRMED_MALICIOUS"
            verdict_str = "CONFIRMED_MALICIOUS"
        elif is_injection:
            classification = "PROMPT_INJECTION_ATTEMPT"
            verdict_str = "MALICIOUS"
        elif det_score >= 50.0:
            classification = "LIKELY_MALICIOUS"
            verdict_str = "LIKELY_MALICIOUS"
        elif det_score >= 25.0:
            classification = "SUSPICIOUS"
            verdict_str = "SUSPICIOUS"
        elif det_score >= 10.0:
            classification = "LIKELY_SAFE"
            verdict_str = "LIKELY_SAFE"
        else:
            classification = "BENIGN"
            verdict_str = "NO_THREAT_DETECTED"

        why_flagged = [ev.description or ev.indicator for ev in deduped_evidence[:5]]

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # ----------------------------------------------------------------------
        # Layer 6: Actionable Recommendations & Structured Output
        # ----------------------------------------------------------------------
        security_checks = {
            "prompt_injection_shield": "ATTACK_FLAGGED" if is_injection else "PASSED",
            "pii_redaction": "SANITIZED" if request.redact_pii else "DISABLED",
            "deterministic_rules": "APPLIED",
            "virustotal_threat_intel": (
                "ENRICHED" if vt_intel else ("SKIPPED_UNCONFIGURED" if not virustotal_client_instance.is_configured else "NO_DOMAINS")
            )
        }

        response = ScamAnalysisResponse(
            analysis_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            risk_level=det_level,
            risk_score=det_score,
            primary_category=primary_category,
            detected_categories=detected_categories,
            confidence_score=analysis_dict.get("confidence_score", 0.90),
            observed_evidence=deduped_evidence,
            ai_assessment=analysis_dict.get("ai_assessment", ""),
            uncertainty_factors=analysis_dict.get("uncertainty_factors", []),
            mitigation_recommendations=analysis_dict.get("mitigation_recommendations", []),
            pii_redacted_content=sanitized_content if request.redact_pii else None,
            pii_entities_found=pii_entities,
            iocs=iocs_model,
            external_threat_intel=vt_intel if vt_intel else None,
            engine_used=analysis_dict.get("engine_used", "unknown"),
            prompt_injection_detected=is_injection,
            processing_time_ms=round(elapsed_ms, 2),
            has_authoritative_match=has_authoritative_match,
            verdict=verdict_str,
            coverage_score=1.0,
            why_flagged=why_flagged,
            # Compatibility aliases
            classification=classification,
            explanation=analysis_dict.get("ai_assessment", ""),
            security_checks=security_checks,
            limitations_and_uncertainty=analysis_dict.get("uncertainty_factors", [])
        )

        return response


# Service singleton
threat_service_instance = ThreatIntelligenceService()
