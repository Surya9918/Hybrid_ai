# AURA OS Portability Layer Specification

**Objective:** Architectural decoupling of the AURA Companion assistant core for seamless porting to the future custom AURA Operating System microkernel.

---

## 1. Decoupled Core Architecture

To prevent vendor lock-in to the Windows platform, the assistant logic (`AuraCore`) is strictly isolated from Win32, WinUI 3, and Windows App SDK APIs.

### Contract Boundary (`IPlatformAdapter`)
The core communicates with the host operating system solely through abstract interfaces:
- `launch_application(app_name, arguments)`
- `switch_to_application(app_name)`
- `find_installed_applications(query)`
- `get_screen_context(monitor_index)`
- `analyze_region(x, y, width, height, question)`
- `read_clipboard_safely()`
- `show_notification(title, body, notification_id)`

---

## 2. Windows-Specific vs. Platform-Neutral Dependencies

| Component | Windows Implementation | Platform-Neutral / AURA OS Strategy |
| :--- | :--- | :--- |
| **Windowing & UI** | WinUI 3, Windows Composition XAML | Headless runtime / Direct Framebuffer Compositor |
| **Screen Capture** | `Windows.Graphics.Capture` | DRM/KMS or AURA Display Compositor IPC |
| **App Automation** | Windows UI Automation (`UIA`) | AURA OS Application IPC protocol |
| **Secure Keyring** | Windows DPAPI (`CryptProtectData`) | AURA Keystore Microkernel Capability |
| **Database** | SQLite WAL | Standard SQLite VFS (POSIX/AURA VFS) |
| **AI Inference** | Qualcomm QNN / DirectML / CPU GGUF | Native NPU driver / llama.cpp ARM64 runtime |

---

## 3. Required Future AURA OS Kernel Services

Before AURA Companion can run natively on the AURA OS microkernel, the OS must provide the following system service endpoints:

1. **`aura.proc.spawn`**: Secure process execution service for launching application packages.
2. **`aura.wm.focus`**: Window manager IPC service for application switching and z-order focus.
3. **`aura.display.capture`**: Compositor service granting pixel-buffer read access for ROI screen analysis.
4. **`aura.notify.dispatch`**: Notification daemon for displaying system alerts and reminder alarms.
5. **`aura.audio.stream`**: Audio stream server providing microphone PCM buffers for Push-to-Talk.

---

## 4. Porting Milestones

- **Milestone 1 (Complete):** Abstract interface contracts defined and verified via `tests/test_aura_portability.py`.
- **Milestone 2:** Implement POSIX/Linux reference adapter for cross-platform desktop testing.
- **Milestone 3:** Create native C/Rust FFI bindings for `IPlatformAdapter`.
- **Milestone 4:** Connect FFI bindings to AURA OS microkernel system calls when available.
