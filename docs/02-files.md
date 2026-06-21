# 02. ファイル別の役割

`ros_ws/src/` 配下を、パッケージ別に上から眺めるカタログです。「自作」「上流（enactic 由来）」「自作（上流の流用）」を明示し、何のために存在するかを書きます。

## openarm_description/

**出所**: [enactic/openarm_description](https://github.com/enactic/openarm_description) を `ros_ws/src/` に clone（subtree でも submodule でもなく素の clone）。

URDF/メッシュ/慣性/コントロールゲイン定義。本プロジェクトでは「形」だけを供給するレイヤとして使う。

| ファイル | 役割 |
|---|---|
| `urdf/robot/v10.urdf.xacro` | top-level xacro。`bimanual:=true` で双腕、`hand:=true` でグリッパ込み、`ros2_control:=false` で ros2_control タグなし。本プロジェクトはこの構成で読む |
| `urdf/robot/openarm_robot.xacro` | マクロ本体（リンク・関節を組み立てる） |
| `urdf/arm/*.xacro` | アーム macro |
| `urdf/body/*.xacro` | ボディ macro |
| `urdf/ee/openarm_hand*.xacro` | グリッパ（openarm_hand）macro |
| `urdf/ros2_control/openarm.bimanual.ros2_control.xacro` | 上流純正の ros2_control。`mock_components/GenericSystem` または `openarm_hardware`（実機 CAN）の 2 択。**本プロジェクトでは使わない**（Gazebo 用は別途自作） |
| `config/arm/v10/joint_limits.yaml` | URDF 用の関節制限（velocity, effort） |
| `config/arm/v10/inertials.yaml` | 慣性パラメータ。**openarm_hand の finger link の off-diagonal が 0 に修正済み**（Gazebo Inertia warning 回避） |
| `config/hand/openarm_hand/inertials.yaml` | グリッパ慣性 |

依存: `realsense2_description`（Dockerfile で apt 経由インストール）。

## openarm_bimanual_moveit_config/

**出所**: upstream `enactic/openarm_ros2/openarm_bimanual_moveit_config` から **`config/` だけ流用**、`launch/` と `package.xml` は再生成。

MoveIt 2 が必要とする設定（planning group, kinematics solver, planner, controller mapping）を 1 か所に集める。

| ファイル | 役割 | 出所 |
|---|---|---|
| `config/openarm_bimanual.srdf` | 4 つの planning group (`left_arm`, `right_arm`, `left_gripper`, `right_gripper`) と、named state (`home`, `hands_up`, `open`, `closed`, `half_closed`)、end_effector、passive joint、ACM (Allowed Collision Matrix) を定義 | 流用 |
| `config/kinematics.yaml` | `left_arm` / `right_arm` に KDL IK plugin を割り当て | 流用 |
| `config/joint_limits.yaml` | MoveIt の planning 用関節制限。**全関節に acceleration limit を入れている**（[01-design.md](01-design.md#7-すべての関節に-acceleration-limit-を入れる) 参照） | 流用 + 自プロジェクトで修正 |
| `config/moveit_controllers.yaml` | MoveIt 側のコントローラ登録。`FollowJointTrajectory` 2 本 + `GripperCommand` 2 本。`MoveItSimpleControllerManager` で管理 | 流用 |
| `config/ompl_planning.yaml` | OMPL planning pipeline 設定。`request_adapters` と `response_adapters` の順序定義（**`AddTimeOptimalParameterization` が response adapter のトップ**） | 流用 |
| `config/ros2_controllers.yaml` | **MoveIt setup assistant が生成した残骸で、本プロジェクトでは未使用**。実際の controller_manager は [`openarm_gz_sim/config/ros2_controllers.yaml`](../ros_ws/src/openarm_gz_sim/config/ros2_controllers.yaml) を読む | 流用 |
| `config/pilz_cartesian_limits.yaml` | Pilz Industrial Motion planner 用の Cartesian 速度・加速度制限。**現在 planner として Pilz は有効化されていない**（参考） | 流用 |
| `config/initial_positions.yaml` | mock hardware 用の初期姿勢。**本プロジェクトでは Gazebo の物理シミュレーションが初期姿勢を決めるので未使用** | 流用 |
| `config/moveit.rviz` | RViz の MotionPlanning パネル設定（保存済みビュー） | 流用 |
| `launch/demo.launch.py` | upstream の demo launch。**本プロジェクトでは未使用**（`openarm_bringup/sim.launch.py` を使う） | 流用、未使用 |
| `launch/move_group.launch.py` | upstream の move_group 単独 launch。**未使用** | 流用、未使用 |
| `launch/moveit_rviz.launch.py` | upstream の RViz 単独 launch。**未使用** | 流用、未使用 |

> 上流の launch を残してあるのは、デバッグ時に「最小構成で動くか」を切り分けるためのリファレンスとしてとっておく目的。本プロジェクトの正規の入口は `openarm_bringup` 経由。

## openarm_gz_sim/

**出所**: 全部自作。Gazebo Harmonic 統合の中核。

| ファイル | 役割 |
|---|---|
| `urdf/openarm_gz_bimanual.urdf.xacro` | top-level wrapper xacro。`v10.urdf.xacro` を `bimanual=true, ros2_control=false, hand=true` で include し、Gazebo 用の ros2_control xacro と `<gazebo><plugin>` 宣言を後ろから付ける |
| `urdf/openarm_gz.ros2_control.xacro` | Gazebo 用 ros2_control 定義。`<plugin>gz_ros2_control/GazeboSimSystem</plugin>` を hardware として宣言。アーム 7×2、グリッパ 1×2 = **計 16 関節** すべてに `<command_interface name="position"/>` と `<state_interface>` (position, velocity) を割り当て |
| `config/ros2_controllers.yaml` | controller_manager 本体の設定（`update_rate: 100Hz`）と 5 コントローラ宣言:<br>- `joint_state_broadcaster`<br>- `left_arm_controller` (JointTrajectoryController, 7 軸)<br>- `right_arm_controller` (JointTrajectoryController, 7 軸)<br>- `left_gripper_controller` (GripperActionController, 1 軸)<br>- `right_gripper_controller` (GripperActionController, 1 軸)<br>JTC には `goal: 0.05` rad と `stopped_velocity_tolerance: 0.05` の goal tolerance を設定 |
| `launch/gz_sim.launch.py` | **Gazebo サーバ起動 + robot_state_publisher + ros_gz_bridge**。`GZ_SIM_RESOURCE_PATH` も設定（`model://<pkg>/...` URI 解決のため） |
| `launch/spawn_robot.launch.py` | **ロボットを Gazebo にスポーン + コントローラ spawner（イベント駆動）**。`OnProcessExit` で 3 段階：spawn → jsb → arm/gripper × 4 並列 |
| `worlds/empty.sdf` | 最小限の Gazebo world。physics, scene_broadcaster, sun, ground_plane のみ |

## openarm_bringup/

**出所**: 全部自作。3 パッケージを束ねる統合層。

| ファイル | 役割 |
|---|---|
| `launch/sim.launch.py` | **唯一のユーザ向けエントリーポイント**。`gz_sim.launch.py` と `spawn_robot.launch.py` を include し、TimerAction で `move_group` (20s) → `rviz2` (30s) → `scene_setup.py` (30s) を順に起動。MoveIt 向けパラメータ（`robot_description`, `robot_description_semantic`, kinematics, joint_limits, controllers, OMPL）を組み立てる |
| `scripts/scene_setup.py` | **planning scene にグラウンドプレーンを publish**。`PlanningScene` に `CollisionObject(BOX, 5×5×0.1m, z=-0.05)` を ADD で 2 秒間隔 × 3 回送って終了 |

## docker/

| ファイル | 役割 |
|---|---|
| `Dockerfile` | ROS 2 Jazzy ベース。MoveIt 2, ros2_control, ros_gz_*, realsense2_description, cyclonedds 等を apt で入れる |
| `docker-compose.yaml` | コンテナ起動定義。`ros_ws` を bind mount、X11 forward、`RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`, `ROS_DOMAIN_ID=42`, `LIBGL_ALWAYS_SOFTWARE=1` |
| `setup_x11.sh` | X11 forwarding 用の `.docker.xauth` を準備するヘルパー |

## ルート

| ファイル | 役割 |
|---|---|
| `README.md` | エンドユーザ向けの Quick Start とトラブルシューティング |
| `PLAN.md` | 実装プラン（Phase 1〜6）。設計の経緯ログとして残してある |
| `openarm_gazebo.repos` | `vcs import` 用の依存リポジトリ宣言（`openarm_description`） |
| `scripts/` | 開発補助スクリプト |

## 「変えたいとき」インデックス

| やりたいこと | 触るファイル |
|---|---|
| 関節の planning 上限を変える | `openarm_bimanual_moveit_config/config/joint_limits.yaml` |
| planner を OMPL 以外に変える | `openarm_bimanual_moveit_config/config/ompl_planning.yaml` を分けて pipeline 追加、`sim.launch.py` の `planning_pipelines` を編集 |
| コントローラの種類・PID を変える | `openarm_gz_sim/config/ros2_controllers.yaml` |
| Gazebo の world / 物理パラメータを変える | `openarm_gz_sim/worlds/empty.sdf` |
| 衝突許容ペアを増やす | `openarm_bimanual_moveit_config/config/openarm_bimanual.srdf` の `<disable_collisions>` |
| RViz の初期表示を変える | `openarm_bimanual_moveit_config/config/moveit.rviz` |
| 起動順序・タイミングを変える | `openarm_bringup/launch/sim.launch.py` |
| Gazebo にスポーンする位置を変える | `openarm_gz_sim/launch/spawn_robot.launch.py` の `-z` 引数 |
| planning scene に追加物体を入れる | `openarm_bringup/scripts/scene_setup.py` を拡張 |
| 単腕構成にする | `openarm_gz_bimanual.urdf.xacro` の `bimanual` arg を `false`、SRDF も差し替え |
| 実機に切り替える | `openarm_gz_sim` を使わず、`openarm_description/urdf/ros2_control/openarm.bimanual.ros2_control.xacro` の `openarm_hardware` モードに切り替えた launch を新規作成 |
