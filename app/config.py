"""Application-wide configuration and constants."""

# --- Network ---
DEFAULT_RPI_IP = "192.168.207.150"

CAM_SOURCES: dict[str, int] = {
    "Camera 0": 8888,
    "Camera 1": 8889,
}

TOF_SOURCES: dict[str, int] = {
    "ToF 0": 5005,
    "ToF 1": 5006,
}

UDP_BIND_IP = "0.0.0.0"

# --- Sensor ---
TOF_GRID_SIZE = 8

# --- Timing ---
UI_UPDATE_INTERVAL_MS = 33       # ~30 fps
CONNECTION_TIMEOUT_S = 3.0       # ToF "no data" threshold
STARTUP_TIMEOUT_S    = 10.0      # time before a stream is marked Off/Error

# --- Layout ---
DASHBOARD_WIDTH = 310

# --- Default eye assignments ---
DEFAULT_LEFT_CAM = "Camera 0"
DEFAULT_LEFT_TOF = "ToF 0"
DEFAULT_RIGHT_CAM = "Camera 1"
DEFAULT_RIGHT_TOF = "ToF 1"

# --- Theme colours ---
BG_DARK   = "#0d0d1a"
BG_PANEL  = "#0a0a18"
BG_WIDGET = "#16162a"
FG_PRIMARY   = "#e0e0ff"
FG_SECONDARY = "#6060a0"
ACCENT  = "#4a4aee"
SUCCESS = "#44cc88"
WARNING = "#ffaa33"
ERROR   = "#ff4455"
