#!/bin/bash

IMAGE_NAME="bebop_autonomy"
DOCKERFILE_PATH="Dockerfile"
PROJECT_DIR="$(pwd)"

# Build image if not already present
if [[ "$(docker images -q $IMAGE_NAME 2> /dev/null)" == "" ]]; then
  echo "Docker image '$IMAGE_NAME' not found. Building it..."
  docker build -t $IMAGE_NAME -f $DOCKERFILE_PATH .
else
  echo "Docker image '$IMAGE_NAME' already exists."
fi

# Run the container
docker run --rm -it \
  --net=host \
  --env="DISPLAY" \
  -v "$PROJECT_DIR":/catkin_ws/src \
  -w /catkin_ws \
  $IMAGE_NAME \
  bash

