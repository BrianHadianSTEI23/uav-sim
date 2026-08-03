# ==============================================================================
# Module 2.5: Vivado Automated Block Design & Bitstream Generation
# Board Target: Xilinx Zynq UltraScale+ ZCU102 / Kria KV260
# ==============================================================================

set project_name "uav_dpu_system"
set project_dir "./vivado_prj"
set output_dir "./output"
set part_number "xczu3eg-sfvc784-1-i" ;# Zynq UltraScale+ MPSoC

# 1. Create Vivado Project
file mkdir $output_dir
create_project -force $project_name $project_dir -part $part_number

# Set IP Repository Path (Include DPUCZDX8G IP Core repository)
set_property ip_repo_paths ../hdl [current_project]
update_ip_catalog

# 2. Create Block Design
create_bd_design "design_1"

# Instantiate Zynq UltraScale+ Processing System (PS)
set zynq_ps [create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e:3.4 zynq_ultra_ps_e_0]
apply_bd_automation -rule xilinx.com:bd_rule:zynq_ultra_ps_e -config {apply_board_preset "1"} $zynq_ps

# Enable AXI High-Performance (HP) Slave ports for DPU DMA access
set_property -dict [list \
  CONFIG.PSU__USE__S_AXI_GP0 {1} \
  CONFIG.PSU__USE__S_AXI_GP1 {1} \
  CONFIG.PSU__USE__M_AXI_GP0 {1} \
] $zynq_ps

# 3. Instantiate DPUCZDX8G IP Core
set dpu_ip [create_bd_cell -type ip -vlnv xilinx.com:ip:DPUCZDX8G:4.1 DPUCZDX8G_0]

# Configure DPU Core Parameters (1 Core, B4096 Architecture)
set_property -dict [list \
  CONFIG.DPU_NUM {1} \
  CONFIG.DPU_ARCH {4096} \
  CONFIG.DPU_RAM_USAGE {low} \
] $dpu_ip

# 4. Instantiate Clocking Wizard (Generate 200MHz dpu_1x_clk and 400MHz dpu_2x_clk)
set clk_wiz [create_bd_cell -type ip -vlnv xilinx.com:ip:clk_wiz:6.0 clk_wiz_0]
set_property -dict [list \
  CONFIG.PRIMITIVE {MMCM} \
  CONFIG.CLKOUT1_USED {true} CONFIG.CLKOUT1_REQUESTED_OUT_FREQ {200.000} \
  CONFIG.CLKOUT2_USED {true} CONFIG.CLKOUT2_REQUESTED_OUT_FREQ {400.000} \
] $clk_wiz

# Connect Clocks and Resets
connect_bd_net [get_bd_pins zynq_ultra_ps_e_0/pl_clk0] [get_bd_pins clk_wiz_0/clk_in1]
connect_bd_net [get_bd_pins clk_wiz_0/clk_out1] [get_bd_pins DPUCZDX8G_0/m_axi_aclk]
connect_bd_net [get_bd_pins clk_wiz_0/clk_out2] [get_bd_pins DPUCZDX8G_0/dpu_2x_clk]

# Connect AXI Interfaces via AXI Interconnect
apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config {Master "/zynq_ultra_ps_e_0/M_AXI_GP0" intc_assign_source "auto"}  [get_bd_intf_pins DPUCZDX8G_0/S_AXI]
apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config {Slave "/zynq_ultra_ps_e_0/S_AXI_GP0" intc_assign_source "auto"}  [get_bd_intf_pins DPUCZDX8G_0/M_AXI_DATA0]

# 5. Validate and Generate Block Design Wrapper
validate_bd_design
save_bd_design

make_wrapper -files [get_files $project_dir/$project_name.srcs/sources_1/bd/design_1/design_1.bd] -top
add_files -norecurse $project_dir/$project_name.gen/sources_1/bd/design_1/hdl/design_1_wrapper.v
set_property top design_1_wrapper [current_fileset]

# 6. Run Synthesis, Implementation, and Generate Bitstream
puts "[INFO] Starting Synthesis and Implementation Pipeline..."
launch_runs synth_1 -jobs 4
wait_on_run synth_1

launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1

# 7. Export Hardware Artifacts (.bit and .hwh)
file copy -force $project_dir/$project_name.runs/impl_1/design_1_wrapper.bit $output_dir/system.bit
file copy -force $project_dir/$project_name.gen/sources_1/bd/design_1/hw_handoff/design_1.hwh $output_dir/system.hwh

puts "[SUCCESS] Hardware bitstream and HWH handoff generated at $output_dir"
exit