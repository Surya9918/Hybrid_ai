# AURA Companion — Privacy and Security Specification

**Philosophy:** Local-First, Zero-Telemetry, Explicit-Consent, Hardware-Grounded Security.

---

## 1. Data Flows & Boundaries

```
[User Audio / Keyboard / Screen]
         │
         ▼
[Local Input Sanitizers] ── (Redacts API keys, credentials, prompt injections)
         │
         ▼
[Local SQLite Storage] ── (Encrypted at rest with Windows DPAPI / BitLocker)
         │
         ▼
[Local AI Inference] ── (Qualcomm Hexagon NPU / Local CPU GGUF)
         │
         ▼
[Local UI Render] (WinUI 3 Floating Orb & Island)
```

**Zero External Leakage:** In default operation and when Strict Offline Mode is enabled, **0 bytes** leave the device. No telemetry, crash dumps, or usage analytics are transmitted to external servers.

---

## 2. Network Behavior & Offline Enforcement

- **Strict Offline Enforcement:** When enabled in Settings, the `ToolRegistry` and `ModelRouter` hard-block all network sockets and API calls.
- **Auditing:** In automated offline testing (`tests/test_inference_offline.py` and `tests/test_tools.py`), requests targeting external services return an explicit refusal: *"Offline mode is strictly enforced. Web search / cloud requests are disabled."*
- **Explicit Cloud Consent:** If cloud providers (Gemini / Anthropic) are configured in hybrid mode, requests leave the device **only** when the user explicitly prefixes or authorizes the query.

---

## 3. Credential Storage & Sensitive Data Protection

- **No Plaintext Secrets:** API keys and sensitive tokens are never stored in plain SQLite tables or log files.
- **Windows DPAPI Integration:** On Windows, credentials use `CryptProtectData` via Windows Data Protection API (DPAPI), binding keys to the local user account.
- **Clipboard History Exclusion:** The `ClipboardPrivacyFilter` scans clipboard events using pattern matching to exclude:
  - Private Keys (RSA, OpenSSH, EC).
  - Bearer / JWT Tokens (`eyJ...`).
  - API Keys (`sk-...`, `ghp_...`, `AKIA...`).
  - Credit card numbers.
  - Password variable assignments.

---

## 4. Threat Model & Untrusted Input Mitigation

| Threat Vector | Potential Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Adversarial Web / OCR Prompt Injection** | Webpage or document text commands the model to delete data or leak information. | Text extracted from OCR or web is classified as **untrusted data**. Regex and structural boundary tokens strip injection triggers and prevent privilege escalation. |
| **Accidental Destructive Tool Execution** | Assistant accidentally deletes tasks or wipes user database. | Destructive actions (`HIGH_RISK_DESTRUCTIVE`) require explicit user confirmation dialogs before execution. |
| **Microphone Snooping** | Background audio listening without consent. | Microphone is active **strictly** during Push-to-Talk activation (`Win + Space` held or toggled). Visual state transitions to Electric Cyan listening orb immediately upon activation. |
| **Screen Snooping** | Uncontrolled background screenshot capture. | Screen capture is triggered **only** when the user initiates ROI selection (`Win + Shift + C`) or confirms screen context sharing. |
