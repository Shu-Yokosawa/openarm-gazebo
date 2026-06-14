"""
Gazebo Harmonic 起動 + robot_state_publisher + ros_gz_bridge
ロボットのスポーンは spawn_robot.launch.py で行う
"""
import os
import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    gz_sim_pkg = get_package_share_directory("openarm_gz_sim")
    desc_pkg = get_package_share_directory("openarm_description")

    # Gazebo は model://<pkg>/... URI を GZ_SIM_RESOURCE_PATH の各エントリ
    # 直下から <pkg>/... として探すので、各パッケージの share 親を渡す
    gz_resource_path = os.pathsep.join([
        os.path.dirname(desc_pkg),
        os.path.dirname(gz_sim_pkg),
    ])

    use_sim_time = LaunchConfiguration("use_sim_time", default="true")
    world = LaunchConfiguration("world", default=os.path.join(gz_sim_pkg, "worlds", "empty.sdf"))

    # URDF (Gazebo用, ros2_control=false — GazeboSystemは別xacroで注入)
    robot_description_content = xacro.process_file(
        os.path.join(gz_sim_pkg, "urdf", "openarm_gz_bimanual.urdf.xacro"),
        mappings={"bimanual": "true", "ros2_control": "false", "hand": "true"},
    ).toprettyxml(indent="  ")
    robot_description = {"robot_description": robot_description_content}

    # Gazebo Harmonic 起動
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("ros_gz_sim"),
                "launch",
                "gz_sim.launch.py",
            )
        ),
        launch_arguments={"gz_args": ["-r -s ", world]}.items(),
    )

    # robot_state_publisher
    rsp_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": use_sim_time}],
    )

    # ros_gz_bridge — clock, joint_states
    bridge_node = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/world/empty/model/openarm/joint_state@sensor_msgs/msg/JointState[gz.msgs.Model",
        ],
        remappings=[
            ("/world/empty/model/openarm/joint_state", "/joint_states"),
        ],
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
    )

    return LaunchDescription([
        SetEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            gz_resource_path + os.pathsep + os.environ.get("GZ_SIM_RESOURCE_PATH", ""),
        ),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument(
            "world",
            default_value=os.path.join(gz_sim_pkg, "worlds", "empty.sdf"),
        ),
        gz_sim,
        rsp_node,
        bridge_node,
    ])
