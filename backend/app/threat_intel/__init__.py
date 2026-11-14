"""CyberShield AI 2.0 External Threat Intelligence Module."""

from backend.app.threat_intel.virustotal_client import (
    VirusTotalClient,
    virustotal_client_instance,
)

__all__ = ["VirusTotalClient", "virustotal_client_instance"]
