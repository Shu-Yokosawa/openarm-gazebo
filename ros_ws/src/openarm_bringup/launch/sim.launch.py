"""
1コマンドで Gazebo + MoveIt + RViz を起動する統合ランチ

起動順序:
  [1] Gazebo サーバー + RSP + ros_gz_bridge (gz_sim.launch.py)
  [2] ロボットスポーン (Gazebo world 準備完了を内部で待機)
  [3] joint_state_broadcaster  (spawn_robot 終了をトリガー)
  [4] 4コントローラー並列起動 (jsb 終了をトリガー)
  [5] MoveIt move_group        (コントローラー群が active になってから起動)
  [6] RViz                     (move_group と同時)
"""
import os
import yaml
import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def load_yaml(pkg_share, *rel_path):
    path = os.path.join(pkg_share, *rel_path)
    with open(path) as f:
        return yaml.safe_load(f)


def generate_launch_description():
    gz_sim_pkg = get_package_share_directory("openarm_gz_sim")
    moveit_pkg = get_package_share_directory("openarm_bimanual_moveit_config")

    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    # --- [1] Gazebo + RSP + bridge ---
    gz_sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gz_sim_pkg, "launch", "gz_sim.launch.py")
        )
    )

    # --- [2][3][4] スポーン + コントローラー (イベント駆動) ---
    spawn_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gz_sim_pkg, "launch", "spawn_robot.launch.py")
        )
    )

    # --- MoveIt パラメータ ---
    robot_description_content = xacro.process_file(
        os.path.join(gz_sim_pkg, "urdf", "openarm_gz_bimanual.urdf.xacro"),
        mappings={"bimanual": "true", "ros2_control": "false", "hand": "true"},
    ).toprettyxml(indent="  ")
    robot_description = {"robot_description": robot_description_content}

    srdf_path = os.path.join(moveit_pkg, "config", "openarm_bimanual.srdf")
    with open(srdf_path) as f:
        srdf_content = f.read()

    kinematics_yaml = load_yaml(moveit_pkg, "config", "kinematics.yaml")
    kinematics = {"robot_description_kinematics": kinematics_yaml}
    # MoveIt の TimeOptimalTrajectoryGeneration adapter は
    # robot_description_planning.joint_limits.* から制限を読むため namespace で wrap する
    joint_limits = {"robot_description_planning": load_yaml(moveit_pkg, "config", "joint_limits.yaml")}
    moveit_controllers = load_yaml(moveit_pkg, "config", "moveit_controllers.yaml")
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

    # --- [5] MoveIt move_group ---
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
            {"use_sim_time": use_sim_time},
        ],
    )

    # --- [6] RViz ---
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
            {"use_sim_time": use_sim_time},
        ],
    )

    # --- [7] Planning scene (ground plane) ---
    scene_setup_node = Node(
        package="openarm_bringup",
        executable="scene_setup.py",
        output="log",
        parameters=[{"use_sim_time": use_sim_time}],
    )

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        gz_sim_launch,
        spawn_launch,
        # 全コントローラー active 後に move_group を起動
        TimerAction(period=20.0, actions=[move_group_node]),
        # move_group 初期化完了を待ってから RViz を起動 (同時起動だと MotionPlanning plugin が crash)
        TimerAction(period=30.0, actions=[rviz_node]),
        # move_group 起動後にプランニングシーンを設定
        TimerAction(period=30.0, actions=[scene_setup_node]),
    ])
