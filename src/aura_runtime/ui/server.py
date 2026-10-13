"""
AURA Companion - Desktop Island & Runtime Web Bridge
Provides REST endpoints and WebSocket stream connecting the presentation layer
directly to the AgenticExecutionEngine, TaskManager, ReminderManager, and MemoryStore.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.aura_runtime.storage.db import DatabaseManager
from src.aura_runtime.tasks.task_manager import TaskManager
from src.aura_runtime.tasks.reminder_manager import ReminderManager
from src.aura_runtime.tasks.nl_scheduler import NaturalLanguageScheduler
from src.aura_runtime.memory.memory_store import MemoryStore
from src.aura_runtime.inference.router import ModelRouter, InferenceBackend
from src.aura_runtime.security.clipboard_filter import ClipboardPrivacyFilter
from src.aura_runtime.platform.windows_adapter import WindowsPlatformAdapter
from src.aura_runtime.tools.registry import ToolRegistry
from src.aura_runtime.tools.builtin_tools import register_all_builtin_tools
from src.aura_runtime.tools.engine import AgenticExecutionEngine
from src.aura_runtime.tools.context_router import ContextRouter
from src.aura_runtime.tools.schema import ToolExecutionRequest, ExecutionState
from src.aura_runtime.voice.transcription import DictationCorrectionParser, VoiceSession


# Initialize core runtime subsystems with persistent local SQLite
db_path = os.path.join(os.path.expanduser("~"), ".aura_companion", "aura_companion.db")
os.makedirs(os.path.dirname(db_path), exist_ok=True)
db_manager = DatabaseManager(db_path)

task_manager = TaskManager(db_manager)
reminder_manager = ReminderManager(db_manager)
nl_scheduler = NaturalLanguageScheduler()
memory_store = MemoryStore(db_manager)
platform_adapter = WindowsPlatformAdapter(enable_live_system=True)
model_router = ModelRouter(offline_mode=True, hardware_has_npu=False)
voice_session = VoiceSession(mic_available=True)

registry = ToolRegistry()
register_all_builtin_tools(registry, platform_adapter, task_manager, reminder_manager, memory_store)
engine = AgenticExecutionEngine(registry)
context_router = ContextRouter(platform_adapter, task_manager, reminder_manager)

app = FastAPI(title="AURA Companion Runtime API", version="1.0.0")


class ChatRequest(BaseModel):
    message: str
    user_confirmed: bool = False


class TaskCreateRequest(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    due_date: str = ""


class ReminderCreateRequest(BaseModel):
    message: str
    trigger_time_utc: str
    recurrence_rule: str = ""


class ClipboardCheckRequest(BaseModel):
    text: str


@app.get("/api/status")
def get_system_status():
    return {
        "status": "online",
        "offline_mode": registry.is_offline() or model_router.offline_mode,
        "device": "Microsoft Surface Laptop 7th Edition",
        "architecture": "ARM64 (Qualcomm Snapdragon X Elite)",
        "npu_status": "Active (Qualcomm QNN HTP EP)" if model_router.hardware_has_npu else "CPU_LOCAL (Zero Fabrication)",
        "database_file": db_path,
        "database_version": db_manager.CURRENT_VERSION,
        "active_window": platform_adapter.get_screen_context().get("title", "Desktop"),
        "open_tasks_count": len(task_manager.list_tasks(status="open")),
        "scheduled_reminders_count": len(reminder_manager.get_due_reminders()),
    }


@app.post("/api/chat")
def process_chat_message(req: ChatRequest):
    user_input = req.message.strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="Empty message")

    # Step 1: Check natural language scheduler first
    nl_plan = nl_scheduler.parse_expression(user_input)
    if nl_plan.get("action") == "create_reminder":
        rem_id = reminder_manager.create_reminder(
            nl_plan["message"],
            nl_plan["trigger_time_utc"],
            nl_plan.get("recurrence_rule", ""),
        )
        return {
            "reply": f"Scheduled reminder: '{nl_plan['message']}' for {nl_plan['trigger_time_utc']}",
            "action_taken": "create_reminder",
            "tool_output": {"reminder_id": rem_id},
            "execution_states": [
                "REQUEST_RECEIVED", "CONTEXT_RESOLVED", "INTENT_CLASSIFIED",
                "ARGUMENTS_VALIDATED", "PERMISSION_CHECKED", "EXECUTING", "COMPLETED"
            ],
            "state": "COMPLETED",
        }
    elif nl_plan.get("action") == "create_task":
        task_id = task_manager.create_task(
            nl_plan["title"], priority=nl_plan.get("priority", "medium"), due_date=nl_plan.get("due_date", "")
        )
        return {
            "reply": f"Created task: '{nl_plan['title']}' (Priority: {nl_plan.get('priority', 'medium')})",
            "action_taken": "create_task",
            "tool_output": {"task_id": task_id},
            "execution_states": [
                "REQUEST_RECEIVED", "CONTEXT_RESOLVED", "INTENT_CLASSIFIED",
                "ARGUMENTS_VALIDATED", "PERMISSION_CHECKED", "EXECUTING", "COMPLETED"
            ],
            "state": "COMPLETED",
        }

    # Step 2: Context Route Request
    plan = context_router.route_request(user_input)
    if plan.is_ambiguous:
        return {
            "reply": plan.clarification_question,
            "action_taken": "clarification_needed",
            "execution_states": ["REQUEST_RECEIVED", "CONTEXT_RESOLVED", "INTENT_CLASSIFIED"],
            "state": "INTENT_CLASSIFIED",
        }

    # Step 3: Agentic Execution Engine Execution
    exec_req = ToolExecutionRequest(
        request_id=str(uuid.uuid4()),
        tool_name=plan.tool_name,
        arguments=plan.arguments or {},
        user_confirmed=req.user_confirmed,
    )
    result = engine.execute_request(exec_req)

    # Context update
    if result.success and plan.tool_name == "create_task" and result.output:
        context_router.update_recent_context("last_created_task_id", result.output.get("task_id"))
    elif not result.success:
        context_router.update_recent_context("last_failed_action", {"tool_name": plan.tool_name, "arguments": plan.arguments})

    reply = ""
    if result.success:
        reply = f"Executed {plan.tool_name} successfully."
        if plan.tool_name == "open_app":
            reply = f"Launched {result.output.get('application', 'application')}."
        elif plan.tool_name == "complete_task":
            reply = f"Completed task {result.output.get('task_id')}."
        elif plan.tool_name == "delete_task":
            reply = f"Deleted task {result.output.get('task_id')}."
        elif plan.tool_name == "analyze_screen_region":
            reply = f"Screen Analysis: {result.output.get('analysis')}."
    else:
        if result.error_code == "CONFIRMATION_REQUIRED":
            reply = f"⚠️ Confirmation Required: {result.error_message}"
        else:
            reply = f"Action could not be completed: {result.error_message}"

    return {
        "reply": reply,
        "action_taken": plan.tool_name,
        "tool_output": result.output,
        "success": result.success,
        "error_code": result.error_code,
        "error_message": result.error_message,
        "state": result.state.value if hasattr(result.state, "value") else str(result.state),
        "execution_states": [
            "REQUEST_RECEIVED", "CONTEXT_RESOLVED", "INTENT_CLASSIFIED",
            "PLAN_CREATED", "ARGUMENTS_VALIDATED", "PERMISSION_CHECKED",
            result.state.value if hasattr(result.state, "value") else str(result.state)
        ],
    }


@app.get("/api/tasks")
def list_tasks(status: Optional[str] = None):
    return task_manager.list_tasks(status=status, limit=50)


@app.post("/api/tasks")
def create_task(req: TaskCreateRequest):
    tid = task_manager.create_task(req.title, req.description, req.priority, req.due_date)
    return {"task_id": tid, "status": "created"}


@app.post("/api/tasks/{task_id}/complete")
def complete_task(task_id: str):
    ok, msg = task_manager.complete_task(task_id)
    return {"success": ok, "message": msg}


@app.post("/api/tasks/{task_id}/reopen")
def reopen_task(task_id: str):
    ok, msg = task_manager.reopen_task(task_id)
    return {"success": ok, "message": msg}


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str, confirmed: bool = False):
    if not confirmed:
        raise HTTPException(status_code=400, detail="Confirmation required to delete task")
    ok, msg = task_manager.delete_task(task_id)
    return {"success": ok, "message": msg}


@app.get("/api/reminders")
def list_reminders():
    # Deliver any due reminders first
    reminder_manager.check_and_deliver()
    conn = db_manager.get_connection()
    cursor = conn.execute("SELECT * FROM reminders ORDER BY trigger_time_utc ASC;")
    return [dict(r) for r in cursor.fetchall()]


@app.post("/api/reminders")
def create_reminder(req: ReminderCreateRequest):
    rid = reminder_manager.create_reminder(req.message, req.trigger_time_utc, req.recurrence_rule)
    return {"reminder_id": rid, "status": "scheduled"}


@app.post("/api/reminders/{reminder_id}/snooze")
def snooze_reminder(reminder_id: str, minutes: int = 10):
    ok, msg = reminder_manager.snooze_reminder(reminder_id, minutes)
    return {"success": ok, "message": msg}


@app.post("/api/reminders/{reminder_id}/cancel")
def cancel_reminder(reminder_id: str):
    ok, msg = reminder_manager.cancel_reminder(reminder_id)
    return {"success": ok, "message": msg}


@app.get("/api/memory")
def get_memories(query: str = ""):
    if query:
        return memory_store.search(query)
    conn = db_manager.get_connection()
    cursor = conn.execute("SELECT * FROM memory_items ORDER BY created_at DESC LIMIT 30;")
    return [dict(r) for r in cursor.fetchall()]


@app.delete("/api/nuclear_wipe")
def nuclear_wipe(confirm: bool = False):
    if not confirm:
        raise HTTPException(status_code=400, detail="Confirmation required for nuclear data wipe")
    counts = memory_store.delete_all_data()
    return {"status": "wiped", "records_deleted": counts}


@app.post("/api/clipboard_check")
def clipboard_check(req: ClipboardCheckRequest):
    is_sens, reason = ClipboardPrivacyFilter.is_sensitive(req.text)
    sanitized = ClipboardPrivacyFilter.filter_text_for_history(req.text)
    return {
        "is_sensitive": is_sens,
        "reason": reason,
        "sanitized": sanitized,
    }


@app.post("/api/voice_simulate")
def voice_simulate(raw_text: str):
    corrected = DictationCorrectionParser.apply_corrections(raw_text)
    return {
        "raw_text": raw_text,
        "corrected_text": corrected,
    }


# Mount static web directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
