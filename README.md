# Hybrid_ai — AURA Companion (Hitodama Replica)

> **Production-Ready, Local-First AI Desktop Companion for Windows on ARM64**  
> Faithfully inspired by Hitodama's publicly observable desktop experience and feature set.  
> Target Device: **Microsoft Surface Laptop 7th Edition** (Snapdragon X Elite / Plus, Hexagon NPU, Adreno GPU).

---

## 1. Project Overview

AURA Companion is a high-performance, power-efficient, offline-first personal desktop AI companion built natively for Windows on ARM64. It provides:
- **Floating Companion Orb & HUD:** Interactive particle/glow companion orb with smooth state transitions (Idle, Listening, Thinking, Speaking, Error).
- **Expandable Desktop Island & Launcher:** Dynamic context workspace, quick command launcher, and notification hub.
- **Context-Aware Agentic Tool Calling:** Typed tool registry with strict JSON schemas, permission gates, idempotency guarantees, and untrusted input defense.
- **Persistent Productivity Engine:** SQLite-backed tasks and timezone-aware reminders with sleep/wake catch-up reconciliation, duplicate-prevention, and natural-language parsing.
- **Local-First AI & Truthful Hardware Telemetry:** Offline inference support with Qualcomm QNN Execution Provider (Hexagon NPU) on Snapdragon X hardware, graceful CPU GGUF fallback, and zero-leakage offline enforcement.
- **Privacy & Security Boundaries:** Automatic redaction of sensitive credentials from clipboard history, explicit user confirmation for destructive actions, and prompt-injection neutralization.
- **AURA OS Portability Layer:** Decoupled platform-neutral assistant core ready for integration with the future AURA custom OS microkernel.

---

## 2. Supported Platforms & System Requirements

- **Primary Target:** Microsoft Surface Laptop 7th Edition (Windows 11 on ARM64, Build 22621+).
- **Architecture:** ARM64 native (`win-arm64`).
- **Processor:** Qualcomm Snapdragon X Elite / Snapdragon X Plus (12-core / 10-core Oryon CPU).
- **NPU Acceleration:** Qualcomm Hexagon NPU (45 TOPS) via Qualcomm QNN Execution Provider / ONNX Runtime GenAI.
- **Memory & Storage:** 16 GB+ LPDDR5x RAM, 512 GB+ NVMe SSD (minimum 4 GB free space for local models and SQLite database).
- **Audio & Input:** Integrated microphone array, Windows Composition APIs, Pen and Touch support.

---

## 3. Installation Guide

### Clean Installation via PowerShell
Run from an elevated PowerShell terminal on Windows on ARM64:
```powershell
# 1. Clone or download package repository
cd C:\AuraCompanion\packaging\scripts

# 2. Run automated installer
.\install.ps1 -PackagePath "..\..\dist\ARM64\AuraCompanion_v1.0.0_arm64.msix"
```

The installer verifies prerequisite runtimes (`Microsoft.WindowsAppRuntime.1.5`) and deploys the ARM64 MSIX application container.

---

## 4. First-Run Configuration & Local Model Setup

1. **First Launch:** Launch AURA Companion from the Start Menu or press `Win + Space`.
2. **Local AI Selection:**
   - Default Offline Model: `Phi-3.5-mini-instruct-Q4_K_M.gguf` (3.8B parameters, 2.2 GB VRAM/RAM footprint).
   - NPU Acceleration: In Settings, select **Hardware Acceleration -> Qualcomm QNN Execution Provider**. AURA will automatically bind to the Hexagon NPU if compatible weights are present.
3. **Permissions Review:**
   - Microphone: Granted for Push-to-Talk voice dictation.
   - Screen Capture: Granted for Region-of-Interest (ROI) selection and OCR.
4. **Offline Enforcement:**
   - Strict Offline Mode is enabled by default. Outbound network sockets are disabled, ensuring no conversation history, screenshots, or memory leave your Surface device.

---

## 5. Feature List & Keyboard Shortcuts

| Shortcut / Action | Feature | Description |
| :--- | :--- | :--- |
| `Win + Space` | Push-to-Talk / Toggle HUD | Activates voice listening state; speaks or types response. |
| `Win + Shift + C` | Screen Selection (ROI) | Opens translucent canvas to circle/drag a region for OCR and Q&A. |
| `Win + Shift + A` | Application Launcher | Fast search and launch for desktop applications. |
| `Win + Shift + I` | Toggle Desktop Island | Expands or collapses the dynamic productivity island. |
| `Win + Shift + S` | Settings & Privacy | Configures offline enforcement, model routing, and data export. |

---

## 6. Known Limitations & Honest Telemetry

- **Physical NPU Silicon Dependency:** Qualcomm Hexagon NPU acceleration requires running natively on Snapdragon X hardware with Qualcomm QNN drivers. On x86_64 virtualization environments, AURA runs on local CPU and transparently reports `CPU_LOCAL` in telemetry.
- **Sleep Wake Reminder Precision:** When the device enters Connected Standby or sleep, reminders due during sleep are dispatched upon wake according to catch-up reconciliation rules. Exact-second firing during deep sleep is subject to Windows power policy.
- **Cloud Fallback:** Cloud AI (Gemini / Anthropic) is disabled by default and completely blocked when Strict Offline Mode is active.

---

## 7. Troubleshooting

- **Microphone not detected:** Ensure microphone privacy is enabled under *Windows Settings > Privacy & Security > Microphone*.
- **Package sideloading warning:** On Windows 11 ARM64, enable *Developer Mode* under *Settings > System > For Developers* if installing an unsigned test build.
- **Database lock or corruption:** AURA uses SQLite WAL mode. In the rare event of sudden power loss, start the app normally; WAL automatic recovery restores database integrity without data loss.
