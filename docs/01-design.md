# 01. 設計思想

## ゴール

OpenArm v10 双腕（左右 7 軸 × 2 + グリッパ × 2）を、ROS 2 Jazzy + Gazebo Harmonic + MoveIt 2 で **GPU 無し PC でも動かせる** ように、**1 コマンド `ros2 launch openarm_bringup sim.launch.py`** で立ち上げる。実機制御コード（`openarm_hardware`）の差し替えを最小の変更で受けられるように、シミュレーション固有のコードは隔離する。

## パッケージ分割の方針

`ros_ws/src/` に 4 つのパッケージがあり、それぞれが「変える理由」を 1 つしか持たないように切ってあります。

| パッケージ | 出所 | 変える理由 |
|---|---|---|
| `openarm_description` | upstream `enactic/openarm_description` を clone | ロボットの形（URDF / メッシュ / 慣性）が変わったとき |
| `openarm_bimanual_moveit_config` | upstream `enactic/openarm_ros2` の `config/` を流用、`launch/` は再作成 | MoveIt の planning 設定（SRDF / planner / IK / コントローラマッピング）を変えたいとき |
| `openarm_gz_sim` | 全部自作 | Gazebo 固有の話（physics、`gz_ros2_control` の hardware plugin、ros_gz_bridge）を変えたいとき |
| `openarm_bringup` | 全部自作 | 起動の組み合わせ・順序を変えたいとき |

この分割により、たとえば

- 実機に切り替える → `openarm_gz_sim` を `openarm_hardware` 系に置き換えるだけで、`description` と `moveit_config` はそのまま使える
- URDF の上流更新を取り込む → `openarm_description` を `git pull` するだけで、自作部分にコンフリクトが起きない
- MoveIt の planner を変える → `openarm_bimanual_moveit_config/config/ompl_planning.yaml` だけ触ればよい

## 主要な設計決定と理由

### 1. upstream の moveit config から `config/` だけ流用し、`launch/` は再作成した

[`enactic/openarm_ros2`](https://github.com/enactic/openarm_ros2) は ROS 2 Humble ベース。yaml/SRDF はバージョン非依存なので流用可能だが、launch ファイルは Jazzy + Gazebo Harmonic 向けに API が違うので作り直した方が確実。

### 2. Gazebo 用 `ros2_control` xacro を別途用意した

upstream の `openarm_description/urdf/ros2_control/openarm.bimanual.ros2_control.xacro` は

- `mock_components/GenericSystem`（fake hardware）
- `openarm_hardware`（CAN 経由の実機）

の 2 モードしか持たない。Gazebo 用の `gz_ros2_control/GazeboSimSystem` プラグインを使うには **別の xacro を新規に書いて include する**形がもっとも干渉が少ない。それが [`openarm_gz_sim/urdf/openarm_gz.ros2_control.xacro`](../ros_ws/src/openarm_gz_sim/urdf/openarm_gz.ros2_control.xacro)。

ラッパー xacro [`openarm_gz_bimanual.urdf.xacro`](../ros_ws/src/openarm_gz_sim/urdf/openarm_gz_bimanual.urdf.xacro) で次の 3 つを束ねる：

1. `v10.urdf.xacro`（upstream の本体、`ros2_control=false` で include）
2. `openarm_gz.ros2_control.xacro`（自作、`GazeboSimSystem` を宣言）
3. `<gazebo><plugin filename="gz_ros2_control-system" ...>` の宣言（コントローラマネージャを Gazebo 内で起動）

### 3. `xacro:arg` は `xacro:include` より前に宣言する

[`openarm_gz_bimanual.urdf.xacro:12-15`](../ros_ws/src/openarm_gz_sim/urdf/openarm_gz_bimanual.urdf.xacro)：

```xml
<xacro:arg name="bimanual" default="true"/>
<xacro:arg name="ros2_control" default="false"/>
...
<xacro:include filename="$(find openarm_description)/urdf/robot/v10.urdf.xacro"/>
```

upstream の [`v10.urdf.xacro:42`](../ros_ws/src/openarm_description/urdf/robot/v10.urdf.xacro) は `bimanual` の default を `false` にしている。これを上書きしたいので、include より **前** に `<xacro:arg>` を宣言する必要がある。順序を逆にすると upstream の default が勝って単腕構成になる。

### 4. コントローラスポーンはイベント駆動

`OnProcessExit` で前段の完了をフックして次段を起動する。[`spawn_robot.launch.py`](../ros_ws/src/openarm_gz_sim/launch/spawn_robot.launch.py) を参照：

```
spawn_robot → [exit] → joint_state_broadcaster
             → [exit] → left_arm / right_arm / left_gripper / right_gripper（並列）
```

「Gazebo が立ち上がったら sleep で 5 秒待つ」式は CPU 負荷に弱く、特に PC が遅いとレース条件で死ぬ。`spawner` プロセスは内部で controller_manager が ready になるまで待つ作りなので、その exit を待てば最も確実。

### 5. RViz は move_group の **10 秒後** に起動する

[`sim.launch.py:130-132`](../ros_ws/src/openarm_bringup/launch/sim.launch.py)：

```python
TimerAction(period=20.0, actions=[move_group_node]),
TimerAction(period=30.0, actions=[rviz_node]),
```

`move_group` と `rviz2` を同時に起動すると、`MotionPlanning` プラグインが `move_group` の `robot_description_semantic` を取りに行くタイミングで NULL を引いて SEGV することがある。10 秒空けるだけで踏まなくなる。

### 6. `joint_limits.yaml` は `robot_description_planning` namespace に wrap する

[`sim.launch.py:66-68`](../ros_ws/src/openarm_bringup/launch/sim.launch.py)：

```python
joint_limits = {"robot_description_planning": load_yaml(moveit_pkg, "config", "joint_limits.yaml")}
```

MoveIt の `AddTimeOptimalParameterization` adapter は `robot_description_planning.joint_limits.<joint>.max_acceleration` から読む。素で渡すとパラメータは存在するが adapter から「ない」扱いされ、Plan & Execute は SUCCESS を見せかけて FAILURE を返す（Gazebo は動かない）。

### 7. すべての関節に acceleration limit を入れる

[`joint_limits.yaml`](../ros_ws/src/openarm_bimanual_moveit_config/config/joint_limits.yaml) は upstream では `has_acceleration_limits: false` だが、これだと `AddTimeOptimalParameterization` が FAILURE で止まる。シミュ目的なら適当な値（max_velocity / 2 程度）で OK。

### 8. プランニング時のグラウンドプレーンは MoveIt に別途教える

Gazebo の SDF world に床はあるが（[`worlds/empty.sdf:23-37`](../ros_ws/src/openarm_gz_sim/worlds/empty.sdf)）、MoveIt の planning scene には自動で入らない。床と衝突する経路を MoveIt に弾かせるために [`scene_setup.py`](../ros_ws/src/openarm_bringup/scripts/scene_setup.py) が `5m × 5m × 0.1m` の `BOX` を `/planning_scene` に publish する。

### 9. ACM（Allowed Collision Matrix）は双腕のまま残す

SRDF の `disable_collisions` は隣接リンク間だけ。左右アーム同士の衝突チェックは生かしてある。安全のためのデフォルトで、必要なら個別に `disable_collisions` を追加する。

### 10. GPU 無し前提

- Mesa のソフトウェアレンダリング（`LIBGL_ALWAYS_SOFTWARE=1`, `MESA_GL_VERSION_OVERRIDE=3.3`）を `docker/docker-compose.yaml` で環境変数として注入
- Gazebo Classic は禁止（`ros-jazzy-gazebo-ros-pkgs` は使わない）。Gazebo Harmonic + `ros_gz_bridge` 一本

### 11. DDS は CycloneDDS

FastCDR 2.2.5 の API break を回避するため `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`。`docker/docker-compose.yaml` で固定。

## 起動シーケンスを支える原則

- **物理的に正しい順序を、待てる仕組みで保証する**（sleep ではなく `OnProcessExit` と `TimerAction`）
- **ノード間の同期は型を介して行う**（`/clock`, `/joint_states`, `/robot_description`）
- **失敗時の戻り値が「Gazebo が動かない」状態と分離して見える** ように、エラーは必ずログに出す（FAILURE を握り潰さない）

詳細は次章以降で。
