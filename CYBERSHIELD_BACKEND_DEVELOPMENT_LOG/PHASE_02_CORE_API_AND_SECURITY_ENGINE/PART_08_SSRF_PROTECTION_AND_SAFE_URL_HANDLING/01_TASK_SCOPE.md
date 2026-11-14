# PART 08: SSRF PROTECTION AND SAFE URL HANDLING — TASK SCOPE

## 1. Goal & Objective
Implement a critical, defense-in-depth Server-Side Request Forgery (SSRF) preflight security guard in `backend/app/engines/ssrf_guard.py` to prevent access to private intranets, loopback interfaces, cloud metadata endpoints, and DNS rebinding attacks.

## 2. In-Scope Tasks
1. Build `SSRFGuard` engine:
   - Validate URL schemes (only `http` and `https` permitted).
   - Validate destination ports (default 80, 443; safe list).
   - Detect direct IP addresses in hostnames (IPv4, IPv6, hex, octal, decimal, IPv4-mapped IPv6).
   - Resolve DNS hostnames safely and inspect all returned A and AAAA records.
   - Match all resolved IPs against complete private/reserved IP blocks (RFC 1918, RFC 3927 link-local, RFC 5737, loopback `127.0.0.0/8`, `::1`, cloud metadata `169.254.169.254`).
   - Block dual-homed DNS records (hostnames resolving to both public and private IPs).
2. Fail-closed architecture: Any resolution failure, timeout, or private IP presence raises `SSRFProtectionError`.
3. Unit tests with mocked DNS fixtures covering all public and private IP ranges.

## 3. Out-of-Scope Tasks
- Performing unrestricted live network requests.
- Sending authentication tokens or headers to untrusted endpoints.

## 4. Acceptance Criteria
- 100% of tested private IPs (127.0.0.1, 10.x, 192.168.x, 172.16.x, 169.254.x, ::1) are blocked.
- Legitimate public domains and IPs are classified as SSRF safe.
- Rebinding and dual-record vulnerabilities are detected and rejected.
