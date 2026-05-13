"""Modal settings dialog for editing stream ports."""

import tkinter as tk
from typing import Optional

from ..config import (
    ACCENT,
    BG_DARK,
    BG_PANEL,
    BG_WIDGET,
    ERROR,
    FG_PRIMARY,
    FG_SECONDARY,
    WARNING,
)
from ..settings import RuntimeSettings

_PORT_MIN = 1
_PORT_MAX = 65535


class SettingsDialog:
    """Modal Toplevel dialog.  Call :meth:`show` — returns the updated
    ``RuntimeSettings`` if the user saved, or ``None`` if cancelled."""

    def __init__(
        self,
        parent: tk.Widget,
        settings: RuntimeSettings,
        is_connected: bool = False,
    ) -> None:
        self._result: Optional[RuntimeSettings] = None
        self._is_connected = is_connected

        self._draft = settings.copy()

        self._win = tk.Toplevel(parent)
        self._win.title("Stream Port Settings")
        self._win.configure(bg=BG_DARK)
        self._win.resizable(False, False)
        self._win.grab_set()
        self._win.focus_set()

        self._vars: dict[str, tk.StringVar] = {}
        self._error_labels: dict[str, tk.Label] = {}

        self._build()

        self._win.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self._win.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self._win.winfo_height()) // 2
        self._win.geometry(f"+{px}+{py}")

    # Public

    def show(self) -> Optional[RuntimeSettings]:
        """Block until the dialog is closed, then return the result."""
        self._win.wait_window()
        return self._result

    # Build

    def _build(self) -> None:
        tk.Label(
            self._win, text="Stream Port Settings",
            bg=BG_DARK, fg=FG_PRIMARY,
            font=("Segoe UI", 13, "bold"),
        ).pack(padx=20, pady=(18, 4))

        tk.Frame(self._win, bg="#1c1c38", height=1).pack(fill=tk.X, padx=16, pady=6)

        self._group_header("Cameras")
        for name, port in self._draft.cam_ports.items():
            self._port_row(name, port, group="cam")

        tk.Frame(self._win, bg="#1c1c38", height=1).pack(fill=tk.X, padx=16, pady=6)

        self._group_header("ToF Sensors")
        for name, port in self._draft.tof_ports.items():
            self._port_row(name, port, group="tof")

        tk.Frame(self._win, bg="#1c1c38", height=1).pack(fill=tk.X, padx=16, pady=8)

        if self._is_connected:
            tk.Label(
                self._win,
                text="Changes take effect on next Connect.",
                bg=BG_DARK, fg=WARNING,
                font=("Segoe UI", 8, "italic"),
            ).pack(padx=20, pady=(0, 8), anchor="w")

        btn_frame = tk.Frame(self._win, bg=BG_DARK)
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 18))

        tk.Button(
            btn_frame, text="Cancel",
            command=self._win.destroy,
            bg=BG_PANEL, fg=FG_SECONDARY,
            activebackground=BG_WIDGET, activeforeground=FG_PRIMARY,
            relief=tk.FLAT, font=("Segoe UI", 9), cursor="hand2", width=10,
        ).pack(side=tk.LEFT)

        tk.Button(
            btn_frame, text="Save",
            command=self._save,
            bg=ACCENT, fg=FG_PRIMARY,
            activebackground="#3535bb", activeforeground=FG_PRIMARY,
            relief=tk.FLAT, font=("Segoe UI", 9, "bold"), cursor="hand2", width=10,
        ).pack(side=tk.RIGHT)

        self._win.bind("<Return>", lambda _e: self._save())
        self._win.bind("<Escape>", lambda _e: self._win.destroy())

    def _group_header(self, text: str) -> None:
        tk.Label(
            self._win, text=text.upper(),
            bg=BG_DARK, fg=FG_SECONDARY,
            font=("Segoe UI", 7, "bold"), anchor="w",
        ).pack(fill=tk.X, padx=20, pady=(4, 2))

    def _port_row(self, name: str, default_port: int, group: str) -> None:
        row = tk.Frame(self._win, bg=BG_DARK)
        row.pack(fill=tk.X, padx=20, pady=2)

        tk.Label(
            row, text=f"{name}:", width=14, anchor="w",
            bg=BG_DARK, fg=FG_PRIMARY, font=("Segoe UI", 9),
        ).pack(side=tk.LEFT)

        var = tk.StringVar(value=str(default_port))
        self._vars[name] = var

        entry = tk.Entry(
            row, textvariable=var,
            width=8,
            bg=BG_WIDGET, fg=FG_PRIMARY,
            insertbackground=FG_PRIMARY,
            relief=tk.FLAT, font=("Segoe UI", 10),
            justify=tk.CENTER,
        )
        entry.pack(side=tk.LEFT, padx=(0, 8))

        err_lbl = tk.Label(
            row, text="", fg=ERROR, bg=BG_DARK, font=("Segoe UI", 8)
        )
        err_lbl.pack(side=tk.LEFT)
        self._error_labels[name] = err_lbl

    # Save / validate

    def _save(self) -> None:
        valid = True
        new_cam: dict[str, int] = {}
        new_tof: dict[str, int] = {}

        for name in self._draft.cam_ports:
            port = self._parse_port(name)
            if port is None:
                valid = False
            else:
                new_cam[name] = port

        for name in self._draft.tof_ports:
            port = self._parse_port(name)
            if port is None:
                valid = False
            else:
                new_tof[name] = port

        if not valid:
            return

        self._result = RuntimeSettings(cam_ports=new_cam, tof_ports=new_tof)
        self._win.destroy()

    def _parse_port(self, name: str) -> Optional[int]:
        raw = self._vars[name].get().strip()
        err_lbl = self._error_labels[name]
        try:
            port = int(raw)
            if _PORT_MIN <= port <= _PORT_MAX:
                err_lbl.config(text="")
                return port
            err_lbl.config(text=f"{_PORT_MIN}–{_PORT_MAX}")
            return None
        except ValueError:
            err_lbl.config(text="invalid")
            return None
