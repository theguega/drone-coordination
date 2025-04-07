#!/bin/bash

IMAGE_NAME="olympe"
PROJECT_DIR="$(pwd)"

# Check if the Docker image exists
if [[ "$(docker images -q $IMAGE_NAME 2> /dev/null)" == "" ]]; then
  echo "Docker image '$IMAGE_NAME' not found. Building it..."
  docker build -t $IMAGE_NAME .
else
  echo "Docker image '$IMAGE_NAME' already exists."
fi

# Run the container
docker run --rm -it \
  -v "$PROJECT_DIR":/olympe \
  $IMAGE_NAME

