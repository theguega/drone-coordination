# Use the official ROS Noetic base image
FROM ros:noetic-ros-base

# Set non-interactive frontend for apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-rosdep \
    python3-catkin-tools \
    git \
    && rm -rf /var/lib/apt/lists/*

# Initialize rosdep
RUN rosdep update --rosdistro noetic

# Create a catkin workspace
RUN mkdir -p /catkin_ws/src

# Set the workspace
WORKDIR /catkin_ws

# Clone the bebop_autonomy repository into the workspace
RUN git clone https://github.com/AutonomyLab/bebop_autonomy.git src/bebop_autonomy

# Install dependencies using rosdep
RUN rosdep install --from-paths src --ignore-src -r -y

# Build the workspace using catkin
RUN /bin/bash -c "source /opt/ros/noetic/setup.bash && catkin_make"

# Source the workspace setup script
RUN echo "source /catkin_ws/devel/setup.bash" >> /root/.bashrc

# Set the default command to run when the container starts
CMD ["/bin/bash"]

