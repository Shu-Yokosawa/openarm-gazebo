#!/bin/bash
# ros_ws を colcon でビルドする

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="${SCRIPT_DIR}/../ros_ws"

cd "${WS_DIR}"

source /opt/ros/jazzy/setup.bash

echo "=== rosdep: 依存解決 ==="
rosdep install --from-paths src --ignore-src -r -y

echo "=== colcon build ==="
colcon build \
  --symlink-install \
  --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  "$@"

echo "=== 完了: source install/setup.bash を実行してください ==="
