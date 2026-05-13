"""TCP MJPEG camera stream receiver."""

import socket
import threading
from typing import Optional

import cv2
import numpy as np

from .connection_state import ConnectionState

_JPEG_SOI = b"\xff\xd8"
_JPEG_EOI = b"\xff\xd9"
_BUF_LIMIT = 500_000


class CameraReceiver:
    """Connects to a TCP MJPEG server and provides the latest decoded frame."""

    def __init__(self) -> None:
        self._ip: str = ""
        self._port: int = 0
        self._sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._generation: int = 0
        self._latest_frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._state = ConnectionState.IDLE

    # Public API

    def start(self, ip: str, port: int) -> None:
        """(Re)connect to *ip:port*.  Stops any existing connection first."""
        self.stop()
        self._ip = ip
        self._port = port
        self._generation += 1
        self._running = True
        self._state = ConnectionState.CONNECTING
        self._thread = threading.Thread(
            target=self._loop, args=(self._generation,),
            daemon=True, name=f"Cam-{port}"
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
        self._state = ConnectionState.IDLE
        with self._lock:
            self._latest_frame = None

    def get_latest_frame(self) -> Optional[np.ndarray]:
        with self._lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None

    @property
    def state(self) -> ConnectionState:
        return self._state

    # Internal

    def _loop(self, gen: int) -> None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((self._ip, self._port))
            self._sock = sock
            if gen != self._generation:
                sock.close()
                return
            self._state = ConnectionState.CONNECTED
            sock.settimeout(2.0)
        except OSError:
            if gen == self._generation:
                self._state = ConnectionState.ERROR
            return

        buf = b""
        while self._running:
            try:
                chunk = self._sock.recv(65536)
                if not chunk:
                    break
                buf += chunk

                if len(buf) > _BUF_LIMIT:
                    buf = b""
                    continue

                latest_jpg: Optional[bytes] = None
                while True:
                    a = buf.find(_JPEG_SOI)
                    b = buf.find(_JPEG_EOI)
                    if a != -1 and b != -1 and b > a:
                        latest_jpg = buf[a : b + 2]
                        buf = buf[b + 2 :]
                    else:
                        break

                if latest_jpg:
                    frame = cv2.imdecode(
                        np.frombuffer(latest_jpg, dtype=np.uint8), cv2.IMREAD_COLOR
                    )
                    if frame is not None:
                        with self._lock:
                            self._latest_frame = frame

            except socket.timeout:
                continue
            except OSError:
                break
            except Exception:
                continue

        if self._running and gen == self._generation:
            self._state = ConnectionState.ERROR
