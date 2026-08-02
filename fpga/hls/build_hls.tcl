open_project -reset prj_path_planner

set_top path_planner_3d

add_files src/path_planner_3d.cpp
add_files src/path_planner_3d.hpp
add_files -tb tb/tb_path_planner.cpp

# Target AMD/Xilinx Zynq UltraScale+ XCZU3EG / MPSoC
open_solution -reset "solution1"
set_part {xczu3eg-sfvc784-1-i}
create_clock -period 10 -name default

# Perform C-Simulation
csim_design

# Perform C-Synthesis
csynth_design

exit