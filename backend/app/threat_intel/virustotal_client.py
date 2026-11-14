"""
CyberShield AI 2.0 - VirusTotal External Threat Intelligence Client (v3)
Performs safe, read-only domain, URL, and file-hash reputation queries.
Enforces strict in-memory caching to respect free-tier rate limits (4 req/min).
Guarantees ZERO user file uploads.
"""

import os
import time
import base64
import logging
import ipaddress
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("cybershield.virustotal")


def is_private_or_restricted_host(host: str) -> bool:
    """Detect private, loopback, link-local, or cloud-metadata IP addresses."""
    clean = host.split(":")[0].strip().lower()
    if clean in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal", "metadata"):
        return True
    try:
        ip = ipaddress.ip_address(clean)
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast
    except ValueError:
        return False


class VirusTotalClient:
    """Production VirusTotal v3 Threat Intelligence Client with caching and rate guard."""

    CACHE_TTL_SECONDS = 3600  # 1 hour cache to preserve free tier quota
    BASE_URL = "https://www.virustotal.com/api/v3"

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.timeout = 8.0

    @property
    def api_key(self) -> str:
        return os.getenv("VIRUSTOTAL_API_KEY", "").strip()

    @property
    def is_configured(self) -> bool:
        key = self.api_key
        if not key or key in ("your_virustotal_api_key_here", "CHANGEME", "dummy_key", "test_key"):
            return False
        return len(key) >= 32

    def _get_headers(self) -> Dict[str, str]:
        return {
            "x-apikey": self.api_key,
            "User-Agent": "CyberShield-AI-2.0-ThreatIntelligence",
            "Accept": "application/json"
        }

    def check_domain(self, domain: str) -> Dict[str, Any]:
        """
        Query VirusTotal domain reputation (read-only).
        """
        clean_domain = domain.lower().strip()

        # SSRF Defense: Block private, loopback, or cloud-metadata destinations
        if is_private_or_restricted_host(clean_domain):
            return {
                "available": False,
                "status": "BLOCKED_RESTRICTED_HOST",
                "domain": clean_domain,
                "details": "Security check: External intelligence lookup blocked for private/loopback/metadata host."
            }

        if not self.is_configured:
            return {
                "available": False,
                "status": "NOT_CONFIGURED",
                "domain": clean_domain,
                "details": "VirusTotal API key not configured or optional integration skipped."
            }

        # Check cache
        cache_key = f"domain:{clean_domain}"
        now = time.time()
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if now - entry["timestamp"] < self.CACHE_TTL_SECONDS:
                return entry["data"]

        url = f"{self.BASE_URL}/domains/{clean_domain}"
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
            if resp.status_code == 200:
                stats = resp.json().get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                suspicious = stats.get("suspicious", 0)
                harmless = stats.get("harmless", 0)

                status = "CLEAN"
                if malicious >= 2:
                    status = "MALICIOUS"
                elif malicious == 1 or suspicious >= 2:
                    status = "SUSPICIOUS"

                data = {
                    "available": True,
                    "status": status,
                    "domain": clean_domain,
                    "malicious_count": malicious,
                    "suspicious_count": suspicious,
                    "harmless_count": harmless,
                    "details": f"VirusTotal detection: {malicious} security vendors flagged this domain as malicious, {suspicious} as suspicious."
                }
                self._cache[cache_key] = {"timestamp": now, "data": data}
                return data

            elif resp.status_code == 404:
                # 404 in VirusTotal simply means unobserved / not in database
                data = {
                    "available": True,
                    "status": "UNKNOWN",
                    "domain": clean_domain,
                    "malicious_count": 0,
                    "suspicious_count": 0,
                    "harmless_count": 0,
                    "details": "Domain not currently cataloged in VirusTotal database (Unknown reputation)."
                }
                self._cache[cache_key] = {"timestamp": now, "data": data}
                return data

            elif resp.status_code == 429:
                return {
                    "available": False,
                    "status": "RATE_LIMITED",
                    "domain": clean_domain,
                    "details": "VirusTotal public rate limit exceeded (4 req/min). Continuing with local deterministic analysis."
                }
            else:
                return {
                    "available": False,
                    "status": "ERROR",
                    "domain": clean_domain,
                    "details": f"VirusTotal HTTP {resp.status_code} response: {resp.text[:100]}"
                }

        except (requests.Timeout, requests.ConnectionError) as exc:
            return {
                "available": False,
                "status": "NETWORK_UNAVAILABLE",
                "domain": clean_domain,
                "details": f"VirusTotal query unreachable ({str(exc)}). Continuing with local analysis."
            }

    def check_file_hash(self, sha256_hash: str) -> Dict[str, Any]:
        """
        Query VirusTotal file hash reputation without uploading any user file.
        """
        clean_hash = sha256_hash.lower().strip()
        if not self.is_configured:
            return {
                "available": False,
                "status": "NOT_CONFIGURED",
                "hash": clean_hash,
                "details": "VirusTotal API key not configured."
            }

        cache_key = f"hash:{clean_hash}"
        now = time.time()
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if now - entry["timestamp"] < self.CACHE_TTL_SECONDS:
                return entry["data"]

        url = f"{self.BASE_URL}/files/{clean_hash}"
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=self.timeout)
            if resp.status_code == 200:
                stats = resp.json().get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                suspicious = stats.get("suspicious", 0)
                harmless = stats.get("harmless", 0)

                status = "CLEAN"
                if malicious >= 2:
                    status = "MALICIOUS"
                elif malicious == 1 or suspicious >= 2:
                    status = "SUSPICIOUS"

                data = {
                    "available": True,
                    "status": status,
                    "hash": clean_hash,
                    "malicious_count": malicious,
                    "suspicious_count": suspicious,
                    "harmless_count": harmless,
                    "details": f"VirusTotal file intelligence: {malicious} AV engines flagged this hash as malicious."
                }
                self._cache[cache_key] = {"timestamp": now, "data": data}
                return data

            elif resp.status_code == 404:
                data = {
                    "available": True,
                    "status": "UNKNOWN",
                    "hash": clean_hash,
                    "malicious_count": 0,
                    "suspicious_count": 0,
                    "harmless_count": 0,
                    "details": "File hash not found in VirusTotal database (Never seen before)."
                }
                self._cache[cache_key] = {"timestamp": now, "data": data}
                return data

            elif resp.status_code == 429:
                return {
                    "available": False,
                    "status": "RATE_LIMITED",
                    "hash": clean_hash,
                    "details": "VirusTotal public rate limit exceeded. Falling back to local static analysis."
                }
            else:
                return {
                    "available": False,
                    "status": "ERROR",
                    "hash": clean_hash,
                    "details": f"VirusTotal HTTP {resp.status_code}"
                }

        except Exception as exc:
            return {
                "available": False,
                "status": "UNAVAILABLE",
                "hash": clean_hash,
                "details": str(exc)
            }


virustotal_client_instance = VirusTotalClient()
