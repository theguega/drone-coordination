# Use official Ubuntu image
FROM ubuntu:20.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=noetic

# Install base system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    curl \
    wget \
    lsb-release \
    gnupg2 \
    git \
    sudo \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Set locale
RUN locale-gen en_US en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Install ROS Noetic
RUN apt-get update && apt-get install -y \
    ros-noetic-desktop-full \
    python3-rosdep \
    python3-catkin-tools \
    ros-noetic-rospy \
    ros-noetic-std-msgs \
    ros-noetic-sensor-msgs

# Initialize rosdep
RUN rosdep init || true
RUN rosdep update

# Create a workspace for catkin
RUN mkdir -p /root/catkin_ws/src

# Clone bebop_autonomy
WORKDIR /root/catkin_ws/src
RUN git clone https://github.com/AutonomyLab/bebop_autonomy.git

# Install dependencies and build
WORKDIR /root/catkin_ws
RUN rosdep install --from-paths src -i -y
RUN /bin/bash -c "source /opt/ros/noetic/setup.bash && catkin build"

# Copy your project inside the container
WORKDIR /root
COPY . drone-following/

# Set working dir to your project
WORKDIR /root/drone-following

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup Python environment
RUN /root/.cargo/bin/uv venv
RUN /root/.cargo/bin/uv pip install -e .

# Source ROS when container starts
RUN echo "source /opt/ros/noetic/setup.bash" >> /root/.bashrc
RUN echo "source /root/catkin_ws/devel/setup.bash" >> /root/.bashrc

# Expose relevant ports if needed (for bebop control etc)
EXPOSE 14550

# Default command (start a bash with ROS + catkin + your venv ready)
CMD ["/bin/bash", "-c", "source /root/.bashrc && bash"]
