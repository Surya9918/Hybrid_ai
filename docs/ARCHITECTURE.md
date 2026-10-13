# AURA Companion — System Architecture

**Document Version:** 1.0.0  
**Target Environment:** Windows 11 on ARM64 (Qualcomm Snapdragon X Elite / Plus, Qualcomm Hexagon NPU)  
**Portability Objective:** AURA OS Microkernel Ready  

---

## 1. High-Level Component Architecture

AURA Companion is structured into three clean, decoupled layers:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER (WinUI 3)                        │
│  OrbWindow (Companion) │ HudWindow │ IslandWindow │ SelectionOverlay   │
│  LauncherWindow        │ SettingsWindow │ Visual Design System (Tokens) │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Direct Event / Binding
┌────────────────────────────────────▼────────────────────────────────────┐
│                  SHARED ASSISTANT CORE (Platform-Neutral)               │
│  - Agentic Execution Engine (Lifecycle State Machine & Bounded Retries) │
│  - Context-Aware Intent Classifier & Reference Resolver                 │
│  - Typed Tool Registry (Schemas, Risk Levels, Idempotency Cache)        │
│  - Persistent Productivity Engine (Tasks, Reminders, NL Parser)         │
│  - Security & Privacy Boundary (Untrusted Sanitizer, Clipboard Filter)  │
│  - Local-First Inference Router (QNN Hexagon NPU / GGUF CPU)            │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ IPlatformAdapter Contract
┌────────────────────────────────────▼────────────────────────────────────┐
│                    OPERATING SYSTEM ADAPTER LAYER                       │
│  WindowsPlatformAdapter (Win32/UWP) │ AuraOsPlatformAdapter (AURA OS)   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Event Flow & Agentic Tool Execution Lifecycle

Every user request follows an explicit, audited finite state machine:

```
[REQUEST_RECEIVED]
        │
        ▼
[CONTEXT_RESOLVED] ── (Resolves recent tasks, active windows, selected ROI)
        │
        ▼
[INTENT_CLASSIFIED] ── (Maps to registered capability or asks clarification)
        │
        ▼
[PLAN_CREATED]
        │
        ▼
[ARGUMENTS_VALIDATED] ── (Validates types against tool JSON Schema)
        │
        ▼
[PERMISSION_CHECKED] ── (Verifies capability against granted permissions)
        │
        ├── High-Risk Destructive? ──► [AWAITING_CONFIRMATION_IF_REQUIRED]
        │                                        │ (Confirmed)
        ▼                                        ▼
[EXECUTING] ◄────────────────────────────────────┘
   (Runs handler with bounded safe retries & idempotency caching)
        │
        ▼
[VERIFYING_RESULT] ── (Checks payload integrity)
        │
        ▼
[COMPLETED] / [FAILED] / [CANCELLED]
```

---

## 3. Context-Aware Routing & Reference Resolution

The `ContextRouter` evaluates natural language inputs and resolves anaphoric references without hallucination:
- **"Open VS Code"** -> Maps to `open_app(app_name="code")`.
- **"Open"** -> Flagged as ambiguous; returns clarification question: *"Which application would you like me to open?"*.
- **"Summarize this"** -> Evaluates active screen region (`selected_roi`); routes to `analyze_screen_region` or foreground window context.
- **"Mark my last task complete"** -> Queries recent tasks from SQLite; extracts the last task ID and passes it to `complete_task`.
- **"Try again"** -> Retrieves the last recoverable failed action and replays execution.

---

## 4. Security & Untrusted Input Boundary

- **Untrusted Sources:** All text extracted via OCR, screen capture, clipboard contents, and web snippets is treated as **untrusted data**.
- **Prompt Injection Defense:** Input is audited for adversarial instructions (e.g., *"Ignore previous instructions"*, *"admin mode"*, *"execute shell command"*). When detected, the content is encapsulated in strict data delimiters and blocked from invoking system tools or changing assistant behavior.
- **Destructive Gates:** Any tool categorized as `HIGH_RISK_DESTRUCTIVE` (such as `delete_task` or data wipes) halts in `AWAITING_CONFIRMATION_IF_REQUIRED` until explicit confirmation is provided.
- **Clipboard Sanitization:** Real-time regex auditing filters private keys, JWTs, API tokens, and passwords from clipboard history.

---

## 5. Persistent Storage & Transactional Guarantees

- **Engine:** SQLite with Write-Ahead Logging (`PRAGMA journal_mode=WAL;`).
- **Schema Migrations:** Managed through an explicit `schema_migrations` table with versioned, non-destructive migration scripts.
- **Search:** Virtual tables using SQLite `fts5` provide sub-millisecond full-text search across conversations, tasks, and memories.
- **Reminders Engine:** Timestamps are stored in UTC (`trigger_time_utc`), while user-intended local timezones (`local_timezone`) are preserved. On startup or system wake, `reconcile_on_startup_or_wake()` detects missed reminders and delivers catch-up alerts with guaranteed single-delivery semantics.

---

## 6. Windows ARM64 Adapters vs. AURA OS Portability

The shared core communicates with the host operating system strictly through the `IPlatformAdapter` interface:
1. **Windows Platform Adapter (`WindowsPlatformAdapter`):**
   - Utilizes Windows App SDK, Win32 Shell APIs, and Windows Composition.
   - Leverages Qualcomm QNN Execution Provider for hardware-accelerated NPU execution on Snapdragon X.
2. **AURA OS Platform Adapter (`AuraOsPlatformAdapter`):**
   - Decoupled from Windows binaries.
   - Defines system call boundaries for the future AURA microkernel (`aura.proc.spawn`, `aura.wm.focus`, `aura.display.capture`).
   - Enables the exact same assistant core to be compiled and linked directly against AURA OS native runtimes.
