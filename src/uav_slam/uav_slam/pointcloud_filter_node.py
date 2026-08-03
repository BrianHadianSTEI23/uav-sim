#!/usr/bin/env python3
"""
Module 4.1: PointCloud Filter & Voxel Downsampling Node
Pre-filters raw 3D LiDAR point clouds before feed into OctoMap and Module 3.2 FPGA Node.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header


class PointCloudFilterNode(Node):
    def __init__(self):
        super().__init__('pointcloud_filter_node')

        self.sub_raw = self.create_subscription(
            PointCloud2,
            '/drone/pointcloud_raw',
            self.cloud_callback,
            10
        )

        self.pub_filtered = self.create_publisher(
            PointCloud2,
            '/drone/pointcloud_filtered',
            10
        )

        self.get_logger().info("PointCloud Pre-filtering Node Online.")

    def cloud_callback(self, msg: PointCloud2):
        """
        Filters NaNs and formats point cloud for downstream processing.
        """
        points = []
        gen = point_cloud2.read_points(msg, field_names=("x", "y", "z"), skip_nans=True)
        
        for p in gen:
            # Range filter: Filter out noise points within 0.3m of drone body
            dist_sq = p[0]**2 + p[1]**2 + p[2]**2
            if dist_sq > 0.09:
                points.append(p)

        # Reconstruct filtered PointCloud2 message
        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = msg.header.frame_id if msg.header.frame_id else "world"

        filtered_msg = point_cloud2.create_cloud_xyz32(header, points)
        self.pub_filtered.publish(filtered_msg)


def main(args=None):
    rclpy.init(args=args)
    node = PointCloudFilterNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()