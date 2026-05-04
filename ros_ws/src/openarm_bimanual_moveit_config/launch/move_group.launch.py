"""
move_group launch — expects robot_state_publisher already running with /robot_description.
Used standalone or included by sim.launch.py.
"""
import os
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
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

    # kinematics.yaml は robot_description_kinematics 名前空間で渡す
    kinematics_yaml = load_yaml(moveit_pkg, "config", "kinematics.yaml")
    kinematics = {"robot_description_kinematics": kinematics_yaml}

    joint_limits = load_yaml(moveit_pkg, "config", "joint_limits.yaml")
    moveit_controllers = load_yaml(moveit_pkg, "config", "moveit_controllers.yaml")

    # Jazzy 形式: planning_plugins (list), request_adapters (list), response_adapters (list)
    ompl_config = load_yaml(moveit_pkg, "config", "ompl_planning.yaml")
    planning_pipelines = {
        "planning_pipelines": ["ompl"],
        "default_planning_pipeline": "ompl",
        "ompl": ompl_config,
    }

    trajectory_execution = {
        "moveit_manage_controllers": True,
        "trajectory_execution.allowed_execution_duration_scaling": 1.2,
        "trajectory_execution.allowed_goal_duration_margin": 0.5,
        "trajectory_execution.allowed_start_tolerance": 0.01,
    }

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            {"robot_description_semantic": srdf_content},
            kinematics,
            joint_limits,
            moveit_controllers,
            planning_pipelines,
            trajectory_execution,
            {"publish_robot_description_semantic": True},
            {"use_sim_time": False},
        ],
    )

    return LaunchDescription([move_group_node])
