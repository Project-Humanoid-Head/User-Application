"""Runtime-mutable stream port configuration."""

from dataclasses import dataclass, field

from .config import CAM_SOURCES, TOF_SOURCES


@dataclass
class RuntimeSettings:
    """Holds the currently active network ports for all streams.

    Initialised from the defaults in ``config.py``.
    Modified at runtime via the Settings dialog.
    """

    cam_ports: dict[str, int] = field(
        default_factory=lambda: dict(CAM_SOURCES)
    )
    tof_ports: dict[str, int] = field(
        default_factory=lambda: dict(TOF_SOURCES)
    )

    def copy(self) -> "RuntimeSettings":
        return RuntimeSettings(
            cam_ports=dict(self.cam_ports),
            tof_ports=dict(self.tof_ports),
        )
