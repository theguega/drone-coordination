#!/bin/bash

set -e

echo "🚀 Starting full setup for drone following"

docker build -t drone-coordination:latest .

docker run -it \
    --network host \
    --env DISPLAY \
    drone-coordination:latest
