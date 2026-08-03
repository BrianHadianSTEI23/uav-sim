#!/usr/bin/env python3
"""
Module 3.1: Low-Level PYNQ Driver for HLS 3D Path Planner IP
Handles Zero-Copy DMA Allocation, MMIO Control Registers, and Execution Handshaking.
"""

import numpy as np
import time
import os
import sys

# Standard PYNQ imports (available on Zynq MPSoC Linux image)
try:
    from pynq import Overlay, allocate
except ImportError:
    # Dummy mock fallback for x86 development/CI testing environments
    print("[WARN] 'pynq' package not detected. Using Ctypes/Numpy fallback emulator.")
    Overlay = None
    allocate = None

# Grid & Waypoint Memory Constraints matching path_planner_3d.hpp
GRID_SIZE_X = 32
GRID_SIZE_Y = 32
GRID_SIZE_Z = 32
TOTAL_VOXELS = GRID_SIZE_X * GRID_SIZE_Y * GRID_SIZE_Z  # 32,768 voxels
MAX_PATH_NODES = 128

# Register Offsets (AXI4-Lite Control Interface)
ADDR_AP_CTRL     = 0x00
ADDR_START_X     = 0x10
ADDR_START_Y     = 0x14
ADDR_START_Z     = 0x18
ADDR_GOAL_X      = 0x20
ADDR_GOAL_Y      = 0x24
ADDR_GOAL_Z      = 0x28
ADDR_GRID_MAP_DATA = 0x30
ADDR_PATH_OUT_DATA = 0x3C
ADDR_PATH_LEN_DATA = 0x48


class PynqPathPlanner:
    """
    Python driver for the HLS 3D Path Planning IP core running on Zynq MPSoC.
    """
    def __init__(self, bitstream_path: str = "../hardware/output/system.bit"):
        self.bitstream_path = bitstream_path
        
        if Overlay is not None and os.path.exists(self.bitstream_path):
            print(f"[PYNQ DRIVER] Loading FPGA Bitstream: {self.bitstream_path}...")
            self.overlay = Overlay(self.bitstream_path)
            # Access the path planner IP block (matches IP instance name in Vivado Block Design)
            self.ip = self.overlay.path_planner_3d_0
            self.hardware_accel = True
        else:
            print("[PYNQ DRIVER] Hardware Bitstream unavailable. Running in Emulated Mode.")
            self.hardware_accel = False

        # Allocate Zero-Copy Contiguous Memory Buffers via PYNQ DMA
        if self.hardware_accel and allocate is not None:
            # Input 3D Occupancy Grid (32,768 bits -> uint8 array)
            self.grid_buffer = allocate(shape=(TOTAL_VOXELS,), dtype=np.uint8)
            # Output Waypoint Buffer (128 nodes x 3 int32 coordinates [x, y, z])
            self.path_buffer = allocate(shape=(MAX_PATH_NODES, 3), dtype=np.int32)
            # Output Path Length Buffer (1 int32)
            self.len_buffer  = allocate(shape=(1,), dtype=np.int32)
        else:
            # Fallback standard NumPy arrays for software verification
            self.grid_buffer = np.zeros(TOTAL_VOXELS, dtype=np.uint8)
            self.path_buffer = np.zeros((MAX_PATH_NODES, 3), dtype=np.int32)
            self.len_buffer  = np.zeros(1, dtype=np.int32)

    def plan_path(self, occupancy_grid: np.ndarray, start: tuple, goal: tuple):
        """
        Executes hardware-accelerated 3D A* Path Planning.
        
        :param occupancy_grid: 1D flat uint8 array of size 32,768 (0=free, 1=occupied)
        :param start: Tuple (x, y, z)
        :param goal: Tuple (x, y, z)
        :return: (waypoints, path_length, execution_time_ms)
        """
        assert len(occupancy_grid) == TOTAL_VOXELS, f"Expected grid size {TOTAL_VOXELS}"

        # Copy occupancy grid into Zero-Copy Physical Memory Buffer
        np.copyto(self.grid_buffer, occupancy_grid.astype(np.uint8))

        start_time = time.perf_counter()

        if self.hardware_accel:
            # 1. Write Base Physical Memory Addresses to AXI-Lite Master Registers
            self.ip.write(ADDR_GRID_MAP_DATA, self.grid_buffer.device_address)
            self.ip.write(ADDR_PATH_OUT_DATA, self.path_buffer.device_address)
            self.ip.write(ADDR_PATH_LEN_DATA, self.len_buffer.device_address)

            # 2. Set Start and Goal Coordinates in Control Registers
            self.ip.write(ADDR_START_X, int(start[0]))
            self.ip.write(ADDR_START_Y, int(start[1]))
            self.ip.write(ADDR_START_Z, int(start[2]))

            self.ip.write(ADDR_GOAL_X, int(goal[0]))
            self.ip.write(ADDR_GOAL_Y, int(goal[1]))
            self.ip.write(ADDR_GOAL_Z, int(goal[2]))

            # 3. Start HLS Execution (Set ap_start bit = 1)
            self.ip.write(ADDR_AP_CTRL, 0x01)

            # 4. Polling ap_done bit (Bit 1 of AP_CTRL register)
            while not (self.ip.read(ADDR_AP_CTRL) & 0x02):
                pass  # Wait for FPGA kernel execution completion

            path_length = int(self.len_buffer[0])
            waypoints = self.path_buffer[:path_length].copy()
        else:
            # Software Fallback Simulation
            waypoints, path_length = self._emulate_planner(start, goal)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return waypoints, path_length, elapsed_ms

    def _emulate_planner(self, start, goal):
        """Pure Python fallback for testing driver logic without FPGA physical target."""
        path = []
        curr = list(start)
        path.append(tuple(curr))
        
        while curr != list(goal) and len(path) < MAX_PATH_NODES:
            for i in range(3):
                if curr[i] < goal[i]:
                    curr[i] += 1
                elif curr[i] > goal[i]:
                    curr[i] -= 1
            path.append(tuple(curr))
            
        return np.array(path, dtype=np.int32), len(path)

    def free_buffers(self):
        """Release contiguous CMA memory allocations."""
        if self.hardware_accel and allocate is not None:
            self.grid_buffer.freebuffer()
            self.path_buffer.freebuffer()
            self.len_buffer.freebuffer()
            print("[PYNQ DRIVER] DMA Buffers freed successfully.")