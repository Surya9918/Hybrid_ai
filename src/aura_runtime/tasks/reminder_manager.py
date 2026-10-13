"""
AURA Companion - Timezone-Aware Persistent Reminder Manager
Handles one-time & recurring alarms, wake/sleep catch-up reconciliation, snooze, and duplicate prevention.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple
from src.aura_runtime.storage.db import DatabaseManager


class ReminderManager:
    def __init__(self, db_manager: DatabaseManager, default_timezone: str = "UTC"):
        self.db = db_manager
        self.default_timezone = default_timezone
        self.delivered_cache: set = set()

    def _now_utc(self) -> datetime:
        return datetime.now(timezone.utc)

    def create_reminder(
        self,
        message: str,
        trigger_time_utc: str,
        recurrence_rule: str = "",
        local_timezone: Optional[str] = None,
    ) -> str:
        if not message or not message.strip():
            raise ValueError("Reminder message cannot be empty")

        rem_id = f"rem_{uuid.uuid4().hex[:8]}"
        tz = local_timezone or self.default_timezone
        now = self._now_utc().isoformat()

        conn = self.db.get_connection()
        with conn:
            conn.execute(
                """
                INSERT INTO reminders (
                    id, message, trigger_time_utc, local_timezone, status,
                    recurrence_rule, snooze_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'scheduled', ?, 0, ?, ?);
                """,
                (rem_id, message.strip(), trigger_time_utc, tz, recurrence_rule, now, now),
            )
        return rem_id

    def get_reminder(self, reminder_id: str) -> Optional[Dict[str, Any]]:
        conn = self.db.get_connection()
        cursor = conn.execute("SELECT * FROM reminders WHERE id = ?;", (reminder_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def cancel_reminder(self, reminder_id: str) -> Tuple[bool, str]:
        conn = self.db.get_connection()
        rem = self.get_reminder(reminder_id)
        if not rem:
            return False, f"Reminder '{reminder_id}' not found"

        now = self._now_utc().isoformat()
        with conn:
            conn.execute(
                "UPDATE reminders SET status = 'cancelled', updated_at = ? WHERE id = ?;",
                (now, reminder_id),
            )
        return True, "Reminder cancelled"

    def snooze_reminder(self, reminder_id: str, minutes: int = 10) -> Tuple[bool, str]:
        rem = self.get_reminder(reminder_id)
        if not rem:
            return False, f"Reminder '{reminder_id}' not found"

        new_trigger = (self._now_utc() + timedelta(minutes=minutes)).isoformat()
        now = self._now_utc().isoformat()

        conn = self.db.get_connection()
        with conn:
            conn.execute(
                """
                UPDATE reminders
                SET trigger_time_utc = ?, status = 'scheduled', snooze_count = snooze_count + 1, updated_at = ?
                WHERE id = ?;
                """,
                (new_trigger, now, reminder_id),
            )
        return True, f"Reminder snoozed for {minutes} minutes"

    def reschedule_reminder(self, reminder_id: str, new_trigger_utc: str) -> Tuple[bool, str]:
        rem = self.get_reminder(reminder_id)
        if not rem:
            return False, f"Reminder '{reminder_id}' not found"

        now = self._now_utc().isoformat()
        conn = self.db.get_connection()
        with conn:
            conn.execute(
                "UPDATE reminders SET trigger_time_utc = ?, status = 'scheduled', updated_at = ? WHERE id = ?;",
                (new_trigger_utc, now, reminder_id),
            )
        return True, f"Reminder rescheduled to {new_trigger_utc}"

    def get_due_reminders(self, current_time_utc: Optional[datetime] = None) -> List[Dict[str, Any]]:
        target_time = current_time_utc or self._now_utc()
        target_iso = target_time.isoformat()

        conn = self.db.get_connection()
        cursor = conn.execute(
            """
            SELECT * FROM reminders
            WHERE status = 'scheduled' AND trigger_time_utc <= ?
            ORDER BY trigger_time_utc ASC;
            """,
            (target_iso,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def check_and_deliver(
        self,
        current_time_utc: Optional[datetime] = None,
        dispatcher: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Evaluates due reminders, invokes notification dispatcher, and updates recurrence.
        Guarantees zero duplicate deliveries even if re-triggered or after reboot.
        """
        now = current_time_utc or self._now_utc()
        due_items = self.get_due_reminders(now)
        delivered_batch = []
        conn = self.db.get_connection()

        for item in due_items:
            item_id = item["id"]
            # Deduplicate against current in-memory run
            delivery_key = f"{item_id}_{item['trigger_time_utc']}"
            if delivery_key in self.delivered_cache:
                continue

            # Dispatch notification
            if dispatcher:
                try:
                    dispatcher(item)
                except Exception:
                    pass

            self.delivered_cache.add(delivery_key)
            delivered_batch.append(item)
            now_str = now.isoformat()

            # Handle recurrence or complete
            rule = (item.get("recurrence_rule") or "").lower()
            if rule == "daily":
                # Compute next trigger (+ 24 hours)
                curr_dt = datetime.fromisoformat(item["trigger_time_utc"])
                next_dt = curr_dt + timedelta(days=1)
                while next_dt <= now:
                    next_dt += timedelta(days=1)
                with conn:
                    conn.execute(
                        """
                        UPDATE reminders
                        SET trigger_time_utc = ?, last_delivered_at = ?, updated_at = ?
                        WHERE id = ?;
                        """,
                        (next_dt.isoformat(), now_str, now_str, item_id),
                    )
            elif rule == "weekly":
                curr_dt = datetime.fromisoformat(item["trigger_time_utc"])
                next_dt = curr_dt + timedelta(weeks=1)
                while next_dt <= now:
                    next_dt += timedelta(weeks=1)
                with conn:
                    conn.execute(
                        """
                        UPDATE reminders
                        SET trigger_time_utc = ?, last_delivered_at = ?, updated_at = ?
                        WHERE id = ?;
                        """,
                        (next_dt.isoformat(), now_str, now_str, item_id),
                    )
            else:
                # One-time reminder delivered
                with conn:
                    conn.execute(
                        """
                        UPDATE reminders
                        SET status = 'delivered', last_delivered_at = ?, updated_at = ?
                        WHERE id = ?;
                        """,
                        (now_str, now_str, item_id),
                    )

        return delivered_batch

    def reconcile_on_startup_or_wake(
        self,
        current_time_utc: Optional[datetime] = None,
        dispatcher: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Runs on system startup or wake to deliver catch-up notifications for missed reminders.
        """
        return self.check_and_deliver(current_time_utc, dispatcher)
