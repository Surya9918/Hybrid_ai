"""
AURA Companion - Natural Language Scheduling Parser
Parses human scheduling expressions ("in 30 mins", "tomorrow at 9 AM", "due Friday") into structured records.
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple


class NaturalLanguageScheduler:
    def __init__(self, local_timezone: str = "UTC"):
        self.local_timezone = local_timezone

    def parse_expression(self, text: str, reference_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Parses text for reminders or tasks.
        Returns a dictionary with parsed action, arguments, and trigger times.
        """
        now = reference_time or datetime.now(timezone.utc)
        text_clean = text.strip()
        lower = text_clean.lower()

        # 1. Snooze expression: "snooze this reminder for 10 minutes" / "snooze for 15 mins"
        snooze_match = re.search(r"snooze(?:\s+this\s+reminder)?\s+for\s+(\d+)\s*(?:minutes?|mins?)", lower)
        if snooze_match:
            mins = int(snooze_match.group(1))
            return {
                "action": "snooze_reminder",
                "minutes": mins,
            }

        # 2. Cancel next reminder: "cancel my next reminder" / "cancel reminder"
        if "cancel my next reminder" in lower or "cancel next reminder" in lower:
            return {
                "action": "cancel_next_reminder",
            }

        # 3. Show tasks for today: "show my tasks for today"
        if "show my tasks for today" in lower or "show tasks for today" in lower or "tasks for today" in lower:
            return {
                "action": "list_tasks_today",
            }

        # 4. Recurring reminder: "remind me every monday at 8 am to <message>"
        every_match = re.search(
            r"(?:remind\s+(?:me\s+)?)?every\s+([a-zA-Z]+)(?:\s+at\s+(\d+)(?:\s*(am|pm))?)?(?:\s+to\s+(.+))?",
            lower,
        )
        if every_match:
            day_name = every_match.group(1)
            hour_str = every_match.group(2) or "9"
            meridiem = every_match.group(3) or "am"
            msg = every_match.group(4) or "Scheduled recurring reminder"

            hour = int(hour_str)
            if meridiem == "pm" and hour < 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0

            weekdays = {
                "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                "friday": 4, "saturday": 5, "sunday": 6,
            }
            target_weekday = weekdays.get(day_name, 0)
            days_ahead = (target_weekday - now.weekday()) % 7
            if days_ahead == 0 and now.hour >= hour:
                days_ahead = 7

            target_dt = (now + timedelta(days=days_ahead)).replace(
                hour=hour, minute=0, second=0, microsecond=0
            )

            return {
                "action": "create_reminder",
                "message": msg.strip(),
                "trigger_time_utc": target_dt.isoformat(),
                "recurrence_rule": "weekly",
            }

        # 5. "Remind me in X minutes/hours to <message>" or "(in) X minutes/hours to <message>"
        in_match = re.search(
            r"(?:remind\s+(?:me\s+)?)?(?:in\s+)?(\d+)\s*(minutes?|mins?|hours?|hrs?)(?:\s+to\s+(.+))?",
            lower,
        )
        if in_match:
            amt = int(in_match.group(1))
            unit = in_match.group(2)
            msg = in_match.group(3) or "Reminder"

            delta = timedelta(minutes=amt) if "min" in unit else timedelta(hours=amt)
            target_dt = now + delta
            return {
                "action": "create_reminder",
                "message": msg.strip(),
                "trigger_time_utc": target_dt.isoformat(),
                "recurrence_rule": "",
            }

        # 6. "Remind me tomorrow at X [AM/PM] to <message>"
        tomorrow_match = re.search(
            r"(?:remind\s+(?:me\s+)?)?tomorrow(?:\s+at\s+(\d+)(?:\s*(am|pm))?)?(?:\s+to\s+(.+))?",
            lower,
        )
        if tomorrow_match:
            hour_str = tomorrow_match.group(1) or "9"
            meridiem = tomorrow_match.group(2) or "am"
            msg = tomorrow_match.group(3) or "Reminder"

            hour = int(hour_str)
            if meridiem == "pm" and hour < 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0

            target_dt = (now + timedelta(days=1)).replace(
                hour=hour, minute=0, second=0, microsecond=0
            )
            return {
                "action": "create_reminder",
                "message": msg.strip(),
                "trigger_time_utc": target_dt.isoformat(),
                "recurrence_rule": "",
            }

        # 7. Create task: "Create a high-priority task due Friday: <title>"
        task_match = re.search(
            r"create\s+(?:a\s+)?(?:(high|urgent|medium|low)[-\s]priority\s+)?task(?:\s+due\s+([a-zA-Z]+))?(?:\s*:\s*|\s+to\s+|\s+titled\s+)(.+)",
            lower,
        )
        if task_match:
            priority = task_match.group(1) or "medium"
            due_day = task_match.group(2)
            title = task_match.group(3)

            due_date = ""
            if due_day:
                weekdays = {
                    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                    "friday": 4, "saturday": 5, "sunday": 6,
                }
                target_wd = weekdays.get(due_day.lower())
                if target_wd is not None:
                    days_ahead = (target_wd - now.weekday()) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    due_date = (now + timedelta(days=days_ahead)).date().isoformat()

            return {
                "action": "create_task",
                "title": title.strip(),
                "priority": priority,
                "due_date": due_date,
            }

        return {"action": "unrecognized", "text": text}
