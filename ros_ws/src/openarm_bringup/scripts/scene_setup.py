#!/usr/bin/env python3
"""Publish static planning scene objects (ground plane) to MoveIt."""
import rclpy
from rclpy.node import Node
from moveit_msgs.msg import PlanningScene, CollisionObject
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import Pose


class SceneSetup(Node):
    def __init__(self):
        super().__init__("scene_setup")
        self._pub = self.create_publisher(PlanningScene, "/planning_scene", 10)
        self._tries = 3
        self.create_timer(2.0, self._publish)

    def _publish(self):
        scene = PlanningScene()
        scene.is_diff = True

        obj = CollisionObject()
        obj.header.frame_id = "world"
        obj.id = "ground_plane"
        obj.operation = CollisionObject.ADD

        box = SolidPrimitive()
        box.type = SolidPrimitive.BOX
        box.dimensions = [5.0, 5.0, 0.1]

        pose = Pose()
        pose.position.z = -0.05  # top surface at z=0 (Gazebo ground level)
        pose.orientation.w = 1.0

        obj.primitives.append(box)
        obj.primitive_poses.append(pose)
        scene.world.collision_objects.append(obj)

        self._pub.publish(scene)
        self.get_logger().info("Published ground_plane to /planning_scene")

        self._tries -= 1
        if self._tries <= 0:
            raise SystemExit


def main():
    rclpy.init()
    node = SceneSetup()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
