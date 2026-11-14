# CYBERSHIELD AI 2.0 — DATABASE INTEGRATION REPORT
## Persistence Architecture, SQLite Repository & Unified Schema Integrity

**Project:** CyberShield AI 2.0  
**Database Path:** `backend/cybershield.db`  
**Execution Timestamp:** 2026-11-14T15:24:00+05:30  
**Database Status:** `OPERATIONAL — ZERO_DUPLICATION`  

---

## 1. PERSISTENCE ARCHITECTURE

CyberShield AI 2.0 enforces a **Single Database Architecture**:

- **Database Engine:** SQLite 3 via SQLAlchemy async engine / sessionmaker.
- **Authoritative Database File:** `backend/cybershield.db`.
- **Primary Repository:** `backend/app/db/repository.py` (`ReportRepository`).
- **Data Safety:** Zero duplicate database files were created. Member 2's components operate statelessly or interface with Member 1's persistence layer, preventing split-brain states.

---

## 2. SCHEMA TABLES & STRUCTURE

The database persists scan records and tamper-evident threat reports:

### Table: `scans`
- `id` (INTEGER, Primary Key, Autoincrement)
- `scan_id` (VARCHAR(64), Unique, Indexed)
- `target` (TEXT, Sanitized input target or URL)
- `target_type` (VARCHAR(16), 'url', 'email', 'sms', 'text', 'file')
- `classification` (VARCHAR(32), 'BENIGN', 'SUSPICIOUS', 'CONFIRMED_MALICIOUS', 'SECURITY_POLICY_VIOLATION')
- `risk_score` (INTEGER, 0 to 100)
- `has_policy_violation` (BOOLEAN, SSRF or security policy flag)
- `status` (VARCHAR(16), 'COMPLETED', 'FAILED')
- `created_at` (DATETIME, UTC timestamp)

### Table: `unified_reports`
- `id` (INTEGER, Primary Key, Autoincrement)
- `scan_id` (VARCHAR(64), Foreign Key -> scans.scan_id, Indexed)
- `report_id` (VARCHAR(64), Unique, Indexed)
- `canonical_sha256` (VARCHAR(64), Deterministic RFC 8785 fingerprint)
- `keccak256_hash` (VARCHAR(66), 0x-prefixed Ethereum hash)
- `blockchain_status` (VARCHAR(32), 'NOT_REGISTERED', 'REGISTERED', 'FAILED')
- `transaction_hash` (VARCHAR(66), Nullable)
- `report_json` (TEXT, Complete serialized UnifiedThreatReport JSON)
- `created_at` (DATETIME, UTC timestamp)

---

## 3. DATA INTEGRITY & AUDIT VERIFICATION

1. **Auto-Initialization:** Database schema initializes automatically on application startup via `init_db()` in `backend/app/db/session.py`.
2. **Transaction Atomicity:** Scans and corresponding Unified Threat Reports are saved in atomic transactions.
3. **No Secret Leaks:** Raw API keys, private passwords, and unredacted PII are strictly filtered before database commits.
4. **Readback & Pagination:** Paginated retrieval (`GET /api/v1/scans?limit=20&offset=0`) verified and operational.
