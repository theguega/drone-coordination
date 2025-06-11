FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

RUN apt-get update && apt-get install -y \
    git build-essential ffmpeg \
    libglib2.0-0 libsm6 libxext6 libxrender-dev \
    net-tools iproute2 iputils-ping \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /drone-coordination

COPY pyproject.toml /drone-coordination
COPY src /drone-coordination/src

RUN uv venv
RUN uv pip install -e .

# Expose les ports nécessaires à la communication avec le drone
EXPOSE 44444/tcp
EXPOSE 44445/tcp
EXPOSE 2233/udp
EXPOSE 14550/udp
EXPOSE 14551/udp
EXPOSE 2233/udp
EXPOSE 9988/udp

CMD ["uv", "run", "src/main.py", "--mavsdk_drone", "--olympe_drone"]
