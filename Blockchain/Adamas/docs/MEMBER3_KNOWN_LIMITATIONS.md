# CyberShield AI 2.0 — Member 3 Known Limitations & Security Boundaries (v2.2)

**Author:** Member 3 (Security Engineering, Cryptography & Blockchain)  
**Date:** November 14, 2026  
**Audience:** Core Engineering Team & Hackathon Evaluators  
**Decision Status:** 🟡 **B. READY WITH DOCUMENTED LIMITATIONS**  

---

## 1. Cryptographic Hashing: Data Integrity vs. Ground Truth

An essential distinction in information security is the difference between **data integrity** and **semantic truth**:

### 1.1 What Cryptographic Hashing Proves
* **Tamper-Evidence:** A cryptographic hash (SHA-256 or Keccak-256) mathematically proves that the serialized report bytes have not been modified, replaced, truncated, or tampered with since the digest was computed.
* **Deterministic Verification:** Any client or independent auditor possessing the report and the original hash can independently recalculate the digest and prove bit-level authenticity.

### 1.2 What Cryptographic Hashing DOES NOT Prove
* **Ground Truth / Accuracy:** A cryptographic digest does **not** prove that the threat intelligence, risk score, or URL analysis inside the report is true or correct. If an upstream detector produced a false positive or hallucinated an indicator, the hash merely guarantees the integrity of that incorrect assessment.
* **Target Website Safety:** A verified report hash does not guarantee that the target website is harmless. Attackers can alter their web server behavior post-scan (e.g. cloaking, delayed payload delivery, or DNS switching).
* **Domain Ownership:** Hashing does not verify domain ownership or certificate provenance; it only fingerprints CyberShield's analysis record.

---

## 2. SSRF, DNS TOCTOU & Outbound Inspection

### 2.1 The DNS Time-of-Check to Time-of-Use (TOCTOU) Window & PinnedSession
* **The Problem:** In standard web clients, performing a DNS lookup to validate an IP (`Time of Check`), followed by an HTTP request using the hostname, triggers a second DNS resolution (`Time of Use`). An attacker running an authoritative DNS server with a 0-second TTL can switch from a public IP to `127.0.0.1` on the second query (DNS Rebinding).
* **CyberShield's Mitigation:** `PinnedHTTPAdapter` and `PinnedSession` override socket creation in `urllib3` to establish the TCP connection directly to the pre-validated IP address, eliminating the second DNS lookup while properly sending the domain name in the HTTP `Host` header and TLS SNI.
* **Double-DNS Resolution Elimination:** `PinnedSession.get(url, validation_result=val)` accepts the pre-computed validation result, ensuring zero redundant DNS lookups and binding `response.pinned_ip = pinned_ip`.
* **Proxy Bypass Mitigation:** By default, `requests.Session` respects `HTTP_PROXY` and `HTTPS_PROXY` environment variables, which can redirect traffic away from the pinned IP to a local proxy. `PinnedSession` sets `trust_env = False` to prevent environment proxy hijacking.
* **Redirect Revalidation:** If an external target website responds with an HTTP 302 redirect pointing to an internal IP or another domain, `PinnedSession` intercepts the `Location` header, runs full SSRF preflight validation on the target, and blocks prohibited destinations.

### 2.2 Client-Side JavaScript & Dynamic Execution
* CyberShield focuses on fast, non-intrusive static and network-layer inspection (HTTP status, headers, certificates, DNS records, lexical patterns).
* It deliberately does **not** execute a headless browser (such as Chromium or Puppeteer) or run client-side JavaScript.
* **Limitation:** Obfuscated JavaScript redirects (e.g., `window.location = "http://169.254.169.254"`) or single-page application (SPA) payloads loaded dynamically via client-side fetch after page load will not be executed or inspected by this module.

### 2.3 IPv6 Tunneling & Complex Transitions
* `SSRFValidator` identifies standard IPv4-mapped IPv6 addresses (`::ffff:0:0/96`), 6to4 (`2002::/16`), Teredo (`2001::/32`), NAT64 (`64:ff9b::/96`), and link-local (`fe80::/10`).
* **Limitation:** In complex enterprise networks with proprietary overlay VPNs, site-to-site GRE tunnels, or software-defined networking (SDN) routing policies, application-layer filtering should be backed by network-level VPC egress rules and firewalls.

---

## 3. Blockchain & Smart Contract Boundaries

### 3.1 Immutability of False Positives
* Once a report hash is registered on the Ethereum / EVM blockchain via `registerReport`, the record in `threatReports[reportId]` is **permanent and immutable**.
* If a security team later audits an incident and determines a URL was falsely classified as malicious, the smart contract record cannot be deleted or overwritten (due to the `reportAlreadyRegistered` guard).
* **Resolution Strategy:** Rectification must be handled by registering a new report with status `false_positive` or `rectified` referencing the original `report_id`.

### 3.2 Network Dependency & Gas Economics
* On a public network (e.g. Ethereum Mainnet or Sepolia), transactions incur gas fees and require block mining latency (12–15 seconds on Ethereum).
* In high-throughput threat scanning environments (e.g. thousands of URLs per minute), anchoring every report directly to an L1 blockchain is economically impractical.
* **Production Recommendation:** For production scale, report hashes should be aggregated into a cryptographic Merkle Tree (e.g., once every hour or every 1,000 reports), anchoring only the Merkle Root on-chain.

### 3.3 Private Key Custody
* For local development and demonstration (`Chain ID 31337`), the adapter permits using unlocked local accounts.
* For external networks (e.g. Sepolia), the adapter enforces the presence of an explicitly configured private key.
* **Limitation:** Storing raw private keys in environment variables is suitable for hackathons, but unsuitable for production. Production deployments must integrate with Key Management Services (AWS KMS, GCP Cloud KMS, HashiCorp Vault) or utilize EIP-4337 Account Abstraction paymasters.

### 3.4 Honest Off-Chain Fallback Mode
* When the blockchain RPC node is unreachable or the contract address is not configured, `BlockchainAdapter` operates in local fallback mode.
* It computes the report ID and Keccak-256 hash locally and performs SHA-256 tamper verification.
* **Transparency Guarantee:** The system explicitly returns `is_on_chain: false` and `blockchain_network: "off-chain (local cryptographic proof)"`. It never generates pseudo-transaction hashes or claims on-chain confirmation when running offline.

---

## 4. Integration Boundaries with Other Members

### 4.1 Member 1 (FastAPI Backend) Integration Boundary
* **Status:** Ready with drop-in snippets; Member 1's full backend repository is external to workspace `E:/Adamas`.
* **Async Event Loop Rule:** Because network I/O (`requests` / socket connection) is synchronous, Member 1 must execute `scanner_session.get` either in standard synchronous `def` endpoints (FastAPI thread-pool) or via `await asyncio.to_thread(...)` inside `async def` endpoints.
* **Schema Contract:** Member 1's backend response must contain `{"integrity": {"status": "verified" | "failed" | "not_available", "evidence_hash": "<64-hex>"}}`. Tested and validated with Pydantic v2.

### 4.2 Member 4 (React Frontend) Integration Boundary
* **Status:** Ready with TypeScript type definitions and CSS styling rules; Member 4's frontend UI application is external to workspace `E:/Adamas`.
* **Visual Rendering:** UI must conditionally render a green verified badge, red tamper warning, or gray unavailable pill based on `integrity.status`.
