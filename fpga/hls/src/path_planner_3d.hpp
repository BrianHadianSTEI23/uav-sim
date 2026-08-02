#ifndef PATH_PLANNER_3D_HPP
#define PATH_PLANNER_3D_HPP

#include <ap_int.h>
#include <hls_math.h>

// 3D Grid Map Dimensions (32x32x32 = 32,768 voxels fits inside BRAM)
#define GRID_SIZE_X 32
#define GRID_SIZE_Y 32
#define GRID_SIZE_Z 32
#define TOTAL_VOXELS (GRID_SIZE_X * GRID_SIZE_Y * GRID_SIZE_Z)
#define MAX_PATH_NODES 128

// 3D Point Coordinate Struct
struct Point3D {
    int x;
    int y;
    int z;
};

// Top-level Kernel Function Signature
extern "C" {
void path_planner_3d(
    const ap_uint<1>* grid_map, // Input AXI4 Occupancy Grid (0=Free, 1=Occupied)
    Point3D start_node,         // Start Coordinate
    Point3D goal_node,          // Goal Coordinate
    Point3D* path_out,          // Output Waypoint Array
    int* path_length            // Total valid path count
);
}

#endif // PATH_PLANNER_3D_HPP