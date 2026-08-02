library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.finish;  -- <--- Add std.env package

entity tb_voxel_downsampler is
end entity tb_voxel_downsampler;

architecture sim of tb_voxel_downsampler is

  constant CLK_PERIOD : time := 10 ns; -- 100 MHz clock
  constant DATA_WIDTH : integer := 32;

  signal clk           : std_logic := '0';
  signal rst_n         : std_logic := '0';
  signal frame_sync    : std_logic := '0';

  signal s_axis_tdata_x, s_axis_tdata_y, s_axis_tdata_z : std_logic_vector(DATA_WIDTH-1 downto 0) := (others => '0');
  signal s_axis_tvalid  : std_logic := '0';
  signal s_axis_tready  : std_logic;

  signal m_axis_tdata_x, m_axis_tdata_y, m_axis_tdata_z : std_logic_vector(DATA_WIDTH-1 downto 0);
  signal m_axis_tvalid  : std_logic;
  signal m_axis_tready  : std_logic := '1';

begin

  -- Instantiate DUT
  uut: entity work.voxel_downsampler
    generic map (
      DATA_WIDTH => 32,
      SHIFT_BITS => 14,
      RAM_ADDR_BITS => 10
    )
    port map (
      clk => clk, rst_n => rst_n, frame_sync => frame_sync,
      s_axis_tdata_x => s_axis_tdata_x, s_axis_tdata_y => s_axis_tdata_y, s_axis_tdata_z => s_axis_tdata_z,
      s_axis_tvalid => s_axis_tvalid, s_axis_tready => s_axis_tready,
      m_axis_tdata_x => m_axis_tdata_x, m_axis_tdata_y => m_axis_tdata_y, m_axis_tdata_z => m_axis_tdata_z,
      m_axis_tvalid => m_axis_tvalid, m_axis_tready => m_axis_tready
    );

  -- Clock Generator
  clk <= not clk after CLK_PERIOD / 2;

  -- Stimulus Process
  stim_proc: process
  begin
    -- Reset sequence
    rst_n <= '0';
    wait for 20 ns;
    rst_n <= '1';
    wait for 10 ns;

    -- Point 1: Bin A (X=1.0, Y=2.0, Z=0.5)
    s_axis_tdata_x <= x"00010000";
    s_axis_tdata_y <= x"00020000";
    s_axis_tdata_z <= x"00008000";
    s_axis_tvalid  <= '1';
    wait for CLK_PERIOD;

    -- Point 2: Duplicate in Bin A (X=1.01, Y=2.01, Z=0.51 -> Should be DROPPED)
    s_axis_tdata_x <= x"00010050";
    s_axis_tdata_y <= x"00020050";
    s_axis_tdata_z <= x"00008050";
    s_axis_tvalid  <= '1';
    wait for CLK_PERIOD;

    -- Point 3: Bin B (X=10.0, Y=5.0, Z=1.0 -> Should PASS)
    s_axis_tdata_x <= x"000A0000";
    s_axis_tdata_y <= x"00050000";
    s_axis_tdata_z <= x"00010000";
    s_axis_tvalid  <= '1';
    wait for CLK_PERIOD;

    s_axis_tvalid <= '0';
    wait for 50 ns;

    -- Clean simulation termination (VHDL-2008 standard)
    report "Simulation Finished Successfully!";
    finish;  -- <--- Clean exit call
  end process;

end architecture sim;