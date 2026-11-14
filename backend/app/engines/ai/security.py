"""Prompt Injection Defense and Adversarial Input Sanitizer.

Guards the AI reasoning engine against adversarial prompt injection, jailbreaks,
system directive overrides, prompt leaking, and boundary escape attempts.
"""

import re
from typing import List, NamedTuple


class InjectionCheckResult(NamedTuple):
    """Result of an adversarial prompt injection check."""
    is_suspicious: bool
    detected_patterns: List[str]
    sanitized_content: str
    matched_categories: List[str] = []


# Pre-compiled regex patterns categorized by attack modality
INJECTION_PATTERNS = [
    # 1. Ignore / disregard / forget instructions or directives
    (
        "INSTRUCTION_OVERRIDE",
        re.compile(
            r"\b(?:ignore|disregard|forget|bypass|override|drop|dismiss)\s+(?:all\s+)?(?:previous|prior|existing|system|security)?\s*(?:instructions|directives|prompts|rules|guidelines|filters|constraints)\b",
            re.IGNORECASE,
        ),
    ),
    # 2. Specific rule overrides (e.g., CyberShield security rules)
    (
        "RULE_OVERRIDE",
        re.compile(
            r"\b(?:ignore|override|bypass|disable)\s+(?:all\s+)?(?:cybershield\s+)?(?:security\s+)?rules\b",
            re.IGNORECASE,
        ),
    ),
    # 3. Reveal system prompt / internal instructions / prompt leaking
    (
        "PROMPT_LEAK_ATTEMPT",
        re.compile(
            r"\b(?:reveal|show|display|print|output|leak|expose|repeat|share)\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions|directives|initial\s+prompt|guidelines)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "PROMPT_LEAK_ATTEMPT",
        re.compile(
            r"\bwhat\s+(?:is|are)\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions|directives)\b",
            re.IGNORECASE,
        ),
    ),
    # 4. Attempts to force classification (CLEAN, SAFE, BENIGN)
    (
        "CLASSIFICATION_FORCING",
        re.compile(
            r"\b(?:you\s+must\s+)?(?:classify|mark|tag|label|declare|treat|rate|consider|say|output)\s+(?:this\s+)?(?:message\s+|email\s+|url\s+|input\s+)?(?:as\s+|is\s+)?(?:clean|safe|benign|legitimate)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "CLASSIFICATION_FORCING",
        re.compile(
            r"\boutput\s+(?:strictly\s+)?(?:clean|safe|benign)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "CLASSIFICATION_FORCING",
        re.compile(
            r'output\s+strictly\s*\{.*?"(?:summary|risk_level|status)"\s*:\s*"clean"',
            re.IGNORECASE,
        ),
    ),
    # 5. Jailbreak / Mode switching / Developer mode
    (
        "JAILBREAK_ATTEMPT",
        re.compile(
            r"\b(?:you\s+are\s+now\s+(?:a|in)|enter|switch\s+to)\s+(?:developer|dan|jailbreak|unrestricted|god)\s+mode\b",
            re.IGNORECASE,
        ),
    ),
    (
        "ROLEPLAY_OVERRIDE",
        re.compile(
            r"\b(?:system\s+(?:prompt|instruction|override)\s*:|\[system\]|\[instruction\])",
            re.IGNORECASE,
        ),
    ),
    # 6. Delimiter escapes
    (
        "BOUNDARY_ESCAPE",
        re.compile(r"</?untrusted_content_to_analyze>", re.IGNORECASE),
    ),
]


def inspect_and_sanitize_untrusted_content(content: str) -> InjectionCheckResult:
    """Scan untrusted input for prompt injection signatures and neutralize boundary escapes."""
    detected: List[str] = []
    categories: List[str] = []

    for category, pattern in INJECTION_PATTERNS:
        match = pattern.search(content)
        if match:
            matched_text = match.group(0)
            if matched_text not in detected:
                detected.append(matched_text)
            if category not in categories:
                categories.append(category)

    # Neutralize any attempts to escape or inject XML delimiter tags
    sanitized = re.sub(
        r"</untrusted_content_to_analyze>",
        "&lt;/UNTRUSTED_CONTENT_TO_ANALYZE&gt;",
        content,
        flags=re.IGNORECASE,
    )
    sanitized = re.sub(
        r"<untrusted_content_to_analyze>",
        "&lt;UNTRUSTED_CONTENT_TO_ANALYZE&gt;",
        sanitized,
        flags=re.IGNORECASE,
    )

    return InjectionCheckResult(
        is_suspicious=bool(detected),
        detected_patterns=detected,
        sanitized_content=sanitized,
        matched_categories=categories,
    )
