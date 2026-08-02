library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity voxel_downsampler is
  generic (
    DATA_WIDTH : integer := 32; -- Q16.16 Fixed point format
    SHIFT_BITS : integer := 14; -- Voxel Resolution Shift (e.g., 2^14 = 0.25m bin)
    RAM_ADDR_BITS : integer := 10 -- 1024-entry hash occupancy table
  );
  port (
    clk           : in  std_logic;
    rst_n         : in  std_logic;
    
    -- Sync signal to clear occupancy map at frame boundaries
    frame_sync    : in  std_logic;

    -- Incoming AXI4-Stream Point Channel
    s_axis_tdata_x : in  std_logic_vector(DATA_WIDTH-1 downto 0);
    s_axis_tdata_y : in  std_logic_vector(DATA_WIDTH-1 downto 0);
    s_axis_tdata_z : in  std_logic_vector(DATA_WIDTH-1 downto 0);
    s_axis_tvalid  : in  std_logic;
    s_axis_tready  : out std_logic;

    -- Downsampled Outgoing AXI4-Stream Point Channel
    m_axis_tdata_x : out std_logic_vector(DATA_WIDTH-1 downto 0);
    m_axis_tdata_y : out std_logic_vector(DATA_WIDTH-1 downto 0);
    m_axis_tdata_z : out std_logic_vector(DATA_WIDTH-1 downto 0);
    m_axis_tvalid  : out std_logic;
    m_axis_tready  : in  std_logic
  );
end entity voxel_downsampler;

architecture rtl of voxel_downsampler is

  -- Occupancy Table RAM Signals
  type ram_type is array (0 to (2**RAM_ADDR_BITS)-1) of std_logic;
  signal occupancy_ram : ram_type := (others => '0');

  -- Pipeline Registers
  signal voxel_hash   : unsigned(RAM_ADDR_BITS-1 downto 0);
  signal x_reg, y_reg, z_reg : std_logic_vector(DATA_WIDTH-1 downto 0);
  signal valid_reg    : std_logic;
  signal is_occupied  : std_logic;

begin

  -- Pass-through ready handshake
  s_axis_tready <= m_axis_tready;

  -- Pipeline Stage 1: Spatial Hash Calculation & Occupancy Check
  process(clk, rst_n)
    variable bin_x, bin_y, bin_z : unsigned(RAM_ADDR_BITS-1 downto 0);
    variable combined_hash      : unsigned(RAM_ADDR_BITS-1 downto 0);
    
    -- Intermediate slices to enforce valid VHDL type conversion rules
    variable slice_x, slice_y, slice_z : std_logic_vector(RAM_ADDR_BITS-1 downto 0);
  begin
    if rst_n = '0' then
      x_reg        <= (others => '0');
      y_reg        <= (others => '0');
      z_reg        <= (others => '0');
      valid_reg    <= '0';
      voxel_hash   <= (others => '0');
      is_occupied  <= '0';
      occupancy_ram <= (others => '0');
    elsif rising_edge(clk) then
      
      -- Clear occupancy RAM on frame boundary sync
      if frame_sync = '1' then
        occupancy_ram <= (others => '0');
      end if;

      if (s_axis_tvalid = '1' and m_axis_tready = '1') then
        
        -- 1. Slice bit vectors first
        slice_x := s_axis_tdata_x(SHIFT_BITS + RAM_ADDR_BITS - 1 downto SHIFT_BITS);
        slice_y := s_axis_tdata_y(SHIFT_BITS + RAM_ADDR_BITS - 1 downto SHIFT_BITS);
        slice_z := s_axis_tdata_z(SHIFT_BITS + RAM_ADDR_BITS - 1 downto SHIFT_BITS);

        -- 2. Convert cleanly without illegal chained operations
        bin_x := unsigned(slice_x);
        bin_y := unsigned(slice_y);
        bin_z := unsigned(slice_z);

        -- XOR Spatial Hashing function for 3D grid address
        combined_hash := bin_x xor bin_y xor bin_z;
        voxel_hash    <= combined_hash;

        -- Register incoming point coordinate data
        x_reg <= s_axis_tdata_x;
        y_reg <= s_axis_tdata_y;
        z_reg <= s_axis_tdata_z;

        -- Check occupancy RAM status
        if occupancy_ram(to_integer(combined_hash)) = '1' then
          is_occupied <= '1'; -- Point falls in an occupied bin -> Drop
          valid_reg   <= '0';
        else
          is_occupied <= '0'; -- First point in bin -> Pass through & set bit
          valid_reg   <= '1';
          occupancy_ram(to_integer(combined_hash)) <= '1';
        end if;
      else
        valid_reg <= '0';
      end if;
    end if;
  end process;

  -- Pipeline Stage 2: Streaming Outputs
  m_axis_tdata_x <= x_reg;
  m_axis_tdata_y <= y_reg;
  m_axis_tdata_z <= z_reg;
  m_axis_tvalid  <= valid_reg;

end architecture rtl;