"""Server-Side Request Forgery (SSRF) Guard Engine.

Provides strict preflight destination verification, defensive DNS inspection,
private IP filtering, cloud metadata blocking, and port restrictions.
"""

from dataclasses import dataclass, field
import ipaddress
import re
import socket
from typing import List, Optional, Set
import urllib.parse

from backend.app.core.exceptions import SSRFProtectionError
from backend.app.utils.sanitizer import normalize_target_url

# Standard web ports permitted for outbound inspection
ALLOWED_PORTS: Set[int] = {80, 443, 8080, 8443, 8000, 3000, 5000}

# Cloud metadata addresses and special internal hostnames
BLOCKED_HOSTNAMES: Set[str] = {
    "localhost",
    "metadata.google.internal",
    "metadata.internal",
    "instance-data",
}

CLOUD_METADATA_IPS: Set[str] = {
    "169.254.169.254",
    "169.254.169.253",
    "100.100.100.200",  # Alibaba cloud metadata
    "fd00:ec2::254",     # AWS IPv6 metadata
}


@dataclass
class SSRFValidationResult:
    """Outcome of SSRF preflight evaluation."""

    is_safe: bool
    normalized_url: str
    scheme: str
    hostname: str
    port: int
    resolved_ips: List[str] = field(default_factory=list)
    blocked_reason: Optional[str] = None


class SSRFGuard:
    """Defensive preflight URL validator preventing SSRF and internal service enumeration."""

    @staticmethod
    def is_ip_private_or_restricted(ip_str: str) -> bool:
        """Check if an IP address belongs to loopback, private, link-local, or metadata ranges."""
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            return True  # Malformed IP string is treated as unsafe

        # Check IPv4-mapped IPv6 address (e.g. ::ffff:127.0.0.1)
        if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped:
            ip_obj = ip_obj.ipv4_mapped

        # Check cloud metadata explicit addresses
        if str(ip_obj) in CLOUD_METADATA_IPS:
            return True

        # Check standard address categories
        if (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_multicast
            or ip_obj.is_reserved
            or ip_obj.is_unspecified
        ):
            return True

        return False

    def validate_url(self, raw_url: str, raise_exception: bool = False) -> SSRFValidationResult:
        """Perform comprehensive SSRF preflight validation on an inbound URL.
        
        Args:
            raw_url: Submitted URL.
            raise_exception: If True, raises SSRFProtectionError on unsafe destinations.
            
        Returns:
            SSRFValidationResult containing inspection details and verdict.
        """
        # Step 1: Normalize URL syntax and scheme
        try:
            normalized = normalize_target_url(raw_url)
        except ValueError as err:
            reason = f"Malformed or invalid URL: {err}"
            if raise_exception:
                raise SSRFProtectionError(reason)
            return SSRFValidationResult(
                is_safe=False,
                normalized_url=raw_url,
                scheme="",
                hostname="",
                port=0,
                blocked_reason=reason,
            )

        parsed = urllib.parse.urlsplit(normalized)
        scheme = parsed.scheme.lower()
        hostname = (parsed.hostname or "").lower()
        port = parsed.port or (443 if scheme == "https" else 80)

        # Step 2: Validate Scheme
        if scheme not in ("http", "https"):
            reason = f"Unsupported scheme '{scheme}'. Only http and https are permitted."
            if raise_exception:
                raise SSRFProtectionError(reason)
            return SSRFValidationResult(
                is_safe=False,
                normalized_url=normalized,
                scheme=scheme,
                hostname=hostname,
                port=port,
                blocked_reason=reason,
            )

        # Step 3: Validate Port
        if port not in ALLOWED_PORTS:
            reason = f"Target port {port} is restricted by security policy."
            if raise_exception:
                raise SSRFProtectionError(reason)
            return SSRFValidationResult(
                is_safe=False,
                normalized_url=normalized,
                scheme=scheme,
                hostname=hostname,
                port=port,
                blocked_reason=reason,
            )

        # Step 4: Check blocked hostnames
        if hostname in BLOCKED_HOSTNAMES or hostname.endswith(".local") or hostname.endswith(".internal"):
            reason = f"Hostname '{hostname}' resolves to an internal or restricted namespace."
            if raise_exception:
                raise SSRFProtectionError(reason)
            return SSRFValidationResult(
                is_safe=False,
                normalized_url=normalized,
                scheme=scheme,
                hostname=hostname,
                port=port,
                blocked_reason=reason,
            )

        # Step 5: Check if hostname is direct IP literal
        try:
            ip_literal = ipaddress.ip_address(hostname)
            if self.is_ip_private_or_restricted(str(ip_literal)):
                reason = f"Target IP '{hostname}' belongs to a private, loopback, or metadata network."
                if raise_exception:
                    raise SSRFProtectionError(reason)
                return SSRFValidationResult(
                    is_safe=False,
                    normalized_url=normalized,
                    scheme=scheme,
                    hostname=hostname,
                    port=port,
                    resolved_ips=[str(ip_literal)],
                    blocked_reason=reason,
                )
            return SSRFValidationResult(
                is_safe=True,
                normalized_url=normalized,
                scheme=scheme,
                hostname=hostname,
                port=port,
                resolved_ips=[str(ip_literal)],
            )
        except ValueError:
            pass  # Hostname is a domain name, proceed to DNS resolution

        # Step 6: Safe DNS Resolution
        resolved_ips: List[str] = []
        try:
            addr_info = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
            for item in addr_info:
                sockaddr = item[4]
                ip_addr = sockaddr[0]
                if ip_addr not in resolved_ips:
                    resolved_ips.append(ip_addr)
        except (socket.gaierror, OSError) as err:
            reason = f"DNS resolution failed for hostname '{hostname}': {err}"
            if raise_exception:
                raise SSRFProtectionError(reason)
            return SSRFValidationResult(
                is_safe=False,
                normalized_url=normalized,
                scheme=scheme,
                hostname=hostname,
                port=port,
                blocked_reason=reason,
            )

        if not resolved_ips:
            reason = f"No IP addresses resolved for hostname '{hostname}'."
            if raise_exception:
                raise SSRFProtectionError(reason)
            return SSRFValidationResult(
                is_safe=False,
                normalized_url=normalized,
                scheme=scheme,
                hostname=hostname,
                port=port,
                blocked_reason=reason,
            )

        # Step 7: Inspect all resolved IPs for private or restricted ranges
        for ip in resolved_ips:
            if self.is_ip_private_or_restricted(ip):
                reason = f"Hostname '{hostname}' resolved to restricted IP address: {ip}."
                if raise_exception:
                    raise SSRFProtectionError(reason)
                return SSRFValidationResult(
                    is_safe=False,
                    normalized_url=normalized,
                    scheme=scheme,
                    hostname=hostname,
                    port=port,
                    resolved_ips=resolved_ips,
                    blocked_reason=reason,
                )

        return SSRFValidationResult(
            is_safe=True,
            normalized_url=normalized,
            scheme=scheme,
            hostname=hostname,
            port=port,
            resolved_ips=resolved_ips,
            blocked_reason=None,
        )

    def validate_redirect(
        self,
        original_url: str,
        redirect_target: str,
        raise_exception: bool = False,
        allow_cross_host: bool = True,
    ) -> SSRFValidationResult:
        """Validate an HTTP redirect target against original URL.

        Supports relative, protocol-relative, and absolute redirects.
        """
        if not original_url or not isinstance(original_url, str):
            reason = "Original URL cannot be empty."
            if raise_exception:
                raise SSRFProtectionError(reason)
            return SSRFValidationResult(
                is_safe=False,
                normalized_url="",
                scheme="",
                hostname="",
                port=0,
                blocked_reason=reason,
            )

        if not redirect_target or not isinstance(redirect_target, str):
            reason = "Redirect target cannot be empty."
            if raise_exception:
                raise SSRFProtectionError(reason)
            return SSRFValidationResult(
                is_safe=False,
                normalized_url="",
                scheme="",
                hostname="",
                port=0,
                blocked_reason=reason,
            )

        target_trimmed = redirect_target.strip()
        if any(c in target_trimmed for c in ("\x00", "\r", "\n")):
            reason = "Redirect target contains prohibited control characters."
            if raise_exception:
                raise SSRFProtectionError(reason)
            return SSRFValidationResult(
                is_safe=False,
                normalized_url=target_trimmed,
                scheme="",
                hostname="",
                port=0,
                blocked_reason=reason,
            )

        combined = urllib.parse.urljoin(original_url, target_trimmed)

        if not allow_cross_host:
            orig_parsed = urllib.parse.urlsplit(original_url)
            target_parsed = urllib.parse.urlsplit(combined)
            orig_host = (orig_parsed.hostname or "").lower()
            target_host = (target_parsed.hostname or "").lower()
            if orig_host and target_host and orig_host != target_host:
                reason = f"Cross-host redirect prohibited: '{orig_host}' -> '{target_host}'."
                if raise_exception:
                    raise SSRFProtectionError(reason)
                return SSRFValidationResult(
                    is_safe=False,
                    normalized_url=combined,
                    scheme=target_parsed.scheme,
                    hostname=target_host,
                    port=0,
                    blocked_reason=reason,
                )

        return self.validate_url(combined, raise_exception=raise_exception)


def validate_redirect(
    original_url: str,
    redirect_target: str,
    resolve_dns: bool = True,
    dns_resolver=None,
    allow_cross_host: bool = True,
):
    """Helper wrapping redirect validation returning (is_valid, resolved_url, error_message)."""
    try:
        from Blockchain.Adamas.security.ssrf_validator import SSRFValidator
        res = SSRFValidator.validate_redirect(
            original_url=original_url,
            redirect_target=redirect_target,
            resolve_dns=resolve_dns,
            dns_resolver=dns_resolver,
            allow_cross_host=allow_cross_host,
        )
        return res.is_safe, res.normalized_url or res.url, res.blocked_reason or ""
    except ImportError:
        # Fallback to internal guard
        guard = SSRFGuard()
        res = guard.validate_redirect(original_url, redirect_target, allow_cross_host=allow_cross_host)
        return res.is_safe, res.normalized_url, res.blocked_reason or ""


