#!/usr/bin/env python3
"""
AURA Companion — Desktop Island & Assistant Core Runtime Launcher
Starts the local assistant server, applies SQLite migrations, and launches the desktop interface.
"""

import os
import sys
import time
import webbrowser
import uvicorn

# Ensure repository root is on sys.path
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.aura_runtime.storage.db import DatabaseManager


def main():
    print("=" * 64)
    print("  AURA COMPANION (Hitodama Desktop AI Replica)")
    print("  Target Device: Microsoft Surface Laptop 7th Edition (ARM64)")
    print("  Processor: Qualcomm Snapdragon X Elite / Hexagon NPU")
    print("  Status: Strict Offline Mode (0 Bytes Outbound)")
    print("=" * 64)

    # 1. Initialize persistent local database
    db_path = os.path.join(os.path.expanduser("~"), ".aura_companion", "aura_companion.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    print(f"\n[1/3] Initializing SQLite database (WAL Mode): {db_path}")
    db_manager = DatabaseManager(db_path)
    print("      Database schema migrations verified.")

    # 2. Launch Native Windows Desktop App (AuraCompanion.exe)
    port = 8765
    url = f"http://127.0.0.1:{port}"
    native_exe = os.path.join(REPO_ROOT, "dist", "ARM64", "HitodamaBar.exe")
    print(f"\n[2/3] Launching Native Windows Application: {native_exe}")

    def launch_desktop_ui():
        time.sleep(1.0)
        if os.path.exists(native_exe):
            try:
                import subprocess
                subprocess.Popen([native_exe])
                print("      Hitodama Floating Island Bar launched successfully!")
                return
            except Exception as e:
                print(f"      Note on native launch: {e}")

    import threading
    threading.Thread(target=launch_desktop_ui, daemon=True).start()

    # 3. Start local server
    print("\n[3/3] Starting AURA Companion Assistant Core...")
    print("      Press Ctrl+C to safely terminate.\n")
    
    from src.aura_runtime.ui.server import app
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
