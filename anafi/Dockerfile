FROM python:3.8-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    iputils-ping \
    net-tools \
    dnsutils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && \
    pip install parrot-olympe==7.5.0

WORKDIR /olympe

CMD ["/bin/bash"]
