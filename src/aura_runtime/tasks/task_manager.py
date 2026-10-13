"""
AURA Companion - Persistent Task Manager
SQLite-backed task CRUD, priority scheduling, recurring definitions, and FTS5 search.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from src.aura_runtime.storage.db import DatabaseManager


class TaskManager:
    VALID_PRIORITIES = {"low", "medium", "high", "urgent"}
    VALID_STATUSES = {"open", "in_progress", "completed", "archived"}

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        due_date: str = "",
        recurring_rule: str = "",
    ) -> str:
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")

        priority = priority.lower()
        if priority not in self.VALID_PRIORITIES:
            priority = "medium"

        task_id = f"task_{uuid.uuid4().hex[:8]}"
        now = self._now_iso()

        conn = self.db.get_connection()
        with conn:
            conn.execute(
                """
                INSERT INTO tasks (id, title, description, priority, due_date, status, recurring_rule, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'open', ?, ?, ?);
                """,
                (task_id, title.strip(), description.strip(), priority, due_date, recurring_rule, now, now),
            )
            try:
                conn.execute(
                    "INSERT INTO task_fts (id, title, description) VALUES (?, ?, ?);",
                    (task_id, title.strip(), description.strip()),
                )
            except Exception:
                pass

        return task_id

    def edit_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> Tuple[bool, str]:
        conn = self.db.get_connection()
        task = self.get_task(task_id)
        if not task:
            return False, f"Task '{task_id}' not found"

        updates = []
        params = []
        now = self._now_iso()

        if title is not None:
            updates.append("title = ?")
            params.append(title.strip())
        if description is not None:
            updates.append("description = ?")
            params.append(description.strip())
        if priority is not None:
            p_clean = priority.lower()
            if p_clean in self.VALID_PRIORITIES:
                updates.append("priority = ?")
                params.append(p_clean)
        if due_date is not None:
            updates.append("due_date = ?")
            params.append(due_date)

        if not updates:
            return True, "No changes requested"

        updates.append("updated_at = ?")
        params.append(now)
        params.append(task_id)

        sql = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?;"
        with conn:
            conn.execute(sql, params)
            # Update FTS
            try:
                conn.execute("DELETE FROM task_fts WHERE id = ?;", (task_id,))
                current = self.get_task(task_id)
                if current:
                    conn.execute(
                        "INSERT INTO task_fts (id, title, description) VALUES (?, ?, ?);",
                        (task_id, current["title"], current["description"] or ""),
                    )
            except Exception:
                pass

        return True, "Task updated successfully"

    def complete_task(self, task_id: str) -> Tuple[bool, str]:
        conn = self.db.get_connection()
        task = self.get_task(task_id)
        if not task:
            return False, f"Task '{task_id}' not found"

        now = self._now_iso()
        with conn:
            conn.execute(
                "UPDATE tasks SET status = 'completed', completed_at = ?, updated_at = ? WHERE id = ?;",
                (now, now, task_id),
            )
        return True, f"Task '{task['title']}' marked complete"

    def reopen_task(self, task_id: str) -> Tuple[bool, str]:
        conn = self.db.get_connection()
        task = self.get_task(task_id)
        if not task:
            return False, f"Task '{task_id}' not found"

        now = self._now_iso()
        with conn:
            conn.execute(
                "UPDATE tasks SET status = 'open', completed_at = NULL, updated_at = ? WHERE id = ?;",
                (now, task_id),
            )
        return True, f"Task '{task['title']}' reopened"

    def delete_task(self, task_id: str) -> Tuple[bool, str]:
        conn = self.db.get_connection()
        task = self.get_task(task_id)
        if not task:
            return False, f"Task '{task_id}' not found"

        with conn:
            conn.execute("DELETE FROM tasks WHERE id = ?;", (task_id,))
            try:
                conn.execute("DELETE FROM task_fts WHERE id = ?;", (task_id,))
            except Exception:
                pass

        return True, f"Task '{task['title']}' deleted successfully"

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        conn = self.db.get_connection()
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?;", (task_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50,
        sort_by: str = "created_at",
    ) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if priority:
            query += " AND priority = ?"
            params.append(priority)

        # Safe order by
        order_col = "due_date" if sort_by == "due_date" else "created_at"
        query += f" ORDER BY {order_col} DESC LIMIT ?;"
        params.append(limit)

        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def search_tasks(self, search_query: str) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT t.* FROM tasks t
                JOIN task_fts fts ON t.id = fts.id
                WHERE task_fts MATCH ?
                ORDER BY rank;
                """,
                (f"{search_query}*",),
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception:
            # Fallback to standard LIKE search
            cursor = conn.execute(
                "SELECT * FROM tasks WHERE title LIKE ? OR description LIKE ?;",
                (f"%{search_query}%", f"%{search_query}%"),
            )
            return [dict(row) for row in cursor.fetchall()]
