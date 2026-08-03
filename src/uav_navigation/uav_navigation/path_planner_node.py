#!/usr/bin/env python3
"""
Module 3.2: ROS 2 Hardware Acceleration Wrapper Node
Bridges ROS 2 PointClouds and Nav2 Goal Poses to the Module 3.1 PYNQ Driver.
"""

import rclpy
from rclpy.node import Node
import numpy as np
import sys
import os

from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path
from std_msgs.msg import Header

# Add driver path to Python environment
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'fpga/drivers')))
WORKSPACE_DIR = "/home/hadynata/vs-code-data/uav-fpga/uav-sim"

# 2. Safely register the hardware module directories to Python's system path
if WORKSPACE_DIR not in sys.path:
    sys.path.append(WORKSPACE_DIR)

# 3. Use an ABSOLUTE absolute import layout now that the root path is registered
try:
    from fpga.drivers.pynq_path_planner import PynqPathPlanner, TOTAL_VOXELS, GRID_SIZE_X, GRID_SIZE_Y, GRID_SIZE_Z
except ImportError as e:
    print(f"[CRITICAL ERROR] Failed to import PYNQ driver layout: {e}")
    sys.exit(1)

class FpgaPathPlannerNode(Node):
    def __init__(self):
        super().__init__('fpga_path_planner_node')

        # Node Parameters
        self.declare_parameter('voxel_resolution', 0.25)  # 0.25m per voxel bin
        self.declare_parameter('bitstream_path', 'fpga/hardware/output/system.bit')
        
        self.voxel_res = self.get_parameter('voxel_resolution').value
        bitstream_path = self.get_parameter('bitstream_path').value

        # Initialize PYNQ Driver Interface (Module 3.1)
        self.get_logger().info("Initializing PYNQ FPGA Driver Interface...")
        self.driver = PynqPathPlanner(bitstream_path=bitstream_path)

        # Internal State Buffers
        self.occupancy_grid = np.zeros(TOTAL_VOXELS, dtype=np.uint8)
        self.latest_goal = None
        self.drone_pos = (2, 2, 2)  # Default current drone voxel position (x, y, z)

        # ROS 2 Subscriptions
        self.sub_cloud = self.create_subscription(
            PointCloud2,
            '/drone/pointcloud_filtered',
            self.pointcloud_callback,
            10
        )
        
        self.sub_goal = self.create_subscription(
            PoseStamped,
            '/goal_pose',
            self.goal_callback,
            10
        )

        # ROS 2 Publisher
        self.pub_path = self.create_publisher(Path, '/drone/planned_path', 10)

        self.get_logger().info("ROS 2 FPGA Acceleration Node Ready!")

    def pointcloud_callback(self, msg: PointCloud2):
        """
        Parses incoming PointCloud2 message and updates the local 3D Occupancy Grid map.
        """
        # Clear Occupancy Grid
        self.occupancy_grid.fill(0)

        # Extract X, Y, Z float coordinates from PointCloud2
        gen = point_cloud2.read_points(msg, field_names=("x", "y", "z"), skip_nans=True)
        
        points_mapped = 0
        for p in gen:
            # Map metric coordinates to discrete voxel grid indices
            vx = int(p[0] / self.voxel_res)
            vy = int(p[1] / self.voxel_res)
            vz = int(p[2] / self.voxel_res)

            if 0 <= vx < GRID_SIZE_X and 0 <= vy < GRID_SIZE_Y and 0 <= vz < GRID_SIZE_Z:
                idx = vx + (vy * GRID_SIZE_X) + (vz * GRID_SIZE_X * GRID_SIZE_Y)
                self.occupancy_grid[idx] = 1
                points_mapped += 1

        # Trigger path planning if a goal pose has been received
        if self.latest_goal is not None:
            self.execute_fpga_planning()

    def goal_callback(self, msg: PoseStamped):
        """
        Updates target destination waypoint when user selects goal in RViz or Web Dashboard.
        """
        gx = int(msg.pose.position.x / self.voxel_res)
        gy = int(msg.pose.position.y / self.voxel_res)
        gz = int(msg.pose.position.z / self.voxel_res)

        # Clamp goal within voxel boundaries
        gx = max(0, min(gx, GRID_SIZE_X - 1))
        gy = max(0, min(gy, GRID_SIZE_Y - 1))
        gz = max(0, min(gz, GRID_SIZE_Z - 1))

        self.latest_goal = (gx, gy, gz)
        self.get_logger().info(f"New Navigation Goal Received: World Target ({msg.pose.position.x:.2f}, {msg.pose.position.y:.2f}, {msg.pose.position.z:.2f}) -> Voxel {self.latest_goal}")
        
        # Immediate execution
        self.execute_fpga_planning()

    def execute_fpga_planning(self):
        """
        Invokes PYNQ FPGA driver and broadcasts resulting path message.
        """
        if self.latest_goal is None:
            return

        # Execute 3D Path Planning on FPGA
        waypoints, length, exec_time_ms = self.driver.plan_path(
            self.occupancy_grid,
            self.drone_pos,
            self.latest_goal
        )

        self.get_logger().info(f"FPGA Kernel Execution Complete: {length} Waypoints generated in {exec_time_ms:.2f} ms")

        # Construct ROS 2 nav_msgs/Path message
        path_msg = Path()
        path_msg.header = Header()
        path_msg.header.stamp = self.get_clock().now().to_msg()
        path_msg.header.frame_id = "world"

        for pt in waypoints:
            pose = PoseStamped()
            pose.header = path_msg.header
            # Convert voxel indices back to continuous world metric coordinates
            pose.pose.position.x = float(pt[0]) * self.voxel_res
            pose.pose.position.y = float(pt[1]) * self.voxel_res
            pose.pose.position.z = float(pt[2]) * self.voxel_res
            pose.pose.orientation.w = 1.0
            path_msg.poses.append(pose)

        # Publish planned trajectory to ROS 2 network
        self.pub_path.publish(path_msg)

    def destroy_node(self):
        # Cleanup PYNQ buffers upon node termination
        self.driver.free_buffers()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = FpgaPathPlannerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()