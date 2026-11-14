"""Deterministic detection rules for URL targets."""

import ipaddress
import re
from typing import List, Optional
from urllib.parse import urlsplit

from backend.app.engines.rules.base import BaseSecurityRule
from backend.app.schemas.analysis import (
    IndicatorCategory,
    IndicatorSeverity,
    SecurityIndicator,
    UrlObservedEvidence,
)

SUSPICIOUS_AUTH_KEYWORDS = [
    "login",
    "signin",
    "verify",
    "verification",
    "secure-login",
    "account-update",
    "banking",
    "wallet",
    "confirm",
    "password-reset",
    "recover",
]

SUSPICIOUS_TLDS = {
    "zip",
    "top",
    "tk",
    "ml",
    "ga",
    "cf",
    "gq",
    "xyz",
    "work",
    "click",
    "loan",
    "men",
}


class IpHyphenRule(BaseSecurityRule):
    """RULE-URL-001: Direct IP address used in place of domain name."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-URL-001",
            category=IndicatorCategory.IP_HOST,
            severity=IndicatorSeverity.HIGH,
            explanation="The URL specifies a raw IP address instead of a legitimate registered domain name.",
            mitigation="Do not submit credentials or navigate to raw IP address targets.",
        )

    def evaluate(self, evidence: UrlObservedEvidence) -> Optional[SecurityIndicator]:
        hostname = evidence.hostname
        try:
            ipaddress.ip_address(hostname)
            return SecurityIndicator(
                rule_id=self.rule_id,
                category=self.category,
                severity=self.severity,
                evidence=f"Direct IP hostname: {hostname}",
                explanation=self.explanation,
                mitigation=self.mitigation,
            )
        except ValueError:
            return None


class PunycodeHomoglyphRule(BaseSecurityRule):
    """RULE-URL-002: Punycode or homoglyphic lookalike character match."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-URL-002",
            category=IndicatorCategory.HOMOGLYPH_SPOOFING,
            severity=IndicatorSeverity.HIGH,
            explanation="The domain uses Punycode (xn--) encoding which frequently indicates Cyrillic/Greek homoglyph brand impersonation.",
            mitigation="Inspect domain spelling carefully; verify the site via official bookmarks.",
        )

    def evaluate(self, evidence: UrlObservedEvidence) -> Optional[SecurityIndicator]:
        if "xn--" in evidence.hostname.lower() or evidence.has_homoglyphs:
            return SecurityIndicator(
                rule_id=self.rule_id,
                category=self.category,
                severity=self.severity,
                evidence=f"Punycode encoded hostname: {evidence.hostname}",
                explanation=self.explanation,
                mitigation=self.mitigation,
            )
        return None


class SuspiciousAuthKeywordsRule(BaseSecurityRule):
    """RULE-URL-003: Phishing and credential harvesting lure keywords in URL structure."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-URL-003",
            category=IndicatorCategory.CREDENTIAL_HARVESTING,
            severity=IndicatorSeverity.MEDIUM,
            explanation="The URL contains authentication or security-alert keywords combined with unusual domain patterns.",
            mitigation="Ensure you are on the authentic domain before entering passwords or PINs.",
        )

    def evaluate(self, evidence: UrlObservedEvidence) -> Optional[SecurityIndicator]:
        target_str = f"{evidence.hostname}{evidence.path}".lower()
        matched_keywords = [kw for kw in SUSPICIOUS_AUTH_KEYWORDS if kw in target_str]

        # Trigger if keyword is found with hyphenated domain or deep path
        if matched_keywords and ("-" in evidence.hostname or len(matched_keywords) >= 2):
            return SecurityIndicator(
                rule_id=self.rule_id,
                category=self.category,
                severity=self.severity,
                evidence=f"Matched lure keywords: {', '.join(matched_keywords)}",
                explanation=self.explanation,
                mitigation=self.mitigation,
            )
        return None


class ExcessiveSubdomainRule(BaseSecurityRule):
    """RULE-URL-004: Excessive subdomain nesting."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-URL-004",
            category=IndicatorCategory.SUSPICIOUS_KEYWORD,
            severity=IndicatorSeverity.MEDIUM,
            explanation="The domain has four or more subdomain labels, a tactic frequently used to disguise the true root domain.",
            mitigation="Check the rightmost domain labels to determine the actual entity controlling the site.",
        )

    def evaluate(self, evidence: UrlObservedEvidence) -> Optional[SecurityIndicator]:
        labels = [part for part in evidence.hostname.split(".") if part]
        if len(labels) >= 5:  # e.g., a.b.c.example.com has 5 labels
            return SecurityIndicator(
                rule_id=self.rule_id,
                category=self.category,
                severity=self.severity,
                evidence=f"Excessive subdomain depth: {len(labels)} labels in '{evidence.hostname}'",
                explanation=self.explanation,
                mitigation=self.mitigation,
            )
        return None


class SuspiciousTldRule(BaseSecurityRule):
    """RULE-URL-005: High-abuse Top-Level Domain (TLD)."""

    def __init__(self):
        super().__init__(
            rule_id="RULE-URL-005",
            category=IndicatorCategory.SUSPICIOUS_TLD,
            severity=IndicatorSeverity.LOW,
            explanation="The URL uses a top-level domain with statistically high abuse and spam concentration.",
            mitigation="Exercise caution before downloading files or submitting personal details.",
        )

    def evaluate(self, evidence: UrlObservedEvidence) -> Optional[SecurityIndicator]:
        labels = evidence.hostname.split(".")
        if len(labels) >= 2:
            tld = labels[-1].lower()
            if tld in SUSPICIOUS_TLDS:
                return SecurityIndicator(
                    rule_id=self.rule_id,
                    category=self.category,
                    severity=self.severity,
                    evidence=f"High-abuse TLD: .{tld}",
                    explanation=self.explanation,
                    mitigation=self.mitigation,
                )
        return None
