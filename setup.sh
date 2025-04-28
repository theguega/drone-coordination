#!/bin/bash

set -e

echo "🚀 Starting full setup for drone-following (uv + ROS)..."

# Check Ubuntu version
UBUNTU_VERSION=$(lsb_release -rs)
if [[ "$UBUNTU_VERSION" != "20.04" && "$UBUNTU_VERSION" != "22.04" ]]; then
    echo "⚠️ This script officially supports Ubuntu 20.04 or 22.04."
fi

# 1. Install system packages
echo "🔧 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    build-essential \
    python3-rosdep \
    python3-catkin-tools \
    ros-$ROS_DISTRO-rospy \
    ros-$ROS_DISTRO-std-msgs \
    ros-$ROS_DISTRO-sensor-msgs \
    git \
    wget \
    curl

# 2. Install ROS (if needed)
if ! [ -x "$(command -v roscore)" ]; then
  echo "🔵 ROS not found. Installing ROS Noetic..."
  # ROS Noetic install
  sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
  curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | sudo apt-key add -
  sudo apt update
  sudo apt install -y ros-noetic-desktop-full
  echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
  source ~/.bashrc
fi

# Initialize rosdep
echo "🔵 Initializing rosdep..."
sudo rosdep init || true
rosdep update

# 3. Install uv if missing
if ! [ -x "$(command -v uv)" ]; then
  echo "📦 uv not found. Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# 4. Clone bebop_autonomy
echo "📦 Setting up bebop_autonomy..."
mkdir -p ~/catkin_ws/src
cd ~/catkin_ws/src
if [ ! -d "bebop_autonomy" ]; then
    git clone https://github.com/AutonomyLab/bebop_autonomy.git
fi
cd ~/catkin_ws
rosdep install --from-paths src -i -y
catkin build
source devel/setup.bash

# 5. Python project setup
echo "🐍 Setting up Python environment with uv..."
cd "$OLDPWD"
uv venv
uv pip install -e .

echo "✅ Setup complete! You can now run your project."
echo "To activate your environment: uv venv exec bash"
