"""AI Threat Analyzer Pipeline.

Orchestrates prompt synthesis, AI provider invocation, JSON response extraction,
and strict Pydantic V2 schema validation for URL, Email, and SMS attack surfaces.
"""

import json
import logging
import re
from typing import Any, Dict, Optional

from pydantic import ValidationError

from backend.app.engines.ai.base import BaseAIProvider
from backend.app.engines.ai.exceptions import AIValidationError
from backend.app.engines.ai.prompts import (
    SYSTEM_INSTRUCTION,
    build_email_analysis_prompt,
    build_sms_analysis_prompt,
    build_url_analysis_prompt,
)
from backend.app.engines.ai.schemas import AiAnalysisResult

logger = logging.getLogger("cybershield.ai.analyzer")


def clean_llm_json_response(raw_text: str) -> str:
    """Strip markdown code block indicators and surrounding prose to extract clean JSON."""
    text = raw_text.strip()

    # Match ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Fallback: extract the first outermost balanced JSON object
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace:last_brace + 1].strip()

    return text


class AIThreatAnalyzer:
    """High-level analyzer coordinating prompt generation and schema-validated reasoning."""

    def __init__(self, provider: BaseAIProvider):
        self.provider = provider

    async def analyze(
        self,
        target_type: str,
        untrusted_content: str,
        observed_evidence: Dict[str, Any],
        heuristic_findings: Dict[str, Any],
        sender: Optional[str] = None,
        subject: Optional[str] = None,
    ) -> AiAnalysisResult:
        """Execute threat reasoning for the given target modality."""
        target_norm = target_type.lower().strip()

        if target_norm == "url":
            prompt = build_url_analysis_prompt(
                target_url=untrusted_content,
                observed_evidence=observed_evidence,
                heuristic_findings=heuristic_findings,
            )
        elif target_norm == "email":
            prompt = build_email_analysis_prompt(
                subject=subject,
                sender=sender,
                body=untrusted_content,
                observed_evidence=observed_evidence,
                heuristic_findings=heuristic_findings,
            )
        elif target_norm in ("sms", "sms_text"):
            prompt = build_sms_analysis_prompt(
                sender=sender,
                message=untrusted_content,
                observed_evidence=observed_evidence,
                heuristic_findings=heuristic_findings,
            )
        else:
            raise ValueError(f"Unsupported target_type: {target_type}")

        raw_output = await self.provider.generate_text(
            prompt=prompt,
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.2,
        )

        return self._parse_and_validate(raw_output)

    def _parse_and_validate(self, raw_output: str) -> AiAnalysisResult:
        """Extract JSON and parse into strict AiAnalysisResult schema."""
        cleaned_json = clean_llm_json_response(raw_output)

        try:
            parsed_dict = json.loads(cleaned_json)
        except Exception as exc:
            logger.warning("Failed to decode JSON from AI output: %s | Raw: %s", exc, raw_output[:200])
            raise AIValidationError("AI provider response was not valid JSON.", details=str(exc))

        # Enforce provider and model attribution if missing
        if "provider" not in parsed_dict or not parsed_dict["provider"]:
            parsed_dict["provider"] = getattr(self.provider, "provider_name", "google-gemini")
        if "model" not in parsed_dict or not parsed_dict["model"]:
            parsed_dict["model"] = getattr(self.provider, "model_name", "gemini-1.5-flash")
        if "status" not in parsed_dict or not parsed_dict["status"]:
            parsed_dict["status"] = "COMPLETED"

        try:
            return AiAnalysisResult.model_validate(parsed_dict)
        except ValidationError as exc:
            logger.warning("AI output failed Pydantic schema validation: %s", exc)
            raise AIValidationError("AI output violates schema contract.", details=str(exc))
