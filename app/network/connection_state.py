from enum import Enum


class ConnectionState(Enum):
    IDLE       = "Idle"
    CONNECTING = "Connecting…"
    CONNECTED  = "Connected"
    NO_DATA    = "Off"
    ERROR      = "Error"
