`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////
// AD9767 DAC Sine Wave Output
// Board: ALINX AX7010 (XC7Z010CLG400-1)
//
// Flow: FPGA (Sine ROM) -> AD9767 DAC (J10) -> Analog Output
//       -> Analog Discovery 2 CH2 -> WaveForms Oscilloscope
//
// Clock: Single MMCM (clk_wiz_0) from 50 MHz -> 65 MHz DAC clock
//////////////////////////////////////////////////////////////////////////////
module dac_output_top(
    input               sys_clk,        // 50 MHz system clock (U18)
    input               rst_n,          // Active-low reset (N15)

    // AD9767 DAC Channel 1 (AN9767 on J10)
    output              da1_clk,
    output              da1_wrt,
    output [13:0]       da1_data,

    // AD9767 DAC Channel 2 (AN9767 on J10)
    output              da2_clk,
    output              da2_wrt,
    output [13:0]       da2_data
);

// =========================================================================
// Internal wires
// =========================================================================
wire            dac_clk;            // ~65 MHz DAC clock
wire            pll_locked;
wire            sys_rst = ~rst_n | ~pll_locked;

// DAC output data
wire [13:0]     sine_data;

// =========================================================================
// Clock Generation - clk_wiz_0 (MMCM)
// 50 MHz -> 65 MHz DAC clock
// =========================================================================
clk_wiz_0 clk_wiz_inst (
    .clk_in1    (sys_clk),
    .clk_out1   (dac_clk),         // ~65 MHz
    .reset      (~rst_n),
    .locked     (pll_locked)
);

// =========================================================================
// DAC Clock and Write assignments
// Both channels output the same sine wave
// =========================================================================
assign da1_clk  = dac_clk;
assign da1_wrt  = dac_clk;
assign da1_data = sine_data;

assign da2_clk  = dac_clk;
assign da2_wrt  = dac_clk;
assign da2_data = sine_data;

// =========================================================================
// Sine Wave Generator
// ROM-based, 1024 samples x 14-bit from sin1024.mem
// =========================================================================
sine_gen sine_gen_inst (
    .clk        (dac_clk),
    .rst        (sys_rst),
    .dac_data   (sine_data)
);

endmodule

// =========================================================================
// Sine Wave Generator Module
// 1024-sample 14-bit ROM loaded from sin1024.mem
// Address step = 1 -> f_out = 65 MHz / 1024 = ~63.5 kHz
// =========================================================================
module sine_gen(
    input               clk,
    input               rst,
    output reg [13:0]   dac_data
);

// Sine wave ROM: 1024 entries x 14 bits
reg [13:0] sin_rom [0:1023];
initial $readmemh("sin1024.mem", sin_rom);

// Address counter
reg [9:0] rom_addr;

always @(posedge clk or posedge rst) begin
    if (rst) begin
        rom_addr <= 10'd0;
        dac_data <= 14'h2000;
    end else begin
        rom_addr <= rom_addr + 10'd1;
        dac_data <= sin_rom[rom_addr];
    end
end

endmodule
