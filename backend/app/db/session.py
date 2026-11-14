"""SQLite Database Connection & Session Management for Part 19.

Provides thread-safe SQLite connection handling, automatic schema initialization,
and WAL mode configuration for concurrent operations.
"""

from contextlib import contextmanager
import logging
import os
import sqlite3
from typing import Generator, Optional

from backend.app.core.config import get_settings

logger = logging.getLogger("cybershield.db")

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "cybershield.db",
)


class DatabaseManager:
    """Manages SQLite database connections, transactions, and table migrations."""

    def __init__(self, db_path: Optional[str] = None):
        settings = get_settings()
        self.db_path = db_path or getattr(settings, "database_url", None) or DEFAULT_DB_PATH
        # If database_url is sqlite:///path, extract path
        if self.db_path.startswith("sqlite:///"):
            self.db_path = self.db_path.replace("sqlite:///", "")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create and configure a new SQLite connection."""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=10.0,
        )
        conn.row_factory = sqlite3.Row
        # Enable WAL mode and foreign keys for durability and concurrency
        if self.db_path != ":memory:":
            conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self) -> None:
        """Initialize database schema if tables do not exist."""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS scan_reports (
                        scan_id TEXT PRIMARY KEY,
                        submitted_input TEXT NOT NULL,
                        input_type TEXT NOT NULL,
                        classification TEXT NOT NULL,
                        risk_score INTEGER,
                        canonical_sha256 TEXT NOT NULL,
                        blockchain_status TEXT NOT NULL DEFAULT 'NOT_REGISTERED',
                        report_json TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_scan_reports_created_at
                    ON scan_reports(created_at DESC);
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_scan_reports_canonical_hash
                    ON scan_reports(canonical_sha256);
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_scan_reports_classification
                    ON scan_reports(classification);
                    """
                )
                conn.commit()
            logger.info("Database schema initialized successfully at %s", self.db_path)
        except Exception as e:
            logger.error("Failed to initialize database schema: %s", e)

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager yielding a transactional connection."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error("Transaction rolled back due to error: %s", e)
            raise
        finally:
            conn.close()

    def check_health(self) -> bool:
        """Verify database connectivity and query execution."""
        try:
            with self.connection() as conn:
                cursor = conn.execute("SELECT 1;")
                row = cursor.fetchone()
                return bool(row and row[0] == 1)
        except Exception as e:
            logger.warning("Database health check failed: %s", e)
            return False


# Singleton instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Return singleton DatabaseManager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
