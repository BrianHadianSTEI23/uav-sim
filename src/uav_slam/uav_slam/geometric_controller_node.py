#!/usr/bin/env python3
"""
Module 4.2: Geometric Flight Controller Node (SE3 Nonlinear Tracking)
Translates FPGA 3D Path Waypoints + Odometry -> Smooth Body Rate & Thrust Commands (cmd_vel).
"""

import rclpy
from rclpy.node import Node
import numpy as np
import math

from nav_msgs.msg import Path, Odometry
from geometry_msgs.msg import Twist, PoseStamped
from uav_slam.trajectory_generator import TrajectoryGenerator


class GeometricControllerNode(Node):
    def __init__(self):
        super().__init__('geometric_controller_node')

        # Load Gains & Physical Parameters
        self.declare_parameter('mass', 1.5)
        self.declare_parameter('gravity', 9.81)
        self.declare_parameter('max_thrust', 30.0)
        self.declare_parameter('max_tilt_deg', 35.0)
        self.declare_parameter('max_velocity', 3.0)
        self.declare_parameter('kp_x', 6.0)
        self.declare_parameter('kp_y', 6.0)
        self.declare_parameter('kp_z', 8.0)
        self.declare_parameter('kd_x', 3.5)
        self.declare_parameter('kd_y', 3.5)
        self.declare_parameter('kd_z', 4.5)
        self.declare_parameter('kp_yaw', 2.5)

        self.m = self.get_parameter('mass').value
        self.g = self.get_parameter('gravity').value
        self.max_thrust = self.get_parameter('max_thrust').value
        self.max_tilt = math.radians(self.get_parameter('max_tilt_deg').value)
        self.max_vel = self.get_parameter('max_velocity').value

        self.Kp = np.array([
            self.get_parameter('kp_x').value,
            self.get_parameter('kp_y').value,
            self.get_parameter('kp_z').value
        ])
        self.Kd = np.array([
            self.get_parameter('kd_x').value,
            self.get_parameter('kd_y').value,
            self.get_parameter('kd_z').value
        ])
        self.kp_yaw = self.get_parameter('kp_yaw').value

        # Trajectory Generator Instance
        self.traj_gen = TrajectoryGenerator(cruise_velocity=self.max_vel)

        # State Variables
        self.current_pos = np.zeros(3)
        self.current_vel = np.zeros(3)
        self.current_yaw = 0.0
        self.active_path = []

        # ROS 2 Subscriptions
        self.sub_odom = self.create_subscription(
            Odometry,
            '/drone/odometry',
            self.odom_callback,
            10
        )
        self.sub_path = self.create_subscription(
            Path,
            '/drone/planned_path',
            self.path_callback,
            10
        )

        # ROS 2 Publisher
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 10)

        # Control Loop Timer (50 Hz / 20 ms update loop)
        self.timer = self.create_timer(0.02, self.control_loop)

        self.get_logger().info("Geometric SE(3) Flight Controller Online (50 Hz).")

    def odom_callback(self, msg: Odometry):
        """Extracts current 3D position, velocity, and orientation from Odometry."""
        self.current_pos = np.array([
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            msg.pose.pose.position.z
        ])
        self.current_vel = np.array([
            msg.twist.twist.linear.x,
            msg.twist.twist.linear.y,
            msg.twist.twist.linear.z
        ])

        # Quaternion to Yaw angle
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.current_yaw = math.atan2(siny_cosp, cosy_cosp)

    def path_callback(self, msg: Path):
        """Stores new incoming planned path waypoints."""
        self.active_path = msg.poses
        if len(self.active_path) > 0:
            self.get_logger().info(f"Controller received new trajectory with {len(self.active_path)} waypoints.")

    def control_loop(self):
        """
        Executes SE(3) Geometric Control Law at 50 Hz.
        Calculates position/velocity tracking errors -> desired thrust vector -> body commands.
        """
        if not self.active_path:
            # Maintain hover in place
            cmd = Twist()
            cmd.linear.x = 0.0
            cmd.linear.y = 0.0
            cmd.linear.z = 0.0
            self.pub_cmd_vel.publish(cmd)
            return

        # Pop reached waypoints
        while len(self.active_path) > 1:
            wp_pos = np.array([
                self.active_path[0].pose.position.x,
                self.active_path[0].pose.position.y,
                self.active_path[0].pose.position.z
            ])
            if np.linalg.norm(wp_pos - self.current_pos) < 0.25:
                self.active_path.pop(0)
            else:
                break

        # Generate target reference state from Trajectory Generator
        pos_des, vel_des, acc_des = self.traj_gen.generate_smooth_target(
            self.current_pos, self.active_path, dt=0.02
        )

        # 1. Compute Position and Velocity Errors
        ep = self.current_pos - pos_des
        ev = self.current_vel - vel_des

        # 2. SE(3) Desired Acceleration Force Vector: F_des = -Kp*e_p - Kd*e_v + m*g*e3 + m*a_des
        e3 = np.array([0.0, 0.0, 1.0])
        F_des = -self.Kp * ep - self.Kd * ev + self.m * self.g * e3 + self.m * acc_des

        # 3. Project Desired Force to Body Velocity Commands
        # Linear velocity outputs in world-frame relative coordinates
        vx_cmd = np.clip(vel_des[0] - (self.Kp[0] / 3.0) * ep[0], -self.max_vel, self.max_vel)
        vy_cmd = np.clip(vel_des[1] - (self.Kp[1] / 3.0) * ep[1], -self.max_vel, self.max_vel)
        vz_cmd = np.clip(vel_des[2] - (self.Kp[2] / 3.0) * ep[2], -self.max_vel, self.max_vel)

        # Yaw rate command
        desired_yaw = math.atan2(vel_des[1], vel_des[0]) if np.linalg.norm(vel_des[:2]) > 0.1 else self.current_yaw
        yaw_err = math.atan2(math.sin(desired_yaw - self.current_yaw), math.cos(desired_yaw - self.current_yaw))
        wz_cmd = self.kp_yaw * yaw_err

        # Construct Twist Command
        cmd = Twist()
        cmd.linear.x = float(vx_cmd)
        cmd.linear.y = float(vy_cmd)
        cmd.linear.z = float(vz_cmd)
        cmd.angular.z = float(wz_cmd)

        self.pub_cmd_vel.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = GeometricControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()