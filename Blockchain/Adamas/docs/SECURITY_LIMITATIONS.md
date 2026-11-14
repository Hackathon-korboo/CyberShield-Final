# CyberShield AI 2.0 — Security & Cryptographic Limitations (v2.1)

**Author:** Member 3 (Security Engineering, Cryptography & Blockchain)  
**Deliverable:** Clearly Documented Security Limitations & Operational Boundaries  
**Scope:** Hackathon Prototype & Operational Deployment Boundaries  

---

## 1. Cryptographic Hashing Limitations

### 1.1 What Cryptographic Fingerprinting Proves
- **Data Integrity:** A cryptographic hash (SHA-256 or Keccak-256) mathematically proves that the serialized canonical report bytes have **not been altered, truncated, or tampered with** since the fingerprint was computed.
- **Tamper Evidence:** Any modification to a risk classification, indicator list, timestamp, or score will produce an entirely different digest, resulting in verification status `failed`.

### 1.2 What Cryptographic Fingerprinting DOES NOT Prove
- **Veracity / Ground Truth:** A cryptographic hash **never proves that the underlying report is true or accurate**. If the URL inspection engine or threat intelligence feed ingested incorrect data, the hash simply guarantees the integrity of that flawed data.
- **Safety of the External Website:** A verified report hash does **not** prove that a target website is safe. Attackers can deploy benign landing pages that later switch to phishing payloads (cloaking/watering hole attacks).
- **Legitimacy of Domain Ownership:** Hashing does not prove who registered or owns the external target domain.

---

## 2. SSRF & Network Inspection Limitations

### 2.1 DNS Time-of-Check to Time-of-Use (TOCTOU) & DNS Rebinding
- **Vulnerability Description:** If a domain is configured with a 0-second DNS TTL and utilizes DNS rebinding techniques, the preflight DNS query may return a legitimate public IP (`93.184.216.34`), but the subsequent HTTP request by the inspection client may re-resolve to `127.0.0.1`.
- **Operational Mitigation in CyberShield (Bug 4 Resolution):**
  - `SSRFValidator.get_dns_pinned_request_params(validation_result)` provides the exact pre-validated IP address to pin the outgoing TCP socket to.
  - Member 1's backend HTTP client must connect directly to the pinned IP while setting the `Host: <domain>` header and TLS SNI `server_hostname = <domain>`.
  - Every redirect destination must be revalidated via `SSRFValidator.validate_redirect()` before following.

### 2.2 Client-Side JavaScript & DOM Execution
- CyberShield performs **non-intrusive static and network-level inspection** (TLS certificates, HTTP security headers, DNS records, and URL lexical patterns).
- It deliberately does **not execute client-side JavaScript** or load heavy headless browser engines. Consequently, sophisticated JavaScript-based redirects (`window.location = "http://internal"`) or delayed client-side DOM cloaking will not be followed by the backend scanner.

### 2.3 IPv6 Transition & Tunneling Mechanisms
- Complex IPv6 tunneling mechanisms (such as 6to4, Teredo, or NAT64) can encapsulate IPv4 packets.
- `SSRFValidator` explicitly unwraps standard IPv4-mapped IPv6 addresses (`::ffff:0:0/96`) and blocks `64:ff9b::/96`, `fe80::/10`, and `fc00::/7`. However, proprietary tunnel interfaces on custom OS networks must be filtered at the OS firewall/VPC egress level.

---

## 3. Blockchain & Decentralized Trust Limitations

### 3.1 Immutability of False Positives
- Once a report fingerprint is anchored to the Ethereum/Hardhat blockchain, the transaction and mapping are **permanent and irreversible**.
- If a report is later audited and determined to be a false positive, the existing block cannot be edited or deleted. Rectification must be handled by publishing a new updated report with status `false_positive` referencing the original report ID.

### 3.2 Offline Fallback vs. On-Chain Anchoring
- When the blockchain node is unreachable or the contract is not deployed, the system gracefully falls back to **off-chain local cryptographic integrity**.
- **Transparency Mandate:** The system explicitly returns `blockchain_network: "off-chain (local cryptographic proof)"` and `is_on_chain: false`. It **never fakes an on-chain transaction hash, block number, or deployment address**.
- Local SHA-256 integrity verification confirms data integrity off-chain, and is never conflated with on-chain consensus.

### 3.3 Private Key Custody & Signer Security (Bug 5 Resolution)
- On local development chains (`Chain ID 31337` / `1337`), the adapter permits using unlocked development accounts with an explicit warning.
- On any external/production chain (`Sepolia`, `Mainnet`, etc.), the adapter **strictly refuses unlocked node accounts** and requires an explicitly configured signer / private key.
- Storing private keys in plain environment variables is unacceptable for production; key custody must migrate to an enterprise KMS (AWS KMS, GCP Cloud KMS, or HashiCorp Vault) or an EIP-4337 Account Abstraction paymaster.
