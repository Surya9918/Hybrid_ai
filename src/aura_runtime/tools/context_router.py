"""
AURA Companion - Context-Aware Router & Intent Classifier
Resolves natural language commands, recent context references, and identifies ambiguities.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from src.aura_runtime.tools.security import SecurityBoundary


@dataclass
class RoutedPlan:
    is_ambiguous: bool
    clarification_question: Optional[str] = None
    tool_name: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    untrusted_injection_detected: bool = False
    context_used: Optional[str] = None


class ContextRouter:
    def __init__(self, platform_adapter, task_manager, reminder_manager):
        self.platform_adapter = platform_adapter
        self.task_manager = task_manager
        self.reminder_manager = reminder_manager
        self.recent_context: Dict[str, Any] = {
            "last_created_task_id": None,
            "last_failed_action": None,
            "active_window": None,
            "selected_roi": None,
        }

    def update_recent_context(self, key: str, value: Any) -> None:
        self.recent_context[key] = value

    def route_request(self, user_text: str, screen_context: Optional[str] = None) -> RoutedPlan:
        # 1. Check for prompt injection in user text or screen context
        sanitized_user, injection_user = SecurityBoundary.sanitize_untrusted_text(user_text)
        _, injection_screen = SecurityBoundary.sanitize_untrusted_text(screen_context or "")
        
        has_injection = injection_user or injection_screen

        text_lower = sanitized_user.strip().lower()

        # 2. Check for ambiguous requests that require clarification
        if text_lower in ["open", "launch", "start"]:
            return RoutedPlan(
                is_ambiguous=True,
                clarification_question="Which application would you like me to open?",
                untrusted_injection_detected=has_injection,
            )

        if text_lower in ["delete", "remove", "delete it", "cancel"]:
            return RoutedPlan(
                is_ambiguous=True,
                clarification_question="Which item or task would you like me to delete?",
                untrusted_injection_detected=has_injection,
            )

        # 3. Anaphoric reference: "mark my last task complete" or "complete my task"
        if "mark my last task complete" in text_lower or "complete last task" in text_lower:
            last_task_id = self.recent_context.get("last_created_task_id")
            if not last_task_id:
                # Query recent open tasks from task manager
                recent = self.task_manager.list_tasks(status="open", limit=1)
                if recent:
                    last_task_id = recent[0]["id"]

            if last_task_id:
                return RoutedPlan(
                    is_ambiguous=False,
                    tool_name="complete_task",
                    arguments={"task_id": last_task_id},
                    untrusted_injection_detected=has_injection,
                    context_used=f"Resolved last task ID: {last_task_id}",
                )
            else:
                return RoutedPlan(
                    is_ambiguous=True,
                    clarification_question="You don't have any recent open tasks. Which task should I complete?",
                    untrusted_injection_detected=has_injection,
                )

        # 4. Anaphoric reference: "summarize this"
        if text_lower in ["summarize this", "what is this", "explain this"]:
            roi = self.recent_context.get("selected_roi")
            if roi:
                return RoutedPlan(
                    is_ambiguous=False,
                    tool_name="analyze_screen_region",
                    arguments={
                        "x": roi["x"],
                        "y": roi["y"],
                        "width": roi["width"],
                        "height": roi["height"],
                        "question": "Summarize this screen area",
                    },
                    untrusted_injection_detected=has_injection,
                    context_used="Resolved active screen selection ROI",
                )
            else:
                # Fallback to general screen context
                return RoutedPlan(
                    is_ambiguous=False,
                    tool_name="read_screen_context",
                    arguments={"monitor_index": 0},
                    untrusted_injection_detected=has_injection,
                    context_used="Resolved active foreground window",
                )

        # 5. Anaphoric reference: "try again" / "retry"
        if text_lower in ["try again", "retry", "retry that"]:
            last_failed = self.recent_context.get("last_failed_action")
            if last_failed:
                return RoutedPlan(
                    is_ambiguous=False,
                    tool_name=last_failed.get("tool_name"),
                    arguments=last_failed.get("arguments"),
                    untrusted_injection_detected=has_injection,
                    context_used=f"Retrying previous failed action: {last_failed.get('tool_name')}",
                )
            else:
                return RoutedPlan(
                    is_ambiguous=True,
                    clarification_question="There is no recent failed action to retry. What would you like me to do?",
                    untrusted_injection_detected=has_injection,
                )

        # 6. Open application: "open <app>" or "launch <app>"
        open_match = re.match(r"^(?:open|launch|start)\s+(.+)$", text_lower)
        if open_match:
            app_target = open_match.group(1).strip()
            # Normalize common names
            if "vs code" in app_target or "visual studio code" in app_target:
                app_target = "code"
            elif "browser" in app_target or "edge" in app_target:
                app_target = "msedge"
            return RoutedPlan(
                is_ambiguous=False,
                tool_name="open_app",
                arguments={"app_name": app_target},
                untrusted_injection_detected=has_injection,
            )

        # 7. Switch application: "switch to <app>"
        switch_match = re.match(r"^switch\s+(?:to\s+)?(.+)$", text_lower)
        if switch_match:
            app_target = switch_match.group(1).strip()
            return RoutedPlan(
                is_ambiguous=False,
                tool_name="switch_app",
                arguments={"app_name": app_target},
                untrusted_injection_detected=has_injection,
            )

        # 8. Web search: "search for <query>" or "web search <query>"
        search_match = re.match(r"^(?:search\s+(?:for|the\s+web\s+for)?|google)\s+(.+)$", text_lower)
        if search_match:
            query = search_match.group(1).strip()
            return RoutedPlan(
                is_ambiguous=False,
                tool_name="web_search",
                arguments={"query": query},
                untrusted_injection_detected=has_injection,
            )

        # 9. List tasks: "list tasks", "show tasks"
        if "list tasks" in text_lower or "show tasks" in text_lower or "show my tasks" in text_lower:
            return RoutedPlan(
                is_ambiguous=False,
                tool_name="list_upcoming_tasks",
                arguments={"status": "open", "limit": 10},
                untrusted_injection_detected=has_injection,
            )

        # Default fallback
        return RoutedPlan(
            is_ambiguous=True,
            clarification_question="Could you please clarify your request?",
            untrusted_injection_detected=has_injection,
        )
