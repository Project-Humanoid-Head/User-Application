"""Main application window — ties together StreamManager, EyePanels and Dashboard."""

import tkinter as tk

from ..config import (
    BG_DARK,
    ERROR,
    FG_SECONDARY,
    SUCCESS,
    UI_UPDATE_INTERVAL_MS,
    WARNING,
)
from ..network.connection_state import ConnectionState
from ..settings import RuntimeSettings
from ..stream_manager import StreamManager
from .dashboard import Dashboard
from .eye_panel import EyePanel
from .settings_dialog import SettingsDialog

_NO_SIGNAL_CONNECTED = "All Streams Disabled\n\nEnable streams in the dashboard  →"
_NO_SIGNAL_IDLE = "Not Connected\n\nEnter IP and click Connect  →"


class MainWindow:
    """Root Tk window.  Create and call :meth:`run` to start the event loop."""

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._root.title("Stereo Vision System")
        self._root.configure(bg=BG_DARK)
        self._root.minsize(900, 560)
        self._root.state("zoomed")

        self._stream_mgr = StreamManager()
        self._settings = RuntimeSettings()
        self._rpi_ip = ""

        self._left_visible = True
        self._right_visible = True

        self._build_layout()
        self._root.protocol("WM_DELETE_WINDOW", self._on_exit)

    # Public

    def run(self) -> None:
        self._schedule_update()
        self._root.mainloop()

    # Layout

    def _build_layout(self) -> None:
        self._dashboard = Dashboard(
            self._root,
            on_connect=self._on_connect,
            on_disconnect=self._on_disconnect,
            on_exit=self._on_exit,
            on_settings=self._on_settings,
        )
        self._dashboard.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Frame(self._root, bg="#1c1c38", width=1).pack(side=tk.RIGHT, fill=tk.Y)

        self._eye_area = tk.Frame(self._root, bg=BG_DARK)
        self._eye_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._left_panel  = EyePanel(self._eye_area, "LEFT EYE")
        self._right_panel = EyePanel(self._eye_area, "RIGHT EYE")

        self._no_signal_label = tk.Label(
            self._eye_area,
            text=_NO_SIGNAL_IDLE,
            bg=BG_DARK,
            fg=FG_SECONDARY,
            font=("Segoe UI", 22),
            justify=tk.CENTER,
        )

        self._apply_layout(show_left=True, show_right=True)

    def _apply_layout(self, show_left: bool, show_right: bool) -> None:
        """Pack / unpack eye panels depending on which eyes are active."""
        self._left_panel.pack_forget()
        self._right_panel.pack_forget()
        self._no_signal_label.pack_forget()

        if not show_left and not show_right:
            self._no_signal_label.pack(fill=tk.BOTH, expand=True)
        else:
            if show_left:
                self._left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            if show_right:
                self._right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._left_visible = show_left
        self._right_visible = show_right

    # Periodic update loop

    def _schedule_update(self) -> None:
        self._root.after(UI_UPDATE_INTERVAL_MS, self._tick)

    def _tick(self) -> None:
        try:
            self._update_frame()
        finally:
            self._schedule_update()

    def _update_frame(self) -> None:
        if self._stream_mgr.is_connected:
            all_states = (
                [self._stream_mgr.cam_state(n) for n in ["Camera 0", "Camera 1"]]
                + [self._stream_mgr.tof_state(n) for n in ["ToF 0", "ToF 1"]]
            )
            if any(s == ConnectionState.CONNECTED for s in all_states):
                self._dashboard.update_status_text(
                    f"Connected  ({self._rpi_ip})", SUCCESS
                )
            elif all(s in (ConnectionState.ERROR, ConnectionState.NO_DATA) for s in all_states):
                self._dashboard.update_status_text(
                    f"Connection failed  —  check IP ({self._rpi_ip})", ERROR
                )

        assignment = self._dashboard.get_assignment()
        enabled    = self._dashboard.get_enabled()

        lc_src = assignment["left_cam"]
        lt_src = assignment["left_tof"]
        rc_src = assignment["right_cam"]
        rt_src = assignment["right_tof"]

        def cam_avail(name: str) -> bool:
            return name != "None" and (
                self._stream_mgr.cam_state(name) == ConnectionState.CONNECTED
            )

        def tof_avail(name: str) -> bool:
            return name != "None" and (
                self._stream_mgr.tof_state(name) == ConnectionState.CONNECTED
            )

        lc_avail = cam_avail(lc_src)
        lt_avail = tof_avail(lt_src)
        rc_avail = cam_avail(rc_src)
        rt_avail = tof_avail(rt_src)

        self._dashboard.update_stream_availability(lc_avail, lt_avail, rc_avail, rt_avail)

        def _st(getter, name: str) -> ConnectionState:
            return getter(name) if name != "None" else ConnectionState.IDLE

        self._dashboard.update_stream_status({
            "left_cam":  _st(self._stream_mgr.cam_state, lc_src),
            "left_tof":  _st(self._stream_mgr.tof_state, lt_src),
            "right_cam": _st(self._stream_mgr.cam_state, rc_src),
            "right_tof": _st(self._stream_mgr.tof_state, rt_src),
        })

        show_lc = enabled["left_cam"]  and lc_avail
        show_lt = enabled["left_tof"]  and lt_avail
        show_rc = enabled["right_cam"] and rc_avail
        show_rt = enabled["right_tof"] and rt_avail

        left_active  = show_lc or show_lt
        right_active = show_rc or show_rt

        if not left_active and not right_active:
            msg = (
                _NO_SIGNAL_CONNECTED
                if self._stream_mgr.is_connected
                else _NO_SIGNAL_IDLE
            )
            self._no_signal_label.config(text=msg)

        if left_active != self._left_visible or right_active != self._right_visible:
            self._apply_layout(left_active, right_active)

        if left_active:
            frame = self._stream_mgr.get_frame(lc_src) if show_lc else None
            tof   = self._stream_mgr.get_tof_data(lt_src) if show_lt else None
            ph_msg = "No Camera Signal" if show_lc else "Camera Disabled"
            self._left_panel.set_placeholder_message(ph_msg)
            self._left_panel.refresh(frame, tof)

        if right_active:
            frame = self._stream_mgr.get_frame(rc_src) if show_rc else None
            tof   = self._stream_mgr.get_tof_data(rt_src) if show_rt else None
            ph_msg = "No Camera Signal" if show_rc else "Camera Disabled"
            self._right_panel.set_placeholder_message(ph_msg)
            self._right_panel.refresh(frame, tof)

    # Dashboard callbacks

    def _on_connect(self, ip: str) -> None:
        self._rpi_ip = ip
        self._stream_mgr.connect(ip, self._settings)
        self._dashboard.set_connection_status(True, "")
        self._dashboard.update_status_text(f"Connecting…  ({ip})", WARNING)

    def _on_disconnect(self) -> None:
        self._stream_mgr.disconnect()
        self._dashboard.set_connection_status(False, "Disconnected")
        self._dashboard.update_stream_availability(False, False, False, False)
        self._left_panel.set_placeholder_message("No Connection")
        self._right_panel.set_placeholder_message("No Connection")
        self._left_panel.refresh(None, None)
        self._right_panel.refresh(None, None)

    def _on_exit(self) -> None:
        self._stream_mgr.disconnect()
        self._root.destroy()

    def _on_settings(self) -> None:
        dialog = SettingsDialog(
            self._root,
            self._settings,
            is_connected=self._stream_mgr.is_connected,
        )
        result = dialog.show()
        if result is not None:
            self._settings = result
