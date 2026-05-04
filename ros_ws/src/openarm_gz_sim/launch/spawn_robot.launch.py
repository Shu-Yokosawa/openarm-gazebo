"""
Gazebo へのロボットスポーン + コントローラー spawner (イベント駆動)

起動順序:
  spawn_robot → [OnProcessExit] → joint_state_broadcaster
              → [OnProcessExit] → left_arm / right_arm / left_gripper / right_gripper (並列)
"""
from launch import LaunchDescription
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    # ロボットを Gazebo にスポーン (/robot_description トピックから)
    # ros_gz_sim create は内部で gz-transport の world サービスを待つため
    # Gazebo 起動直後でも安全に呼び出せる
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name", "openarm",
            "-topic", "/robot_description",
            "-z", "0.01",
        ],
        output="screen",
    )

    def spawner(name):
        return Node(
            package="controller_manager",
            executable="spawner",
            arguments=[name, "--controller-manager", "/controller_manager"],
            output="screen",
            parameters=[{"use_sim_time": use_sim_time}],
        )

    jsb = spawner("joint_state_broadcaster")

    # spawn_robot 完了後に joint_state_broadcaster をロード
    # jsb 完了後に残り4コントローラーを並列ロード
    return LaunchDescription([
        spawn_robot,
        RegisterEventHandler(
            OnProcessExit(
                target_action=spawn_robot,
                on_exit=[jsb],
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=jsb,
                on_exit=[
                    spawner("left_arm_controller"),
                    spawner("right_arm_controller"),
                    spawner("left_gripper_controller"),
                    spawner("right_gripper_controller"),
                ],
            )
        ),
    ])
