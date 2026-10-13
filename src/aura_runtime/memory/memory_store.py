"""
AURA Companion - Editable Local Memory Store
SQLite-backed persistent memory with full-text search, deletion controls, and JSON export.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from src.aura_runtime.storage.db import DatabaseManager


class MemoryStore:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def add_memory(self, content: str, category: str = "general") -> str:
        if not content or not content.strip():
            raise ValueError("Memory content cannot be empty")

        mem_id = f"mem_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()

        conn = self.db.get_connection()
        with conn:
            conn.execute(
                "INSERT INTO memory_items (id, content, category, created_at) VALUES (?, ?, ?, ?);",
                (mem_id, content.strip(), category, now),
            )
        return mem_id

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        cursor = conn.execute(
            "SELECT * FROM memory_items WHERE content LIKE ? ORDER BY created_at DESC LIMIT ?;",
            (f"%{query}%", limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def delete_memory(self, memory_id: str) -> bool:
        conn = self.db.get_connection()
        with conn:
            cursor = conn.execute("DELETE FROM memory_items WHERE id = ?;", (memory_id,))
            return cursor.rowcount > 0

    def delete_all_data(self) -> Dict[str, int]:
        """
        Nuclear wipe for all user data (tasks, reminders, memory, audit logs).
        """
        conn = self.db.get_connection()
        counts = {}
        with conn:
            for table in ["tasks", "reminders", "memory_items", "audit_events"]:
                c = conn.execute(f"DELETE FROM {table};").rowcount
                counts[table] = c
            try:
                conn.execute("DELETE FROM task_fts;")
            except Exception:
                pass
        return counts

    def export_all_data(self) -> Dict[str, Any]:
        conn = self.db.get_connection()
        data = {}
        for table in ["tasks", "reminders", "memory_items"]:
            cursor = conn.execute(f"SELECT * FROM {table};")
            data[table] = [dict(r) for r in cursor.fetchall()]
        return data
