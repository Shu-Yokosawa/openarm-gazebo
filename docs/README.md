# openarm_gazebo 開発者向けドキュメント

このフォルダは、openarm_gazebo のコードを読み解くための地図です。プロジェクトトップの `README.md` は「使う人」向けの Quick Start ですが、ここは「中身を理解したい・改造したい人」向けに、設計の意図とコードの責務を順を追って説明します。

## 読む順序

1. **[01-design.md](01-design.md)** — 全体の設計思想。なぜパッケージを 4 つに分けたか、なぜ Gazebo 用 ros2_control xacro を別途用意したか、なぜ joint_limits を `robot_description_planning` namespace に包むのか、といった「形になった理由」をまず押さえる。
2. **[02-files.md](02-files.md)** — 各ファイルが何を担当しているか。`ros_ws/src/` 配下を上から舐めるカタログ。
3. **[03-nodes.md](03-nodes.md)** — 実行時の ROS 2 ノード構成。誰が誰の出力を受けて何を出力するか、起動シーケンスのタイムライン。
4. **[04-interfaces.md](04-interfaces.md)** — 全 topic / service / action の一覧表。型、提供元（MoveIt / ros2_control / sensor_msgs / 自作）、用途。
5. **[05-motion-planning.md](05-motion-planning.md)** — RViz の `Plan & Execute` を押したら何が起きるかを Mermaid シーケンス図で追う。失敗パターンと切り分け。

## 一行で言うと

- **`openarm_description`** = 形（URDF/メッシュ、upstream そのまま）
- **`openarm_bimanual_moveit_config`** = MoveIt の頭脳の設定（SRDF, planner, IK, controller マッピング）
- **`openarm_gz_sim`** = Gazebo の体（physics プラグイン、ros2_control の hardware backend、bridge）
- **`openarm_bringup`** = 上記 3 つを 1 コマンドで起動する統合ランチ

データの流れは **「MoveIt が考えて → ros2_control が伝えて → Gazebo が動かす → 結果が `/joint_states` で全員に戻る」** という単方向ループ。これさえ頭に入っていれば残りは細部です。
