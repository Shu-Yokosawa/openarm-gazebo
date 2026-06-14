# OpenArm Gazebo MoveIt2 Simulation

ROS 2 Jazzy + Gazebo Harmonic + MoveIt 2 simulation for the OpenArm v10 bimanual robot (2 × 7-DOF arms + OpenArm Hand grippers).

## Prerequisites

- Docker (with `docker compose`)
- No GPU required (uses Mesa software rendering)

## Quick Start

```bash
# 1. Build the Docker image
cd /path/to/openarm_gazebo
docker compose build

# 2. Start a container
docker compose up -d

# 3. Connect to the container
docker exec -it openarm_sim bash

# 4. Build the workspace (first time only)
source /opt/ros/jazzy/setup.bash
cd ~/ros_ws
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release

# 5. Launch the simulation
source ~/ros_ws/install/setup.bash
ros2 launch openarm_bringup sim.launch.py
```

RViz opens automatically ~20 seconds after launch. The planning scene ground plane is published at ~30 seconds.

## What You Can Do

### Move the arm via RViz MotionPlanning (the recommended workflow)

The RViz window that opens at ~30 s contains the **MotionPlanning** plugin in the left dock. Follow these steps — each one matters; skipping any of them is the usual reason the robot does not move in Gazebo.

1. **Wait for the simulation to finish initializing.** In the terminal that started the launch, wait until you see `You can start planning now!` from `move_group` and the RViz window has loaded the robot. This takes ~30 s.
2. **Select a planning group** in the MotionPlanning panel → *Planning* tab → *Planning Group*. Pick one of `left_arm`, `right_arm`, `left_gripper`, `right_gripper`. Each plan moves only one group.
3. **Set a goal state**. Either
   - drag the orange interactive marker at the arm tip in the 3D view, or
   - choose a named state from *Goal State* dropdown — `home` (all zeros), `hands_up` (joint4 = 2 rad). Grippers have `open` (0.044 m) / `half_closed` (0.022 m) / `closed` (0 m).
4. **Click `Plan`.** RViz visualizes the planned trajectory as a ghost arm sweeping from start to goal. **Plan only renders in RViz — it does NOT move Gazebo.**
5. **Click `Plan & Execute`** (or `Execute` after a successful Plan). *This* is the step that sends the trajectory to ros2_control and drives Gazebo. The real robot in the Gazebo window will move to the goal pose within a few seconds.
6. **Confirm it moved** with `ros2 topic echo /joint_states --once` — the positions should match the goal.

If `Plan & Execute` reports failure, check the move_group terminal output. The most common causes:
- *“No acceleration limit was defined for joint …”* — `joint_limits.yaml` is missing acceleration limits (this repo ships with them set; if you replace the file, keep them).
- *“Aborted due to goal_time_tolerance”* — the trajectory was too aggressive for sim physics. Lower `Velocity Scaling` / `Accel Scaling` sliders in the MotionPlanning panel.
- *“Start state appears to be in collision”* — the planning scene thinks the arm is colliding with itself. Click *Update* under *Current State* or wait until the ground plane is published (~30 s).

### Move the arm via CLI

```bash
# Plan for left arm — error_code.val=1 is SUCCESS, 99999 is FAILURE (Jazzy moveit_msgs/MoveItErrorCodes)
ros2 service call /plan_kinematic_path moveit_msgs/srv/GetMotionPlan \
  '{motion_plan_request: {group_name: "left_arm",
    goal_constraints: [{joint_constraints: [
      {joint_name: "openarm_left_joint1", position: 0.5, tolerance_above: 0.01, tolerance_below: 0.01, weight: 1.0},
      {joint_name: "openarm_left_joint2", position: 0.3, tolerance_above: 0.01, tolerance_below: 0.01, weight: 1.0}
    ]}],
    num_planning_attempts: 5, allowed_planning_time: 5.0}}'
```

`/plan_kinematic_path` only plans — it does not execute. To plan *and* execute, send a `moveit_msgs/action/MoveGroup` goal to `/move_action` with `planning_options.plan_only = false`, or drive the controller directly with a `control_msgs/action/FollowJointTrajectory` goal on `/<arm>_controller/follow_joint_trajectory`.

### Check Controller State

```bash
ros2 control list_controllers
# Expected: joint_state_broadcaster, left_arm_controller, right_arm_controller,
#           left_gripper_controller, right_gripper_controller — all active
```

### Monitor Joint States

```bash
ros2 topic echo /joint_states --once
# 16 joints at ~100 Hz
```

## Package Structure

```
ros_ws/src/
├── openarm_description/         # Upstream URDF (enactic/openarm_description)
│   └── config/hand/openarm_hand/inertials.yaml  # finger off-diagonal inertia = 0
├── openarm_bimanual_moveit_config/
│   └── config/
│       ├── openarm_bimanual.srdf   # planning groups, ACM, end-effectors
│       ├── kinematics.yaml         # KDL kinematics
│       ├── joint_limits.yaml       # velocity scaling 0.1 (10% of max)
│       ├── moveit_controllers.yaml # FollowJointTrajectory + GripperCommand
│       └── ompl_planning.yaml      # OMPL planner config
├── openarm_gz_sim/
│   ├── urdf/
│   │   ├── openarm_gz_bimanual.urdf.xacro    # top-level xacro (bimanual=true)
│   │   └── openarm_gz.ros2_control.xacro     # GazeboSimSystem hardware plugin
│   ├── config/ros2_controllers.yaml          # 5 controllers + trajectory constraints
│   └── launch/
│       ├── gz_sim.launch.py    # Gazebo + RSP + ros_gz_bridge
│       └── spawn_robot.launch.py  # event-driven spawn + controller spawner
└── openarm_bringup/
    ├── scripts/scene_setup.py   # publishes ground plane to planning scene
    └── launch/sim.launch.py     # top-level: Gazebo + MoveIt + RViz
```

## Launch Sequence

| Time (s) | Event |
|----------|-------|
| 0 | Gazebo Harmonic + robot_state_publisher + ros_gz_bridge |
| ~3 | Robot spawned in Gazebo (event-driven after Gazebo ready) |
| ~4 | joint_state_broadcaster activated |
| ~5 | left_arm / right_arm / left_gripper / right_gripper controllers activated |
| 20 | move_group + RViz started |
| 30 | ground_plane collision object published to planning scene |

## Controller Details

| Controller | Type | Joints |
|-----------|------|--------|
| `joint_state_broadcaster` | JointStateBroadcaster | all 16 |
| `left_arm_controller` | JointTrajectoryController | left_joint1–7 |
| `right_arm_controller` | JointTrajectoryController | right_joint1–7 |
| `left_gripper_controller` | GripperActionController | left_finger_joint1 |
| `right_gripper_controller` | GripperActionController | right_finger_joint1 |

Trajectory goal tolerance: 0.05 rad per joint. Gripper position tolerance: 0.005 m.

## Known Limitations

- Collision mesh warnings: `model://openarm_description/meshes/.../link*_symp.stl` not found — non-critical, simplified collision shapes are missing from upstream but visual/inertial meshes load correctly.
- Velocity scaling defaults to 10% (`default_velocity_scaling_factor: 0.1` in `joint_limits.yaml`). Increase up to 1.0 in motion requests for faster motion.
- No GPU required; if Gazebo rendering is slow, set `LIBGL_ALWAYS_SOFTWARE=1 MESA_GL_VERSION_OVERRIDE=3.3` (already set in Docker entrypoint).

## Troubleshooting

**Stale processes from a previous run cause DDS namespace pollution:**
```bash
docker compose restart
```

**Controllers fail to activate:**
Check that the robot was spawned successfully first:
```bash
docker exec openarm_sim bash -c "source /opt/ros/jazzy/setup.bash && ros2 topic echo /joint_states --once"
```

**MoveIt cannot find the planning group:**
Wait for "You can start planning now!" in the move_group output (~20–25 s after launch).
