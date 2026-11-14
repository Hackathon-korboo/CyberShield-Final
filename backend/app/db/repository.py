"""Scan Report Database Repository for Part 19.

Provides CRUD and search operations for Unified Threat Reports with automatic
Pydantic validation, transaction management, and pagination.
"""

import json
import logging
from typing import List, Optional, Tuple

from backend.app.db.session import DatabaseManager, get_db_manager
from backend.app.schemas.unified_report import UnifiedThreatReport

logger = logging.getLogger("cybershield.db.repository")


class ReportRepository:
    """Repository managing scan report persistence, retrieval, and pagination."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or get_db_manager()

    def save_report(self, report: UnifiedThreatReport) -> bool:
        """Persist a completed unified threat report to SQLite."""
        try:
            report_json = report.model_dump_json()
            score = report.risk_assessment.risk_score
            classification = report.risk_assessment.classification.value
            canonical_hash = report.report_integrity.canonical_sha256
            blockchain_status = report.report_integrity.blockchain_status
            created_at = report.timestamp.isoformat()

            with self.db.connection() as conn:
                conn.execute(
                    """
                    INSERT INTO scan_reports (
                        scan_id,
                        submitted_input,
                        input_type,
                        classification,
                        risk_score,
                        canonical_sha256,
                        blockchain_status,
                        report_json,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(scan_id) DO UPDATE SET
                        classification=excluded.classification,
                        risk_score=excluded.risk_score,
                        canonical_sha256=excluded.canonical_sha256,
                        blockchain_status=excluded.blockchain_status,
                        report_json=excluded.report_json,
                        created_at=excluded.created_at;
                    """,
                    (
                        report.scan_id,
                        report.submitted_input,
                        report.input_type,
                        classification,
                        score,
                        canonical_hash,
                        blockchain_status,
                        report_json,
                        created_at,
                    ),
                )
            logger.info("Successfully persisted scan report: %s", report.scan_id)
            return True
        except Exception as e:
            logger.error("Failed to persist scan report %s: %s", report.scan_id, e)
            return False

    def get_report(self, scan_id: str) -> Optional[UnifiedThreatReport]:
        """Retrieve a scan report by its unique scan_id."""
        try:
            with self.db.connection() as conn:
                cursor = conn.execute(
                    "SELECT report_json FROM scan_reports WHERE scan_id = ?;",
                    (scan_id,),
                )
                row = cursor.fetchone()
                if row:
                    return UnifiedThreatReport.model_validate_json(row["report_json"])
                return None
        except Exception as e:
            logger.error("Error retrieving scan report %s: %s", scan_id, e)
            return None

    def get_report_by_hash(self, canonical_sha256: str) -> Optional[UnifiedThreatReport]:
        """Retrieve a scan report by its canonical SHA-256 fingerprint."""
        try:
            with self.db.connection() as conn:
                cursor = conn.execute(
                    "SELECT report_json FROM scan_reports WHERE canonical_sha256 = ? LIMIT 1;",
                    (canonical_sha256,),
                )
                row = cursor.fetchone()
                if row:
                    return UnifiedThreatReport.model_validate_json(row["report_json"])
                return None
        except Exception as e:
            logger.error("Error retrieving scan report by hash %s: %s", canonical_sha256, e)
            return None

    def list_reports(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[UnifiedThreatReport], int]:
        """List scan reports with pagination ordered by newest first."""
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        reports: List[UnifiedThreatReport] = []
        total_count = 0

        try:
            with self.db.connection() as conn:
                # Get total count
                count_cur = conn.execute("SELECT COUNT(*) FROM scan_reports;")
                total_count = count_cur.fetchone()[0]

                # Get page rows
                cur = conn.execute(
                    """
                    SELECT report_json FROM scan_reports
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?;
                    """,
                    (limit, offset),
                )
                for row in cur.fetchall():
                    try:
                        rep = UnifiedThreatReport.model_validate_json(row["report_json"])
                        reports.append(rep)
                    except Exception as err:
                        logger.warning("Corrupted report JSON in database: %s", err)

            return reports, total_count
        except Exception as e:
            logger.error("Error listing scan reports: %s", e)
            return [], 0

    def delete_report(self, scan_id: str) -> bool:
        """Delete a report by scan_id (primarily for testing and cleanup)."""
        try:
            with self.db.connection() as conn:
                cur = conn.execute("DELETE FROM scan_reports WHERE scan_id = ?;", (scan_id,))
                return cur.rowcount > 0
        except Exception as e:
            logger.error("Error deleting scan report %s: %s", scan_id, e)
            return False
