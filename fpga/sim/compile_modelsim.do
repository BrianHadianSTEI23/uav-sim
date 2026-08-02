# ==============================================================================
# ModelSim / QuestaSim Compilation Script for AXI4-Stream Co-Simulation
# ==============================================================================

# 1. Create Working Library
vlib work
vmap work work

# 2. Compile VHDL 2008 Source Files
vcom -2008 -work work ../hdl/voxel_downsampler.vhd
vcom -2008 -work work ../tb/tb_axi_stream_cosim.vhd

# 3. Load Simulation Top Entity
vsim -t 1ns -voptargs="+acc" work.tb_axi_stream_cosim

# 4. Load Waveform Configuration
do wave.do

# 5. Run Simulation
run -all