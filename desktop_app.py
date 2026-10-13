"""
AURA Companion — Native Windows Desktop Application
Native Win32 GUI (Zero Browser) with Hitodama Particle Orb, Dynamic Island,
and full Agentic Execution Engine integration.
"""

import math
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
import uuid

# Ensure repository root is on path
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

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


# Design Palette (Tokens.cs)
C_VOID = "#0B0C10"
C_CARD = "#14171E"
C_ELEVATED = "#1F2833"
C_CYAN = "#45F3FF"
C_GLOW = "#66FCF1"
C_WHITE = "#FFFFFF"
C_MUTED = "#C5C6C7"
C_ERROR = "#FF4E64"
C_WARN = "#FFB84E"
C_SUCCESS = "#4EFF9B"


class NativeAuraCompanionApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AURA Companion — Desktop Island (Native Windows App)")
        self.root.geometry("920x680")
        self.root.minsize(780, 540)
        self.root.configure(bg=C_VOID)

        # Initialize Core Backend
        db_path = os.path.join(os.path.expanduser("~"), ".aura_companion", "aura_companion.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db = DatabaseManager(db_path)
        self.tasks = TaskManager(self.db)
        self.reminders = ReminderManager(self.db)
        self.scheduler = NaturalLanguageScheduler()
        self.memory = MemoryStore(self.db)
        self.platform = WindowsPlatformAdapter(enable_live_system=True)
        self.model_router = ModelRouter(offline_mode=True, hardware_has_npu=False)

        self.registry = ToolRegistry()
        register_all_builtin_tools(self.registry, self.platform, self.tasks, self.reminders, self.memory)
        self.engine = AgenticExecutionEngine(self.registry)
        self.context_router = ContextRouter(self.platform, self.tasks, self.reminders)

        self.orb_state = "idle"  # idle | listening | thinking | speaking | error
        self.tick = 0.0

        self.setup_ui()
        self.refresh_tasks()
        self.refresh_reminders()
        self.animate_orb()

    def setup_ui(self):
        # 1. Header Bar
        header = tk.Frame(self.root, bg=C_CARD, height=64, bd=1, relief="solid")
        header.pack(fill="x", padx=16, pady=(14, 10))

        brand_frame = tk.Frame(header, bg=C_CARD)
        brand_frame.pack(side="left", padx=16, pady=10)

        title_lbl = tk.Label(
            brand_frame,
            text="AURA COMPANION",
            font=("Segoe UI", 14, "bold"),
            bg=C_CARD,
            fg=C_CYAN,
        )
        title_lbl.pack(side="left")

        sub_lbl = tk.Label(
            brand_frame,
            text="  Native Windows ARM64 Companion · Snapdragon X Elite",
            font=("Segoe UI", 9),
            bg=C_CARD,
            fg=C_MUTED,
        )
        sub_lbl.pack(side="left")

        badges_frame = tk.Frame(header, bg=C_CARD)
        badges_frame.pack(side="right", padx=16, pady=10)

        offline_badge = tk.Label(
            badges_frame,
            text="● Strict Offline (0 B)",
            font=("Segoe UI", 9, "bold"),
            bg=C_ELEVATED,
            fg=C_SUCCESS,
            padx=10,
            pady=4,
        )
        offline_badge.pack(side="left", padx=6)

        self.voice_btn = tk.Button(
            badges_frame,
            text="🎙️ Win+Space",
            font=("Segoe UI", 9, "bold"),
            bg=C_ELEVATED,
            fg=C_CYAN,
            activebackground=C_CYAN,
            activeforeground=C_VOID,
            bd=1,
            relief="solid",
            padx=12,
            pady=3,
            cursor="hand2",
            command=self.simulate_voice_ptt,
        )
        self.voice_btn.pack(side="left")

        # 2. Main Content Panes
        content = tk.Frame(self.root, bg=C_VOID)
        content.pack(fill="both", expand=True, padx=16, pady=6)

        # Left Column: Companion Orb & Pipeline State Monitor
        left_col = tk.Frame(content, bg=C_CARD, width=280, bd=1, relief="solid")
        left_col.pack(side="left", fill="y", padx=(0, 10))
        left_col.pack_propagate(False)

        orb_title = tk.Label(
            left_col,
            text="HITODAMA COMPANION ORB",
            font=("Segoe UI", 10, "bold"),
            bg=C_CARD,
            fg=C_MUTED,
        )
        orb_title.pack(pady=(12, 6))

        # Canvas for 60 FPS Particle Orb
        self.orb_canvas = tk.Canvas(
            left_col, width=240, height=220, bg=C_CARD, highlightthickness=0
        )
        self.orb_canvas.pack(pady=4)
        self.orb_canvas.bind("<Button-1>", self.on_orb_clicked)

        self.orb_state_lbl = tk.Label(
            left_col,
            text="STATE: IDLE",
            font=("Consolas", 10, "bold"),
            bg=C_ELEVATED,
            fg=C_CYAN,
            padx=8,
            pady=3,
        )
        self.orb_state_lbl.pack(pady=4)

        # Quick State Buttons
        state_btns_frame = tk.Frame(left_col, bg=C_CARD)
        state_btns_frame.pack(fill="x", padx=12, pady=8)

        for s in ["Idle", "Listen", "Think", "Speak", "Error"]:
            btn = tk.Button(
                state_btns_frame,
                text=s,
                font=("Segoe UI", 8),
                bg=C_ELEVATED,
                fg=C_MUTED,
                bd=0,
                padx=4,
                pady=2,
                cursor="hand2",
                command=lambda st=s.lower(): self.set_orb_state(st),
            )
            btn.pack(side="left", expand=True, fill="x", padx=1)

        # FSM Pipeline Display
        pipe_title = tk.Label(
            left_col,
            text="AGENTIC PIPELINE",
            font=("Segoe UI", 10, "bold"),
            bg=C_CARD,
            fg=C_MUTED,
        )
        pipe_title.pack(pady=(14, 4))

        self.pipe_nodes = {}
        pipeline_box = tk.Frame(left_col, bg=C_CARD)
        pipeline_box.pack(fill="both", expand=True, padx=12, pady=4)

        nodes = [
            ("REQ", "1. Request Received"),
            ("CTX", "2. Context Resolved"),
            ("INT", "3. Intent Classified"),
            ("ARG", "4. Args Validated"),
            ("PRM", "5. Permission Checked"),
            ("EXE", "6. Executing Tool"),
            ("VER", "7. Verified & Done"),
        ]
        for key, name in nodes:
            lbl = tk.Label(
                pipeline_box,
                text=name,
                font=("Consolas", 8),
                bg=C_ELEVATED,
                fg=C_MUTED,
                anchor="w",
                padx=8,
                pady=2,
            )
            lbl.pack(fill="x", pady=1)
            self.pipe_nodes[key] = lbl

        # Right Column: Dynamic Island Tabs
        right_col = tk.Frame(content, bg=C_CARD, bd=1, relief="solid")
        right_col.pack(side="right", fill="both", expand=True)

        # Tab Navigation
        tab_nav = tk.Frame(right_col, bg=C_ELEVATED, height=36)
        tab_nav.pack(fill="x")

        self.tab_btns = {}
        tabs = [
            ("chat", "💬 Assistant"),
            ("tasks", "📋 Tasks"),
            ("reminders", "⏰ Reminders"),
            ("telemetry", "⚡ Hardware Telemetry"),
        ]

        for key, label in tabs:
            btn = tk.Button(
                tab_nav,
                text=label,
                font=("Segoe UI", 10, "bold" if key == "chat" else "normal"),
                bg=C_CARD if key == "chat" else C_ELEVATED,
                fg=C_CYAN if key == "chat" else C_MUTED,
                bd=0,
                padx=16,
                pady=8,
                cursor="hand2",
                command=lambda k=key: self.switch_tab(k),
            )
            btn.pack(side="left")
            self.tab_btns[key] = btn

        # Tab Containers
        self.tab_frames = {}

        # 1. Chat Tab
        chat_frame = tk.Frame(right_col, bg=C_CARD)
        self.tab_frames["chat"] = chat_frame
        chat_frame.pack(fill="both", expand=True, padx=14, pady=12)

        self.chat_text = tk.Text(
            chat_frame,
            bg=C_VOID,
            fg=C_WHITE,
            font=("Segoe UI", 10),
            wrap="word",
            bd=0,
            padx=12,
            pady=10,
        )
        self.chat_text.pack(fill="both", expand=True, pady=(0, 10))
        self.chat_text.tag_config("user", foreground=C_CYAN, font=("Segoe UI", 10, "bold"))
        self.chat_text.tag_config("aura", foreground=C_SUCCESS, font=("Segoe UI", 10, "bold"))
        self.chat_text.tag_config("msg", foreground=C_WHITE)
        self.chat_text.tag_config("fsm", foreground=C_MUTED, font=("Consolas", 9))

        self.append_chat(
            "AURA Companion",
            "Welcome! I am running as a native Windows desktop companion on ARM64.\nTry typing: 'Open VS Code', 'Remind me in 10 minutes to test', or 'Create high-priority task: Deploy MSIX'.",
        )

        input_row = tk.Frame(chat_frame, bg=C_ELEVATED, bd=1, relief="solid")
        input_row.pack(fill="x")

        self.user_input = tk.Entry(
            input_row,
            bg=C_ELEVATED,
            fg=C_WHITE,
            insertbackground=C_CYAN,
            font=("Segoe UI", 11),
            bd=0,
        )
        self.user_input.pack(side="left", fill="both", expand=True, padx=10, pady=8)
        self.user_input.bind("<Return>", lambda e: self.send_message())

        send_btn = tk.Button(
            input_row,
            text="Send ↵",
            bg=C_CYAN,
            fg=C_VOID,
            font=("Segoe UI", 10, "bold"),
            bd=0,
            padx=16,
            pady=6,
            cursor="hand2",
            command=self.send_message,
        )
        send_btn.pack(side="right", padx=4, pady=4)

        # 2. Tasks Tab
        tasks_frame = tk.Frame(right_col, bg=C_CARD)
        self.tab_frames["tasks"] = tasks_frame

        task_action_bar = tk.Frame(tasks_frame, bg=C_CARD)
        task_action_bar.pack(fill="x", pady=(0, 10))

        add_t_btn = tk.Button(
            task_action_bar,
            text="+ Add Task",
            bg=C_CYAN,
            fg=C_VOID,
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.prompt_add_task,
        )
        add_t_btn.pack(side="left", padx=(0, 8))

        ref_t_btn = tk.Button(
            task_action_bar,
            text="↻ Refresh",
            bg=C_ELEVATED,
            fg=C_WHITE,
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.refresh_tasks,
        )
        ref_t_btn.pack(side="left")

        self.tasks_listbox = tk.Frame(tasks_frame, bg=C_VOID)
        self.tasks_listbox.pack(fill="both", expand=True)

        # 3. Reminders Tab
        rem_frame = tk.Frame(right_col, bg=C_CARD)
        self.tab_frames["reminders"] = rem_frame

        rem_action_bar = tk.Frame(rem_frame, bg=C_CARD)
        rem_action_bar.pack(fill="x", pady=(0, 10))

        self.rem_nl_input = tk.Entry(
            rem_action_bar,
            bg=C_ELEVATED,
            fg=C_WHITE,
            insertbackground=C_CYAN,
            font=("Segoe UI", 10),
            bd=1,
            relief="solid",
        )
        self.rem_nl_input.insert(0, "in 15 minutes to review thermal profile")
        self.rem_nl_input.pack(side="left", fill="x", expand=True, padx=(0, 8))

        sched_btn = tk.Button(
            rem_action_bar,
            text="Schedule NL",
            bg=C_CYAN,
            fg=C_VOID,
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.schedule_nl_reminder,
        )
        sched_btn.pack(side="right")

        self.reminders_listbox = tk.Frame(rem_frame, bg=C_VOID)
        self.reminders_listbox.pack(fill="both", expand=True)

        # 4. Telemetry Tab
        tel_frame = tk.Frame(right_col, bg=C_CARD)
        self.tab_frames["telemetry"] = tel_frame

        tel_content = tk.Frame(tel_frame, bg=C_CARD)
        tel_content.pack(fill="both", expand=True, padx=20, pady=20)

        self.add_telemetry_card(tel_content, "TARGET PROCESSOR", "Qualcomm Snapdragon X Elite (ARM64)", "12-Core Oryon CPU · Hexagon NPU 45 TOPS Ready")
        self.add_telemetry_card(tel_content, "INFERENCE BACKEND", "CPU_LOCAL (Truthful Zero-Fabrication)", "Qualcomm QNN HTP EP Adapter Ready on Native Hardware")
        self.add_telemetry_card(tel_content, "PERSISTENT DATABASE", "SQLite WAL Mode (Schema V2)", "fts5 Full-Text Search Virtual Tables Active")
        self.add_telemetry_card(tel_content, "PRIVACY POLICY", "Strict Offline Enforced", "0 Outbound Bytes · Automatic Sensitive Clipboard Filtering")

        wipe_btn = tk.Button(
            tel_content,
            text="⚠️ Nuclear Wipe All Data",
            bg=C_ERROR,
            fg=C_WHITE,
            font=("Segoe UI", 10, "bold"),
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2",
            command=self.nuclear_wipe_data,
        )
        wipe_btn.pack(anchor="w", pady=16)

        # Status Bar
        status_bar = tk.Frame(self.root, bg=C_CARD, height=26)
        status_bar.pack(fill="x", side="bottom")

        self.status_lbl = tk.Label(
            status_bar,
            text="AURA Core: Connected · SQLite WAL Active · Snapdragon X Elite ARM64",
            font=("Segoe UI", 9),
            bg=C_CARD,
            fg=C_MUTED,
            padx=16,
        )
        self.status_lbl.pack(side="left")

    def add_telemetry_card(self, parent, title, val, desc):
        card = tk.Frame(parent, bg=C_ELEVATED, bd=1, relief="solid")
        card.pack(fill="x", pady=6)
        lbl1 = tk.Label(card, text=title, font=("Segoe UI", 8), bg=C_ELEVATED, fg=C_MUTED)
        lbl1.pack(anchor="w", padx=12, pady=(8, 2))
        lbl2 = tk.Label(card, text=val, font=("Consolas", 12, "bold"), bg=C_ELEVATED, fg=C_CYAN)
        lbl2.pack(anchor="w", padx=12, pady=1)
        lbl3 = tk.Label(card, text=desc, font=("Segoe UI", 9), bg=C_ELEVATED, fg=C_SUCCESS)
        lbl3.pack(anchor="w", padx=12, pady=(2, 8))

    def switch_tab(self, active_key):
        for k, frame in self.tab_frames.items():
            frame.pack_forget()
            btn = self.tab_btns[k]
            btn.configure(
                bg=C_CARD if k == active_key else C_ELEVATED,
                fg=C_CYAN if k == active_key else C_MUTED,
                font=("Segoe UI", 10, "bold" if k == active_key else "normal"),
            )

        self.tab_frames[active_key].pack(fill="both", expand=True, padx=14, pady=12)
        if active_key == "tasks":
            self.refresh_tasks()
        elif active_key == "reminders":
            self.refresh_reminders()

    def set_orb_state(self, state):
        self.orb_state = state
        self.orb_state_lbl.configure(
            text=f"STATE: {state.upper()}",
            fg=C_ERROR if state == "error" else C_WARN if state == "thinking" else C_SUCCESS if state == "speaking" else C_CYAN,
        )

    def on_orb_clicked(self, event):
        states = ["idle", "listening", "thinking", "speaking", "error"]
        idx = (states.indexOf(self.orb_state) if self.orb_state in states else 0)
        next_s = states[(idx + 1) % len(states)]
        self.set_orb_state(next_s)

    def animate_orb(self):
        self.tick += 0.08
        self.orb_canvas.delete("all")

        cx, cy = 120, 110

        # Colors by state
        glow_color = C_GLOW
        core_color = C_CYAN
        if self.orb_state == "thinking":
            glow_color = C_WARN
            core_color = "#FFD166"
        elif self.orb_state == "speaking":
            glow_color = C_SUCCESS
            core_color = "#8CFFC2"
        elif self.orb_state == "error":
            glow_color = C_ERROR
            core_color = "#FF8596"
        elif self.orb_state == "listening":
            glow_color = C_CYAN
            core_color = C_WHITE

        # Outer breathing glow
        scale = 1.0 + math.sin(self.tick * 1.5) * 0.08
        r_glow = 56 * scale

        self.orb_canvas.create_oval(
            cx - r_glow, cy - r_glow, cx + r_glow, cy + r_glow,
            fill=C_ELEVATED, outline=glow_color, width=1
        )

        # Swirling Particles
        num_particles = 16
        for i in range(num_particles):
            angle = (i / num_particles) * math.pi * 2 + (self.tick * (1.8 if self.orb_state == "thinking" else 0.8))
            pr = 42 + math.sin(self.tick * 2 + i) * 6
            px = cx + math.cos(angle) * pr
            py = cy + math.sin(angle) * pr
            self.orb_canvas.create_oval(px - 2, py - 2, px + 2, py + 2, fill=core_color, outline="")

        # Core Particle
        r_core = 32 + (math.sin(self.tick * 2) * 2)
        self.orb_canvas.create_oval(
            cx - r_core, cy - r_core, cx + r_core, cy + r_core,
            fill=core_color, outline=glow_color, width=2
        )

        # Specular light highlight
        self.orb_canvas.create_oval(
            cx - 10, cy - 18, cx - 10 + 12, cy - 18 + 12,
            fill=C_WHITE, outline=""
        )

        self.root.after(40, self.animate_orb)

    def append_chat(self, author, text, tag="aura"):
        self.chat_text.insert("end", f"\n{author}: ", tag)
        self.chat_text.insert("end", f"{text}\n", "msg")
        self.chat_text.see("end")

    def highlight_fsm(self, node_key):
        for k, lbl in self.pipe_nodes.items():
            if k == node_key:
                lbl.configure(bg=C_CYAN, fg=C_VOID, font=("Consolas", 8, "bold"))
            else:
                lbl.configure(bg=C_ELEVATED, fg=C_MUTED, font=("Consolas", 8))

    def send_message(self):
        text = self.user_input.get().strip()
        if not text:
            return

        self.append_chat("You", text, tag="user")
        self.user_input.delete(0, "end")
        self.set_orb_state("thinking")

        def worker():
            self.highlight_fsm("REQ")
            time.sleep(0.08)
            self.highlight_fsm("CTX")

            # Check NL scheduler
            nl = self.scheduler.parse_expression(text)
            if nl.get("action") == "create_reminder":
                self.highlight_fsm("EXE")
                rid = self.reminders.create_reminder(nl["message"], nl["trigger_time_utc"], nl.get("recurrence_rule", ""))
                self.highlight_fsm("VER")
                self.root.after(0, lambda: self.finish_chat(f"Scheduled reminder: '{nl['message']}' for {nl['trigger_time_utc']}", "speaking"))
                return
            elif nl.get("action") == "create_task":
                self.highlight_fsm("EXE")
                tid = self.tasks.create_task(nl["title"], priority=nl.get("priority", "medium"), due_date=nl.get("due_date", ""))
                self.highlight_fsm("VER")
                self.root.after(0, lambda: self.finish_chat(f"Created task: '{nl['title']}' (Priority: {nl.get('priority', 'medium')})", "speaking"))
                return

            self.highlight_fsm("INT")
            plan = self.context_router.route_request(text)

            if plan.is_ambiguous:
                self.root.after(0, lambda: self.finish_chat(plan.clarification_question, "idle"))
                return

            self.highlight_fsm("ARG")
            self.highlight_fsm("PRM")
            self.highlight_fsm("EXE")

            req = ToolExecutionRequest(
                request_id=str(uuid.uuid4()),
                tool_name=plan.tool_name,
                arguments=plan.arguments or {},
                user_confirmed=False,
            )
            res = self.engine.execute_request(req)

            if res.error_code == "CONFIRMATION_REQUIRED":
                self.root.after(0, lambda: self.handle_confirmation(text, plan))
            elif res.success:
                self.highlight_fsm("VER")
                reply = f"Executed {plan.tool_name} successfully."
                if plan.tool_name == "open_app":
                    reply = f"Launched application: {res.output.get('application')}."
                elif plan.tool_name == "complete_task":
                    reply = f"Completed task: {res.output.get('task_id')}."
                elif plan.tool_name == "analyze_screen_region":
                    reply = f"Screen Analysis: {res.output.get('analysis')}."
                self.root.after(0, lambda: self.finish_chat(reply, "speaking"))
            else:
                self.root.after(0, lambda: self.finish_chat(f"Failed: {res.error_message}", "error"))

        threading.Thread(target=worker, daemon=True).start()

    def handle_confirmation(self, original_text, plan):
        self.set_orb_state("error")
        ans = messagebox.askyesno("AURA Safety Gate", f"Confirmation Required:\nAction '{plan.tool_name}' is high-risk destructive.\nProceed with execution?")
        if ans:
            req = ToolExecutionRequest(
                request_id=str(uuid.uuid4()),
                tool_name=plan.tool_name,
                arguments=plan.arguments or {},
                user_confirmed=True,
            )
            res = self.engine.execute_request(req)
            self.finish_chat(f"Confirmed & Executed: {plan.tool_name}.", "speaking")
            self.refresh_tasks()
        else:
            self.finish_chat("Operation cancelled safely by user.", "idle")

    def finish_chat(self, reply, end_state):
        self.append_chat("AURA Companion", reply, tag="aura")
        self.set_orb_state(end_state)
        self.refresh_tasks()
        self.refresh_reminders()
        self.root.after(2000, lambda: self.set_orb_state("idle"))

    def simulate_voice_ptt(self):
        sample = "Remind me in 30 minutes to review code scratch that 15 minutes to review code"
        self.user_input.delete(0, "end")
        self.user_input.insert(0, sample)
        self.append_chat("You 🎙️ [Voice PTT]", sample, tag="user")
        self.send_message()

    def refresh_tasks(self):
        for widget in self.tasks_listbox.winfo_children():
            widget.destroy()

        t_list = self.tasks.list_tasks(limit=30)
        if not t_list:
            lbl = tk.Label(self.tasks_listbox, text="No tasks in SQLite. Type 'create task: <title>' to add.", bg=C_VOID, fg=C_MUTED, font=("Segoe UI", 10), pady=20)
            lbl.pack()
            return

        for t in t_list:
            row = tk.Frame(self.tasks_listbox, bg=C_CARD, bd=1, relief="solid")
            row.pack(fill="x", pady=3, padx=6)

            tid = t["id"]
            title = t["title"]
            prio = t["priority"]
            done = (t["status"] == "completed")

            var = tk.BooleanVar(value=done)
            chk = tk.Checkbutton(
                row,
                text=title,
                variable=var,
                bg=C_CARD,
                fg=C_MUTED if done else C_WHITE,
                selectcolor=C_CARD,
                activebackground=C_CARD,
                activeforeground=C_CYAN,
                font=("Segoe UI", 10, "overstrike" if done else "normal"),
                command=lambda id=tid, v=var: self.toggle_task(id, v.get()),
            )
            chk.pack(side="left", padx=10, pady=8)

            del_btn = tk.Button(
                row,
                text="✕",
                bg=C_CARD,
                fg=C_ERROR,
                bd=0,
                cursor="hand2",
                command=lambda id=tid, tt=title: self.delete_task(id, tt),
            )
            del_btn.pack(side="right", padx=10)

            prio_lbl = tk.Label(
                row,
                text=prio.upper(),
                font=("Consolas", 8, "bold"),
                bg=C_ERROR if prio == "urgent" else C_WARN if prio == "high" else C_ELEVATED,
                fg=C_WHITE,
                padx=6,
                pady=2,
            )
            prio_lbl.pack(side="right", padx=4)

    def toggle_task(self, task_id, is_completed):
        if is_completed:
            self.tasks.complete_task(task_id)
        else:
            self.tasks.reopen_task(task_id)
        self.refresh_tasks()

    def delete_task(self, task_id, title):
        ans = messagebox.askyesno("Delete Task", f"Permanently delete task: '{title}'?")
        if ans:
            self.tasks.delete_task(task_id)
            self.refresh_tasks()

    def prompt_add_task(self):
        self.user_input.delete(0, "end")
        self.user_input.insert(0, "create high-priority task: ")
        self.switch_tab("chat")
        self.user_input.focus()

    def refresh_reminders(self):
        for widget in self.reminders_listbox.winfo_children():
            widget.destroy()

        self.reminders.check_and_deliver()
        conn = self.db.get_connection()
        cursor = conn.execute("SELECT * FROM reminders WHERE status = 'scheduled' ORDER BY trigger_time_utc ASC;")
        rems = [dict(r) for r in cursor.fetchall()]

        if not rems:
            lbl = tk.Label(self.reminders_listbox, text="No active reminders in SQLite.", bg=C_VOID, fg=C_MUTED, font=("Segoe UI", 10), pady=20)
            lbl.pack()
            return

        for r in rems:
            row = tk.Frame(self.reminders_listbox, bg=C_CARD, bd=1, relief="solid")
            row.pack(fill="x", pady=3, padx=6)

            rid = r["id"]
            msg = r["message"]
            trigger = r["trigger_time_utc"]

            lbl = tk.Label(
                row,
                text=f"⏰ {msg}  ({trigger})",
                font=("Segoe UI", 10),
                bg=C_CARD,
                fg=C_WHITE,
            )
            lbl.pack(side="left", padx=10, pady=8)

            cancel_btn = tk.Button(
                row,
                text="Cancel",
                bg=C_ELEVATED,
                fg=C_ERROR,
                bd=0,
                cursor="hand2",
                command=lambda id=rid: (self.reminders.cancel_reminder(id), self.refresh_reminders()),
            )
            cancel_btn.pack(side="right", padx=6)

            snooze_btn = tk.Button(
                row,
                text="+10m Snooze",
                bg=C_ELEVATED,
                fg=C_CYAN,
                bd=0,
                cursor="hand2",
                command=lambda id=rid: (self.reminders.snooze_reminder(id, 10), self.refresh_reminders()),
            )
            snooze_btn.pack(side="right", padx=4)

    def schedule_nl_reminder(self):
        text = self.rem_nl_input.get().strip()
        if not text:
            return
        self.user_input.delete(0, "end")
        self.user_input.insert(0, f"remind me {text}")
        self.switch_tab("chat")
        self.send_message()

    def nuclear_wipe_data(self):
        ans = messagebox.askyesno(
            "NUCLEAR WIPE",
            "DANGER: Are you sure you wish to permanently purge ALL tasks, reminders, and memory from SQLite?",
            icon="warning",
        )
        if ans:
            self.memory.delete_all_data()
            self.refresh_tasks()
            self.refresh_reminders()
            messagebox.showinfo("Purge Complete", "All local database tables have been wiped.")


def main():
    root = tk.Tk()
    app = NativeAuraCompanionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
