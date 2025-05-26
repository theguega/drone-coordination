# VTOL and FPV Drone Coordination

# 🚀 Getting Started

## 🔧 Prerequisites

- Ubuntu (Xorg for tkinter)
- Docker
- uv for Python virtualenv

## 🛠️ Installation for Anafi

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Forwarding Mavlink
QGroundControl's MAVLink Forwarding
QGroundControl has built-in MAVLink forwarding:

In QGroundControl: Application Settings → General → MAVLink
Enable "Forward MAVLink"
Set output to UDP port (e.g., 14550)
Your Python script connects to udp://127.0.0.1:14550

## Launching the application

```bash
uv run src/main.py
```
