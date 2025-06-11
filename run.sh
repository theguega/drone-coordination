#!/bin/zsh

set -e

PLATFORM=$(uname)

if [[ "$PLATFORM" == "Linux" ]]; then
  echo "🔧 Detected Ubuntu (or Linux). Setting up and running with uv..."

  # Create virtual environment if not exists
  if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment with uv..."
    uv venv
  fi

  echo "✅ Activating virtual environment..."
  source .venv/bin/activate

  echo "📥 Installing dependencies..."
  uv pip install -e .

  echo "🚀 Launching application..."
  uv run src/main.py

elif [[ "$PLATFORM" == "Darwin" ]]; then
  echo "🍎 Detected macOS. Running with Docker..."

  echo "🐳 Building Docker image..."
  docker build -t drone-coordination .

  echo "🚀 Launching Docker container..."
  docker run -it --rm \
    -P \
    --net=host \
    drone-coordination

else
  echo "❌ Unsupported platform: $PLATFORM"
  echo "Please run manually using appropriate instructions."
  exit 1
fi
