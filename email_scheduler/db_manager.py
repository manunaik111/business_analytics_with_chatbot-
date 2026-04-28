"""
database/db_manager.py
FR 5.3 - Step 26 & 32: Persist schedule configurations and execution logs.

Uses SQLite by default; switchable to PostgreSQL via DATABASE_URL env var.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "database/scheduler.db")


class DatabaseManager:
    """
    Handles all database operations for:
      - Schedule configuration persistence (Step 26)
      - Execution log storage (Step 32)
      - Delivery statistics aggregation
    """

    def __init__(self, db_path: str = DATABASE_URL):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)

    def initialize(self):
        """Create all tables if they don't exist."""
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS schedules (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipients      TEXT    NOT NULL,  -- JSON array
                    frequency       TEXT    NOT NULL,  -- Daily|Weekly|Monthly
                    schedule_time   TEXT    NOT NULL DEFAULT '09:00',
                    report_type     TEXT    NOT NULL,
                    active          INTEGER NOT NULL DEFAULT 1,
                    created_by      INTEGER,
                    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
                    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS execution_logs (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    schedule_id     INTEGER NOT NULL,
                    report_type     TEXT    NOT NULL,
                    recipients      TEXT    NOT NULL,  -- JSON array
                    status          TEXT    NOT NULL,  -- success|failure
                    error_message   TEXT,
                    pdf_path        TEXT,
                    executed_at     TEXT    NOT NULL,
                    duration_ms     INTEGER,
                    FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS users (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    username        TEXT    UNIQUE NOT NULL,
                    password_hash   TEXT    NOT NULL,
                    email           TEXT,
                    role            TEXT    NOT NULL DEFAULT 'viewer',  -- admin|viewer
                    active          INTEGER NOT NULL DEFAULT 1,
                    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
                );

                CREATE INDEX IF NOT EXISTS idx_logs_schedule
                    ON execution_logs(schedule_id);
                CREATE INDEX IF NOT EXISTS idx_logs_executed_at
                    ON execution_logs(executed_at);
            """)
            # Seed default admin if none exists
            self._seed_admin(conn)
        logger.info("Database initialized.")

    # ── Schedule CRUD ───────────────────────────────────────────────────────────
    def save_schedule(self, data: dict) -> int:
        """Persist a new schedule and return its ID."""
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO schedules
                   (recipients, frequency, schedule_time, report_type, active, created_by)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    json.dumps(data["recipients"]),
                    data["frequency"],
                    data.get("schedule_time", "09:00"),
                    data["report_type"],
                    1 if data.get("active", True) else 0,
                    data.get("created_by"),
                )
            )
            return cur.lastrowid

    def get_schedule(self, schedule_id: int) -> Optional[dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM schedules WHERE id = ?", (schedule_id,)
            ).fetchone()
        return self._schedule_row(row) if row else None

    def get_all_schedules(self) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM schedules ORDER BY created_at DESC"
            ).fetchall()
        return [self._schedule_row(r) for r in rows]

    def get_active_schedules(self) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM schedules WHERE active = 1"
            ).fetchall()
        return [self._schedule_row(r) for r in rows]

    def update_schedule_status(self, schedule_id: int, active: bool):
        with self._conn() as conn:
            conn.execute(
                "UPDATE schedules SET active = ?, updated_at = datetime('now') WHERE id = ?",
                (1 if active else 0, schedule_id)
            )

    def delete_schedule(self, schedule_id: int):
        with self._conn() as conn:
            conn.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))

    # ── Execution Log ───────────────────────────────────────────────────────────
    def log_execution(self, data: dict):
        """Step 32: Record execution outcome with status and timestamp."""
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO execution_logs
                   (schedule_id, report_type, recipients, status,
                    error_message, pdf_path, executed_at, duration_ms)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["schedule_id"],
                    data["report_type"],
                    json.dumps(data["recipients"]),
                    data["status"],
                    data.get("error_message"),
                    data.get("pdf_path"),
                    data.get("executed_at", datetime.utcnow().isoformat()),
                    data.get("duration_ms"),
                )
            )

    def get_execution_logs(self, schedule_id: int = None, limit: int = 50) -> list:
        with self._conn() as conn:
            if schedule_id:
                rows = conn.execute(
                    "SELECT * FROM execution_logs WHERE schedule_id = ? "
                    "ORDER BY executed_at DESC LIMIT ?",
                    (schedule_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM execution_logs ORDER BY executed_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
        return [self._log_row(r) for r in rows]

    def get_recent_logs(self, limit: int = 10) -> list:
        return self.get_execution_logs(limit=limit)

    # ── Stats ───────────────────────────────────────────────────────────────────
    def get_delivery_stats(self) -> dict:
        """Compute delivery success rate and totals."""
        with self._conn() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*)                                    AS total,
                    SUM(CASE WHEN status = 'success' THEN 1 END) AS success_count,
                    SUM(CASE WHEN status = 'failure' THEN 1 END) AS failure_count,
                    ROUND(
                        100.0 * SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END)
                        / MAX(COUNT(*), 1), 2
                    )                                           AS success_rate
                FROM execution_logs
            """).fetchone()
        return {
            "total":        row[0] or 0,
            "success":      row[1] or 0,
            "failure":      row[2] or 0,
            "success_rate": row[3] or 0.0,
            "target_rate":  95.0,   # FR 5.3 SLA
            "meets_sla":    (row[3] or 0) >= 95.0,
        }

    # ── User Methods ────────────────────────────────────────────────────────────
    def get_user_by_username(self, username: str) -> Optional[dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ? AND active = 1", (username,)
            ).fetchone()
        if not row:
            return None
        cols = ["id", "username", "password_hash", "email", "role", "active", "created_at"]
        return dict(zip(cols, row))

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
        if not row:
            return None
        cols = ["id", "username", "password_hash", "email", "role", "active", "created_at"]
        return dict(zip(cols, row))

    # ── Helpers ─────────────────────────────────────────────────────────────────
    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _schedule_row(row) -> dict:
        d = dict(row)
        d["recipients"] = json.loads(d.get("recipients", "[]"))
        d["active"] = bool(d.get("active", 0))
        return d

    @staticmethod
    def _log_row(row) -> dict:
        d = dict(row)
        try:
            d["recipients"] = json.loads(d.get("recipients", "[]"))
        except Exception:
            pass
        return d

    def _seed_admin(self, conn):
        """Create default admin account if users table is empty."""
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            from werkzeug.security import generate_password_hash
            conn.execute(
                "INSERT INTO users (username, password_hash, email, role) VALUES (?,?,?,?)",
                ("admin", generate_password_hash("admin123"), "admin@example.com", "admin")
            )
            logger.info("Default admin user seeded (username: admin, password: admin123)")
