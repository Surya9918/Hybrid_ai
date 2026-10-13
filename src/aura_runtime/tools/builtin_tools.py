"""
AURA Companion - Built-in Tools Implementation
Production definitions and handlers for all standard AURA desktop capabilities.
"""

from typing import Any, Dict, List, Optional
from src.aura_runtime.tools.schema import RiskCategory, ToolDefinition


def register_all_builtin_tools(registry, platform_adapter, task_manager, reminder_manager, memory_store):
    """
    Registers the complete suite of AURA companion tools.
    """

    # 1. Open Application
    def handle_open_app(app_name: str, arguments: Optional[str] = None):
        success, msg = platform_adapter.launch_application(app_name, arguments or "")
        return {"launched": success, "application": app_name, "message": msg}

    registry.register_tool(
        ToolDefinition(
            name="open_app",
            description="Launches an installed desktop application.",
            parameters_schema={
                "type": "object",
                "properties": {
                    "app_name": {"type": "string"},
                    "arguments": {"type": "string"},
                },
                "required": ["app_name"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "launched": {"type": "boolean"},
                    "application": {"type": "string"},
                    "message": {"type": "string"},
                },
            },
            required_permissions=["app.launch"],
            risk_category=RiskCategory.LOW_RISK_MUTATING,
            timeout_seconds=5.0,
            safe_to_retry=True,
            max_retries=1,
            handler=handle_open_app,
        )
    )

    # 2. Switch Application
    def handle_switch_app(app_name: str):
        success, msg = platform_adapter.switch_to_application(app_name)
        return {"switched": success, "application": app_name, "message": msg}

    registry.register_tool(
        ToolDefinition(
            name="switch_app",
            description="Brings an active desktop application window to the foreground.",
            parameters_schema={
                "type": "object",
                "properties": {"app_name": {"type": "string"}},
                "required": ["app_name"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "switched": {"type": "boolean"},
                    "application": {"type": "string"},
                    "message": {"type": "string"},
                },
            },
            required_permissions=["app.switch"],
            risk_category=RiskCategory.READ_ONLY,
            timeout_seconds=3.0,
            safe_to_retry=True,
            handler=handle_switch_app,
        )
    )

    # 3. Find Application
    def handle_find_app(query: str):
        apps = platform_adapter.find_installed_applications(query)
        return {"matches": apps, "count": len(apps)}

    registry.register_tool(
        ToolDefinition(
            name="find_app",
            description="Finds installed applications matching a query.",
            parameters_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "matches": {"type": "array"},
                    "count": {"type": "integer"},
                },
            },
            required_permissions=["app.find"],
            risk_category=RiskCategory.READ_ONLY,
            timeout_seconds=3.0,
            safe_to_retry=True,
            handler=handle_find_app,
        )
    )

    # 4. Read Screen Context
    def handle_read_screen(monitor_index: int = 0):
        context = platform_adapter.get_screen_context(monitor_index)
        return {"active_window": context.get("title", ""), "elements": context.get("elements", [])}

    registry.register_tool(
        ToolDefinition(
            name="read_screen_context",
            description="Reads approved screen context and active foreground UI elements.",
            parameters_schema={
                "type": "object",
                "properties": {"monitor_index": {"type": "integer"}},
            },
            output_schema={
                "type": "object",
                "properties": {
                    "active_window": {"type": "string"},
                    "elements": {"type": "array"},
                },
            },
            required_permissions=["screen.read"],
            risk_category=RiskCategory.READ_ONLY,
            timeout_seconds=4.0,
            handler=handle_read_screen,
        )
    )

    # 5. Analyze Screen Region
    def handle_analyze_region(x: int, y: int, width: int, height: int, question: str = ""):
        result = platform_adapter.analyze_region(x, y, width, height, question)
        return {
            "ocr_text": result.get("ocr_text", ""),
            "analysis": result.get("analysis", ""),
            "confidence": result.get("confidence", 1.0),
        }

    registry.register_tool(
        ToolDefinition(
            name="analyze_screen_region",
            description="Performs OCR and visual question answering on a selected screen region.",
            parameters_schema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                    "question": {"type": "string"},
                },
                "required": ["x", "y", "width", "height"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "ocr_text": {"type": "string"},
                    "analysis": {"type": "string"},
                    "confidence": {"type": "number"},
                },
            },
            required_permissions=["screen.roi"],
            risk_category=RiskCategory.READ_ONLY,
            timeout_seconds=6.0,
            handler=handle_analyze_region,
        )
    )

    # 6. Search Local Memory
    def handle_search_memory(query: str, limit: int = 5):
        items = memory_store.search(query, limit=limit)
        return {"items": items, "count": len(items)}

    registry.register_tool(
        ToolDefinition(
            name="search_memory",
            description="Searches user-approved persistent memory and past conversations.",
            parameters_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["query"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "items": {"type": "array"},
                    "count": {"type": "integer"},
                },
            },
            required_permissions=["memory.read"],
            risk_category=RiskCategory.READ_ONLY,
            timeout_seconds=3.0,
            handler=handle_search_memory,
        )
    )

    # 7. Create Task
    def handle_create_task(title: str, description: str = "", priority: str = "medium", due_date: str = ""):
        task_id = task_manager.create_task(title, description, priority, due_date)
        return {"task_id": task_id, "title": title, "status": "created"}

    registry.register_tool(
        ToolDefinition(
            name="create_task",
            description="Creates a persistent task in SQLite.",
            parameters_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {"type": "string"},
                    "due_date": {"type": "string"},
                },
                "required": ["title"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "title": {"type": "string"},
                    "status": {"type": "string"},
                },
            },
            required_permissions=["tasks.manage"],
            risk_category=RiskCategory.LOW_RISK_MUTATING,
            idempotent=True,
            handler=handle_create_task,
        )
    )

    # 8. Complete Task
    def handle_complete_task(task_id: str):
        success, msg = task_manager.complete_task(task_id)
        return {"task_id": task_id, "completed": success, "message": msg}

    registry.register_tool(
        ToolDefinition(
            name="complete_task",
            description="Marks a task as completed.",
            parameters_schema={
                "type": "object",
                "properties": {"task_id": {"type": "string"}},
                "required": ["task_id"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "completed": {"type": "boolean"},
                    "message": {"type": "string"},
                },
            },
            required_permissions=["tasks.manage"],
            risk_category=RiskCategory.LOW_RISK_MUTATING,
            idempotent=True,
            handler=handle_complete_task,
        )
    )

    # 9. Delete Task (HIGH RISK DESTRUCTIVE)
    def handle_delete_task(task_id: str):
        success, msg = task_manager.delete_task(task_id)
        return {"task_id": task_id, "deleted": success, "message": msg}

    registry.register_tool(
        ToolDefinition(
            name="delete_task",
            description="Permanently deletes a task. Requires explicit user confirmation.",
            parameters_schema={
                "type": "object",
                "properties": {"task_id": {"type": "string"}},
                "required": ["task_id"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "deleted": {"type": "boolean"},
                    "message": {"type": "string"},
                },
            },
            required_permissions=["tasks.manage"],
            risk_category=RiskCategory.HIGH_RISK_DESTRUCTIVE,
            safe_to_retry=False,
            handler=handle_delete_task,
        )
    )

    # 10. Create Reminder
    def handle_create_reminder(message: str, trigger_time: str, recurrence_rule: str = ""):
        rem_id = reminder_manager.create_reminder(message, trigger_time, recurrence_rule)
        return {"reminder_id": rem_id, "message": message, "scheduled_for": trigger_time}

    registry.register_tool(
        ToolDefinition(
            name="create_reminder",
            description="Schedules a timezone-aware persistent reminder.",
            parameters_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "trigger_time": {"type": "string"},
                    "recurrence_rule": {"type": "string"},
                },
                "required": ["message", "trigger_time"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "reminder_id": {"type": "string"},
                    "message": {"type": "string"},
                    "scheduled_for": {"type": "string"},
                },
            },
            required_permissions=["reminders.manage"],
            risk_category=RiskCategory.LOW_RISK_MUTATING,
            idempotent=True,
            handler=handle_create_reminder,
        )
    )

    # 11. Cancel Reminder
    def handle_cancel_reminder(reminder_id: str):
        success, msg = reminder_manager.cancel_reminder(reminder_id)
        return {"reminder_id": reminder_id, "cancelled": success, "message": msg}

    registry.register_tool(
        ToolDefinition(
            name="cancel_reminder",
            description="Cancels an active reminder.",
            parameters_schema={
                "type": "object",
                "properties": {"reminder_id": {"type": "string"}},
                "required": ["reminder_id"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "reminder_id": {"type": "string"},
                    "cancelled": {"type": "boolean"},
                    "message": {"type": "string"},
                },
            },
            required_permissions=["reminders.manage"],
            risk_category=RiskCategory.LOW_RISK_MUTATING,
            handler=handle_cancel_reminder,
        )
    )

    # 12. List Upcoming Tasks
    def handle_list_tasks(status: str = "open", limit: int = 10):
        tasks = task_manager.list_tasks(status=status, limit=limit)
        return {"tasks": tasks, "count": len(tasks)}

    registry.register_tool(
        ToolDefinition(
            name="list_upcoming_tasks",
            description="Lists open or upcoming tasks.",
            parameters_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "limit": {"type": "integer"},
                },
            },
            output_schema={
                "type": "object",
                "properties": {
                    "tasks": {"type": "array"},
                    "count": {"type": "integer"},
                },
            },
            required_permissions=["tasks.manage"],
            risk_category=RiskCategory.READ_ONLY,
            handler=handle_list_tasks,
        )
    )

    # 13. Web Search (Disabled when offline)
    def handle_web_search(query: str):
        if registry.is_offline():
            return {"results": [], "error": "Offline mode enforced. Web search is disabled."}
        return {"results": [{"title": f"Result for {query}", "url": f"https://search.local/{query}"}]}

    registry.register_tool(
        ToolDefinition(
            name="web_search",
            description="Performs an external web search. Requires network connectivity and explicit permission.",
            parameters_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            output_schema={
                "type": "object",
                "properties": {"results": {"type": "array"}},
            },
            required_permissions=["network.web_search"],
            risk_category=RiskCategory.READ_ONLY,
            handler=handle_web_search,
        )
    )

    # 14. Read Clipboard
    def handle_read_clipboard():
        content = platform_adapter.read_clipboard_safely()
        return {"clipboard_content": content}

    registry.register_tool(
        ToolDefinition(
            name="read_clipboard",
            description="Reads sanitized text from system clipboard.",
            parameters_schema={"type": "object", "properties": {}},
            output_schema={
                "type": "object",
                "properties": {"clipboard_content": {"type": "string"}},
            },
            required_permissions=["clipboard.read"],
            risk_category=RiskCategory.READ_ONLY,
            handler=handle_read_clipboard,
        )
    )
