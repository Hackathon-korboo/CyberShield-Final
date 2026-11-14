"""
CyberShield AI 2.0 - Indicator of Compromise (IOC) & URL/Domain Analysis Module
Extracts URLs, domains, email addresses, phone numbers, and UPI handles from untrusted text.
Performs deterministic link inspection (typosquatting, IP hosts, shorteners, suspicious TLDs).
"""

import re
from urllib.parse import urlparse
from typing import List, Dict, Any, Set
from backend.app.schemas.threat_models import ThreatCategory, EvidenceItem


class IOCExtractor:
    """Extracts and analyzes network and identity IOCs from unstructured text."""

    URL_PATTERN = re.compile(
        r'https?://(?:[a-zA-Z0-9-._~:/?#\[\]@!$&\'()*+,;=]|%[0-9a-fA-F]{2})+|'
        r'\b(?:www\.)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?\b'
    )

    DOMAIN_PATTERN = re.compile(
        r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+(?:[a-zA-Z]{2,63})\b'
    )

    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    )

    PHONE_PATTERN = re.compile(
        r'(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?[6-9]\d{4}[-.\s]?\d{5}\b|'
        r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    )

    UPI_PATTERN = re.compile(
        r'\b[a-zA-Z0-9.\-_]{2,256}@(?:okhdfcbank|okaxis|okicici|oksbi|paytm|ybl|ibl|axl|upi|sbi|icici)\b'
    )

    IP_URL_PATTERN = re.compile(
        r'https?://(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?(?:/[^\s]*)?'
    )

    SUSPICIOUS_TLDS = {
        "xyz", "top", "work", "click", "cfd", "rest", "monster",
        "cam", "buzz", "online", "live", "site", "support-account"
    }

    URL_SHORTENERS = {
        "bit.ly", "tinyurl.com", "is.gd", "cutt.ly", "t.co",
        "rb.gy", "ow.ly", "buff.ly", "rebrand.ly"
    }

    POPULAR_BRANDS = {
        "paypal", "google", "microsoft", "apple", "amazon",
        "netflix", "chase", "wellsfargo", "sbi", "hdfc", "icici", "axis"
    }

    def extract_iocs(self, text: str) -> Dict[str, Any]:
        """Extract structured indicators of compromise from content."""
        if not text:
            return {"urls": [], "domains": [], "emails": [], "phones": [], "upi_ids": []}

        # 1. Extract URLs
        raw_urls = self.URL_PATTERN.findall(text)
        urls = list(dict.fromkeys([u.strip(".,;:)") for u in raw_urls]))

        # 2. Extract Domains
        domains: Set[str] = set()
        for u in urls:
            parsed = urlparse(u if "://" in u else f"http://{u}")
            if parsed.netloc:
                domains.add(parsed.netloc.split(":")[0].lower())

        # Also extract standalone domains
        standalone_domains = self.DOMAIN_PATTERN.findall(text)
        for d in standalone_domains:
            clean_d = d.lower().strip(".,;:)")
            # Filter common English words matching domain pattern
            if "." in clean_d and not clean_d.endswith((".txt", ".png", ".jpg", ".pdf", ".py")):
                domains.add(clean_d)

        # 3. Extract Emails
        emails = list(dict.fromkeys(self.EMAIL_PATTERN.findall(text)))

        # 4. Extract Phones
        raw_phones = self.PHONE_PATTERN.findall(text)
        phones = list(dict.fromkeys([re.sub(r'[\s\-\(\)\.]', '', p) for p in raw_phones if len(re.sub(r'\D', '', p)) >= 10]))

        # 5. Extract UPI IDs
        upi_matches = self.UPI_PATTERN.findall(text)
        upi_ids = list(dict.fromkeys(upi_matches))

        return {
            "urls": urls,
            "domains": sorted(list(domains)),
            "emails": emails,
            "phones": phones,
            "upi_ids": upi_ids,
        }

    def analyze_urls_and_domains(self, text: str) -> List[EvidenceItem]:
        """Analyze extracted links and domains for suspicious structural anomalies."""
        evidence: List[EvidenceItem] = []
        iocs = self.extract_iocs(text)

        # 1. Check for raw IP address in URL
        if self.IP_URL_PATTERN.search(text):
            evidence.append(
                EvidenceItem(
                    indicator="IP Address Hostname in URL",
                    description="URL contains a raw numerical IP address instead of a legitimate registered domain name.",
                    confidence=0.90,
                    category=ThreatCategory.PHISHING_EMAIL,
                    raw_snippet=self.IP_URL_PATTERN.search(text).group(0)
                )
            )

        # 1B. Check for Private/Loopback/Metadata SSRF Targets in URL
        for u in iocs.get("urls", []):
            try:
                parsed_u = urlparse(u if "://" in u else f"http://{u}")
                host = parsed_u.netloc.split(":")[0].lower()
                if host in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "169.254.169.254", "metadata.google.internal"):
                    evidence.append(
                        EvidenceItem(
                            indicator="Internal / Link-Local IP Host Target",
                            description=f"URL specifies loopback or internal metadata address '{host}', commonly used in SSRF or lateral attacks.",
                            confidence=0.95,
                            category=ThreatCategory.PHISHING_EMAIL,
                            raw_snippet=u
                        )
                    )
                # Check for unencrypted HTTP on sensitive domains/keywords
                if parsed_u.scheme == "http" and any(k in text.lower() for k in ("login", "password", "bank", "pay", "verify", "account")):
                    evidence.append(
                        EvidenceItem(
                            indicator="Unencrypted HTTP Communication on Sensitive Action",
                            description="Communication requests sensitive account action over plain unencrypted HTTP.",
                            confidence=0.70,
                            category=ThreatCategory.PHISHING_EMAIL,
                            raw_snippet=u
                        )
                    )
            except Exception:
                pass

        # 2. Inspect domains
        for domain in iocs["domains"]:
            parts = domain.split(".")
            tld = parts[-1].lower() if parts else ""

            # Check excessive subdomains (phishing obfuscation)
            if len(parts) >= 4:
                evidence.append(
                    EvidenceItem(
                        indicator="Excessive Subdomain Obfuscation",
                        description=f"Domain '{domain}' has {len(parts)-1} subdomains, a technique frequently used to hide actual destination domains.",
                        confidence=0.80,
                        category=ThreatCategory.PHISHING_EMAIL,
                        raw_snippet=domain
                    )
                )

            # Check Suspicious TLDs
            if tld in self.SUSPICIOUS_TLDS:
                evidence.append(
                    EvidenceItem(
                        indicator=f"Suspicious Low-Reputation TLD (.{tld})",
                        description=f"Domain '{domain}' utilizes a top-level domain frequently associated with automated phishing campaigns.",
                        confidence=0.85,
                        category=ThreatCategory.PHISHING_EMAIL,
                        raw_snippet=domain
                    )
                )

            # Check URL Shorteners
            if domain in self.URL_SHORTENERS:
                evidence.append(
                    EvidenceItem(
                        indicator="Obfuscated URL Shortener",
                        description=f"Shortened link via '{domain}' conceals final destination domain from security filters.",
                        confidence=0.75,
                        category=ThreatCategory.SCAM_SMS,
                        raw_snippet=domain
                    )
                )

            # Check Brand Typosquatting / Lookalikes
            for brand in self.POPULAR_BRANDS:
                if brand in domain and not (domain.endswith(f".{brand}.com") or domain == f"{brand}.com"):
                    evidence.append(
                        EvidenceItem(
                            indicator="Brand Impersonation / Typosquatting Domain",
                            description=f"Domain '{domain}' mimics trusted brand '{brand}' to deceive victims.",
                            confidence=0.95,
                            category=ThreatCategory.PHISHING_EMAIL,
                            raw_snippet=domain
                        )
                    )
                    break

            # Check Punycode / IDN Homograph
            if "xn--" in domain:
                evidence.append(
                    EvidenceItem(
                        indicator="Punycode Homograph Domain Vector",
                        description=f"Domain '{domain}' contains internationalized homograph characters mimicking lookalike Latin characters.",
                        confidence=0.95,
                        category=ThreatCategory.PHISHING_EMAIL,
                        raw_snippet=domain
                    )
                )

        return evidence


ioc_extractor_instance = IOCExtractor()
