"""
AURA Companion - Floating Desktop Companion Orb
Native Windows transparent floating widget representing the Hitodama companion orb on the desktop.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


class FloatingOrbWidget:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AURA Companion Orb")
        self.root.geometry("88x88+100+100")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)

        # Transparency key for Windows
        self.bg_color = "#0B0C10"
        self.root.configure(bg=self.bg_color)

        try:
            self.root.wm_attributes("-transparentcolor", self.bg_color)
        except Exception:
            pass

        self.canvas = tk.Canvas(
            root, width=88, height=88, bg=self.bg_color, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.offset_x = 0
        self.offset_y = 0
        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_motion)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)

        self.tick = 0
        self.state = "idle"
        self.draw_orb()

    def on_drag_start(self, event):
        self.offset_x = event.x
        self.offset_y = event.y

    def on_drag_motion(self, event):
        x = self.root.winfo_x() - self.offset_x + event.x
        y = self.root.winfo_y() - self.offset_y + event.y
        self.root.geometry(f"+{x}+{y}")

    def on_double_click(self, event):
        import webbrowser
        webbrowser.open("http://127.0.0.1:8765")

    def draw_orb(self):
        self.tick += 0.08
        self.canvas.delete("all")

        cx, cy = 44, 44

        # Outer energy glow
        import math
        r_glow = 32 + math.sin(self.tick * 2) * 3
        self.canvas.create_oval(
            cx - r_glow, cy - r_glow, cx + r_glow, cy + r_glow,
            fill="#1F2833", outline="#45F3FF", width=1
        )

        # Core cyan particle
        r_core = 22
        self.canvas.create_oval(
            cx - r_core, cy - r_core, cx + r_core, cy + r_core,
            fill="#45F3FF", outline="#66FCF1", width=2
        )

        # Highlight
        r_hi = 6
        self.canvas.create_oval(
            cx - 8, cy - 14, cx - 8 + r_hi, cy - 14 + r_hi,
            fill="#FFFFFF", outline=""
        )

        self.root.after(33, self.draw_orb)


def launch_orb():
    root = tk.Tk()
    app = FloatingOrbWidget(root)
    root.mainloop()


if __name__ == "__main__":
    launch_orb()
