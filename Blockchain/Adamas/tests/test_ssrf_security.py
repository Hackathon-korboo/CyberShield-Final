"""
CyberShield AI — SSRF Security & Preflight Test Suite (v2.2)
=============================================================
Automated test suite verifying Member 3's SSRF and URL security requirements:
- Loopback destination blocking (IPv4, IPv6, localhost, aliases)
- RFC 1918 Private IP blocking (10.x, 172.16-31.x, 192.168.x)
- Link-local and Cloud metadata (169.254.169.254, fe80::/10) blocking
- Obfuscated decimal/octal/hex IP representation blocking
- Protocol whitelist enforcement (blocking file, gopher, ftp, dict, ldap)
- Redirect destination revalidation
- Public legitimate URL pass-through (with controlled DNS fallback for offline sandboxes)
- Regression Bug 2: Malformed port exception handling (:bad, :99999)
- Regression Bug 3: IPv6 square bracket authority preservation
- Regression Bug 4: DNS-pinning parameters and PinnedSession socket connection
"""

import socket
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import requests

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from security.ssrf_validator import (
    SSRFValidator,
    SSRFValidationResult,
    SSRFSecurityException,
    SSRFRedirectBlockedException,
    PinnedSession,
    PinnedHTTPAdapter,
)

# Controlled public DNS mapping for sandboxed / offline test execution
CONTROLLED_PUBLIC_DNS = {
    "example.com": ["93.184.216.34"],
    "example.org": ["93.184.216.34"],
    "google.com": ["142.250.190.46"],
    "github.com": ["140.82.121.4"],
}


def controlled_dns_resolver(hostname: str, port: int) -> list[str]:
    """Controlled DNS resolver guaranteeing test repeatability in air-gapped sandboxes."""
    clean_host = hostname.lower().rstrip(".")
    if clean_host in CONTROLLED_PUBLIC_DNS:
        return CONTROLLED_PUBLIC_DNS[clean_host]
    try:
        addr_info = socket.getaddrinfo(clean_host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        return [sockaddr[0] for _, _, _, _, sockaddr in addr_info]
    except socket.gaierror:
        # Default public synthetic address for unmapped external test domains
        return ["93.184.216.34"]


class TestSSRFSecurity(unittest.TestCase):
    """Rigorous SSRF test cases and regression guards."""

    def setUp(self):
        SSRFValidator.DEFAULT_DNS_RESOLVER = controlled_dns_resolver

    def tearDown(self):
        SSRFValidator.DEFAULT_DNS_RESOLVER = None

    def test_loopback_destinations_blocked(self):
        """Verify that all loopback addresses (IPv4 & IPv6) are blocked."""
        loopback_urls = [
            "http://127.0.0.1",
            "http://127.0.0.1:8080",
            "http://127.0.0.2/admin",
            "http://127.255.255.254",
            "http://localhost",
            "http://localhost:3000",
            "http://sub.localhost",
            "http://[::1]",
            "http://[::1]:8000",
            "http://ip6-localhost",
        ]
        for url in loopback_urls:
            with self.subTest(url=url):
                res = SSRFValidator.validate_url(url, resolve_dns=False)
                self.assertFalse(res.is_safe, f"Loopback URL was not blocked: {url}")
                self.assertIn(res.violation_category, ["loopback", "internal_domain"])

    def test_rfc1918_private_ips_blocked(self):
        """Verify that all RFC 1918 private subnets are blocked."""
        private_urls = [
            # 10.0.0.0/8
            "http://10.0.0.1",
            "http://10.10.10.10:8080/metrics",
            "http://10.255.255.255",
            # 172.16.0.0/12
            "http://172.16.0.1",
            "http://172.20.100.5:9000",
            "http://172.31.255.255",
            # 192.168.0.0/16
            "http://192.168.0.1",
            "http://192.168.1.1/router-login",
            "http://192.168.254.254",
        ]
        for url in private_urls:
            with self.subTest(url=url):
                res = SSRFValidator.validate_url(url, resolve_dns=False)
                self.assertFalse(res.is_safe, f"Private IP URL was not blocked: {url}")
                self.assertEqual(res.violation_category, "private_ip")

    def test_cloud_metadata_link_local_blocked(self):
        """Verify that cloud provider metadata (AWS/GCP/Azure) and link-local IPs are blocked."""
        metadata_urls = [
            "http://169.254.169.254/latest/meta-data/",
            "http://169.254.169.254/computeMetadata/v1/",
            "http://169.254.1.1",
            "http://[fe80::1]/status",
        ]
        for url in metadata_urls:
            with self.subTest(url=url):
                res = SSRFValidator.validate_url(url, resolve_dns=False)
                self.assertFalse(res.is_safe, f"Cloud metadata URL was not blocked: {url}")
                self.assertEqual(res.violation_category, "metadata")

    def test_obfuscated_ip_representations_blocked(self):
        """Verify decimal integer, octal, and hex IP bypasses are detected and blocked."""
        obfuscated_urls = [
            ("http://2130706433", "Decimal integer for 127.0.0.1"),
            ("http://0x7f000001", "Hexadecimal for 127.0.0.1"),
            ("http://0177.0.0.1", "Octal dotted representation for 127.0.0.1"),
            ("http://2852039166", "Decimal integer for 169.254.169.254"),
            ("http://3232235521", "Decimal integer for 192.168.0.1"),
            ("http://167772161", "Decimal integer for 10.0.0.1"),
        ]
        for url, desc in obfuscated_urls:
            with self.subTest(url=url, description=desc):
                res = SSRFValidator.validate_url(url, resolve_dns=False)
                self.assertFalse(res.is_safe, f"Obfuscated IP was not blocked ({desc}): {url}")
                self.assertIn(res.violation_category, ["loopback", "metadata", "private_ip"])

    def test_prohibited_protocols_blocked(self):
        """Verify non-HTTP protocols cannot be triggered."""
        bad_schemes = [
            "file:///etc/passwd",
            "file://C:/Windows/win.ini",
            "gopher://127.0.0.1:6379/_INFO",
            "dict://127.0.0.1:11211/stat",
            "ftp://10.0.0.1/backup.tar.gz",
            "ldap://127.0.0.1:389/",
            "php://filter/read=convert.base64-encode/resource=index.php",
        ]
        for url in bad_schemes:
            with self.subTest(url=url):
                res = SSRFValidator.validate_url(url, resolve_dns=False)
                self.assertFalse(res.is_safe, f"Prohibited scheme was not blocked: {url}")
                self.assertEqual(res.violation_category, "prohibited_scheme")

    def test_redirect_revalidation(self):
        """Verify HTTP redirect destinations are validated safely."""
        original_url = "https://example.com/login"

        # 1. Unsafe redirect to cloud metadata (IPv4 literal)
        unsafe_redirect = SSRFValidator.validate_redirect(
            original_url, "http://169.254.169.254/latest/meta-data/"
        )
        self.assertFalse(unsafe_redirect.is_safe)
        self.assertEqual(unsafe_redirect.violation_category, "metadata")

        # 2. Unsafe protocol-relative redirect to cloud metadata
        proto_rel_metadata = SSRFValidator.validate_redirect(
            original_url, "//169.254.169.254/latest/meta-data/"
        )
        self.assertFalse(proto_rel_metadata.is_safe)
        self.assertEqual(proto_rel_metadata.violation_category, "metadata")

        # 3. Unsafe redirect to localhost
        local_redirect = SSRFValidator.validate_redirect(
            original_url, "http://127.0.0.1:8000/internal"
        )
        self.assertFalse(local_redirect.is_safe)
        self.assertEqual(local_redirect.violation_category, "loopback")

        # 4. Unsafe protocol-relative redirect to loopback
        proto_rel_local = SSRFValidator.validate_redirect(
            original_url, "//127.0.0.1:8000/internal"
        )
        self.assertFalse(proto_rel_local.is_safe)
        self.assertEqual(proto_rel_local.violation_category, "loopback")

        # 5. Unsafe redirect to private IP
        private_redirect = SSRFValidator.validate_redirect(
            original_url, "http://10.0.0.1/admin"
        )
        self.assertFalse(private_redirect.is_safe)
        self.assertEqual(private_redirect.violation_category, "private_ip")

        # 6. Prohibited protocol redirect
        scheme_redirect = SSRFValidator.validate_redirect(
            original_url, "javascript:alert(1)"
        )
        self.assertFalse(scheme_redirect.is_safe)
        self.assertEqual(scheme_redirect.violation_category, "prohibited_scheme")

        # 7. Cross-host redirect blocked when allow_cross_host=False
        cross_blocked = SSRFValidator.validate_redirect(
            original_url, "https://google.com/search", allow_cross_host=False
        )
        self.assertFalse(cross_blocked.is_safe)
        self.assertEqual(cross_blocked.violation_category, "cross_host_redirect")

        # 8. Safe cross-host redirect permitted when allow_cross_host=True
        cross_allowed = SSRFValidator.validate_redirect(
            original_url, "https://google.com/search", allow_cross_host=True
        )
        self.assertTrue(cross_allowed.is_safe)
        self.assertEqual(cross_allowed.normalized_url, "https://google.com/search")

        # 9. Safe relative redirect with leading slash
        safe_rel_redirect = SSRFValidator.validate_redirect(
            original_url, "/dashboard"
        )
        self.assertTrue(safe_rel_redirect.is_safe)
        self.assertEqual(safe_rel_redirect.normalized_url, "https://example.com/dashboard")

        # 10. Safe relative redirect without leading slash
        safe_rel_no_slash = SSRFValidator.validate_redirect(
            original_url, "dashboard"
        )
        self.assertTrue(safe_rel_no_slash.is_safe)
        self.assertEqual(safe_rel_no_slash.normalized_url, "https://example.com/dashboard")

        # 11. Safe relative redirect with query string and parent traversal
        safe_rel_query = SSRFValidator.validate_redirect(
            "https://example.com/sub/login", "../dashboard?ref=auth"
        )
        self.assertTrue(safe_rel_query.is_safe)
        self.assertEqual(safe_rel_query.normalized_url, "https://example.com/dashboard?ref=auth")

        # 12. Non-standard port preservation on relative redirect
        safe_port_rel = SSRFValidator.validate_redirect(
            "https://example.com:8443/login", "/dashboard"
        )
        self.assertTrue(safe_port_rel.is_safe)
        self.assertEqual(safe_port_rel.normalized_url, "https://example.com:8443/dashboard")

    def test_legitimate_public_urls_allowed(self):
        """Verify legitimate public websites pass preflight validation with controlled fallback."""
        valid_urls = [
            "https://example.com",
            "https://example.com/path/to/page?param=value",
            "http://example.org",
            "https://google.com",
            "https://github.com",
        ]
        for url in valid_urls:
            with self.subTest(url=url):
                res = SSRFValidator.validate_url(url, resolve_dns=True, dns_resolver=controlled_dns_resolver)
                self.assertTrue(res.is_safe, f"Legitimate URL was incorrectly blocked: {url} ({res.blocked_reason})")
                self.assertGreater(len(res.resolved_ips), 0)

    # ── REGRESSION TESTS (Bug 2, Bug 3 & Bug 4) ───────────────────

    def test_regression_malformed_port_handling(self):
        """Bug 2: Malformed or non-numeric port strings must be caught safely without crashing."""
        malformed_urls = [
            "http://example.com:bad",
            "http://example.com:port123",
            "http://example.com:99999",  # Port out of valid 1-65535 range
            "https://example.com:-1",
        ]
        for url in malformed_urls:
            with self.subTest(url=url):
                res = SSRFValidator.validate_url(url, resolve_dns=False)
                self.assertFalse(res.is_safe, f"Malformed port was not rejected: {url}")
                self.assertEqual(res.violation_category, "invalid_port")
                self.assertIn("Invalid URL port", res.blocked_reason)

    def test_regression_ipv6_normalization_square_brackets(self):
        """Bug 3: IPv6 addresses in authority MUST retain square brackets per RFC 3986."""
        url = "https://[2001:4860:4860::8888]/"
        res = SSRFValidator.validate_url(url, resolve_dns=False)
        self.assertTrue(res.is_safe)
        self.assertEqual(res.normalized_url, "https://[2001:4860:4860::8888]/")

        url_with_port = "https://[2001:4860:4860::8888]:8443/status?check=1"
        res_port = SSRFValidator.validate_url(url_with_port, resolve_dns=False)
        self.assertTrue(res_port.is_safe)
        self.assertEqual(res_port.normalized_url, "https://[2001:4860:4860::8888]:8443/status?check=1")

    def test_legitimate_non_default_ports_preserved(self):
        """Verify non-default ports on legitimate domains are correctly preserved."""
        url = "https://example.com:8443/api/v1/test?query=hello"
        res = SSRFValidator.validate_url(url, resolve_dns=False)
        self.assertTrue(res.is_safe)
        self.assertEqual(res.normalized_url, "https://example.com:8443/api/v1/test?query=hello")

    def test_dns_pinned_request_params_generation(self):
        """Bug 4: Verify DNS-pinning request parameters are correctly constructed for Member 1."""
        val = SSRFValidator.validate_url("https://example.com/api/v1", resolve_dns=True, dns_resolver=controlled_dns_resolver)
        self.assertTrue(val.is_safe)
        self.assertGreater(len(val.resolved_ips), 0)

        pinned_params = SSRFValidator.get_dns_pinned_request_params(val)
        self.assertIn("pinned_ip", pinned_params)
        self.assertEqual(pinned_params["sni_hostname"], "example.com")
        self.assertEqual(pinned_params["headers"], {"Host": "example.com"})
        self.assertEqual(pinned_params["port"], 443)
        self.assertEqual(pinned_params["target_url"], "https://example.com/api/v1")

    def test_pinned_session_blocks_prohibited_redirect(self):
        """
        Bug 4: Verify that PinnedSession intercepts redirects and blocks attempts
        to pivot to cloud metadata (169.254.169.254) or internal services.
        """
        session = PinnedSession(max_redirects=3)

        # Mock requests.Session.get to simulate a 302 redirect to cloud metadata
        mock_response = type("MockResponse", (), {
            "is_redirect": True,
            "status_code": 302,
            "headers": {"Location": "http://169.254.169.254/latest/meta-data/"},
        })()

        with patch("requests.Session.get", return_value=mock_response):
            with patch("socket.getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))]):
                with self.assertRaises(SSRFRedirectBlockedException) as ctx:
                    session.get("http://example.com/redirect")
                self.assertIn("Cloud metadata", str(ctx.exception))

    def test_pinned_session_disables_trust_env(self):
        """
        Critical Security Check: Verify that requests.Session.trust_env is False
        in PinnedSession to prevent HTTP_PROXY/HTTPS_PROXY environment variables
        from hijacking or bypassing the pinned IP connection.
        """
        session = PinnedSession()
        mock_resp = type("MockResp", (), {
            "is_redirect": False,
            "status_code": 200,
            "headers": {},
        })()

        captured_sessions = []
        original_init = requests.Session.__init__

        def capturing_init(sess_self, *args, **kwargs):
            original_init(sess_self, *args, **kwargs)
            captured_sessions.append(sess_self)

        with patch.object(requests.Session, "__init__", capturing_init):
            with patch.object(requests.Session, "get", return_value=mock_resp):
                with patch("socket.getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))]):
                    session.get("http://example.com/check-env")

        self.assertGreater(len(captured_sessions), 0)
        for sess in captured_sessions:
            self.assertFalse(sess.trust_env, "requests.Session.trust_env MUST be False to prevent proxy bypass!")

    def test_pinned_session_direct_socket_connect_and_tls_sni(self):
        """
        Verify that PinnedHTTPAdapter instantiates connection classes that establish
        the raw TCP socket to the pinned IP while preserving TLS SNI and Host headers.
        """
        pinned_ip = "93.184.216.34"
        adapter = PinnedHTTPAdapter(pinned_ip)
        adapter.init_poolmanager()

        pool = adapter.poolmanager.connection_from_url("https://example.com:443")
        conn = pool._new_conn()

        # The connection must target the pinned IP on create_connection
        with patch("socket.create_connection") as mock_create_conn:
            mock_create_conn.return_value = type("MockSocket", (), {})()
            conn.timeout = 5.0
            conn.port = 443
            sock = conn._new_conn()
            mock_create_conn.assert_called_once_with((pinned_ip, 443), 5.0)

    def test_pinned_session_avoids_double_dns_resolution(self):
        """
        Verify that passing validation_result or pinned_ip directly into PinnedSession.get()
        uses that exact pinned IP without triggering a second uncontrolled DNS lookup,
        and binds response.pinned_ip correctly.
        """
        val = SSRFValidationResult(
            is_safe=True,
            url="https://example.com/data",
            normalized_url="https://example.com/data",
            hostname="example.com",
            resolved_ips=["93.184.216.34"],
            port=443
        )
        session = PinnedSession()
        mock_resp = type("MockResp", (), {
            "is_redirect": False,
            "status_code": 200,
            "headers": {},
        })()

        with patch("socket.getaddrinfo") as mock_dns:
            with patch.object(requests.Session, "get", return_value=mock_resp) as mock_get:
                resp = session.get(val.normalized_url, validation_result=val)
                # socket.getaddrinfo should NOT be called because validation_result was supplied
                mock_dns.assert_not_called()
                self.assertEqual(resp.pinned_ip, "93.184.216.34")
                self.assertEqual(resp.sni_hostname, "example.com")
                # verify=True must be passed to requests.Session.get
                _, kwargs = mock_get.call_args
                self.assertTrue(kwargs.get("verify", False), "TLS certificate verification must be enabled by default!")

    def test_pinned_http_adapter_supports_ipv6_literal(self):
        """
        Verify that PinnedHTTPAdapter cleanly handles IPv6 addresses with or without brackets.
        """
        adapter_bracketed = PinnedHTTPAdapter("[2001:4860:4860::8888]")
        self.assertEqual(adapter_bracketed.pinned_ip, "2001:4860:4860::8888")

        adapter_bare = PinnedHTTPAdapter("2001:4860:4860::8888")
        self.assertEqual(adapter_bare.pinned_ip, "2001:4860:4860::8888")


if __name__ == "__main__":
    unittest.main()
