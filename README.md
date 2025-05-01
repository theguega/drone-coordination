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

## 🛠️ Installation for Bebop

1. Build and run docker image that contains ROS dependencies.

```bash
./setup.sh
```

## Launching the application

```bash
uv run src/main.py
```
