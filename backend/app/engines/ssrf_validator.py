"""
CyberShield AI — SSRF Protection & URL Preflight Validator
===========================================================
Enterprise-grade SSRF defense module:
1. Enforces strict protocol whitelist (http, https only).
2. Parses & normalizes hostnames and IP addresses:
   - Robust port parsing with explicit exception handling (rejects :bad, :99999).
   - Strict IPv6 bracket preservation in authority ([2001:4860:4860::8888]).
   - Preserves non-default legitimate ports (e.g. :8443, :8080) and query strings.
3. Detects obfuscated IP formats (decimal integer, octal, hex, mixed).
4. Enforces IP range blocking:
   - Loopback (127.0.0.0/8, ::1)
   - RFC 1918 Private networks (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
   - Link-local / Cloud Metadata (169.254.0.0/16, fe80::/10)
   - Carrier-grade NAT (100.64.0.0/10)
   - Broadcast / Multicast / Unspecified / Reserved
   - IPv4-mapped IPv6 (::ffff:127.0.0.1, etc.)
5. Performs DNS resolution preflight to stop DNS rebinding to internal hosts.
6. Validates redirect destinations before outbound request execution.
7. Provides full DNS-pinned HTTP client (`PinnedSession`) and connection parameters:
   - Connects directly to pre-validated IP (zero secondary uncontrolled DNS query).
   - Preserves original hostname in TLS SNI (server_hostname) and certificate verification.
   - Preserves correct Host header (including non-default ports).
   - Revalidates every redirect destination and pins each hop independently.
"""

from __future__ import annotations

import ipaddress
import re
import socket
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import urlparse, urljoin


# Prohibited IPv4 networks
PROHIBITED_IPV4_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),          # Current network ("this host")
    ipaddress.ip_network("10.0.0.0/8"),         # RFC 1918 Private
    ipaddress.ip_network("100.64.0.0/10"),      # Carrier-Grade NAT
    ipaddress.ip_network("127.0.0.0/8"),        # Loopback
    ipaddress.ip_network("169.254.0.0/16"),     # Link-Local / Cloud Metadata (169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),      # RFC 1918 Private
    ipaddress.ip_network("192.0.0.0/24"),       # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),       # TEST-NET-1
    ipaddress.ip_network("192.168.0.0/16"),     # RFC 1918 Private
    ipaddress.ip_network("198.18.0.0/15"),      # Benchmark testing
    ipaddress.ip_network("198.51.100.0/24"),    # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),     # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),        # Multicast
    ipaddress.ip_network("240.0.0.0/4"),        # Reserved / Future use
    ipaddress.ip_network("255.255.255.255/32"), # Broadcast
]

# Prohibited IPv6 networks
PROHIBITED_IPV6_NETWORKS = [
    ipaddress.ip_network("::1/128"),            # Loopback
    ipaddress.ip_network("::/128"),             # Unspecified
    ipaddress.ip_network("::ffff:0:0/96"),      # IPv4-mapped IPv6 (evaluated separately)
    ipaddress.ip_network("64:ff9b::/96"),       # IPv4/IPv6 translation
    ipaddress.ip_network("100::/64"),           # Discard prefix
    ipaddress.ip_network("2001:db8::/32"),      # Documentation
    ipaddress.ip_network("fc00::/7"),           # Unique Local Address (ULA)
    ipaddress.ip_network("fe80::/10"),          # Link-local
    ipaddress.ip_network("ff00::/8"),           # Multicast
]

# Prohibited loopback hostnames
PROHIBITED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "local",
    "broadcasthost",
    "ip6-localhost",
    "ip6-loopback",
}


class SSRFSecurityException(Exception):
    """Raised when an outbound URL violates SSRF security policies."""
    pass


class SSRFRedirectBlockedException(SSRFSecurityException):
    """Raised when an HTTP redirect target violates SSRF security policies."""
    pass


@dataclass
class SSRFValidationResult:
    """Detailed result of SSRF preflight validation."""
    is_safe: bool
    url: str
    normalized_url: str
    hostname: str
    resolved_ips: list[str] = field(default_factory=list)
    port: int | None = None
    blocked_reason: str | None = None
    violation_category: str | None = None  # e.g., 'loopback', 'private_ip', 'metadata', 'invalid_port', 'bad_scheme'


class SSRFValidator:
    """Preflight safety checker for URL investigation."""

    ALLOWED_SCHEMES = {"http", "https"}
    MAX_URL_LENGTH = 2048
    DEFAULT_DNS_RESOLVER: Callable[[str, int], list[str]] | None = None

    @classmethod
    def _parse_obfuscated_ip(cls, host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
        """
        Detect and decode obfuscated IP addresses (decimal integers, hex, octal).
        E.g.: 2130706433 -> 127.0.0.1, 0x7f000001 -> 127.0.0.1, 0177.0.0.1 -> 127.0.0.1
        """
        clean_host = host.strip("[]")

        if re.match(r"^(?:0x[0-9a-fA-F]+|[0-9]+)$", clean_host):
            try:
                base = 16 if clean_host.startswith("0x") else 10
                num = int(clean_host, base)
                if 0 <= num <= 0xFFFFFFFF:
                    return ipaddress.IPv4Address(num)
            except ValueError:
                pass

        parts = clean_host.split(".")
        if 1 < len(parts) <= 4:
            try:
                parsed_octets = []
                for p in parts:
                    if p.startswith(("0x", "0X")):
                        parsed_octets.append(int(p, 16))
                    elif p.startswith("0") and len(p) > 1 and all(c in "01234567" for c in p):
                        parsed_octets.append(int(p, 8))
                    elif p.isdigit():
                        parsed_octets.append(int(p, 10))
                    else:
                        return None
                if len(parsed_octets) == 4 and all(0 <= o <= 255 for o in parsed_octets):
                    ip_str = ".".join(str(o) for o in parsed_octets)
                    return ipaddress.IPv4Address(ip_str)
            except (ValueError, ipaddress.AddressValueError):
                pass

        try:
            return ipaddress.ip_address(clean_host)
        except ValueError:
            return None

    @classmethod
    def is_prohibited_ip(cls, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> tuple[bool, str]:
        """
        Check if an IP address belongs to any prohibited network.
        Returns (is_prohibited, category_reason).
        """
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            ip = ip.ipv4_mapped

        if isinstance(ip, ipaddress.IPv4Address):
            if ip in ipaddress.ip_network("169.254.0.0/16"):
                return True, "Cloud metadata & link-local address prohibited (RFC 3927)"

            if ip.is_loopback or ip in ipaddress.ip_network("127.0.0.0/8"):
                return True, "Loopback address prohibited (RFC 1122)"

            if ip.is_private:
                return True, "Private internal network address prohibited (RFC 1918)"

            for network in PROHIBITED_IPV4_NETWORKS:
                if ip in network:
                    return True, f"Prohibited IPv4 network range: {network}"

        elif isinstance(ip, ipaddress.IPv6Address):
            if ip.is_loopback:
                return True, "IPv6 loopback address prohibited (::1)"

            if ip.is_link_local:
                return True, "IPv6 link-local address prohibited (fe80::/10)"

            if ip.is_private:
                return True, "IPv6 private/unique-local address prohibited (fc00::/7)"

            for network in PROHIBITED_IPV6_NETWORKS:
                if ip in network:
                    return True, f"Prohibited IPv6 network range: {network}"

        return False, ""

    @classmethod
    def validate_url(
        cls,
        raw_url: str,
        resolve_dns: bool = True,
        dns_resolver: Callable[[str, int], list[str]] | None = None,
    ) -> SSRFValidationResult:
        """
        Perform complete preflight SSRF validation on a candidate URL.
        Supports custom dns_resolver for controlled testing in air-gapped or sandboxed environments.
        """
        if not raw_url or not isinstance(raw_url, str):
            return SSRFValidationResult(
                is_safe=False,
                url=str(raw_url),
                normalized_url="",
                hostname="",
                blocked_reason="URL cannot be empty",
                violation_category="empty_input",
            )

        trimmed = raw_url.strip()
        if len(trimmed) > cls.MAX_URL_LENGTH:
            return SSRFValidationResult(
                is_safe=False,
                url=trimmed,
                normalized_url="",
                hostname="",
                blocked_reason=f"URL exceeds maximum length of {cls.MAX_URL_LENGTH} characters",
                violation_category="length_exceeded",
            )

        if any(c in trimmed for c in ("\x00", "\r", "\n")):
            return SSRFValidationResult(
                is_safe=False,
                url=trimmed,
                normalized_url="",
                hostname="",
                blocked_reason="URL contains prohibited control characters",
                violation_category="malformed_url",
            )

        try:
            parsed = urlparse(trimmed)
        except Exception as e:
            return SSRFValidationResult(
                is_safe=False,
                url=trimmed,
                normalized_url="",
                hostname="",
                blocked_reason=f"URL parsing failed: {e}",
                violation_category="malformed_url",
            )

        # 1. Scheme check
        scheme = parsed.scheme.lower()
        if not scheme:
            return SSRFValidationResult(
                is_safe=False,
                url=trimmed,
                normalized_url="",
                hostname="",
                blocked_reason="Missing URL scheme. Only http:// or https:// are permitted.",
                violation_category="missing_scheme",
            )

        if scheme not in cls.ALLOWED_SCHEMES:
            return SSRFValidationResult(
                is_safe=False,
                url=trimmed,
                normalized_url="",
                hostname="",
                blocked_reason=f"Prohibited scheme '{scheme}'. Only http and https are allowed.",
                violation_category="prohibited_scheme",
            )

        # 2. Port validation with exception handling
        parsed_port: int | None = None
        try:
            parsed_port = parsed.port
        except ValueError as e:
            return SSRFValidationResult(
                is_safe=False,
                url=trimmed,
                normalized_url="",
                hostname="",
                blocked_reason=f"Invalid URL port: {e}",
                violation_category="invalid_port",
            )

        if parsed_port is not None and not (1 <= parsed_port <= 65535):
            return SSRFValidationResult(
                is_safe=False,
                url=trimmed,
                normalized_url="",
                hostname="",
                blocked_reason=f"Port {parsed_port} is outside valid range (1-65535)",
                violation_category="invalid_port",
            )

        # 3. Host check
        hostname = (parsed.hostname or "").lower().rstrip(".")
        if not hostname:
            return SSRFValidationResult(
                is_safe=False,
                url=trimmed,
                normalized_url="",
                hostname="",
                blocked_reason="URL does not contain a valid hostname.",
                violation_category="empty_host",
            )

        if parsed.username or parsed.password:
            return SSRFValidationResult(
                is_safe=False,
                url=trimmed,
                normalized_url="",
                hostname=hostname,
                port=parsed_port,
                blocked_reason="Embedded user credentials in URL are prohibited.",
                violation_category="userinfo_prohibited",
            )

        if hostname in PROHIBITED_HOSTNAMES:
            return SSRFValidationResult(
                is_safe=False,
                url=trimmed,
                normalized_url="",
                hostname=hostname,
                port=parsed_port,
                blocked_reason=f"Prohibited localhost name '{hostname}'",
                violation_category="loopback",
            )

        if hostname.endswith((".localhost", ".local", ".internal")):
            return SSRFValidationResult(
                is_safe=False,
                url=trimmed,
                normalized_url="",
                hostname=hostname,
                port=parsed_port,
                blocked_reason=f"Prohibited internal domain suffix: {hostname}",
                violation_category="internal_domain",
            )

        # 4. Check for direct IP literal (including obfuscated forms)
        direct_ip = cls._parse_obfuscated_ip(hostname)
        if direct_ip is not None:
            prohibited, reason = cls.is_prohibited_ip(direct_ip)
            if prohibited:
                r_lower = reason.lower()
                category = "metadata" if ("metadata" in r_lower or "link-local" in r_lower) else (
                    "loopback" if "loopback" in r_lower else "private_ip"
                )
                return SSRFValidationResult(
                    is_safe=False,
                    url=trimmed,
                    normalized_url="",
                    hostname=hostname,
                    resolved_ips=[str(direct_ip)],
                    port=parsed_port,
                    blocked_reason=reason,
                    violation_category=category,
                )

        # 5. DNS Resolution Check
        resolved_ips: list[str] = []
        if resolve_dns:
            target_port = parsed_port or (443 if scheme == "https" else 80)
            effective_resolver = dns_resolver if dns_resolver is not None else cls.DEFAULT_DNS_RESOLVER
            if effective_resolver is not None:
                # Custom controlled resolver provided (for tests / offline sandboxes)
                try:
                    resolved_ips = effective_resolver(hostname, target_port)
                except Exception as e:
                    return SSRFValidationResult(
                        is_safe=False,
                        url=trimmed,
                        normalized_url="",
                        hostname=hostname,
                        port=parsed_port,
                        blocked_reason=f"DNS resolution failed: {e}",
                        violation_category="dns_resolution_failure",
                    )
            else:
                try:
                    addr_info = socket.getaddrinfo(
                        hostname, target_port, socket.AF_UNSPEC, socket.SOCK_STREAM
                    )
                    for family, _, _, _, sockaddr in addr_info:
                        ip_str = sockaddr[0]
                        if ip_str not in resolved_ips:
                            resolved_ips.append(ip_str)
                except socket.gaierror as e:
                    return SSRFValidationResult(
                        is_safe=False,
                        url=trimmed,
                        normalized_url="",
                        hostname=hostname,
                        port=parsed_port,
                        blocked_reason=f"DNS resolution failed: {e}",
                        violation_category="dns_resolution_failure",
                    )
                except Exception as e:
                    return SSRFValidationResult(
                        is_safe=False,
                        url=trimmed,
                        normalized_url="",
                        hostname=hostname,
                        port=parsed_port,
                        blocked_reason=f"Host validation error: {e}",
                        violation_category="validation_error",
                    )

            if not resolved_ips:
                return SSRFValidationResult(
                    is_safe=False,
                    url=trimmed,
                    normalized_url="",
                    hostname=hostname,
                    port=parsed_port,
                    blocked_reason="DNS lookup returned no address records",
                    violation_category="dns_nxdomain",
                )

            for ip_str in resolved_ips:
                try:
                    resolved_ip_obj = ipaddress.ip_address(ip_str)
                    prohibited, reason = cls.is_prohibited_ip(resolved_ip_obj)
                    if prohibited:
                        r_lower = reason.lower()
                        category = "metadata" if ("metadata" in r_lower or "link-local" in r_lower) else (
                            "loopback" if "loopback" in r_lower else "private_ip"
                        )
                        return SSRFValidationResult(
                            is_safe=False,
                            url=trimmed,
                            normalized_url="",
                            hostname=hostname,
                            resolved_ips=resolved_ips,
                            port=parsed_port,
                            blocked_reason=f"DNS resolved to prohibited destination {ip_str}: {reason}",
                            violation_category=category,
                        )
                except ValueError:
                    continue

        # 6. IPv6 normalization with square brackets (RFC 3986 §3.2.2)
        if ":" in hostname:
            authority_host = f"[{hostname}]"
        else:
            authority_host = hostname

        default_port = 443 if scheme == "https" else 80
        if parsed_port and parsed_port != default_port:
            netloc = f"{authority_host}:{parsed_port}"
        else:
            netloc = authority_host

        path = parsed.path or "/"
        normalized = f"{scheme}://{netloc}{path}"
        if parsed.query:
            normalized = f"{normalized}?{parsed.query}"

        return SSRFValidationResult(
            is_safe=True,
            url=trimmed,
            normalized_url=normalized,
            hostname=hostname,
            resolved_ips=resolved_ips,
            port=parsed_port,
        )

    @classmethod
    def validate_redirect(
        cls,
        original_url: str,
        redirect_target: str,
        resolve_dns: bool = True,
        dns_resolver: Callable[[str, int], list[str]] | None = None,
        allow_cross_host: bool = True,
    ) -> SSRFValidationResult:
        """
        Validate an HTTP redirect destination before following it.
        Supports absolute, protocol-relative, and relative redirect URLs.
        """
        if not original_url or not isinstance(original_url, str):
            return SSRFValidationResult(
                is_safe=False,
                url=str(original_url),
                normalized_url="",
                hostname="",
                blocked_reason="Original URL cannot be empty",
                violation_category="empty_input",
            )

        if not redirect_target or not isinstance(redirect_target, str):
            return SSRFValidationResult(
                is_safe=False,
                url=str(redirect_target),
                normalized_url="",
                hostname="",
                blocked_reason="Redirect target cannot be empty",
                violation_category="empty_input",
            )

        target_trimmed = redirect_target.strip()
        if any(c in target_trimmed for c in ("\x00", "\r", "\n")):
            return SSRFValidationResult(
                is_safe=False,
                url=target_trimmed,
                normalized_url="",
                hostname="",
                blocked_reason="Redirect target contains prohibited control characters",
                violation_category="malformed_url",
            )

        combined_target = urljoin(original_url, target_trimmed)

        if not allow_cross_host:
            orig_parsed = urlparse(original_url)
            target_parsed = urlparse(combined_target)
            orig_host = (orig_parsed.hostname or "").lower()
            target_host = (target_parsed.hostname or "").lower()
            if orig_host and target_host and orig_host != target_host:
                return SSRFValidationResult(
                    is_safe=False,
                    url=combined_target,
                    normalized_url=combined_target,
                    hostname=target_host,
                    blocked_reason=f"Cross-host redirect prohibited: '{orig_host}' -> '{target_host}'.",
                    violation_category="cross_host_redirect",
                )

        resolver = dns_resolver if dns_resolver is not None else cls.DEFAULT_DNS_RESOLVER
        return cls.validate_url(combined_target, resolve_dns=resolve_dns, dns_resolver=resolver)

    @classmethod
    def get_dns_pinned_request_params(cls, validation_result: SSRFValidationResult) -> dict[str, Any]:
        """
        Helper returning connection parameters for custom HTTP clients.
        """
        if not validation_result.is_safe:
            raise ValueError(f"Cannot pin connection for unsafe URL: {validation_result.blocked_reason}")

        if not validation_result.resolved_ips:
            raise ValueError(f"No resolved IP addresses available for {validation_result.hostname}")

        pinned_ip = validation_result.resolved_ips[0]
        parsed = urlparse(validation_result.normalized_url)
        scheme = parsed.scheme
        port = validation_result.port or (443 if scheme == "https" else 80)

        host_header = validation_result.hostname
        default_port = 443 if scheme == "https" else 80
        if port != default_port:
            host_header = f"{validation_result.hostname}:{port}"

        return {
            "pinned_ip": pinned_ip,
            "sni_hostname": validation_result.hostname,
            "headers": {"Host": host_header},
            "port": port,
            "scheme": scheme,
            "target_url": validation_result.normalized_url,
        }


__version__ = "2.2.0"

# ─────────────────────────────────────────────────────────────────────────────
#  Enterprise DNS-Pinned HTTP Client with Mandatory Redirect Revalidation
# ─────────────────────────────────────────────────────────────────────────────

try:
    import urllib3
    from urllib3.connection import HTTPSConnection, HTTPConnection
    from urllib3.connectionpool import HTTPSConnectionPool, HTTPConnectionPool
    from requests.adapters import HTTPAdapter
    import requests

    class PinnedHTTPAdapter(HTTPAdapter):
        """
        urllib3/requests adapter connecting directly to a pre-validated IP address.
        Preserves original hostname for TLS SNI (server_hostname) and certificate verification.
        Supports both IPv4 and IPv6 literal destinations.
        """
        def __init__(self, pinned_ip: str, *args: Any, **kwargs: Any) -> None:
            self.pinned_ip = pinned_ip.strip("[]")
            super().__init__(*args, **kwargs)

        def init_poolmanager(self, *args: Any, **kwargs: Any) -> None:
            target_ip = self.pinned_ip

            class PinnedHTTPSConnection(HTTPSConnection):
                def _new_conn(conn_self: Any) -> socket.socket:
                    return socket.create_connection((target_ip, conn_self.port), conn_self.timeout)

            class PinnedHTTPConnection(HTTPConnection):
                def _new_conn(conn_self: Any) -> socket.socket:
                    return socket.create_connection((target_ip, conn_self.port), conn_self.timeout)

            class PinnedPoolManager(urllib3.PoolManager):
                def _new_pool(pool_self: Any, scheme: str, host: str, port: int, request_context: Any = None) -> Any:
                    if scheme == "https":
                        pool = HTTPSConnectionPool(host, port, **pool_self.connection_pool_kw)
                        pool.ConnectionCls = PinnedHTTPSConnection
                        return pool
                    else:
                        pool = HTTPConnectionPool(host, port, **pool_self.connection_pool_kw)
                        pool.ConnectionCls = PinnedHTTPConnection
                        return pool

            self.poolmanager = PinnedPoolManager(*args, **kwargs)

    class PinnedSession:
        """
        DNS-pinned HTTP session for Member 1's URL inspection engine.
        Enforces:
        1. Environment proxies disabled (session.trust_env = False) to prevent bypass.
        2. Direct TCP connection to pre-validated IP (eliminating DNS TOCTOU window).
        3. TLS SNI hostname preservation and mandatory certificate verification (verify=True).
        4. Independent preflight revalidation and IP re-pinning on every HTTP redirect.
        5. Prevention of double-DNS-resolution drift via optional validation_result or pinned_ip.
        """
        def __init__(self, max_redirects: int = 5, timeout: float = 5.0) -> None:
            self.max_redirects = max_redirects
            self.timeout = timeout

        def get(
            self,
            url: str,
            pinned_ip: Optional[str] = None,
            validation_result: Optional[SSRFValidationResult] = None,
            **kwargs: Any,
        ) -> requests.Response:
            current_url = url
            redirects_followed = 0
            current_val = validation_result
            current_pinned_ip = pinned_ip

            while True:
                # 1. Enforce SSRF preflight check if not already provided
                if current_val is None:
                    current_val = SSRFValidator.validate_url(current_url, resolve_dns=True)

                if not current_val.is_safe:
                    if redirects_followed > 0:
                        raise SSRFRedirectBlockedException(
                            f"Redirect to {current_url} blocked by SSRF policy: {current_val.blocked_reason}"
                        )
                    raise SSRFSecurityException(
                        f"URL {current_url} blocked by SSRF policy: {current_val.blocked_reason}"
                    )

                if not current_pinned_ip:
                    if not current_val.resolved_ips:
                        raise SSRFSecurityException(f"No resolved IP addresses for {current_val.hostname}")
                    current_pinned_ip = current_val.resolved_ips[0]

                # 2. Disable trust_env to prevent environment proxies from bypassing pinned IP
                session = requests.Session()
                session.trust_env = False

                parsed = urlparse(current_val.normalized_url or current_url)
                adapter = PinnedHTTPAdapter(current_pinned_ip)

                # Mount adapter across host, host:port, and entire scheme
                mount_host = f"{parsed.scheme}://{current_val.hostname}"
                session.mount(mount_host, adapter)
                if parsed.port:
                    session.mount(f"{mount_host}:{parsed.port}", adapter)
                session.mount(f"{parsed.scheme}://", adapter)

                # Enforce parameters: no auto-redirects, TLS verify=True by default
                kwargs["allow_redirects"] = False
                kwargs["timeout"] = kwargs.get("timeout", self.timeout)
                if "verify" not in kwargs:
                    kwargs["verify"] = True

                target_request_url = current_val.normalized_url or current_url
                response = session.get(target_request_url, **kwargs)

                # Attach provenance attributes to response
                response.pinned_ip = current_pinned_ip
                response.sni_hostname = current_val.hostname

                # 3. Handle HTTP redirects (301, 302, 303, 307, 308)
                if response.is_redirect and "Location" in response.headers:
                    redirect_target = response.headers["Location"]
                    redirects_followed += 1
                    if redirects_followed > self.max_redirects:
                        raise SSRFSecurityException(f"Exceeded maximum allowed redirects ({self.max_redirects})")

                    # Revalidate redirect target independently (forces new DNS resolution for new host)
                    combined = urljoin(current_url, redirect_target)
                    current_url = combined
                    current_val = None        # Force full revalidation of next hop
                    current_pinned_ip = None  # Force new IP pinning for next hop
                    continue

                return response

except ImportError:
    # Requests / urllib3 not available; custom adapter omitted
    pass
