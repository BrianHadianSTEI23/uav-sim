#!/usr/bin/env python3
"""
Module 4.2: Minimum-Jerk Trajectory Generator
Interpolates discrete 3D waypoints into smooth continuous time-stamped trajectory targets.
"""

import numpy as np

class TrajectoryGenerator:
    def __init__(self, cruise_velocity: float = 1.5):
        self.cruise_velocity = cruise_velocity

    def generate_smooth_target(self, current_pos: np.ndarray, path_waypoints: list, dt: float = 0.02):
        """
        Takes a list of discrete geometry_msgs/PoseStamped waypoints and computes
        the immediate desired target position, velocity, and acceleration vectors.
        """
        if not path_waypoints:
            return current_pos, np.zeros(3), np.zeros(3)

        # Target next immediate waypoint in path sequence
        target_wp = np.array([
            path_waypoints[0].pose.position.x,
            path_waypoints[0].pose.position.y,
            path_waypoints[0].pose.position.z
        ])

        direction = target_wp - current_pos
        dist = np.linalg.norm(direction)

        if dist < 0.05:
            # Reached waypoint
            return target_wp, np.zeros(3), np.zeros(3)

        unit_dir = direction / dist
        desired_speed = min(self.cruise_velocity, dist / dt)
        
        # Desired state
        pos_des = current_pos + unit_dir * desired_speed * dt
        vel_des = unit_dir * desired_speed
        acc_des = np.zeros(3)  # First-order feedforward

        return pos_des, vel_des, acc_des