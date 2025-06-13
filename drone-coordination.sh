#!/bin/zsh

set -e

if [[ $# -eq 0 ]]; then
  echo "❌ No argument provided. Use 'build' or 'run'."
  exit 1
fi

ACTION=$1
PLATFORM=$(uname)

case "$ACTION" in
  build)
    if [[ "$PLATFORM" == "Linux" ]]; then
      echo "🔧 [BUILD] Linux: Setting up Python environment with uv..."

      if [ ! -d ".venv" ]; then
        echo "📦 Creating Python virtual environment with uv..."
        uv venv
      fi

      echo "✅ Activating virtual environment..."
      source .venv/bin/activate

      echo "📥 Installing dependencies..."
      uv pip install -e .

    elif [[ "$PLATFORM" == "Darwin" ]]; then
      echo "🍎 [BUILD] macOS: Building Docker image..."
      docker build -t drone-coordination .
    else
      echo "❌ Unsupported platform: $PLATFORM"
      exit 1
    fi
    ;;

  run)
    if [[ "$PLATFORM" == "Linux" ]]; then
      echo "🚀 [RUN] Linux: Running with uv..."
      source .venv/bin/activate
      python src/main.py --mavsdk_drone --olympe_drone

    elif [[ "$PLATFORM" == "Darwin" ]]; then
      echo "🚀 [RUN] macOS: Running Docker container..."
      docker run -it --rm \
        -P \
        --net=host \
        drone-coordination
    else
      echo "❌ Unsupported platform: $PLATFORM"
      exit 1
    fi
    ;;

  *)
    echo "❌ Invalid argument: $ACTION"
    echo "Usage: $0 [build|run]"
    exit 1
    ;;
esac
