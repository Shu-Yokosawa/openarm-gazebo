FROM osrf/ros:jazzy-desktop

ENV DEBIAN_FRONTEND=noninteractive

# Rename existing ubuntu user (uid=1000) to rosdev, add sudo privileges
RUN usermod -l rosdev -d /home/rosdev -m ubuntu && \
    groupmod -n rosdev ubuntu && \
    echo "rosdev ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Install development tools and ROS packages
RUN apt-get update && apt-get install -y \
    # Build tools
    gcc \
    g++ \
    cmake \
    ninja-build \
    ccache \
    # Utilities
    git \
    vim \
    tmux \
    tree \
    curl \
    wget \
    # ROS 2 development tools
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    python3-pip \
    python3-flake8 \
    python3-pytest \
    # URDF / xacro
    ros-jazzy-xacro \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-joint-state-publisher \
    ros-jazzy-joint-state-publisher-gui \
    # Gazebo Harmonic 連携 (Gazebo Classic は使用不可)
    ros-jazzy-ros-gz \
    ros-jazzy-ros-gz-sim \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-ros-gz-image \
    # ros2_control + Gazebo プラグイン
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-gz-ros2-control \
    # MoveIt 2
    ros-jazzy-moveit \
    ros-jazzy-moveit-ros-visualization \
    # OpenArm description の依存
    ros-jazzy-realsense2-description \
    # 通信・可視化
    ros-jazzy-rmw-fastrtps-cpp \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-tf2-tools \
    ros-jazzy-rviz2 \
    ros-jazzy-rqt \
    ros-jazzy-rqt-common-plugins \
    && rm -rf /var/lib/apt/lists/*

# Initialize rosdep
RUN rosdep update

# ccache を PATH に追加
ENV PATH="/usr/lib/ccache:${PATH}"

USER rosdev
WORKDIR /home/rosdev

# ROS ワークスペース作成
RUN mkdir -p /home/rosdev/ros_ws/src

# bashrc: ROS 環境 + ワークスペースを自動 source
RUN cat >> /home/rosdev/.bashrc << 'EOF'

# ROS 2 environment
source /opt/ros/jazzy/setup.bash

# Workspace overlay (ビルド後に有効)
if [ -f ~/ros_ws/install/setup.bash ]; then
  source ~/ros_ws/install/setup.bash
fi

# Gazebo resource paths
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:~/ros_ws/install
export GZ_SIM_SYSTEM_PLUGIN_PATH=$GZ_SIM_SYSTEM_PLUGIN_PATH:~/ros_ws/install/lib

# Software rendering (GPU なし環境)
export LIBGL_ALWAYS_SOFTWARE=1
export MESA_GL_VERSION_OVERRIDE=3.3
EOF

ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV ROS_DOMAIN_ID=42
ENV LIBGL_ALWAYS_SOFTWARE=1
ENV MESA_GL_VERSION_OVERRIDE=3.3

WORKDIR /home/rosdev/ros_ws
CMD ["/bin/bash"]
