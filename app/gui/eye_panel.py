"""Widget that displays one eye's camera feed with an optional ToF overlay."""

import tkinter as tk
from typing import Optional

import numpy as np

from ..config import BG_DARK, BG_WIDGET, FG_SECONDARY
from .utils import bgr_to_photoimage, draw_tof_overlay, scale_frame_to_fit


class EyePanel(tk.Frame):
    """Canvas-based panel.  Call :meth:`refresh` each frame from the main thread."""

    def __init__(self, parent: tk.Widget, label: str) -> None:
        super().__init__(parent, bg=BG_DARK)

        self._label_text = label
        self._photo_ref = None
        self._last_frame: Optional[np.ndarray] = None
        self._last_tof: Optional[np.ndarray] = None
        self._placeholder_msg = "No Connection"

        tk.Label(
            self,
            text=label,
            bg=BG_DARK,
            fg=FG_SECONDARY,
            font=("Segoe UI", 10, "bold"),
        ).pack(side=tk.TOP, pady=(5, 0))

        self._canvas = tk.Canvas(self, bg=BG_WIDGET, highlightthickness=0)
        self._canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=(2, 4))
        self._canvas.bind("<Configure>", lambda _e: self._redraw())

    # Public

    def refresh(
        self,
        frame: Optional[np.ndarray],
        tof_data: Optional[np.ndarray],
    ) -> None:
        """Update the displayed content.  Must be called from the Tk main thread."""
        self._last_frame = frame
        self._last_tof = tof_data
        self._redraw()

    def set_placeholder_message(self, msg: str) -> None:
        self._placeholder_msg = msg

    # Internal

    def _redraw(self) -> None:
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        if w < 4 or h < 4:
            return

        if self._last_frame is None and self._last_tof is None:
            self._draw_placeholder(w, h)
            return

        if self._last_frame is not None:
            base = self._last_frame
        else:
            base = np.zeros((480, 640, 3), dtype=np.uint8)

        scaled = scale_frame_to_fit(base, w, h)

        if self._last_tof is not None:
            scaled = draw_tof_overlay(scaled, self._last_tof)

        self._photo_ref = bgr_to_photoimage(scaled)
        self._canvas.delete("all")
        self._canvas.create_image(w // 2, h // 2, anchor=tk.CENTER, image=self._photo_ref)

    def _draw_placeholder(self, w: int, h: int) -> None:
        self._canvas.delete("all")
        self._canvas.create_text(
            w // 2,
            h // 2,
            text=self._placeholder_msg,
            fill="#353565",
            font=("Segoe UI", 16),
            justify=tk.CENTER,
        )
        self._canvas.create_text(
            w // 2,
            h // 2 - 36,
            text=self._label_text,
            fill="#252550",
            font=("Segoe UI", 11, "bold"),
        )
