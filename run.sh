#!/bin/zsh

source .venv/bin/activate
uv run src/main.py --mavsdk_drone --olympe_drone
