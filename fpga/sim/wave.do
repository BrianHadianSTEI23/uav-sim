onerror {resume}
quietly WaveActivateNextPane {} 0

add wave -noupdate -divider {System Clock & Control}
add wave -noupdate -format Logic /tb_axi_stream_cosim/clk
add wave -noupdate -format Logic /tb_axi_stream_cosim/rst_n
add wave -noupdate -format Logic /tb_axi_stream_cosim/frame_sync

add wave -noupdate -divider {AXI4-Stream Slave Input (LiDAR)}
add wave -noupdate -format Literal -radix hexadecimal /tb_axi_stream_cosim/s_axis_tdata_x
add wave -noupdate -format Literal -radix hexadecimal /tb_axi_stream_cosim/s_axis_tdata_y
add wave -noupdate -format Literal -radix hexadecimal /tb_axi_stream_cosim/s_axis_tdata_z
add wave -noupdate -format Logic /tb_axi_stream_cosim/s_axis_tvalid
add wave -noupdate -format Logic /tb_axi_stream_cosim/s_axis_tready

add wave -noupdate -divider {AXI4-Stream Master Output (Filtered)}
add wave -noupdate -format Literal -radix hexadecimal /tb_axi_stream_cosim/m_axis_tdata_x
add wave -noupdate -format Literal -radix hexadecimal /tb_axi_stream_cosim/m_axis_tdata_y
add wave -noupdate -format Literal -radix hexadecimal /tb_axi_stream_cosim/m_axis_tdata_z
add wave -noupdate -format Logic /tb_axi_stream_cosim/m_axis_tvalid
add wave -noupdate -format Logic /tb_axi_stream_cosim/m_axis_tready

add wave -noupdate -divider {Internal Occupancy Status}
add wave -noupdate -format Logic /tb_axi_stream_cosim/dut/is_occupied

TreeUpdate [SetDefaultTree]
WaveRestoreZoom {0 ns} {300 ns}