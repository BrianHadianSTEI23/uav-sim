#include <iostream>
#include "../src/path_planner_3d.hpp"

int main() {
    std::cout << "==========================================" << std::endl;
    std::cout << "   Starting Vitis HLS Path Planner TB     " << std::endl;
    std::cout << "==========================================" << std::endl;

    // Allocate Grid Map Buffer
    ap_uint<1> grid_map[TOTAL_VOXELS];
    for (int i = 0; i < TOTAL_VOXELS; i++) {
        grid_map[i] = 0; // Clear grid (All free space)
    }

    // Set a dummy obstacle wall in the middle
    for (int y = 0; y < GRID_SIZE_Y; y++) {
        for (int z = 0; z < GRID_SIZE_Z; z++) {
            grid_map[16 + (y * GRID_SIZE_X) + (z * GRID_SIZE_X * GRID_SIZE_Y)] = 1;
        }
    }

    Point3D start = {2, 2, 2};
    Point3D goal = {10, 10, 10};
    Point3D path_out[MAX_PATH_NODES];
    int path_length = 0;

    // Execute HLS C-Simulation Kernel
    path_planner_3d(grid_map, start, goal, path_out, &path_length);

    std::cout << "Planner Finished! Path Node Count: " << path_length << std::endl;

    if (path_length > 0) {
        std::cout << "First Waypoint: (" << path_out[0].x << ", " << path_out[0].y << ", " << path_out[0].z << ")" << std::endl;
        std::cout << "SUCCESS: 3D Path Planning C-Simulation Complete!" << std::endl;
        return 0;
    } else {
        std::cerr << "ERROR: Failed to calculate path!" << std::endl;
        return 1;
    }
}