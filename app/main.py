from __future__ import annotations

import json
import os
import platform
import queue
import threading
import time
import tkinter as tk
from dataclasses import asdict, dataclass
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable


APP_NAME = "Simple GUI Demo"
APP_DIR_NAME = "simple-gui-demo"


@dataclass
class AppSettings:
    counter: int = 0
    interval_seconds: float = 1.0
    note: str = ""


def user_config_dir() -> Path:
    system = platform.system()

    if system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / APP_NAME

    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME

    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_DIR_NAME


class SettingsStore:
    def __init__(self) -> None:
        self.path = user_config_dir() / "settings.json"

    def load(self) -> AppSettings:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return AppSettings(
                counter=int(data.get("counter", 0)),
                interval_seconds=float(data.get("interval_seconds", 1.0)),
                note=str(data.get("note", "")),
            )
        except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError):
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")


class CounterWorker:
    def __init__(self, events: queue.Queue[str], get_interval: Callable[[], float]) -> None:
        self.events = events
        self.get_interval = get_interval
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return

        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()

    def _run(self) -> None:
        while not self.stop_event.is_set():
            self.events.put("tick")
            self.stop_event.wait(max(0.05, self.get_interval()))


class DesktopApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.store = SettingsStore()
        self.settings = self.store.load()
        self.events: queue.Queue[str] = queue.Queue()
        self.worker = CounterWorker(self.events, self.current_interval)
        self.running = False

        self.counter_var = tk.IntVar(value=self.settings.counter)
        self.interval_var = tk.StringVar(value=str(self.settings.interval_seconds))
        self.status_var = tk.StringVar(value="Stopped")

        self._build_window()
        self._poll_worker_events()

    def _build_window(self) -> None:
        self.root.title(APP_NAME)
        self.root.geometry("460x340")
        self.root.minsize(420, 320)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self._build_menu()

        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(outer, text=APP_NAME, font=("Segoe UI", 18, "bold"))
        title.pack(anchor=tk.W)

        subtitle = ttk.Label(
            outer,
            text="A small packaged desktop app example using Python, Tkinter, PyInstaller, and Inno Setup.",
            wraplength=390,
        )
        subtitle.pack(anchor=tk.W, pady=(4, 16))

        counter_row = ttk.Frame(outer)
        counter_row.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(counter_row, text="Counter", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        ttk.Label(counter_row, textvariable=self.counter_var, font=("Segoe UI", 24)).pack(side=tk.RIGHT)

        interval_row = ttk.Frame(outer)
        interval_row.pack(fill=tk.X, pady=(0, 14))

        ttk.Label(interval_row, text="Interval seconds").pack(side=tk.LEFT)
        interval_entry = ttk.Entry(interval_row, textvariable=self.interval_var, width=10)
        interval_entry.pack(side=tk.RIGHT)

        controls = ttk.Frame(outer)
        controls.pack(fill=tk.X, pady=(0, 16))

        self.start_button = ttk.Button(controls, text="Start", command=self.toggle_worker)
        self.start_button.pack(side=tk.LEFT)

        ttk.Button(controls, text="Reset", command=self.reset_counter).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(controls, text="Save", command=self.save).pack(side=tk.RIGHT)

        ttk.Label(outer, text="Note").pack(anchor=tk.W)
        self.note_text = tk.Text(outer, height=5, wrap=tk.WORD)
        self.note_text.pack(fill=tk.BOTH, expand=True, pady=(4, 12))
        self.note_text.insert("1.0", self.settings.note)

        status = ttk.Label(outer, textvariable=self.status_var)
        status.pack(anchor=tk.W)

    def _build_menu(self) -> None:
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="Save", command=self.save)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.close)
        menu_bar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menu_bar, tearoff=False)
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menu_bar)

    def current_interval(self) -> float:
        try:
            return float(self.interval_var.get())
        except ValueError:
            return self.settings.interval_seconds

    def toggle_worker(self) -> None:
        if self.running:
            self.worker.stop()
            self.running = False
            self.start_button.configure(text="Start")
            self.status_var.set("Stopped")
            return

        try:
            interval = float(self.interval_var.get())
            if interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid interval", "Enter a positive number of seconds.")
            return

        self.settings.interval_seconds = interval
        self.worker.start()
        self.running = True
        self.start_button.configure(text="Stop")
        self.status_var.set("Running")

    def reset_counter(self) -> None:
        self.counter_var.set(0)
        self.status_var.set("Counter reset")

    def save(self) -> None:
        try:
            interval = float(self.interval_var.get())
            if interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid interval", "Enter a positive number of seconds.")
            return

        self.settings.counter = self.counter_var.get()
        self.settings.interval_seconds = interval
        self.settings.note = self.note_text.get("1.0", tk.END).strip()
        self.store.save(self.settings)
        self.status_var.set(f"Saved to {self.store.path}")

    def show_about(self) -> None:
        messagebox.showinfo(
            "About",
            f"{APP_NAME}\n\nA minimal Python desktop app packaged with PyInstaller and Inno Setup.",
        )

    def close(self) -> None:
        self.worker.stop()
        self.save()
        self.root.destroy()

    def _poll_worker_events(self) -> None:
        while True:
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break

            if event == "tick":
                self.counter_var.set(self.counter_var.get() + 1)

        self.root.after(50, self._poll_worker_events)


def main() -> None:
    root = tk.Tk()
    DesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
