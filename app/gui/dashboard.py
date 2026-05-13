"""Right-side control dashboard widget."""

import tkinter as tk
from typing import Callable

from ..config import (
    ACCENT,
    BG_PANEL,
    BG_WIDGET,
    DASHBOARD_WIDTH,
    DEFAULT_LEFT_CAM,
    DEFAULT_LEFT_TOF,
    DEFAULT_RIGHT_CAM,
    DEFAULT_RIGHT_TOF,
    DEFAULT_RPI_IP,
    ERROR,
    FG_PRIMARY,
    FG_SECONDARY,
    SUCCESS,
    WARNING,
    CAM_SOURCES,
    TOF_SOURCES,
)
from ..network.connection_state import ConnectionState

_CAM_OPTIONS = ["None"] + list(CAM_SOURCES.keys())
_TOF_OPTIONS = ["None"] + list(TOF_SOURCES.keys())

_STATE_COLORS = {
    ConnectionState.CONNECTED:  SUCCESS,
    ConnectionState.CONNECTING: WARNING,
    ConnectionState.NO_DATA:    WARNING,
    ConnectionState.ERROR:      ERROR,
    ConnectionState.IDLE:       FG_SECONDARY,
}


class Dashboard(tk.Frame):
    """Fixed-width panel with IP connection, stream assignment, toggles and status."""

    def __init__(
        self,
        parent: tk.Widget,
        on_connect: Callable[[str], None],
        on_disconnect: Callable[[], None],
        on_exit: Callable[[], None],
        on_settings: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent, bg=BG_PANEL, width=DASHBOARD_WIDTH)
        self.pack_propagate(False)

        self._on_connect = on_connect
        self._on_disconnect = on_disconnect
        self._on_exit = on_exit
        self._on_settings = on_settings

        self._ip_var = tk.StringVar(value=DEFAULT_RPI_IP)

        self._left_cam_var  = tk.StringVar(value=DEFAULT_LEFT_CAM)
        self._left_tof_var  = tk.StringVar(value=DEFAULT_LEFT_TOF)
        self._right_cam_var = tk.StringVar(value=DEFAULT_RIGHT_CAM)
        self._right_tof_var = tk.StringVar(value=DEFAULT_RIGHT_TOF)

        self._left_cam_en  = tk.BooleanVar(value=True)
        self._left_tof_en  = tk.BooleanVar(value=True)
        self._right_cam_en = tk.BooleanVar(value=True)
        self._right_tof_en = tk.BooleanVar(value=True)

        self._checkboxes: dict[str, tk.Checkbutton] = {}
        self._stream_status_labels: dict[str, tk.Label] = {}

        self._build()

    # Public API (called by MainWindow)

    def get_assignment(self) -> dict:
        return {
            "left_cam":  self._left_cam_var.get(),
            "left_tof":  self._left_tof_var.get(),
            "right_cam": self._right_cam_var.get(),
            "right_tof": self._right_tof_var.get(),
        }

    def get_enabled(self) -> dict:
        return {
            "left_cam":  self._left_cam_en.get(),
            "left_tof":  self._left_tof_en.get(),
            "right_cam": self._right_cam_en.get(),
            "right_tof": self._right_tof_en.get(),
        }

    def update_stream_availability(
        self,
        left_cam: bool,
        left_tof: bool,
        right_cam: bool,
        right_tof: bool,
    ) -> None:
        """Enable/disable checkboxes depending on whether each stream has data."""
        avail = {
            "left_cam":  left_cam,
            "left_tof":  left_tof,
            "right_cam": right_cam,
            "right_tof": right_tof,
        }
        for key, cb in self._checkboxes.items():
            cb.config(state=tk.NORMAL if avail.get(key) else tk.DISABLED)

    def update_stream_status(self, statuses: dict) -> None:
        """Update the small coloured state label next to each stream assignment."""
        for key, lbl in self._stream_status_labels.items():
            state = statuses.get(key, ConnectionState.IDLE)
            lbl.config(text=state.value, fg=_STATE_COLORS.get(state, FG_SECONDARY))

    def set_connection_status(self, connected: bool, detail: str = "") -> None:
        if connected:
            self._status_label.config(
                text=f"Connected  {detail}", fg=SUCCESS
            )
            self._connect_btn.config(text="Disconnect", command=self._do_disconnect)
        else:
            self._status_label.config(
                text=detail if detail else "Disconnected", fg=ERROR
            )
            self._connect_btn.config(text="Connect", command=self._do_connect)

    def update_status_text(self, text: str, color: str) -> None:
        """Update only the status label text/colour (does not touch the button)."""
        self._status_label.config(text=text, fg=color)

    # Build helpers

    def _build(self) -> None:
        # Title
        tk.Label(
            self, text="Control Dashboard",
            bg=BG_PANEL, fg=FG_PRIMARY,
            font=("Segoe UI", 13, "bold"),
        ).pack(pady=(14, 4))

        self._sep()

        # --- Connection ---
        self._section_header("Connection")

        frm = self._row_frame()
        tk.Label(
            frm, text="Raspberry Pi IP:", bg=BG_PANEL, fg=FG_SECONDARY,
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=12, pady=(4, 0))

        tk.Entry(
            frm,
            textvariable=self._ip_var,
            bg=BG_WIDGET, fg=FG_PRIMARY,
            insertbackground=FG_PRIMARY,
            relief=tk.FLAT,
            font=("Segoe UI", 10),
        ).pack(fill=tk.X, padx=12, pady=(2, 0))

        self._connect_btn = tk.Button(
            frm,
            text="Connect",
            command=self._do_connect,
            bg=ACCENT, fg=FG_PRIMARY,
            activebackground="#3535bb", activeforeground=FG_PRIMARY,
            relief=tk.FLAT,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        )
        self._connect_btn.pack(fill=tk.X, padx=12, pady=(6, 4))

        tk.Button(
            frm,
            text="⚙  Port Settings",
            command=lambda: self._on_settings() if self._on_settings else None,
            bg=BG_WIDGET, fg=FG_SECONDARY,
            activebackground=BG_PANEL, activeforeground=FG_PRIMARY,
            relief=tk.FLAT,
            font=("Segoe UI", 8),
            cursor="hand2",
        ).pack(fill=tk.X, padx=12, pady=(2, 8))

        self._sep()

        # --- Stream assignment ---
        self._section_header("Stream Assignment")
        self._build_eye_assignment(
            "Left Eye",
            self._left_cam_var, self._left_tof_var,
            "left_cam", "left_tof",
        )
        self._build_eye_assignment(
            "Right Eye",
            self._right_cam_var, self._right_tof_var,
            "right_cam", "right_tof",
        )

        self._sep()

        # --- Enable / Disable ---
        self._section_header("Enable / Disable")
        self._build_eye_toggles(
            "Left Eye",
            self._left_cam_en, self._left_tof_en,
            "left_cam", "left_tof",
        )
        self._build_eye_toggles(
            "Right Eye",
            self._right_cam_en, self._right_tof_en,
            "right_cam", "right_tof",
        )

        self._sep()

        # --- Status ---
        self._section_header("Status")
        self._status_label = tk.Label(
            self,
            text="Disconnected",
            bg=BG_PANEL, fg=ERROR,
            font=("Segoe UI", 9),
            wraplength=DASHBOARD_WIDTH - 24,
            justify=tk.LEFT,
        )
        self._status_label.pack(padx=14, pady=(4, 8), anchor="w")

        self._sep()

        # --- Exit ---
        tk.Button(
            self,
            text="Exit Application",
            command=self._on_exit,
            bg="#200808", fg=ERROR,
            activebackground="#3a0000", activeforeground=ERROR,
            relief=tk.FLAT,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        ).pack(fill=tk.X, padx=12, pady=12)

    def _build_eye_assignment(
        self,
        eye_label: str,
        cam_var: tk.StringVar,
        tof_var: tk.StringVar,
        cam_key: str,
        tof_key: str,
    ) -> None:
        frm = self._row_frame()
        tk.Label(
            frm, text=eye_label, bg=BG_PANEL, fg=FG_PRIMARY,
            font=("Segoe UI", 9, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(6, 2))

        # Camera row
        tk.Label(frm, text="Camera:", bg=BG_PANEL, fg=FG_SECONDARY,
                 font=("Segoe UI", 8)).grid(row=1, column=0, sticky="w", padx=(14, 4))
        self._option_menu(frm, cam_var, _CAM_OPTIONS).grid(row=1, column=1, sticky="ew", pady=2)
        st_cam = tk.Label(frm, text="Idle", bg=BG_PANEL, fg=FG_SECONDARY,
                          font=("Segoe UI", 7), width=10, anchor="w")
        st_cam.grid(row=1, column=2, padx=(4, 8))

        # ToF row
        tk.Label(frm, text="ToF Sensor:", bg=BG_PANEL, fg=FG_SECONDARY,
                 font=("Segoe UI", 8)).grid(row=2, column=0, sticky="w", padx=(14, 4))
        self._option_menu(frm, tof_var, _TOF_OPTIONS).grid(row=2, column=1, sticky="ew", pady=(2, 6))
        st_tof = tk.Label(frm, text="Idle", bg=BG_PANEL, fg=FG_SECONDARY,
                          font=("Segoe UI", 7), width=10, anchor="w")
        st_tof.grid(row=2, column=2, padx=(4, 8))

        frm.columnconfigure(1, weight=1)
        self._stream_status_labels[cam_key] = st_cam
        self._stream_status_labels[tof_key] = st_tof

    def _build_eye_toggles(
        self,
        eye_label: str,
        cam_var: tk.BooleanVar,
        tof_var: tk.BooleanVar,
        cam_key: str,
        tof_key: str,
    ) -> None:
        frm = self._row_frame()
        tk.Label(
            frm, text=eye_label, bg=BG_PANEL, fg=FG_PRIMARY,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", padx=12, pady=(6, 2))

        cb_cam = tk.Checkbutton(
            frm, text="Camera", variable=cam_var,
            bg=BG_PANEL, fg=FG_SECONDARY,
            selectcolor=BG_WIDGET,
            activebackground=BG_PANEL, activeforeground=FG_PRIMARY,
            font=("Segoe UI", 9),
            state=tk.DISABLED,
        )
        cb_cam.pack(anchor="w", padx=24)

        cb_tof = tk.Checkbutton(
            frm, text="ToF Sensor", variable=tof_var,
            bg=BG_PANEL, fg=FG_SECONDARY,
            selectcolor=BG_WIDGET,
            activebackground=BG_PANEL, activeforeground=FG_PRIMARY,
            font=("Segoe UI", 9),
            state=tk.DISABLED,
        )
        cb_tof.pack(anchor="w", padx=24, pady=(0, 6))

        self._checkboxes[cam_key] = cb_cam
        self._checkboxes[tof_key] = cb_tof

    # Layout utilities

    def _section_header(self, text: str) -> None:
        tk.Label(
            self, text=text.upper(),
            bg=BG_PANEL, fg=FG_SECONDARY,
            font=("Segoe UI", 7, "bold"),
            anchor="w",
        ).pack(fill=tk.X, padx=14, pady=(6, 0))

    def _row_frame(self) -> tk.Frame:
        f = tk.Frame(self, bg=BG_PANEL)
        f.pack(fill=tk.X)
        return f

    def _sep(self) -> None:
        tk.Frame(self, bg="#1c1c38", height=1).pack(fill=tk.X, padx=8, pady=3)

    def _option_menu(self, parent: tk.Widget, var: tk.StringVar, options: list) -> tk.OptionMenu:
        btn = tk.OptionMenu(parent, var, *options)
        btn.config(
            bg=BG_WIDGET, fg=FG_PRIMARY,
            activebackground=ACCENT, activeforeground=FG_PRIMARY,
            highlightthickness=0, relief=tk.FLAT,
            font=("Segoe UI", 8),
            width=10,
        )
        btn["menu"].config(
            bg=BG_WIDGET, fg=FG_PRIMARY,
            activebackground=ACCENT, activeforeground=FG_PRIMARY,
            font=("Segoe UI", 8),
        )
        return btn

    # Button callbacks

    def _do_connect(self) -> None:
        ip = self._ip_var.get().strip()
        if ip:
            self._on_connect(ip)

    def _do_disconnect(self) -> None:
        self._on_disconnect()
