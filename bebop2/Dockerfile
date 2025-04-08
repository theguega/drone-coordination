# Use the official ROS Noetic image as the base
FROM ros:noetic-ros-core

# Set the working directory for the project
WORKDIR /workspace

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-rosdep \
    python3-catkin-tools \
    git \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    ros-noetic-image-transport \
    ros-noetic-tf2 \
    ros-noetic-tf2-ros \
    ros-noetic-tf2-geometry-msgs \
    ros-noetic-roslint \
    ros-noetic-angles \
    ros-noetic-joy \
    ros-noetic-joy-teleop \
    ros-noetic-image-view \
    && rm -rf /var/lib/apt/lists/*

# Initialize rosdep and update the database
RUN rosdep init && rosdep update

# Create and initialize the catkin workspace
RUN mkdir -p /workspace/bebop_ws/src && cd /workspace/bebop_ws && catkin init

# Clone bebop_autonomy into the workspace
RUN git clone https://github.com/AutonomyLab/bebop_autonomy.git /workspace/bebop_ws/src/bebop_autonomy

# Skip the rosdep install step for now (it can fail due to parrot_arsdk)
# RUN rosdep install --from-paths /workspace/bebop_ws/src -i --rosdistro=noetic -y

# Switch to bash and build the workspace using catkin build
RUN /bin/bash -c "source /opt/ros/noetic/setup.bash && cd /workspace/bebop_ws && catkin build"

# Set the default shell to bash
SHELL ["/bin/bash", "-c"]

# Source ROS and catkin environment variables for any new shell
RUN echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc && \
    echo "source /workspace/bebop_ws/devel/setup.bash" >> ~/.bashrc

# Set the default command to run when the container starts
CMD ["/bin/bash"]
