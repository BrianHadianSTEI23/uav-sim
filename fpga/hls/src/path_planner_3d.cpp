#include "path_planner_3d.hpp"

// Linear index conversion for 3D array mapping
inline int get_index(int x, int y, int z) {
    #pragma HLS INLINE
    return x + (y * GRID_SIZE_X) + (z * GRID_SIZE_X * GRID_SIZE_Y);
}

// Manhattan 3D Distance Heuristic
inline int calculate_heuristic(Point3D a, Point3D b) {
    #pragma HLS INLINE
    return hls::abs(a.x - b.x) + hls::abs(a.y - b.y) + hls::abs(a.z - b.z);
}

extern "C" {
void path_planner_3d(
    const ap_uint<1>* grid_map,
    Point3D start_node,
    Point3D goal_node,
    Point3D* path_out,
    int* path_length
) {
    // -------------------------------------------------------------------------
    // HLS Interface Pragmas (AXI4-Lite for controls, AXI4-Master for Memory)
    // -------------------------------------------------------------------------
    #pragma HLS INTERFACE m_axi port=grid_map offset=slave bundle=gmem0 depth=32768
    #pragma HLS INTERFACE m_axi port=path_out  offset=slave bundle=gmem1 depth=128
    #pragma HLS INTERFACE m_axi port=path_length offset=slave bundle=gmem1 depth=1

    #pragma HLS INTERFACE s_axilite port=start_node bundle=control
    #pragma HLS INTERFACE s_axilite port=goal_node  bundle=control
    #pragma HLS INTERFACE s_axilite port=return     bundle=control

    // Local BRAM Buffers for Fast Parallel On-Chip Access
    ap_uint<1> local_grid[TOTAL_VOXELS];
    #pragma HLS ARRAY_PARTITION variable=local_grid cyclic factor=8 dim=1

    int g_score[TOTAL_VOXELS];
    #pragma HLS ARRAY_PARTITION variable=g_score cyclic factor=8 dim=1

    int parent_index[TOTAL_VOXELS];

    // Burst Read Occupancy Grid Map from Global Memory to Local BRAM
    LOAD_GRID: for (int i = 0; i < TOTAL_VOXELS; i++) {
        #pragma HLS PIPELINE II=1
        local_grid[i] = grid_map[i];
        g_score[i] = 1000000; // Initialize with infinity
        parent_index[i] = -1;
    }

    int start_idx = get_index(start_node.x, start_node.y, start_node.z);
    int goal_idx  = get_index(goal_node.x, goal_node.y, goal_node.z);

    g_score[start_idx] = 0;

    // Standard 3D Search Loop
    Point3D current = start_node;
    int current_idx = start_idx;
    bool goal_reached = false;

    SEARCH_LOOP: for (int iter = 0; iter < MAX_PATH_NODES; iter++) {
        #pragma HLS LOOP_TRIPCOUNT min=1 max=128
        
        if (current.x == goal_node.x && current.y == goal_node.y && current.z == goal_node.z) {
            goal_reached = true;
            break;
        }

        // Evaluate 26-Neighborhood
        NEIGHBOR_Z: for (int dz = -1; dz <= 1; dz++) {
            NEIGHBOR_Y: for (int dy = -1; dy <= 1; dy++) {
                NEIGHBOR_X: for (int dx = -1; dx <= 1; dx++) {
                    #pragma HLS PIPELINE II=1
                    #pragma HLS UNROLL factor=2

                    if (dx == 0 && dy == 0 && dz == 0) continue;

                    int nx = current.x + dx;
                    int ny = current.y + dy;
                    int nz = current.z + dz;

                    // Bounds Check
                    if (nx >= 0 && nx < GRID_SIZE_X &&
                        ny >= 0 && ny < GRID_SIZE_Y &&
                        nz >= 0 && nz < GRID_SIZE_Z) {

                        int n_idx = get_index(nx, ny, nz);

                        // Check collision
                        if (local_grid[n_idx] == 0) { // Free voxel
                            int new_g = g_score[current_idx] + 1;
                            if (new_g < g_score[n_idx]) {
                                g_score[n_idx] = new_g;
                                parent_index[n_idx] = current_idx;
                            }
                        }
                    }
                }
            }
        }

        // Advance dummy path stepping towards goal (simplified spatial step for demonstration)
        if (current.x < goal_node.x) current.x++;
        else if (current.x > goal_node.x) current.x--;
        if (current.y < goal_node.y) current.y++;
        else if (current.y > goal_node.y) current.y--;
        if (current.z < goal_node.z) current.z++;
        else if (current.z > goal_node.z) current.z--;

        current_idx = get_index(current.x, current.y, current.z);
    }

    // Write back generated path
    int length = 0;
    Point3D trace = goal_node;

    WRITE_PATH: for (int p = 0; p < MAX_PATH_NODES; p++) {
        #pragma HLS PIPELINE II=1
        if (length >= MAX_PATH_NODES) break;

        path_out[length] = trace;
        length++;

        if (trace.x == start_node.x && trace.y == start_node.y && trace.z == start_node.z) break;

        // Trace backwards step
        if (trace.x > start_node.x) trace.x--;
        if (trace.y > start_node.y) trace.y--;
        if (trace.z > start_node.z) trace.z--;
    }

    *path_length = length;
}
}