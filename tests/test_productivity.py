"""
AURA Companion - Acceptance Tests for Tasks and Reminders (Section 7.4)
Covers all 12 mandatory acceptance scenarios:
1. Task creation, editing, completion and deletion.
2. Task persistence after restarting the app.
3. Reminder delivery at the expected time under normal operating conditions.
4. Correct handling of a reminder due while the app or device is unavailable.
5. Correct recurrence behavior.
6. No duplicate notification after retry or restart.
7. Correct local-time display.
8. Cancellation and rescheduling.
9. Voice-created reminders.
10. UI-created reminders.
11. Tool-created reminders.
12. Recovery after a database interruption without corrupting existing tasks.
"""

import os
import shutil
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from src.aura_runtime.storage.db import DatabaseManager
from src.aura_runtime.tasks.task_manager import TaskManager
from src.aura_runtime.tasks.reminder_manager import ReminderManager
from src.aura_runtime.tasks.nl_scheduler import NaturalLanguageScheduler
from src.aura_runtime.voice.transcription import DictationCorrectionParser
from src.aura_runtime.tools.registry import ToolRegistry
from src.aura_runtime.tools.builtin_tools import register_all_builtin_tools
from src.aura_runtime.tools.engine import AgenticExecutionEngine
from src.aura_runtime.tools.schema import ToolExecutionRequest
from src.aura_runtime.platform.windows_adapter import WindowsPlatformAdapter
from src.aura_runtime.memory.memory_store import MemoryStore


class TestProductivitySuite(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_aura_productivity.db")
        self.db = DatabaseManager(self.db_path)
        self.task_manager = TaskManager(self.db)
        self.reminder_manager = ReminderManager(self.db, default_timezone="America/New_York")
        self.scheduler = NaturalLanguageScheduler(local_timezone="America/New_York")

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # Scenario 1: Task creation, editing, completion and deletion
    def test_01_task_lifecycle_crud(self):
        # Create
        task_id = self.task_manager.create_task("Implement WinUI 3 Orb XAML", priority="high")
        task = self.task_manager.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task["title"], "Implement WinUI 3 Orb XAML")
        self.assertEqual(task["priority"], "high")
        self.assertEqual(task["status"], "open")

        # Edit
        ok, msg = self.task_manager.edit_task(
            task_id, title="Implement WinUI 3 Orb Composition", priority="urgent"
        )
        self.assertTrue(ok)
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task["title"], "Implement WinUI 3 Orb Composition")
        self.assertEqual(task["priority"], "urgent")

        # Complete
        ok, msg = self.task_manager.complete_task(task_id)
        self.assertTrue(ok)
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task["status"], "completed")
        self.assertIsNotNone(task["completed_at"])

        # Delete
        ok, msg = self.task_manager.delete_task(task_id)
        self.assertTrue(ok)
        self.assertIsNone(self.task_manager.get_task(task_id))

    # Scenario 2: Task persistence after restarting the app
    def test_02_task_persistence_after_app_restart(self):
        task_id = self.task_manager.create_task("Verify ARM64 Hexagon NPU QNN EP", priority="urgent")

        # Simulate full application crash/close and restart
        self.db.close()
        new_db = DatabaseManager(self.db_path)
        new_task_mgr = TaskManager(new_db)

        recovered = new_task_mgr.get_task(task_id)
        self.assertIsNotNone(recovered)
        self.assertEqual(recovered["title"], "Verify ARM64 Hexagon NPU QNN EP")
        self.assertEqual(recovered["priority"], "urgent")
        new_db.close()

    # Scenario 3: Reminder delivery at the expected time under normal operating conditions
    def test_03_reminder_delivery_normal_operating_conditions(self):
        now = datetime.now(timezone.utc)
        target = now + timedelta(seconds=2)
        rem_id = self.reminder_manager.create_reminder(
            "Sync Git branch with upstream",
            target.isoformat(),
        )

        delivered = []
        def notification_handler(rem):
            delivered.append(rem)

        # Before target time: should not trigger
        batch_early = self.reminder_manager.check_and_deliver(
            now, dispatcher=notification_handler
        )
        self.assertEqual(len(batch_early), 0)

        # At target time: triggers immediately
        batch_due = self.reminder_manager.check_and_deliver(
            target + timedelta(seconds=1), dispatcher=notification_handler
        )
        self.assertEqual(len(batch_due), 1)
        self.assertEqual(batch_due[0]["id"], rem_id)
        self.assertEqual(len(delivered), 1)

    # Scenario 4: Correct handling of a reminder due while the app or device is unavailable
    def test_04_reminder_due_while_app_asleep_or_closed(self):
        past_due = datetime.now(timezone.utc) - timedelta(minutes=45)
        rem_id = self.reminder_manager.create_reminder(
            "Check Snapdragon thermal dissipation",
            past_due.isoformat(),
        )

        # Re-open app fresh (simulating wake from sleep / reboot)
        self.db.close()
        wake_db = DatabaseManager(self.db_path)
        wake_rem_mgr = ReminderManager(wake_db)

        catchup_delivered = []
        def catchup_dispatcher(r):
            catchup_delivered.append(r)

        now = datetime.now(timezone.utc)
        reconciled = wake_rem_mgr.reconcile_on_startup_or_wake(
            now, dispatcher=catchup_dispatcher
        )

        self.assertEqual(len(reconciled), 1)
        self.assertEqual(reconciled[0]["id"], rem_id)
        self.assertEqual(len(catchup_delivered), 1)
        wake_db.close()

    # Scenario 5: Correct recurrence behavior
    def test_05_recurring_reminder_behavior(self):
        now = datetime.now(timezone.utc)
        trigger = now - timedelta(minutes=5)
        rem_id = self.reminder_manager.create_reminder(
            "Daily Standup Review",
            trigger.isoformat(),
            recurrence_rule="daily",
        )

        delivered = self.reminder_manager.check_and_deliver(now)
        self.assertEqual(len(delivered), 1)

        # Verify reminder is updated for tomorrow, not marked dead/delivered
        updated = self.reminder_manager.get_reminder(rem_id)
        self.assertEqual(updated["status"], "scheduled")
        new_dt = datetime.fromisoformat(updated["trigger_time_utc"])
        self.assertGreater(new_dt, now)

    # Scenario 6: No duplicate notification after retry or restart
    def test_06_no_duplicate_notifications(self):
        now = datetime.now(timezone.utc)
        rem_id = self.reminder_manager.create_reminder(
            "One-time safety check",
            (now - timedelta(seconds=10)).isoformat(),
        )

        delivered_log = []
        def disp(r):
            delivered_log.append(r)

        # First run delivers
        self.reminder_manager.check_and_deliver(now, dispatcher=disp)
        self.assertEqual(len(delivered_log), 1)

        # Immediate rerun must NOT deliver again
        self.reminder_manager.check_and_deliver(now, dispatcher=disp)
        self.assertEqual(len(delivered_log), 1)

        # Reboot app and reconcile
        self.db.close()
        reboot_db = DatabaseManager(self.db_path)
        reboot_mgr = ReminderManager(reboot_db)
        reboot_mgr.reconcile_on_startup_or_wake(now + timedelta(minutes=5), dispatcher=disp)

        self.assertEqual(len(delivered_log), 1)  # Still exactly 1
        reboot_db.close()

    # Scenario 7: Correct local-time display
    def test_07_correct_local_time_preservation(self):
        rem_id = self.reminder_manager.create_reminder(
            "Meeting with Seattle team",
            "2026-10-15T16:00:00+00:00",
            local_timezone="America/Los_Angeles",
        )
        rem = self.reminder_manager.get_reminder(rem_id)
        self.assertEqual(rem["local_timezone"], "America/Los_Angeles")
        self.assertIn("2026-10-15T16:00:00+00:00", rem["trigger_time_utc"])

    # Scenario 8: Cancellation and rescheduling
    def test_08_cancellation_and_rescheduling(self):
        rem_id = self.reminder_manager.create_reminder(
            "Review pull request",
            "2026-10-20T10:00:00+00:00",
        )
        # Reschedule
        ok, _ = self.reminder_manager.reschedule_reminder(rem_id, "2026-10-20T14:00:00+00:00")
        self.assertTrue(ok)
        self.assertEqual(
            self.reminder_manager.get_reminder(rem_id)["trigger_time_utc"],
            "2026-10-20T14:00:00+00:00",
        )

        # Cancel
        ok, _ = self.reminder_manager.cancel_reminder(rem_id)
        self.assertTrue(ok)
        self.assertEqual(self.reminder_manager.get_reminder(rem_id)["status"], "cancelled")

    # Scenario 9: Voice-created reminders (with spoken correction parsing)
    def test_09_voice_created_reminder(self):
        raw_voice_input = "Remind me in 30 minutes to review code scratch that 15 minutes to review code"
        corrected = DictationCorrectionParser.apply_corrections(raw_voice_input)
        self.assertIn("15 minutes to review code", corrected)

        parsed = self.scheduler.parse_expression(corrected)
        self.assertEqual(parsed["action"], "create_reminder")
        self.assertEqual(parsed["message"], "review code")
        rem_id = self.reminder_manager.create_reminder(
            parsed["message"], parsed["trigger_time_utc"]
        )
        self.assertIsNotNone(self.reminder_manager.get_reminder(rem_id))

    # Scenario 10: UI-created reminders
    def test_10_ui_created_reminder(self):
        ui_form_data = {
            "message": "Submit weekly telemetry report",
            "trigger_time_utc": (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat(),
            "recurrence_rule": "weekly",
            "local_timezone": "America/New_York",
        }
        rem_id = self.reminder_manager.create_reminder(
            ui_form_data["message"],
            ui_form_data["trigger_time_utc"],
            ui_form_data["recurrence_rule"],
            ui_form_data["local_timezone"],
        )
        rem = self.reminder_manager.get_reminder(rem_id)
        self.assertEqual(rem["message"], "Submit weekly telemetry report")
        self.assertEqual(rem["recurrence_rule"], "weekly")

    # Scenario 11: Tool-created reminders
    def test_11_tool_created_reminder(self):
        platform_adapter = WindowsPlatformAdapter()
        memory_store = MemoryStore(self.db)
        registry = ToolRegistry()
        register_all_builtin_tools(
            registry, platform_adapter, self.task_manager, self.reminder_manager, memory_store
        )
        engine = AgenticExecutionEngine(registry)

        req = ToolExecutionRequest(
            request_id=str(uuid.uuid4()),
            tool_name="create_reminder",
            arguments={
                "message": "Verify Snapdragon X Elite power profile",
                "trigger_time": "2026-10-18T09:00:00Z",
            },
        )
        res = engine.execute_request(req)
        self.assertTrue(res.success)
        rem_id = res.output["reminder_id"]
        rem = self.reminder_manager.get_reminder(rem_id)
        self.assertIsNotNone(rem)
        self.assertEqual(rem["message"], "Verify Snapdragon X Elite power profile")

    # Scenario 12: Recovery after a database interruption without corrupting existing tasks
    def test_12_database_interruption_recovery(self):
        t1 = self.task_manager.create_task("Task before crash 1")
        t2 = self.task_manager.create_task("Task before crash 2")

        # Simulate sudden crash/interruption without clean close
        conn = self.db.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            conn.execute("INSERT INTO tasks (id, title, priority, status, created_at, updated_at) VALUES ('bad', 'incomplete', 'low', 'open', 'now', 'now');")
            # Force uncommitted rollback (interruption)
            conn.rollback()
        except Exception:
            pass

        # Reopen connection
        self.db.close()
        recovered_db = DatabaseManager(self.db_path)
        recovered_tm = TaskManager(recovered_db)

        # Existing valid tasks must be preserved unharmed
        self.assertIsNotNone(recovered_tm.get_task(t1))
        self.assertIsNotNone(recovered_tm.get_task(t2))
        self.assertIsNone(recovered_tm.get_task("bad"))
        recovered_db.close()


if __name__ == "__main__":
    unittest.main()
