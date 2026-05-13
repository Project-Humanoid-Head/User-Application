"""UDP receiver for a single VL53L8CX ToF sensor broadcast stream."""

import socket
import threading
import time
from typing import Optional

import numpy as np

from .connection_state import ConnectionState
from ..config import UDP_BIND_IP, TOF_GRID_SIZE, CONNECTION_TIMEOUT_S, STARTUP_TIMEOUT_S


class ToFReceiver:
    """Listens for CSV broadcast packets on *port* and exposes the latest 8×8 frame."""

    def __init__(self, port: int) -> None:
        self._port = port
        self._sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._latest_data: Optional[np.ndarray] = None
        self._last_received: float = 0.0
        self._start_time: float = 0.0
        self._lock = threading.Lock()

    # Public API

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._last_received = 0.0
        self._start_time = time.time()
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name=f"ToF-{self._port}"
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
        with self._lock:
            self._latest_data = None
        self._last_received = 0.0

    def get_latest_data(self) -> Optional[np.ndarray]:
        with self._lock:
            return self._latest_data.copy() if self._latest_data is not None else None

    @property
    def state(self) -> ConnectionState:
        if not self._running:
            return ConnectionState.IDLE
        if self._last_received == 0.0:
            if time.time() - self._start_time > STARTUP_TIMEOUT_S:
                return ConnectionState.NO_DATA
            return ConnectionState.CONNECTING
        if time.time() - self._last_received > CONNECTION_TIMEOUT_S:
            return ConnectionState.NO_DATA
        return ConnectionState.CONNECTED

    # Internal

    def _loop(self) -> None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(1.0)
            sock.bind((UDP_BIND_IP, self._port))
            self._sock = sock
        except OSError:
            return

        expected = TOF_GRID_SIZE * TOF_GRID_SIZE

        while self._running:
            try:
                data, _ = self._sock.recvfrom(2048)
                text = data.decode("utf-8", errors="replace")
                parts = text.strip(",").split(",")
                if len(parts) == expected:
                    arr = np.array(parts, dtype=np.float32).reshape(
                        (TOF_GRID_SIZE, TOF_GRID_SIZE)
                    )
                    with self._lock:
                        self._latest_data = arr
                    self._last_received = time.time()
            except socket.timeout:
                continue
            except OSError:
                break
            except Exception:
                continue
