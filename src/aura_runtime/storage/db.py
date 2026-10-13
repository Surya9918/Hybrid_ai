"""
AURA Companion - SQLite Database Manager & Migrations
Provides transactional guarantees, WAL mode, schema versioning, and FTS5 search.
"""

import os
import sqlite3
from typing import Any, Dict, List, Optional, Tuple


class DatabaseManager:
    CURRENT_VERSION = 2

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._init_connection()
        self._run_migrations()

    def _init_connection(self) -> None:
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._connection = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            isolation_level="DEFERRED",
        )
        self._connection.row_factory = sqlite3.Row
        # Enable WAL mode for high concurrency & integrity on Windows/ARM64 and Linux
        if self.db_path != ":memory:":
            self._connection.execute("PRAGMA journal_mode=WAL;")
        self._connection.execute("PRAGMA foreign_keys=ON;")

    def get_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            self._init_connection()
        return self._connection

    def _get_schema_version(self) -> int:
        conn = self.get_connection()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            );
            """
        )
        cursor = conn.execute("SELECT MAX(version) as ver FROM schema_migrations;")
        row = cursor.fetchone()
        return row["ver"] if row and row["ver"] is not None else 0

    def _run_migrations(self) -> None:
        current = self._get_schema_version()
        conn = self.get_connection()

        if current < 1:
            # Migration V1: Core schema for tasks, reminders, memory, and audit events
            with conn:
                conn.execute(
                    """
                    CREATE TABLE tasks (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        priority TEXT NOT NULL DEFAULT 'medium',
                        due_date TEXT,
                        status TEXT NOT NULL DEFAULT 'open',
                        recurring_rule TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        completed_at TEXT
                    );
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE reminders (
                        id TEXT PRIMARY KEY,
                        message TEXT NOT NULL,
                        trigger_time_utc TEXT NOT NULL,
                        local_timezone TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'scheduled',
                        recurrence_rule TEXT,
                        last_delivered_at TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE memory_items (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        category TEXT NOT NULL DEFAULT 'general',
                        created_at TEXT NOT NULL
                    );
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE audit_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,
                        details TEXT NOT NULL,
                        timestamp TEXT NOT NULL
                    );
                    """
                )
                # FTS5 virtual table for lightning-fast memory & task search
                try:
                    conn.execute(
                        """
                        CREATE VIRTUAL TABLE task_fts USING fts5(
                            id UNINDEXED,
                            title,
                            description
                        );
                        """
                    )
                except sqlite3.OperationalError:
                    pass  # Fallback if fts5 not compiled in standard build

                conn.execute(
                    "INSERT INTO schema_migrations (version, applied_at) VALUES (1, datetime('now'));"
                )

        if current < 2:
            # Migration V2: Add indexes and snooze tracking
            with conn:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_reminders_trigger ON reminders(trigger_time_utc, status);"
                )
                # Ensure snooze tracking column exists
                columns = [
                    r["name"]
                    for r in conn.execute("PRAGMA table_info(reminders);").fetchall()
                ]
                if "snooze_count" not in columns:
                    conn.execute(
                        "ALTER TABLE reminders ADD COLUMN snooze_count INTEGER NOT NULL DEFAULT 0;"
                    )
                conn.execute(
                    "INSERT INTO schema_migrations (version, applied_at) VALUES (2, datetime('now'));"
                )

    def close(self) -> None:
        if self._connection:
            self._connection.close()
            self._connection = None
