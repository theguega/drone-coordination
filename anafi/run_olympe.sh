#!/bin/bash

IMAGE_NAME="olympe"
PROJECT_DIR="$(pwd)"
DRONE_IP="192.168.42.1"  # Update this if needed

# Check if the Docker image exists
if [[ "$(docker images -q $IMAGE_NAME 2> /dev/null)" == "" ]]; then
  echo "Docker image '$IMAGE_NAME' not found. Building it..."
  docker build -t $IMAGE_NAME .
else
  echo "Docker image '$IMAGE_NAME' already exists."
fi

docker run --rm -it --net=host \
  -e ARSDK_DEVICE_IP="$DRONE_IP" \
  -v "$PROJECT_DIR":/olympe \
  $IMAGE_NAME
