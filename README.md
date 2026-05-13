# Stereo Vision System — User Application

A desktop GUI application for monitoring a dual-camera stereo vision system running on a Raspberry Pi 5. It displays live MJPEG video streams from two RGB cameras and overlays real-time depth data from two VL53L8CX Time-of-Flight sensors.

## Features

- **Dual eye view** — side-by-side left and right eye panels, each showing a camera feed with an optional ToF depth grid overlay
- **Real-time ToF overlay** — 8 × 8 distance grid drawn directly on the scaled camera frame at ~30 fps
- **Live connection status** — colour-coded label that transitions through *Connecting → Connected / Connection failed* based on actual stream states
- **Per-stream controls** — independently enable or disable each camera and ToF sensor via checkboxes; panels appear/disappear automatically
- **Port settings dialog** — change all four network ports (Camera 0/1, ToF 0/1) at runtime without restarting
- **Dark theme UI** — low-glare interface

## Requirements

- Python ≥ 3.10
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

Dependencies (managed via `pyproject.toml`):

| Package | Version |
|:---|:---|
| `opencv-python` | ≥ 4.8.0 |
| `numpy` | ≥ 1.24.0 |
| `Pillow` | ≥ 10.0.0 |

## Installation & Running

```bash
git clone https://github.com/Project-Humanoid-Head/User-Application.git
cd User-Application
py -m pip install -e .
python main.py
```

## Network Protocol

The application expects the following services to be running on the Raspberry Pi:

| Stream | Protocol | Default Port |
|:---|:---|:---|
| Camera 0 (MJPEG) | TCP | 8888 |
| Camera 1 (MJPEG) | TCP | 8889 |
| ToF Sensor 0 | UDP broadcast | 5005 |
| ToF Sensor 1 | UDP broadcast | 5006 |

### Camera streams
`rpicam-vid` runs with `--listen` on each port. The app connects as a TCP client and reads a raw MJPEG byte stream, extracting frames by locating JPEG SOI (`0xFF 0xD8`) and EOI (`0xFF 0xD9`) markers.

### ToF streams
Each `tof_streamer` process broadcasts CSV packets over UDP containing 64 comma-separated distance values (8 × 8 grid, millimetres). The application binds a UDP socket on `0.0.0.0` and reads broadcast packets.

## Project Structure

```
User-Application/
├── main.py                      # Entry point
├── pyproject.toml               # Project metadata & dependencies
├── app/
│   ├── config.py                # All constants and default values
│   ├── settings.py              # Runtime-mutable port configuration
│   ├── stream_manager.py        # Owns all network receiver instances
│   ├── network/
│   │   ├── connection_state.py  # ConnectionState enum
│   │   ├── camera_receiver.py   # TCP MJPEG client thread
│   │   └── tof_receiver.py      # UDP ToF listener thread
│   └── gui/
│       ├── main_window.py       # Root Tk window and update loop
│       ├── dashboard.py         # Right-side control panel
│       ├── eye_panel.py         # Single-eye canvas widget
│       ├── settings_dialog.py   # Port settings modal dialog
│       └── utils.py             # Image scaling and ToF overlay helpers
```

## Usage

1. Launch the application — the window opens maximised.
2. Enter the Raspberry Pi IP address in the **Connection** section of the dashboard (default: `192.168.207.150`).
3. Click **Connect**. The status label will update to *Connecting…* and then *Connected* once any stream starts receiving data.
4. Use the **Stream Assignment** dropdowns to choose which camera/sensor feeds each eye.
5. Use the **Enable / Disable** checkboxes to show or hide individual streams.
6. Click **Port Settings** to change network ports if the defaults do not match your backend configuration.
7. Click **Disconnect** to stop all streams, or **Exit Application** to close the app.

## Connection State Reference

| State | Meaning |
|:---|:---|
| `Idle` | Receiver not started |
| `Connecting…` | Attempting to connect (within startup window) |
| `Connected` | Data is being received |
| `Off` | No data received after timeout |
| `Error` | TCP connection failed or dropped |

The startup grace period is **10 seconds** before a stream transitions from *Connecting* to *Off/Error*. After the first packet is received, a stream transitions to *Off* if no packet arrives within **3 seconds**.

## Backend

See [`RPI5-Backend repository`](https://github.com/Project-Humanoid-Head/RPI5-Backend) for instructions on setting up the Raspberry Pi backend services.