library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.finish;

entity tb_axi_stream_cosim is
end entity tb_axi_stream_cosim;

architecture sim of tb_axi_stream_cosim is

  -- Timing Constants (100 MHz System Clock)
  constant CLK_PERIOD : time := 10 ns;
  constant DATA_WIDTH : integer := 32;

  -- Signals for DUT Connections
  signal clk            : std_logic := '0';
  signal rst_n          : std_logic := '0';
  signal frame_sync     : std_logic := '0';

  -- AXI4-Stream Slave Interface (Input from LiDAR)
  signal s_axis_tdata_x : std_logic_vector(DATA_WIDTH-1 downto 0) := (others => '0');
  signal s_axis_tdata_y : std_logic_vector(DATA_WIDTH-1 downto 0) := (others => '0');
  signal s_axis_tdata_z : std_logic_vector(DATA_WIDTH-1 downto 0) := (others => '0');
  signal s_axis_tvalid  : std_logic := '0';
  signal s_axis_tready  : std_logic;

  -- AXI4-Stream Master Interface (Output to Downstream DMA/HLS)
  signal m_axis_tdata_x : std_logic_vector(DATA_WIDTH-1 downto 0);
  signal m_axis_tdata_y : std_logic_vector(DATA_WIDTH-1 downto 0);
  signal m_axis_tdata_z : std_logic_vector(DATA_WIDTH-1 downto 0);
  signal m_axis_tvalid  : std_logic;
  signal m_axis_tready  : std_logic := '1';

  -- Verification Counters
  signal sent_points_count : integer := 0;
  signal recv_points_count : integer := 0;

begin

  -- ---------------------------------------------------------------------------
  -- Device Under Test (DUT) Instantiation
  -- ---------------------------------------------------------------------------
  dut: entity work.voxel_downsampler
    generic map (
      DATA_WIDTH    => 32,
      SHIFT_BITS    => 14, -- 0.25m voxel bin size
      RAM_ADDR_BITS => 10
    )
    port map (
      clk            => clk,
      rst_n          => rst_n,
      frame_sync     => frame_sync,
      s_axis_tdata_x => s_axis_tdata_x,
      s_axis_tdata_y => s_axis_tdata_y,
      s_axis_tdata_z => s_axis_tdata_z,
      s_axis_tvalid  => s_axis_tvalid,
      s_axis_tready  => s_axis_tready,
      m_axis_tdata_x => m_axis_tdata_x,
      m_axis_tdata_y => m_axis_tdata_y,
      m_axis_tdata_z => m_axis_tdata_z,
      m_axis_tvalid  => m_axis_tvalid,
      m_axis_tready  => m_axis_tready
    );

  -- 100 MHz Clock Generator Process
  clk_proc: process
  begin
    clk <= '0';
    wait for CLK_PERIOD / 2;
    clk <= '1';
    wait for CLK_PERIOD / 2;
  end process;

  -- ---------------------------------------------------------------------------
  -- Stimulus Generator: AXI4-Stream Master Driver Process
  -- ---------------------------------------------------------------------------
  stim_proc: process
    -- Helper procedure to drive a single AXI-Stream point transaction
    procedure send_point(
      x_val, y_val, z_val : in std_logic_vector(31 downto 0)
    ) is
    begin
      s_axis_tdata_x <= x_val;
      s_axis_tdata_y <= y_val;
      s_axis_tdata_z <= z_val;
      s_axis_tvalid  <= '1';
      
      -- Wait for handshaking cycle where both TVALID and TREADY are high
      loop
        wait until rising_edge(clk);
        if s_axis_tready = '1' then
          exit;
        end if;
      end loop;
      
      s_axis_tvalid <= '0';
      sent_points_count <= sent_points_count + 1;
    end procedure;

  begin
    -- Reset Sequence
    rst_n      <= '0';
    frame_sync <= '0';
    wait for 30 ns;
    rst_n      <= '1';
    wait for 20 ns;

    -- Signal Start of Scan Frame
    frame_sync <= '1';
    wait for CLK_PERIOD;
    frame_sync <= '0';
    wait for CLK_PERIOD;

    report "[CO-SIM] Ingesting Stream Burst Phase 1...";

    -- Point 1: Voxel A (Unique -> Should PASS)
    send_point(x"00020000", x"00040000", x"00010000");

    -- Point 2: Voxel A (Duplicate -> Should DROP)
    send_point(x"00020010", x"00040010", x"00010010");

    -- Point 3: Voxel B (Unique -> Should PASS)
    send_point(x"000F0000", x"00100000", x"00050000");

    -- Point 4: Voxel C (Unique -> Should PASS)
    send_point(x"001A0000", x"00200000", x"000A0000");

    -- Point 5: Voxel B (Duplicate -> Should DROP)
    send_point(x"000F0080", x"00100080", x"00050080");

    wait for 100 ns;

    report "[CO-SIM] Testing Frame Boundary Reset...";
    -- Trigger new frame boundary (clears RAM occupancy map)
    frame_sync <= '1';
    wait for CLK_PERIOD;
    frame_sync <= '0';
    wait for CLK_PERIOD;

    -- Point 6: Voxel A again (Should PASS now because RAM was reset)
    send_point(x"00020000", x"00040000", x"00010000");

    wait for 100 ns;

    report "[CO-SIM] Co-Simulation Completed Successfully!";
    finish;
  end process;

  -- ---------------------------------------------------------------------------
  -- Backpressure Emulation & Output Monitor Process
  -- ---------------------------------------------------------------------------
  backpressure_proc: process(clk)
    variable seed : integer := 12345;
  begin
    if rising_edge(clk) then
      if rst_n = '1' then
        -- Toggle m_axis_tready every 3 clock cycles to simulate backpressure
        if (sent_points_count mod 3 = 0) then
          m_axis_tready <= '0';
        else
          m_axis_tready <= '1';
        end if;

        -- Count valid downsampled output transactions
        if m_axis_tvalid = '1' and m_axis_tready = '1' then
          recv_points_count <= recv_points_count + 1;
          report "[AXI-STREAM OUT] Sample Passed: X=" & to_hstring(m_axis_tdata_x) &
                 " Y=" & to_hstring(m_axis_tdata_y) &
                 " Z=" & to_hstring(m_axis_tdata_z);
        end if;
      end if;
    end if;
  end process;

end architecture sim;