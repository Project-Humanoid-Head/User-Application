"""Shared GUI utility functions for image conversion and ToF overlay rendering."""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageTk

from ..config import TOF_GRID_SIZE


def draw_tof_overlay(frame: np.ndarray, tof_data: np.ndarray) -> np.ndarray:
    """Return a copy of *frame* (BGR) with an 8×8 ToF distance grid overlaid."""
    h, w = frame.shape[:2]
    cell = h // TOF_GRID_SIZE
    x0 = (w - cell * TOF_GRID_SIZE) // 2
    result = frame.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = max(0.32, cell / 130)

    for row in range(TOF_GRID_SIZE):
        for col in range(TOF_GRID_SIZE):
            val = int(tof_data[row, col])
            xl = x0 + col * cell
            yt = row * cell

            if val == -1:
                label, rect_col, txt_col = "---", (55, 55, 55), (110, 110, 110)
            else:
                label, rect_col, txt_col = str(val), (0, 200, 80), (255, 255, 255)

            cv2.rectangle(result, (xl, yt), (xl + cell, yt + cell), rect_col, 1)
            (tw, th), _ = cv2.getTextSize(label, font, scale, 1)
            tx = xl + (cell - tw) // 2
            ty = yt + (cell + th) // 2
            cv2.putText(result, label, (tx, ty), font, scale, (0, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(result, label, (tx, ty), font, scale, txt_col, 1, cv2.LINE_AA)

    return result


def scale_frame_to_fit(frame: np.ndarray, target_w: int, target_h: int) -> np.ndarray:
    """Return *frame* scaled to fit within *target_w × target_h*, aspect ratio preserved."""
    fh, fw = frame.shape[:2]
    scale = min(target_w / fw, target_h / fh)
    new_w, new_h = max(1, int(fw * scale)), max(1, int(fh * scale))
    return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)


def bgr_to_photoimage(frame: np.ndarray) -> ImageTk.PhotoImage:
    """Convert a BGR ndarray directly to a PhotoImage (no scaling)."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return ImageTk.PhotoImage(Image.fromarray(rgb))


def frame_to_photoimage(
    frame: np.ndarray, target_w: int, target_h: int
) -> ImageTk.PhotoImage:
    """Scale *frame* (BGR) to fit *target_w × target_h* and return a PhotoImage."""
    return bgr_to_photoimage(scale_frame_to_fit(frame, target_w, target_h))


def make_placeholder(width: int, height: int, text: str, bg: str = "#0d0d1a") -> ImageTk.PhotoImage:
    """Create a solid-colour placeholder PhotoImage with centred text."""
    img = Image.new("RGB", (max(1, width), max(1, height)), color=bg)
    draw = ImageDraw.Draw(img)
    try:
        fnt = ImageFont.truetype("arial.ttf", 20)
    except OSError:
        fnt = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((width - tw) // 2, (height - th) // 2), text, fill="#383870", font=fnt)
    return ImageTk.PhotoImage(img)
