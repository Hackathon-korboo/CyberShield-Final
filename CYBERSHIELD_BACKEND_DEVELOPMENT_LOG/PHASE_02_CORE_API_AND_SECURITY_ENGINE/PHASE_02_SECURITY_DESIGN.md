# CYBERSHIELD AI 2.0 — PHASE 02 SECURITY DESIGN SPECIFICATION

**Document Version:** 2.0.0  
**Phase:** 02 — Core API and Security Engine  
**Status:** Approved for Implementation  
**Architect:** Senior Backend Engineer & Application Security Engineer  

---

## 1. Threat Model & Security Objectives

Phase 02 introduces active input validation and security evaluation for untrusted inputs submitted by clients.

### 1.1 Inbound Threats Considered
1. **Server-Side Request Forgery (SSRF):** Attacker submits target URLs pointing to internal services, loopback interfaces (`127.0.0.1`, `::1`), private intranets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local IPs (`169.254.0.0/16`), or cloud instance metadata services (`169.254.169.254`, `metadata.google.internal`).
2. **DNS Rebinding & Multi-IP Evasion:** Attacker points hostname to dual records (one public, one private) or changes DNS records during redirects.
3. **Punycode / Homoglyph Spoofing:** Attacker uses lookalike Cyrillic/Greek characters (e.g., `раураl.com` with Cyrillic 'а') to impersonate legitimate domains.
4. **Denial of Service (DoS) via Payload Inflation:** Attacker sends massive payloads (>10MB) or deeply nested data to starve CPU/memory.
5. **Credential / Sensitive Data Leakage in Logs:** Attacker submits sensitive content; logs must redact raw tokens, passwords, and sensitive keys.

---

## 2. SSRF Protection Architecture (Part 08)

### 2.1 Defense-in-Depth Preflight Validation
Before any network operation or URL inspection:
1. **Scheme Whitelist:** Strictly allow `http` and `https`. Block all other schemes (`file`, `gopher`, `ftp`, `ldap`, `dict`, `data`).
2. **Port Restrictions:** Permit standard web ports (80, 443, 8080, 8443). Block restricted ports (e.g. 22 SSH, 25 SMTP, 6379 Redis, 27017 Mongo, 2375 Docker).
3. **Safe DNS Resolution:** Resolve hostname using system resolver. Inspect **all** returned IP addresses.
4. **IP Blacklist Evaluation:** Reject if any resolved IP falls into:
   - `0.0.0.0/8` (Current network)
   - `10.0.0.0/8` (Private network RFC 1918)
   - `127.0.0.0/8` (Loopback)
   - `169.254.0.0/16` (Link-local / Cloud metadata)
   - `172.16.0.0/12` (Private network RFC 1918)
   - `192.0.0.0/24` (IETF Protocol Assignments)
   - `192.168.0.0/16` (Private network RFC 1918)
   - `198.18.0.0/15` (Benchmarking)
   - `::1/128` (IPv6 Loopback)
   - `fc00::/7` (IPv6 Unique Local)
   - `fe80::/10` (IPv6 Link-local)
   - `::ffff:0:0/96` (IPv4-mapped IPv6 representing private IPv4s)

### 2.2 Preflight Mode (No Unrestricted Outbound Requests)
In Phase 02, URL analysis operates primarily via **safe preflight analysis** without unrestricted outbound network connections. If destination verification fails or resolves to an unsafe IP, the request fails closed immediately with `SSRFProtectionError`.

---

## 3. Deterministic Heuristic Engine Architecture (Part 09)

The rules engine evaluates inputs against pure deterministic rules without external blackbox dependencies:
1. **URL Rules (`RULE-URL-*`):**
   - Direct IP as hostname (`http://192.0.2.1/login`)
   - Punycode / Homoglyph lookalikes (`xn--...`)
   - Suspicious brand keyword concatenation (`paypal-security-update.com`)
   - Excessive subdomain depth (> 4 subdomains)
   - High entropy or random string hostnames
2. **Email Rules (`RULE-EML-*`):**
   - High-urgency social engineering triggers ("Account suspended within 24 hours")
   - Suspicious sender mismatch (display name claims Bank, domain is generic free mail)
   - Credential harvesting links
   - Urgent payment requests with cryptocurrency addresses or gift cards
3. **SMS Rules (`RULE-SMS-*`):**
   - Explicit OTP / PIN requests ("Share your 6-digit verification code")
   - Banking card blockage alerts with shortened URLs
   - Work-from-home lottery / part-time job fraud lures ("Earn $500/day clicking links")

---

## 4. Evidence Integrity & Separation
Every rule match generates a structured finding:
- `rule_id`: Unique identifier (e.g., `RULE-SMS-001`)
- `category`: Category enum (e.g., `OTP_HARVESTING`)
- `severity`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- `evidence`: Exact substring or parsed token that triggered the rule
- `explanation`: Clear reason why the indicator is suspicious
- `mitigation`: Concrete defense advice for the user

*Rule 13 strictly enforced:* Finding indicators never declares an input "confirmed fraudulent"; it classifies risk into transparent categories (`CLEAN`, `LOW_RISK`, `SUSPICIOUS`, `HIGH_RISK`).
