# PART 08: SSRF PROTECTION AND SAFE URL HANDLING — IMPLEMENTATION DETAILS

## 1. Work Performed
1. Constructed `SSRFGuard` engine in `backend/app/engines/ssrf_guard.py` with multi-tier validation:
   - URL scheme checking (strictly http/https).
   - Port whitelist enforcement (permitting web ports 80, 443, 8080, 8443, 8000, 3000, 5000; rejecting infrastructure ports).
   - Hostname restriction against `localhost`, `metadata.google.internal`, `.local`, and `.internal`.
   - Direct IP inspection with detection of private RFC 1918, loopback, link-local, multicast, reserved, and cloud metadata IPs (`169.254.169.254`, `169.254.169.253`, `fd00:ec2::254`).
   - IPv4-mapped IPv6 address unmasking (`::ffff:x.x.x.x`).
   - Comprehensive DNS preflight resolving via `socket.getaddrinfo()`. All returned IP records are verified; if any resolved IP is restricted, the domain fails closed.
2. Exported `SSRFGuard` and `SSRFValidationResult` in `backend/app/engines/__init__.py`.
3. Created 10 unit tests in `backend/tests/test_ssrf.py` testing IPv4 loopbacks, private subnets, cloud metadata, IPv6 loopbacks, IPv4-mapped IPv6, dual-record DNS, restricted ports, and legitimate public IPs.
4. Executed full test suite (45 tests passed).

## 2. Technical Decisions
- **Decision 1: Fail-Closed Multi-Record DNS:** Even if 9 out of 10 A records are public, if a single record is a private IP, the entire request is blocked to prevent DNS rebinding attacks.
- **Decision 2: Square Brackets for IPv6 Netloc:** Updated URL normalizer to ensure IPv6 literals are preserved in RFC 3986 square brackets (`[::1]`) during reconstruction.
- **Decision 3: Preflight Protection Without Outbound Fetch:** Validates destination safety before any network requests are dispatched.
