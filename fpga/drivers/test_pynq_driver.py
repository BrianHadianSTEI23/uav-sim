#!/usr/bin/env python3
"""
Integration test script for PynqPathPlanner driver.
"""

import numpy as np
from pynq_path_planner import PynqPathPlanner, TOTAL_VOXELS

def main():
    print("=======================================================")
    print("       Testing Module 3.1: PYNQ Driver & DMA           ")
    print("=======================================================")

    # Initialize PYNQ Driver
    driver = PynqPathPlanner()

    # Create dummy occupancy map (all free space)
    occupancy_grid = np.zeros(TOTAL_VOXELS, dtype=np.uint8)

    # Insert a simulated obstacle block
    # Occupy voxel block at x=15
    for y in range(32):
        for z in range(32):
            idx = 15 + (y * 32) + (z * 32 * 32)
            occupancy_grid[idx] = 1

    start_pt = (2, 2, 2)
    goal_pt  = (28, 28, 28)

    print(f"[TEST] Planning path from {start_pt} to {goal_pt}...")
    waypoints, length, exec_time = driver.plan_path(occupancy_grid, start_pt, goal_pt)

    print(f"[RESULT] Waypoints Calculated : {length}")
    print(f"[RESULT] Driver Execution Time: {exec_time:.3f} ms")
    if length > 0:
        print(f"[RESULT] First Waypoint: {waypoints[0]}")
        print(f"[RESULT] Last Waypoint : {waypoints[-1]}")
        print("[SUCCESS] Module 3.1 PYNQ Driver Integration Test PASSED!")
    else:
        print("[ERROR] Path planning failed!")

    driver.free_buffers()

if __name__ == "__main__":
    main()