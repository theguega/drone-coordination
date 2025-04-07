# Use the official Python 3.10 slim image as the base
FROM python:3.10-slim

# Set non-interactive frontend for apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Olympe using pip
RUN pip install --upgrade pip && \
    pip install parrot-olympe

# Set the working directory
WORKDIR /olympe

# Set the default command to run when the container starts
CMD ["/bin/bash"]

