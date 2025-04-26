#!/bin/bash

set -e

PROJECT_DIR="$(pwd)"

if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -Ls https://astral.sh/uv/install.sh | bash
  else
    echo "uv already installed."
  fi

  if ! command -v ffmpeg &> /dev/null; then
    echo "Installing ffmpeg via package manager..."
    sudo apt update && sudo apt install -y ffmpeg
  else
    echo "ffmpeg already installed."
  fi

  uv venv --python=3.10
  source .venv/bin/activate

  echo "Installing your project in editable mode with [feetech]..."
  uv pip install parrot-olympe

  echo "✅ Linux environment setup complete!"
