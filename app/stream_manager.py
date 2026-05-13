"""Central manager for all network stream receivers."""

from typing import Optional

import numpy as np

from .config import CAM_SOURCES, TOF_SOURCES
from .network.camera_receiver import CameraReceiver
from .network.connection_state import ConnectionState
from .network.tof_receiver import ToFReceiver
from .settings import RuntimeSettings


class StreamManager:
    """Owns one CameraReceiver per camera port and one ToFReceiver per sensor port."""

    def __init__(self) -> None:
        self._cam_receivers: dict[str, CameraReceiver] = {
            name: CameraReceiver() for name in CAM_SOURCES
        }
        self._tof_receivers: dict[str, ToFReceiver] = {
            name: ToFReceiver(port) for name, port in TOF_SOURCES.items()
        }
        self._connected = False

    # Connection control

    def connect(self, ip: str, settings: RuntimeSettings | None = None) -> None:
        """Start all receivers.  Uses *settings* ports when provided."""
        cam_ports = settings.cam_ports if settings else CAM_SOURCES
        tof_ports = settings.tof_ports if settings else TOF_SOURCES

        for name, tof in self._tof_receivers.items():
            tof.stop()
        self._tof_receivers = {
            name: ToFReceiver(tof_ports.get(name, TOF_SOURCES[name]))
            for name in TOF_SOURCES
        }

        self._connected = True
        for name, cam in self._cam_receivers.items():
            cam.start(ip, cam_ports.get(name, CAM_SOURCES[name]))
        for tof in self._tof_receivers.values():
            tof.start()

    def disconnect(self) -> None:
        self._connected = False
        for cam in self._cam_receivers.values():
            cam.stop()
        for tof in self._tof_receivers.values():
            tof.stop()

    @property
    def is_connected(self) -> bool:
        return self._connected

    # Data access

    def get_frame(self, cam_name: str) -> Optional[np.ndarray]:
        receiver = self._cam_receivers.get(cam_name)
        return receiver.get_latest_frame() if receiver else None

    def get_tof_data(self, tof_name: str) -> Optional[np.ndarray]:
        receiver = self._tof_receivers.get(tof_name)
        return receiver.get_latest_data() if receiver else None

    def cam_state(self, cam_name: str) -> ConnectionState:
        receiver = self._cam_receivers.get(cam_name)
        return receiver.state if receiver else ConnectionState.IDLE

    def tof_state(self, tof_name: str) -> ConnectionState:
        receiver = self._tof_receivers.get(tof_name)
        return receiver.state if receiver else ConnectionState.IDLE
