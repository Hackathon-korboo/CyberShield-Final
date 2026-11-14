"""
CyberShield AI 2.0 - API Connection & Credential Setup Service
Manages secure credential storage, masking, live backend connection testing,
and runtime environment synchronization for Gemini, VirusTotal, and Safe Browsing.
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import requests
from dotenv import load_dotenv

logger = logging.getLogger("cybershield.config")

# Project paths resolved dynamically relative to project root or from CYBERSHIELD_ROOT env var
BASE_DIR = Path(os.getenv("CYBERSHIELD_ROOT", Path(__file__).resolve().parent.parent.parent.parent))
ENV_PATH = BASE_DIR / ".env"
ENV_EXAMPLE_PATH = BASE_DIR / ".env.example"

# Provider Constants
PROVIDER_GEMINI = "gemini"
PROVIDER_VIRUSTOTAL = "virustotal"
PROVIDER_SAFEBROWSING = "safebrowsing"

PROVIDER_METADATA = {
    PROVIDER_GEMINI: {
        "id": PROVIDER_GEMINI,
        "name": "Google Gemini",
        "env_var": "GEMINI_API_KEY",
        "required": True,
        "purpose": (
            "AI scam analysis, phishing email analysis, SMS smishing, fake job detection, "
            "threat explanation, and evidence-based recommendations."
        ),
        "docs_url": "https://aistudio.google.com/",
        "notice": "Required for deep reasoning and conversational scam analysis. Automatic local heuristic fallback activates if offline."
    },
    PROVIDER_VIRUSTOTAL: {
        "id": PROVIDER_VIRUSTOTAL,
        "name": "VirusTotal (v3)",
        "env_var": "VIRUSTOTAL_API_KEY",
        "required": False,
        "purpose": (
            "File hash reputation lookup, URL reputation lookup, and global malware intelligence. "
            "Safe read-only querying without uploading user files."
        ),
        "docs_url": "https://www.virustotal.com/gui/my-apikey",
        "notice": "OPTIONAL: Private user files are NEVER uploaded automatically. Public free-tier rate limits apply."
    },
    PROVIDER_SAFEBROWSING: {
        "id": PROVIDER_SAFEBROWSING,
        "name": "Google Safe Browsing (v4)",
        "env_var": "GOOGLE_SAFE_BROWSING_API_KEY",
        "required": False,
        "purpose": (
            "Malicious URL lookup, phishing website detection, and unsafe domain reputation."
        ),
        "docs_url": "https://console.cloud.google.com/apis/library/safebrowsing.googleapis.com",
        "notice": "OPTIONAL: For non-commercial usage terms only. Evaluate Google Web Risk separately for commercial deployments."
    }
}


def mask_api_key(key: Optional[str]) -> str:
    """Mask sensitive API key to protect secrets from being leaked to UI or logs."""
    if not key or key in ("your_gemini_api_key_here", "your_virustotal_api_key_here", "your_google_safe_browsing_api_key_here", "CHANGEME"):
        return ""
    stripped = key.strip()
    if len(stripped) <= 8:
        return "••••••••"
    return f"{stripped[:6]}••••••••••••{stripped[-4:]}"


def is_placeholder(key: Optional[str]) -> bool:
    """Check if API key is empty, None, or a placeholder template string."""
    if not key:
        return True
    cleaned = key.strip()
    placeholders = {
        "your_gemini_api_key_here",
        "your_virustotal_api_key_here",
        "your_google_safe_browsing_api_key_here",
        "dummy_key",
        "test_key",
        "changeme",
        "none",
        ""
    }
    return cleaned.lower() in placeholders or len(cleaned) < 10


class ConfigService:
    """Production service for connection testing, credential management, and .env persistence."""

    def __init__(self):
        self.env_path = ENV_PATH
        self.load_env()

    def load_env(self) -> None:
        """Load or reload environment variables from .env file."""
        if ENV_PATH.exists():
            load_dotenv(dotenv_path=ENV_PATH, override=True)
        elif ENV_EXAMPLE_PATH.exists():
            load_dotenv(dotenv_path=ENV_EXAMPLE_PATH, override=False)

    def get_raw_key(self, provider_id: str) -> str:
        """Retrieve raw key from environment."""
        meta = PROVIDER_METADATA.get(provider_id)
        if not meta:
            return ""
        return os.getenv(meta["env_var"], "").strip()

    def get_provider_status(self, provider_id: str) -> Dict[str, Any]:
        """
        Get the current configuration and connection status for a provider.
        Does NOT execute network requests automatically on read.
        """
        meta = PROVIDER_METADATA.get(provider_id)
        if not meta:
            raise ValueError(f"Unknown provider: {provider_id}")

        raw_key = self.get_raw_key(provider_id)
        is_configured = not is_placeholder(raw_key)

        return {
            "provider_id": provider_id,
            "name": meta["name"],
            "env_var": meta["env_var"],
            "required": meta["required"],
            "purpose": meta["purpose"],
            "docs_url": meta["docs_url"],
            "notice": meta["notice"],
            "is_configured": is_configured,
            "masked_key": mask_api_key(raw_key) if is_configured else "",
            "status": "CONFIGURED" if is_configured else "NOT_CONFIGURED"
        }

    def get_all_providers_status(self) -> Dict[str, Any]:
        """Get configuration overview for all registered providers."""
        self.load_env()
        return {
            "providers": [
                self.get_provider_status(pid) for pid in (PROVIDER_GEMINI, PROVIDER_VIRUSTOTAL, PROVIDER_SAFEBROWSING)
            ],
            "env_file_exists": ENV_PATH.exists()
        }

    # ==========================================================================
    # Live Connection Tests
    # ==========================================================================

    def test_connection(self, provider_id: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute an actual backend connection test against the chosen provider.
        Never simulates success.
        """
        key_to_test = (api_key if api_key is not None else self.get_raw_key(provider_id)).strip()

        if is_placeholder(key_to_test):
            return {
                "provider_id": provider_id,
                "status": "NOT_CONFIGURED",
                "connected": False,
                "message": "NOT CONFIGURED: No API key provided or placeholder detected.",
                "details": {}
            }

        if provider_id == PROVIDER_GEMINI:
            success, msg, details = self._test_gemini(key_to_test)
        elif provider_id == PROVIDER_VIRUSTOTAL:
            success, msg, details = self._test_virustotal(key_to_test)
        elif provider_id == PROVIDER_SAFEBROWSING:
            success, msg, details = self._test_safebrowsing(key_to_test)
        else:
            return {
                "provider_id": provider_id,
                "status": "CONNECTION_FAILED",
                "connected": False,
                "message": f"Unsupported provider: {provider_id}",
                "details": {}
            }

        return {
            "provider_id": provider_id,
            "status": "CONNECTED" if success else "CONNECTION_FAILED",
            "connected": success,
            "message": msg,
            "details": details
        }

    def _test_gemini(self, api_key: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Verify Gemini connection via models list endpoint."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        try:
            resp = requests.get(url, timeout=9.0)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name", "").replace("models/", "") for m in data.get("models", [])[:5]]
                return True, f"CONNECTED: Authenticated successfully with Google Gemini ({len(data.get('models', []))} models available).", {"sample_models": models}
            elif resp.status_code in (400, 401, 403):
                err = resp.json().get("error", {}).get("message", resp.text)
                return False, f"CONNECTION FAILED: HTTP {resp.status_code} - {err}", {}
            elif resp.status_code == 429:
                return False, "CONNECTION FAILED: HTTP 429 - Google Gemini API quota or rate limit exceeded.", {}
            else:
                return False, f"CONNECTION FAILED: HTTP {resp.status_code} - {resp.text[:150]}", {}
        except requests.Timeout:
            return False, "CONNECTION FAILED: Request to Google Gemini timed out (9s limit).", {}
        except requests.ConnectionError:
            return False, "CONNECTION FAILED: Network connection error reaching Google Gemini API.", {}
        except Exception as exc:
            return False, f"CONNECTION FAILED: {str(exc)}", {}

    def _test_virustotal(self, api_key: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verify VirusTotal v3 authentication using a safe, read-only endpoint.
        Never uploads private files.
        """
        # Safe read-only lookup on Google Public DNS 8.8.8.8
        url = "https://www.virustotal.com/api/v3/ip_addresses/8.8.8.8"
        headers = {
            "x-apikey": api_key,
            "User-Agent": "CyberShield-AI-2.0"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=9.0)
            if resp.status_code == 200:
                return True, "CONNECTED: Authenticated successfully with VirusTotal API v3 (Read-only reputation lookup active).", {"test_endpoint": "ip_addresses/8.8.8.8"}
            elif resp.status_code == 401:
                return False, "CONNECTION FAILED: HTTP 401 Unauthorized - Invalid VirusTotal API key.", {}
            elif resp.status_code == 403:
                return False, "CONNECTION FAILED: HTTP 403 Forbidden - Access denied or public rate limit exceeded.", {}
            elif resp.status_code == 429:
                return False, "CONNECTION FAILED: HTTP 429 - VirusTotal API rate limit exceeded (Public limit: 4 req/min).", {}
            else:
                return False, f"CONNECTION FAILED: HTTP {resp.status_code} - {resp.text[:150]}", {}
        except requests.Timeout:
            return False, "CONNECTION FAILED: Request to VirusTotal timed out (9s limit).", {}
        except requests.ConnectionError:
            return False, "CONNECTION FAILED: Network connection error reaching VirusTotal API.", {}
        except Exception as exc:
            return False, f"CONNECTION FAILED: {str(exc)}", {}

    def _test_safebrowsing(self, api_key: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Verify Google Safe Browsing v4 threatMatches endpoint."""
        url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={api_key}"
        payload = {
            "client": {
                "clientId": "cybershield-member2",
                "clientVersion": "2.0.0"
            },
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [
                    {"url": "http://testsafebrowsing.appspot.com/s/malware.html"}
                ]
            }
        }
        try:
            resp = requests.post(url, json=payload, timeout=9.0)
            if resp.status_code == 200:
                data = resp.json()
                matches_count = len(data.get("matches", []))
                return True, f"CONNECTED: Authenticated successfully with Google Safe Browsing API v4 ({matches_count} test threat matches confirmed).", {"test_url": "malware.html"}
            elif resp.status_code == 400:
                err = resp.json().get("error", {}).get("message", resp.text)
                return False, f"CONNECTION FAILED: HTTP 400 - Invalid Safe Browsing API key or request ({err}).", {}
            elif resp.status_code == 403:
                err = resp.json().get("error", {}).get("message", "API not enabled")
                return False, f"CONNECTION FAILED: HTTP 403 Forbidden - Safe Browsing API may not be enabled on your Google Cloud Project ({err}).", {}
            else:
                return False, f"CONNECTION FAILED: HTTP {resp.status_code} - {resp.text[:150]}", {}
        except requests.Timeout:
            return False, "CONNECTION FAILED: Request to Google Safe Browsing timed out (9s limit).", {}
        except requests.ConnectionError:
            return False, "CONNECTION FAILED: Network connection error reaching Google Safe Browsing API.", {}
        except Exception as exc:
            return False, f"CONNECTION FAILED: {str(exc)}", {}

    # ==========================================================================
    # Secure Persistence
    # ==========================================================================

    def save_credentials(
        self,
        gemini_api_key: Optional[str] = None,
        virustotal_api_key: Optional[str] = None,
        google_safebrowsing_api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Securely save credentials into root .env file.
        Creates a timestamped backup before modification.
        Only overwrites provided keys. Preserves comments, limits, and server configs.
        """
        # 1. Create backup if .env exists
        if ENV_PATH.exists():
            import datetime
            backup_dir = BASE_DIR / "Brain" / "BACKUPS"
            backup_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f".env.backup_{ts}"
            backup_path.write_text(ENV_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            logger.info(f"Created configuration backup at {backup_path}")

        # 2. Read existing content or base on .env.example
        if ENV_PATH.exists():
            content = ENV_PATH.read_text(encoding="utf-8")
        elif ENV_EXAMPLE_PATH.exists():
            content = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
        else:
            content = ""

        updates = {}
        if gemini_api_key is not None and not is_placeholder(gemini_api_key):
            updates["GEMINI_API_KEY"] = gemini_api_key.strip()
        if virustotal_api_key is not None and not is_placeholder(virustotal_api_key):
            updates["VIRUSTOTAL_API_KEY"] = virustotal_api_key.strip()
        if google_safebrowsing_api_key is not None and not is_placeholder(google_safebrowsing_api_key):
            updates["GOOGLE_SAFE_BROWSING_API_KEY"] = google_safebrowsing_api_key.strip()

        # Update lines matching key=
        for var_name, var_val in updates.items():
            pattern = re.compile(rf'^{var_name}=.*$', re.MULTILINE)
            if pattern.search(content):
                content = pattern.sub(f"{var_name}={var_val}", content)
            else:
                content += f"\n{var_name}={var_val}"
            # Synchronize process environment immediately
            os.environ[var_name] = var_val

        # Also sync gemini_client_instance if GEMINI_API_KEY was updated
        if "GEMINI_API_KEY" in updates:
            from backend.app.gemini.gemini_client import gemini_client_instance
            gemini_client_instance.api_key = updates["GEMINI_API_KEY"]

        # Write to .env strictly inside root
        ENV_PATH.write_text(content, encoding="utf-8")
        logger.info(f"Updated configuration saved securely to {ENV_PATH}")

        return {
            "success": True,
            "message": "Configuration successfully saved to local .env",
            "updated_providers": list(updates.keys())
        }


# Singleton service
config_service_instance = ConfigService()
