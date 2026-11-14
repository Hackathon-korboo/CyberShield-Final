"""Comprehensive unit tests for SSRFGuard."""

from unittest.mock import patch
import pytest

from backend.app.core.exceptions import SSRFProtectionError
from backend.app.engines.ssrf_guard import SSRFGuard


@pytest.fixture
def ssrf_guard() -> SSRFGuard:
    """Fixture providing an instance of SSRFGuard."""
    return SSRFGuard()


def test_ssrf_rejects_loopback_ipv4(ssrf_guard: SSRFGuard):
    """Verify 127.0.0.1 and loopback IPs are blocked."""
    res = ssrf_guard.validate_url("http://127.0.0.1/admin")
    assert res.is_safe is False
    assert "private, loopback, or metadata" in res.blocked_reason


def test_ssrf_rejects_localhost_hostname(ssrf_guard: SSRFGuard):
    """Verify localhost is blocked."""
    res = ssrf_guard.validate_url("http://localhost:8000/")
    assert res.is_safe is False
    assert "internal or restricted namespace" in res.blocked_reason


def test_ssrf_rejects_private_subnets(ssrf_guard: SSRFGuard):
    """Verify RFC 1918 private subnets are blocked."""
    for ip in ["10.0.1.5", "192.168.0.1", "172.16.0.10", "172.31.255.254"]:
        res = ssrf_guard.validate_url(f"http://{ip}/api")
        assert res.is_safe is False, f"Expected {ip} to be rejected"


def test_ssrf_rejects_cloud_metadata(ssrf_guard: SSRFGuard):
    """Verify cloud metadata endpoints (169.254.169.254) are strictly blocked."""
    res = ssrf_guard.validate_url("http://169.254.169.254/latest/meta-data/")
    assert res.is_safe is False
    assert "private, loopback, or metadata" in res.blocked_reason


def test_ssrf_rejects_ipv6_loopback_and_link_local(ssrf_guard: SSRFGuard):
    """Verify IPv6 loopback [::1] and link-local [fe80::1] are blocked."""
    res_loopback = ssrf_guard.validate_url("http://[::1]/")
    assert res_loopback.is_safe is False

    res_link_local = ssrf_guard.validate_url("http://[fe80::1]/")
    assert res_link_local.is_safe is False


def test_ssrf_rejects_ipv4_mapped_ipv6(ssrf_guard: SSRFGuard):
    """Verify IPv4-mapped IPv6 loopback is rejected."""
    assert ssrf_guard.is_ip_private_or_restricted("::ffff:127.0.0.1") is True
    assert ssrf_guard.is_ip_private_or_restricted("::ffff:192.168.1.1") is True


def test_ssrf_rejects_restricted_ports(ssrf_guard: SSRFGuard):
    """Verify infrastructure ports like 22 (SSH) and 6379 (Redis) are rejected."""
    res_ssh = ssrf_guard.validate_url("http://example.com:22/")
    assert res_ssh.is_safe is False
    assert "restricted by security policy" in res_ssh.blocked_reason

    res_redis = ssrf_guard.validate_url("http://example.com:6379/")
    assert res_redis.is_safe is False


def test_ssrf_permits_public_ip(ssrf_guard: SSRFGuard):
    """Verify legitimate public IP addresses pass preflight."""
    res = ssrf_guard.validate_url("http://93.184.216.34/")
    assert res.is_safe is True
    assert res.blocked_reason is None


def test_ssrf_blocks_dual_homed_dns(ssrf_guard: SSRFGuard):
    """Verify that if a domain resolves to both public and private IPs, it is blocked."""
    mock_addrinfo = [
        (2, 1, 6, "", ("93.184.216.34", 80)),
        (2, 1, 6, "", ("192.168.1.1", 80)),
    ]
    with patch("socket.getaddrinfo", return_value=mock_addrinfo):
        res = ssrf_guard.validate_url("http://dual-record.attacker.com/")
        assert res.is_safe is False
        assert "resolved to restricted IP address" in res.blocked_reason


def test_ssrf_raises_exception_when_requested(ssrf_guard: SSRFGuard):
    """Verify raise_exception=True triggers SSRFProtectionError."""
    with pytest.raises(SSRFProtectionError):
        ssrf_guard.validate_url("http://127.0.0.1/admin", raise_exception=True)
