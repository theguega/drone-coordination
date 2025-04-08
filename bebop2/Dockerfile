FROM ros:kinetic-ros-core

WORKDIR /root

# Install necessary dependencies
RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y \
    build-essential \
    python-rosdep \
    python-catkin-tools \
    git \
    ros-kinetic-catkin \
    ros-kinetic-angles \
    ros-kinetic-image-view \
    ros-kinetic-dynamic-reconfigure \
    ros-kinetic-urdf \
    ros-kinetic-xacro \
    ros-kinetic-roslint \
    ros-kinetic-joy-teleop \
    ros-kinetic-tf2-geometry-msgs \
    ros-kinetic-joy \
    ros-kinetic-camera-info-manager \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update
RUN rosdep init || true
RUN rosdep update

RUN mkdir -p /root/bebop_ws/src
RUN git clone https://github.com/AutonomyLab/bebop_autonomy.git /root/bebop_ws/src/bebop_autonomy
RUN git clone https://github.com/AutonomyLab/parrot_arsdk.git /root/bebop_ws/src/parrot_arsdk

RUN /bin/bash -c "source /opt/ros/kinetic/setup.bash && rosdep install --from-paths /root/bebop_ws/src -i --rosdistro kinetic -y"

RUN /bin/bash -c "source /opt/ros/kinetic/setup.bash && cd /root/bebop_ws && catkin build"

CMD ["bash", "-c", "source /opt/ros/kinetic/setup.bash && source /root/bebop_ws/devel/setup.bash && bash"]
