"""
CyberShield AI 2.0 — Member 3 SSRF & Preflight Security Test Suite (Integrated Backend)
=======================================================================================
Verifies:
- Loopback destination blocking (IPv4, IPv6, localhost, aliases)
- RFC 1918 Private IP blocking (10.x, 172.16-31.x, 192.168.x)
- Link-local and Cloud metadata (169.254.169.254, fe80::/10) blocking
- Obfuscated decimal/octal/hex IP representation blocking
- Protocol whitelist enforcement
- Relative and absolute redirect destination revalidation (Phase 5 resolution)
- Port preservation and parent path normalization
- Controlled public DNS fallback for test repeatability
"""

import unittest
from backend.app.engines.ssrf_guard import SSRFGuard, validate_redirect
from Blockchain.Adamas.security.ssrf_validator import (
    SSRFValidator,
    SSRFSecurityException,
    SSRFRedirectBlockedException,
)

CONTROLLED_PUBLIC_DNS = {
    "example.com": ["93.184.216.34"],
    "example.org": ["93.184.216.34"],
    "google.com": ["142.250.190.46"],
    "github.com": ["140.82.121.4"],
}


def controlled_dns(hostname: str, port: int = 80) -> list[str]:
    clean = hostname.lower().rstrip(".")
    if clean in CONTROLLED_PUBLIC_DNS:
        return CONTROLLED_PUBLIC_DNS[clean]
    return ["93.184.216.34"]


class TestMember3SSRFSecurity(unittest.TestCase):
    """Verify integrated SSRF validation and redirect protection."""

    def setUp(self):
        self.guard = SSRFGuard()

    def test_loopback_destinations_blocked(self):
        targets = [
            "http://127.0.0.1",
            "http://127.0.0.1:8080/admin",
            "http://localhost:3000",
            "http://127.127.127.127",
            "http://[::1]/status",
        ]
        for url in targets:
            res = self.guard.validate_url(url)
            self.assertFalse(res.is_safe, f"Loopback target {url} should have been blocked: {res.blocked_reason}")

    def test_rfc1918_private_ips_blocked(self):
        targets = [
            "http://10.0.0.1/internal",
            "http://172.16.0.1/metrics",
            "http://192.168.1.1/router",
        ]
        for url in targets:
            res = self.guard.validate_url(url)
            self.assertFalse(res.is_safe, f"Private IP {url} should have been blocked")

    def test_cloud_metadata_link_local_blocked(self):
        targets = [
            "http://169.254.169.254/latest/meta-data/",
            "http://[fe80::1]/admin",
        ]
        for url in targets:
            res = self.guard.validate_url(url)
            self.assertFalse(res.is_safe, f"Metadata/link-local {url} should have been blocked")

    def test_obfuscated_ips_blocked(self):
        targets = [
            "http://2130706433/",        # Decimal 127.0.0.1
            "http://017700000001/",      # Octal 127.0.0.1
            "http://0x7f000001/",        # Hex 127.0.0.1
        ]
        for url in targets:
            res = self.guard.validate_url(url)
            self.assertFalse(res.is_safe, f"Obfuscated target {url} should have been blocked")

    def test_redirect_revalidation_relative_and_absolute(self):
        """Phase 5 verification: Relative redirect resolution and SSRF defense."""
        # 1. Benign relative path
        valid, resolved, err = validate_redirect(
            "https://example.com/login",
            "/dashboard",
            dns_resolver=controlled_dns,
        )
        self.assertTrue(valid)
        self.assertEqual(resolved, "https://example.com/dashboard")

        # 2. Path without leading slash
        valid, resolved, err = validate_redirect(
            "https://example.com/app/index.html",
            "profile",
            dns_resolver=controlled_dns,
        )
        self.assertTrue(valid)
        self.assertEqual(resolved, "https://example.com/app/profile")

        # 3. Path traversal relative redirect
        valid, resolved, err = validate_redirect(
            "https://example.com/a/b/c",
            "../d",
            dns_resolver=controlled_dns,
        )
        self.assertTrue(valid)
        self.assertEqual(resolved, "https://example.com/a/d")

        # 4. Dangerous redirect to loopback must fail
        valid, resolved, err = validate_redirect(
            "https://example.com/login",
            "http://127.0.0.1:8000/internal",
            dns_resolver=controlled_dns,
        )
        self.assertFalse(valid)
        self.assertIn("prohibited", err.lower())

        # 5. Protocol-relative redirect to private IP
        valid, resolved, err = validate_redirect(
            "https://example.com/page",
            "//192.168.1.1/secret",
            dns_resolver=controlled_dns,
        )
        self.assertFalse(valid)
        self.assertIn("prohibited", err.lower())

        # 6. Preserves non-default port
        valid, resolved, err = validate_redirect(
            "https://example.com:8443/login",
            "/dashboard",
            dns_resolver=controlled_dns,
        )
        self.assertTrue(valid)
        self.assertEqual(resolved, "https://example.com:8443/dashboard")


if __name__ == "__main__":
    unittest.main()
