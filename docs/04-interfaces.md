# 04. ROS 2 インターフェース一覧

`ros2 topic list` / `ros2 service list` / `ros2 action list` を眺めるときの早見表。`移行版` のように頻繁に名前が変わる API は本プロジェクトでは使っていない。

凡例：

- **提供元**: パッケージ／元になっている標準コンポーネント
- **方向**: P=Publish, S=Subscribe (Client / Server)
- **自作**: 本プロジェクトで定義したか、それとも標準（MoveIt / ros2_control / sensor_msgs / 等）の利用か

> 「全て標準。本プロジェクトはノード/launch/config を組み合わせているだけで、ROS interface 自体は一切自作していない」が結論。下の表でその対応を確認できます。

## Topics

| Topic | 型 | Publisher | Subscriber | 自作？ | 用途 |
|---|---|---|---|---|---|
| `/robot_description` | `std_msgs/String` (latched) | `robot_state_publisher` | `ros_gz_sim::create`, `move_group`, `rviz2` | 標準 | URDF を全員に配る |
| `/robot_description_semantic` | `std_msgs/String` (latched) | `move_group` | `rviz2` | MoveIt 標準 | SRDF を RViz へ配る。`sim.launch.py` で `publish_robot_description_semantic: True` を指定して有効化 |
| `/clock` | `rosgraph_msgs/Clock` | `ros_gz_bridge` (← Gazebo) | 全 `use_sim_time:=true` ノード | 標準 | sim time の唯一の出所 |
| `/tf` | `tf2_msgs/TFMessage` | `robot_state_publisher` | `move_group`, `rviz2` | 標準 | 関節 → リンク TF |
| `/tf_static` | `tf2_msgs/TFMessage` (latched) | `robot_state_publisher` | `move_group`, `rviz2` | 標準 | 固定 TF |
| `/joint_states` | `sensor_msgs/JointState` | `joint_state_broadcaster` (+ `ros_gz_bridge`) | `move_group`, `robot_state_publisher`, `rviz2` | 標準 | 16 関節の位置/速度を 100 Hz で配信 |
| `/planning_scene` | `moveit_msgs/PlanningScene` | `scene_setup`, `move_group` | `move_group`, `rviz2` | MoveIt 標準 | collision object 追加/差分更新 |
| `/monitored_planning_scene` | `moveit_msgs/PlanningScene` | `move_group` | `rviz2` | MoveIt 標準 | move_group が保有する scene の最新スナップ |
| `/display_planned_path` | `moveit_msgs/DisplayTrajectory` | `move_group` | `rviz2` | MoveIt 標準 | Plan 結果のゴースト表示用 |
| `/display_contacts` | `visualization_msgs/MarkerArray` | `move_group` | `rviz2` | MoveIt 標準 | 衝突可視化（必要時） |
| `/trajectory_execution_event` | `std_msgs/String` | `rviz2`, ユーザ | `move_group` | MoveIt 標準 | `"stop"` を送ると実行中の軌道を中断できる |
| `/attached_collision_object` | `moveit_msgs/AttachedCollisionObject` | ユーザ | `move_group` | MoveIt 標準 | ロボットに物体を attach する |
| `/collision_object` | `moveit_msgs/CollisionObject` | ユーザ | `move_group` | MoveIt 標準 | scene 単体オブジェクトのショートカット publish |
| `/world/empty/model/openarm/joint_state` | `sensor_msgs/JointState` (gz→ros 変換) | `ros_gz_bridge` | （`/joint_states` に remap） | 標準 (gz topic) | Gazebo 内部のジョイント状態 |

## Services

| Service | 型 | Server | Client | 自作？ | 用途 |
|---|---|---|---|---|---|
| `/plan_kinematic_path` | `moveit_msgs/srv/GetMotionPlan` | `move_group` | ユーザ / CLI | MoveIt 標準 | planning だけ（execute はしない） |
| `/compute_ik` | `moveit_msgs/srv/GetPositionIK` | `move_group` | ユーザ, RViz | MoveIt 標準 | 単発 IK |
| `/compute_fk` | `moveit_msgs/srv/GetPositionFK` | `move_group` | ユーザ | MoveIt 標準 | 単発 FK |
| `/compute_cartesian_path` | `moveit_msgs/srv/GetCartesianPath` | `move_group` | RViz (インタラクティブマーカー drag) | MoveIt 標準 | 直線補間軌道生成 |
| `/get_planner_params` | `moveit_msgs/srv/GetPlannerParams` | `move_group` | RViz | MoveIt 標準 | 利用可能 planner の問い合わせ |
| `/set_planner_params` | `moveit_msgs/srv/SetPlannerParams` | `move_group` | RViz | MoveIt 標準 | planner パラメータ動的更新 |
| `/query_planner_interface` | `moveit_msgs/srv/QueryPlannerInterfaces` | `move_group` | RViz | MoveIt 標準 | planner 一覧 |
| `/get_planning_scene` | `moveit_msgs/srv/GetPlanningScene` | `move_group` | RViz | MoveIt 標準 | scene 全体取得 |
| `/apply_planning_scene` | `moveit_msgs/srv/ApplyPlanningScene` | `move_group` | ユーザ | MoveIt 標準 | scene 全置換 |
| `/controller_manager/list_controllers` | `controller_manager_msgs/srv/ListControllers` | `controller_manager` | `ros2 control` CLI | ros2_control 標準 | 状態確認 |
| `/controller_manager/list_hardware_interfaces` | `controller_manager_msgs/srv/ListHardwareInterfaces` | `controller_manager` | `ros2 control` CLI | ros2_control 標準 | command/state interface 一覧 |
| `/controller_manager/switch_controller` | `controller_manager_msgs/srv/SwitchController` | `controller_manager` | `spawner`, ユーザ | ros2_control 標準 | active/inactive 切替 |
| `/controller_manager/load_controller` | `controller_manager_msgs/srv/LoadController` | `controller_manager` | `spawner` | ros2_control 標準 | controller プラグインの load |
| `/controller_manager/configure_controller` | `controller_manager_msgs/srv/ConfigureController` | `controller_manager` | `spawner` | ros2_control 標準 | controller の lifecycle 遷移 |

> その他、各 controller / move_group / ros2_control ノードは多数のパラメータ get/set, lifecycle, describe_parameters service を提供しますがここでは省略。

## Actions

| Action | 型 | Server | Client | 自作？ | 用途 |
|---|---|---|---|---|---|
| `/move_action` | `moveit_msgs/action/MoveGroup` | `move_group` | RViz (Plan & Execute), ユーザ | MoveIt 標準 | **plan + 任意で execute をまとめて行う**。`planning_options.plan_only` で挙動切替 |
| `/execute_trajectory` | `moveit_msgs/action/ExecuteTrajectory` | `move_group` | RViz (`Execute`), ユーザ | MoveIt 標準 | 既存軌道を controller に流すだけ |
| `/left_arm_controller/follow_joint_trajectory` | `control_msgs/action/FollowJointTrajectory` | `joint_trajectory_controller` (Gazebo 内) | `move_group`, ユーザ | ros2_control 標準 | 7 軸の関節軌道を時間付きで投げる |
| `/right_arm_controller/follow_joint_trajectory` | `control_msgs/action/FollowJointTrajectory` | 同上 | 同上 | ros2_control 標準 | 同上 |
| `/left_gripper_controller/gripper_cmd` | `control_msgs/action/GripperCommand` | `position_controllers/GripperActionController` | `move_group`, ユーザ | ros2_control 標準 | 指の位置を 1 値で指示（0〜0.044 m） |
| `/right_gripper_controller/gripper_cmd` | `control_msgs/action/GripperCommand` | 同上 | 同上 | ros2_control 標準 | 同上 |

## 「触ってもいいやつ」と「触らないでいいやつ」

ユーザが意図的に叩くのは（普通）次だけ：

- **RViz の MotionPlanning パネル** → 内部で `/move_action` を呼ぶ
- **CLI** で：
  - `ros2 action send_goal /left_arm_controller/follow_joint_trajectory ...` （MoveIt スキップで直接）
  - `ros2 action send_goal /left_gripper_controller/gripper_cmd ...` （グリッパ駆動）
  - `ros2 action send_goal /move_action moveit_msgs/action/MoveGroup '<yaml>'` （MoveIt 経由でやりたい場合）
  - `ros2 service call /plan_kinematic_path ...` （plan だけ確認したい）
- **planning scene への物体追加** → `/planning_scene` に `PlanningScene{is_diff=true, world.collision_objects=[...]}` を publish

それ以外は内部結線のための I/F なので、原則触らない。

## 主要メッセージのフィールド早見

### `control_msgs/action/FollowJointTrajectory`

```
# Goal
trajectory:
  joint_names: [str]
  points:
    - positions: [float]
      velocities: [float]   # 省略可
      accelerations: [float] # 省略可
      time_from_start: {sec, nanosec}
path_tolerance: [JointTolerance]    # 各点での許容誤差
goal_tolerance: [JointTolerance]    # 最終点での許容誤差
goal_time_tolerance: {sec, nanosec} # 軌道終端時刻の許容遅延

# Result
error_code: int (0=SUCCESSFUL, -1=INVALID_GOAL, -3=PATH_TOLERANCE_VIOLATED,
                 -4=GOAL_TOLERANCE_VIOLATED, -5=OLD_HEADER_TIMESTAMP)
error_string: str
```

### `control_msgs/action/GripperCommand`

```
# Goal
command:
  position: float    # m or rad
  max_effort: float  # N or N·m

# Result
position, effort, stalled, reached_goal: bool
```

### `moveit_msgs/action/MoveGroup`

```
# Goal
request:                  # moveit_msgs/MotionPlanRequest
  group_name: str
  start_state: RobotState  # 通常 empty で「現状から」
  goal_constraints: [Constraints]
  path_constraints: Constraints
  num_planning_attempts: int
  allowed_planning_time: float
  max_velocity_scaling_factor: float
  max_acceleration_scaling_factor: float
planning_options:
  plan_only: bool          # false で plan + execute, true で plan のみ
  planning_scene_diff: PlanningScene

# Result
error_code:                # moveit_msgs/MoveItErrorCodes
  val: int                 # 1=SUCCESS, 99999=FAILURE, -1=PLANNING_FAILED, ...
planned_trajectory: RobotTrajectory
executed_trajectory: RobotTrajectory
planning_time: float
```

`MoveItErrorCodes` の主な値：

| val | 意味 |
|---|---|
| 1 | SUCCESS |
| 99999 | FAILURE（汎用失敗） |
| -1 | PLANNING_FAILED |
| -2 | INVALID_MOTION_PLAN |
| -10 | START_STATE_IN_COLLISION |
| -12 | GOAL_IN_COLLISION |
| -17 | TIMED_OUT |

### `moveit_msgs/msg/PlanningScene` (差分モード)

```
is_diff: true   # ← 必ず true にする (false は scene 全置換で危険)
world:
  collision_objects:
    - header: {frame_id: "world"}
      id: "ground_plane"      # 同じ id で再 publish すると上書き
      operation: ADD | REMOVE | APPEND | MOVE
      primitives: [SolidPrimitive]
      primitive_poses: [Pose]
```

[`scene_setup.py`](../ros_ws/src/openarm_bringup/scripts/scene_setup.py) はこれを 2 秒間隔で 3 回送って終了します（move_group がまだ subscribe してないタイミングを救うため）。
