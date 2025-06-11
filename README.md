# VTOL and FPV Drone Coordination

# 🚀 Automated setup with script

```bash
./run.sh # should work on Linux and MacOS
```

# 🚀 Getting Started - Ubuntu

## 🔧 Prerequisites

- Ubuntu
- Docker
- uv for Python virtualenv

## 🛠️ Installation

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

Or you can follow isntructions in [proxy.md](proxy.md)

## Launching the application

```bash
uv run src/main.py
```

# 🚀 Getting Started - MacOS - Windows (WSL)

## 🔧 Prerequisites

- MacOS
- Docker

## 🛠️ Installation

```bash
docker build -t drone-coordination .
docker run -it --rm \
  -p 44444:44444/tcp \
  -p 44445:44445/tcp \
  -p 2233:2233/udp \
  -p 9988:9988/udp \
  --net=host \
  drone-coordination
```
