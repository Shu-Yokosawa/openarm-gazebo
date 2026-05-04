"""
MoveIt RViz launch — starts move_group and rviz2 with MoveIt plugin.
Expects robot_state_publisher already running with /robot_description.
"""
import os
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def load_yaml(pkg_share, *rel_path):
    path = os.path.join(pkg_share, *rel_path)
    with open(path) as f:
        return yaml.safe_load(f)


def generate_launch_description():
    moveit_pkg = get_package_share_directory("openarm_bimanual_moveit_config")

    srdf_path = os.path.join(moveit_pkg, "config", "openarm_bimanual.srdf")
    with open(srdf_path) as f:
        srdf_content = f.read()

    kinematics = {"robot_description_kinematics": load_yaml(moveit_pkg, "config", "kinematics.yaml")}

    rviz_config = os.path.join(moveit_pkg, "config", "moveit.rviz")

    move_group_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(moveit_pkg, "launch", "move_group.launch.py")
        )
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config],
        parameters=[
            {"robot_description_semantic": srdf_content},
            kinematics,
        ],
    )

    return LaunchDescription([move_group_launch, rviz_node])
