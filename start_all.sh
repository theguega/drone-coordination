#!/bin/bash

set -e

echo "🚀 Starting roscore, bebop_autonomy, and your drone-following Python app..."

# Source ROS environment
source /opt/ros/noetic/setup.bash
source /root/catkin_ws/devel/setup.bash

# Source Python uv virtualenv
eval "$(/root/.cargo/bin/uv venv activate)"

# Start roscore in a detached background process
echo "🔵 Starting roscore..."
roscore &
ROSCORE_PID=$!
sleep 3 # Wait for roscore to fully start

# Start bebop_autonomy driver
echo "🛩️ Starting bebop_autonomy driver..."
roslaunch bebop_driver bebop_node.launch &
BEBOP_PID=$!
sleep 5 # Wait for bebop_driver to stabilize

# Run your Python application
echo "🐍 Running drone-following Python app..."
python3 main.py

# Cleanup: Kill background processes when done
trap "echo '🛑 Stopping background processes...'; kill $BEBOP_PID $ROSCORE_PID" EXIT
wait
