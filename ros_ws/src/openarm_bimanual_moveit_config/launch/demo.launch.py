"""
Standalone demo — fake hardware (no Gazebo).
Starts: robot_state_publisher, ros2_control_node (fake), all controller spawners,
        move_group, rviz2.
"""
import os
import xacro
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node


def load_yaml(pkg_share, *rel_path):
    path = os.path.join(pkg_share, *rel_path)
    with open(path) as f:
        return yaml.safe_load(f)


def generate_launch_description():
    desc_pkg = get_package_share_directory("openarm_description")
    moveit_pkg = get_package_share_directory("openarm_bimanual_moveit_config")

    # --- URDF (fake hardware) ---
    robot_description_content = xacro.process_file(
        os.path.join(desc_pkg, "urdf", "robot", "v10.urdf.xacro"),
        mappings={
            "arm_type": "v10",
            "bimanual": "true",
            "ros2_control": "true",
            "use_fake_hardware": "true",
            "fake_sensor_commands": "false",
        },
    ).toprettyxml(indent="  ")
    robot_description = {"robot_description": robot_description_content}

    # --- MoveIt configs ---
    srdf_path = os.path.join(moveit_pkg, "config", "openarm_bimanual.srdf")
    with open(srdf_path) as f:
        srdf_content = f.read()

    kinematics_yaml = load_yaml(moveit_pkg, "config", "kinematics.yaml")
    kinematics = {"robot_description_kinematics": kinematics_yaml}
    joint_limits = load_yaml(moveit_pkg, "config", "joint_limits.yaml")
    moveit_controllers = load_yaml(moveit_pkg, "config", "moveit_controllers.yaml")
    ros2_controllers_file = os.path.join(moveit_pkg, "config", "ros2_controllers.yaml")

    # Jazzy: planning_plugins (list), request_adapters/response_adapters (list)
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

    # --- Nodes ---
    rsp_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description],
    )

    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        output="screen",
        parameters=[robot_description, ros2_controllers_file],
    )

    def spawner(name):
        return Node(
            package="controller_manager",
            executable="spawner",
            arguments=[name, "--controller-manager", "/controller_manager"],
            output="screen",
        )

    jsb_spawner = TimerAction(period=2.0, actions=[spawner("joint_state_broadcaster")])
    left_arm_spawner = TimerAction(period=3.0, actions=[spawner("left_arm_controller")])
    right_arm_spawner = TimerAction(period=3.0, actions=[spawner("right_arm_controller")])
    left_gripper_spawner = TimerAction(period=3.0, actions=[spawner("left_gripper_controller")])
    right_gripper_spawner = TimerAction(period=3.0, actions=[spawner("right_gripper_controller")])

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            robot_description,
            {"robot_description_semantic": srdf_content},
            kinematics,
            joint_limits,
            moveit_controllers,
            planning_pipelines,
            trajectory_execution,
            {"publish_robot_description_semantic": True},
        ],
    )

    rviz_config = os.path.join(moveit_pkg, "config", "moveit.rviz")
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config],
        parameters=[
            robot_description,
            {"robot_description_semantic": srdf_content},
            kinematics,
        ],
    )

    return LaunchDescription([
        rsp_node,
        ros2_control_node,
        jsb_spawner,
        left_arm_spawner,
        right_arm_spawner,
        left_gripper_spawner,
        right_gripper_spawner,
        TimerAction(period=4.0, actions=[move_group_node]),
        TimerAction(period=5.0, actions=[rviz_node]),
    ])
