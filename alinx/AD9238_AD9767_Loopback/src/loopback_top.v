`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////
// AD9767 -> AD9238 Loopback Test with HDMI Waveform Display
// Board: ALINX AX7010 (XC7Z010CLG400-1)
//
// Flow: FPGA -> AD9767 DAC (J10) -> Analog -> AD9238 ADC (J11) -> FPGA -> HDMI
//
// Clock: Single MMCM (clk_wiz_0) generates all clocks from 50 MHz input:
//   clk_out1: ~74.25 MHz  (pixel clock for 720p HDMI)
//   clk_out2: ~371.25 MHz (5x serial clock for TMDS)
//   clk_out3: ~65 MHz     (ADC/DAC shared clock)
//////////////////////////////////////////////////////////////////////////////
module loopback_top(
    input                       sys_clk,            // 50 MHz system clock (U18)
    input                       rst_n,              // Active-low reset (N15)

    // AD9238 ADC interface (AN9238 module on J11)
    output                      ad9238_clk_ch0,     // ADC channel 0 clock
    output                      ad9238_clk_ch1,     // ADC channel 1 clock
    input  [11:0]               ad9238_data_ch0,    // ADC channel 0 data (12-bit)
    input  [11:0]               ad9238_data_ch1,    // ADC channel 1 data (12-bit)

    // AD9767 DAC interface (AN9767 module on J10)
    output                      da1_clk,            // DAC channel 1 clock
    output                      da1_wrt,            // DAC channel 1 write
    output [13:0]               da1_data,           // DAC channel 1 data (14-bit)
    output                      da2_clk,            // DAC channel 2 clock
    output                      da2_wrt,            // DAC channel 2 write
    output [13:0]               da2_data,           // DAC channel 2 data (14-bit)

    // HDMI output
    output                      TMDS_clk_p,
    output                      TMDS_clk_n,
    output [2:0]                TMDS_data_p,
    output [2:0]                TMDS_data_n,
    output                      hdmi_oen
);

// =========================================================================
// Internal wires
// =========================================================================
wire            video_clk;          // ~74.25 MHz pixel clock
wire            video_clk5x;        // ~371.25 MHz TMDS serial clock
wire            adc_dac_clk;        // ~65 MHz shared ADC/DAC clock
wire            pll_locked;
wire            sys_rst = ~rst_n | ~pll_locked;

// Video pipeline wires
wire            vid_hs, vid_vs, vid_de;
wire [7:0]      vid_r, vid_g, vid_b;

wire            grid_hs, grid_vs, grid_de;
wire [7:0]      grid_r, grid_g, grid_b;

wire            wave0_hs, wave0_vs, wave0_de;
wire [7:0]      wave0_r, wave0_g, wave0_b;

wire            wave1_hs, wave1_vs, wave1_de;
wire [7:0]      wave1_r, wave1_g, wave1_b;

// ADC sample buffer wires
wire            adc0_buf_wr;
wire [10:0]     adc0_buf_addr;
wire [7:0]      adc0_buf_data;

wire            adc1_buf_wr;
wire [10:0]     adc1_buf_addr;
wire [7:0]      adc1_buf_data;

// DAC output data
wire [13:0]     dac_data;

// =========================================================================
// Clock assignments
// =========================================================================
assign ad9238_clk_ch0 = adc_dac_clk;
assign ad9238_clk_ch1 = adc_dac_clk;

// DAC clock and write = shared clock (data latched on rising edge)
assign da1_clk  = adc_dac_clk;
assign da1_wrt  = adc_dac_clk;
assign da1_data = dac_data;

assign da2_clk  = adc_dac_clk;
assign da2_wrt  = adc_dac_clk;
assign da2_data = dac_data;

// =========================================================================
// Clock Generation - clk_wiz_0 (MMCM)
// 50 MHz -> 74.25 MHz (pixel), 371.25 MHz (5x serial), 65 MHz (ADC/DAC)
// =========================================================================
clk_wiz_0 clk_wiz_inst (
    .clk_in1    (sys_clk),
    .clk_out1   (video_clk),           // ~74.25 MHz
    .clk_out2   (video_clk5x),         // ~371.25 MHz
    .clk_out3   (adc_dac_clk),         // ~65 MHz
    .reset      (~rst_n),
    .locked     (pll_locked)
);

// =========================================================================
// HDMI Output - Pure Verilog TMDS transmitter
// =========================================================================
hdmi_tx hdmi_inst (
    .pixel_clk      (video_clk),
    .serial_clk     (video_clk5x),
    .rst            (sys_rst),
    .vid_r          (wave1_r),
    .vid_g          (wave1_g),
    .vid_b          (wave1_b),
    .vid_de         (wave1_de),
    .vid_hsync      (wave1_hs),
    .vid_vsync      (wave1_vs),
    .TMDS_clk_p     (TMDS_clk_p),
    .TMDS_clk_n     (TMDS_clk_n),
    .TMDS_data_p    (TMDS_data_p),
    .TMDS_data_n    (TMDS_data_n),
    .hdmi_oen       (hdmi_oen)
);

// =========================================================================
// Video Timing Generator (1280x720 @ 74.25 MHz)
// =========================================================================
video_timing_720p video_timing_inst (
    .clk    (video_clk),
    .rst    (sys_rst),
    .hs     (vid_hs),
    .vs     (vid_vs),
    .de     (vid_de),
    .rgb_r  (vid_r),
    .rgb_g  (vid_g),
    .rgb_b  (vid_b)
);

// =========================================================================
// Grid Display Overlay (oscilloscope grid)
// =========================================================================
grid_overlay grid_inst (
    .rst_n      (~sys_rst),
    .pclk       (video_clk),
    .i_hs       (vid_hs),
    .i_vs       (vid_vs),
    .i_de       (vid_de),
    .i_data     ({vid_r, vid_g, vid_b}),
    .o_hs       (grid_hs),
    .o_vs       (grid_vs),
    .o_de       (grid_de),
    .o_data     ({grid_r, grid_g, grid_b})
);

// =========================================================================
// ADC Sampling - Channel 0 (loopback from DAC)
// =========================================================================
adc_sampler adc_sample_ch0 (
    .adc_clk        (adc_dac_clk),
    .rst            (sys_rst),
    .adc_data       (ad9238_data_ch0),
    .adc_buf_wr     (adc0_buf_wr),
    .adc_buf_addr   (adc0_buf_addr),
    .adc_buf_data   (adc0_buf_data)
);

// =========================================================================
// ADC Sampling - Channel 1
// =========================================================================
adc_sampler adc_sample_ch1 (
    .adc_clk        (adc_dac_clk),
    .rst            (sys_rst),
    .adc_data       (ad9238_data_ch1),
    .adc_buf_wr     (adc1_buf_wr),
    .adc_buf_addr   (adc1_buf_addr),
    .adc_buf_data   (adc1_buf_data)
);

// =========================================================================
// Waveform Display - Channel 0 (Green - loopback signal)
// =========================================================================
waveform_display wav_display_ch0 (
    .rst_n          (~sys_rst),
    .pclk           (video_clk),
    .wave_color     (24'h00FF00),       // Green for loopback channel
    .adc_clk        (adc_dac_clk),
    .adc_buf_wr     (adc0_buf_wr),
    .adc_buf_addr   (adc0_buf_addr),
    .adc_buf_data   (adc0_buf_data),
    .i_hs           (grid_hs),
    .i_vs           (grid_vs),
    .i_de           (grid_de),
    .i_data         ({grid_r, grid_g, grid_b}),
    .o_hs           (wave0_hs),
    .o_vs           (wave0_vs),
    .o_de           (wave0_de),
    .o_data         ({wave0_r, wave0_g, wave0_b})
);

// =========================================================================
// Waveform Display - Channel 1 (Blue)
// =========================================================================
waveform_display wav_display_ch1 (
    .rst_n          (~sys_rst),
    .pclk           (video_clk),
    .wave_color     (24'h0080FF),       // Light blue for CH1
    .adc_clk        (adc_dac_clk),
    .adc_buf_wr     (adc1_buf_wr),
    .adc_buf_addr   (adc1_buf_addr),
    .adc_buf_data   (adc1_buf_data),
    .i_hs           (wave0_hs),
    .i_vs           (wave0_vs),
    .i_de           (wave0_de),
    .i_data         ({wave0_r, wave0_g, wave0_b}),
    .o_hs           (wave1_hs),
    .o_vs           (wave1_vs),
    .o_de           (wave1_de),
    .o_data         ({wave1_r, wave1_g, wave1_b})
);

// =========================================================================
// DAC Square Wave Generator
// Generates test signal for loopback: FPGA -> DAC -> ADC -> HDMI
// =========================================================================
dac_square_gen dac_gen_inst (
    .clk            (adc_dac_clk),
    .rst            (sys_rst),
    .dac_data       (dac_data)
);

endmodule

// =========================================================================
// Video Timing Generator - 1280x720p @ 74.25 MHz
// Dark background (oscilloscope style)
// =========================================================================
module video_timing_720p(
    input               clk,
    input               rst,
    output              hs,
    output              vs,
    output              de,
    output [7:0]        rgb_r,
    output [7:0]        rgb_g,
    output [7:0]        rgb_b
);

// 1280x720 timing parameters
localparam H_ACTIVE = 16'd1280;
localparam H_FP     = 16'd110;
localparam H_SYNC   = 16'd40;
localparam H_BP     = 16'd220;
localparam V_ACTIVE = 16'd720;
localparam V_FP     = 16'd5;
localparam V_SYNC   = 16'd5;
localparam V_BP     = 16'd20;
localparam H_TOTAL  = H_ACTIVE + H_FP + H_SYNC + H_BP;
localparam V_TOTAL  = V_ACTIVE + V_FP + V_SYNC + V_BP;

reg         hs_reg, vs_reg;
reg         hs_reg_d0, vs_reg_d0;
reg [11:0]  h_cnt, v_cnt;
reg         h_active, v_active;
reg         video_active_d0;
reg [7:0]   rgb_r_reg, rgb_g_reg, rgb_b_reg;

wire video_active = h_active & v_active;

assign hs    = hs_reg_d0;
assign vs    = vs_reg_d0;
assign de    = video_active_d0;
assign rgb_r = rgb_r_reg;
assign rgb_g = rgb_g_reg;
assign rgb_b = rgb_b_reg;

// Delay registers
always @(posedge clk or posedge rst) begin
    if (rst) begin
        hs_reg_d0       <= 1'b0;
        vs_reg_d0       <= 1'b0;
        video_active_d0 <= 1'b0;
    end else begin
        hs_reg_d0       <= hs_reg;
        vs_reg_d0       <= vs_reg;
        video_active_d0 <= video_active;
    end
end

// Horizontal counter
always @(posedge clk or posedge rst) begin
    if (rst)
        h_cnt <= 12'd0;
    else if (h_cnt == H_TOTAL - 1)
        h_cnt <= 12'd0;
    else
        h_cnt <= h_cnt + 12'd1;
end

// Vertical counter
always @(posedge clk or posedge rst) begin
    if (rst)
        v_cnt <= 12'd0;
    else if (h_cnt == H_FP - 1)
        if (v_cnt == V_TOTAL - 1)
            v_cnt <= 12'd0;
        else
            v_cnt <= v_cnt + 12'd1;
end

// Horizontal sync
always @(posedge clk or posedge rst) begin
    if (rst)
        hs_reg <= 1'b0;
    else if (h_cnt == H_FP - 1)
        hs_reg <= 1'b1;
    else if (h_cnt == H_FP + H_SYNC - 1)
        hs_reg <= ~hs_reg;
end

// Horizontal active
always @(posedge clk or posedge rst) begin
    if (rst)
        h_active <= 1'b0;
    else if (h_cnt == H_FP + H_SYNC + H_BP - 1)
        h_active <= 1'b1;
    else if (h_cnt == H_TOTAL - 1)
        h_active <= 1'b0;
end

// Vertical sync
always @(posedge clk or posedge rst) begin
    if (rst)
        vs_reg <= 1'b0;
    else if ((v_cnt == V_FP - 1) && (h_cnt == H_FP - 1))
        vs_reg <= 1'b1;
    else if ((v_cnt == V_FP + V_SYNC - 1) && (h_cnt == H_FP - 1))
        vs_reg <= ~vs_reg;
end

// Vertical active
always @(posedge clk or posedge rst) begin
    if (rst)
        v_active <= 1'b0;
    else if ((v_cnt == V_FP + V_SYNC + V_BP - 1) && (h_cnt == H_FP - 1))
        v_active <= 1'b1;
    else if ((v_cnt == V_TOTAL - 1) && (h_cnt == H_FP - 1))
        v_active <= 1'b0;
end

// Dark background (oscilloscope style)
always @(posedge clk or posedge rst) begin
    if (rst) begin
        rgb_r_reg <= 8'h00;
        rgb_g_reg <= 8'h00;
        rgb_b_reg <= 8'h00;
    end else begin
        rgb_r_reg <= 8'h00;
        rgb_g_reg <= 8'h00;
        rgb_b_reg <= 8'h00;
    end
end

endmodule

// =========================================================================
// Grid Overlay - Draws oscilloscope grid on video
// =========================================================================
module grid_overlay(
    input               rst_n,
    input               pclk,
    input               i_hs,
    input               i_vs,
    input               i_de,
    input  [23:0]       i_data,
    output              o_hs,
    output              o_vs,
    output              o_de,
    output [23:0]       o_data
);

// Pixel position tracking
reg         de_d0, de_d1;
reg         vs_d0, vs_d1;
reg         hs_d0, hs_d1;
reg [23:0]  data_d0, data_d1;
reg [11:0]  x_cnt, y_cnt;

wire vs_edge    = vs_d0 & ~vs_d1;
wire de_falling = ~de_d0 & de_d1;

always @(posedge pclk) begin
    de_d0   <= i_de;
    de_d1   <= de_d0;
    vs_d0   <= i_vs;
    vs_d1   <= vs_d0;
    hs_d0   <= i_hs;
    hs_d1   <= hs_d0;
    data_d0 <= i_data;
    data_d1 <= data_d0;
end

always @(posedge pclk or negedge rst_n) begin
    if (!rst_n)
        x_cnt <= 12'd0;
    else if (de_d0)
        x_cnt <= x_cnt + 12'd1;
    else
        x_cnt <= 12'd0;
end

always @(posedge pclk or negedge rst_n) begin
    if (!rst_n)
        y_cnt <= 12'd0;
    else if (vs_edge)
        y_cnt <= 12'd0;
    else if (de_falling)
        y_cnt <= y_cnt + 12'd1;
end

wire [11:0] pos_x = x_cnt;
wire [11:0] pos_y = y_cnt;

assign o_hs = hs_d1;
assign o_vs = vs_d1;
assign o_de = de_d1;

// Grid display logic
reg [23:0]  v_data;
reg [8:0]   grid_x;
reg         region_active;

assign o_data = v_data;

always @(posedge pclk) begin
    if (pos_y >= 12'd9 && pos_y <= 12'd308 && pos_x >= 12'd9 && pos_x <= 12'd1018)
        region_active <= 1'b1;
    else
        region_active <= 1'b0;
end

always @(posedge pclk) begin
    if (region_active && de_d1)
        grid_x <= (grid_x == 9'd9) ? 9'd0 : grid_x + 9'd1;
    else
        grid_x <= 9'd0;
end

// Draw grid lines and dots
always @(posedge pclk) begin
    if (region_active)
        if (pos_y == 12'd287 || pos_y == 12'd32 || pos_y == 12'd159 ||
            (pos_y < 12'd287 && pos_y > 12'd32 && grid_x == 9'd9 && pos_y[0]))
            v_data <= {8'd139, 8'd129, 8'd29};     // Grid color (dark yellow)
        else
            v_data <= 24'h000000;                   // Black background
    else
        v_data <= data_d1;
end

endmodule

// =========================================================================
// ADC Sampler - Samples 1280 points from AD9238, then waits
// =========================================================================
module adc_sampler(
    input               adc_clk,
    input               rst,
    input  [11:0]       adc_data,
    output reg          adc_buf_wr,
    output [10:0]       adc_buf_addr,
    output [7:0]        adc_buf_data
);

localparam S_IDLE   = 2'd0;
localparam S_SAMPLE = 2'd1;
localparam S_WAIT   = 2'd2;

reg [1:0]   state;
reg [7:0]   adc_data_narrow;
reg [10:0]  sample_cnt;
reg [31:0]  wait_cnt;

assign adc_buf_addr = sample_cnt;
assign adc_buf_data = adc_data_narrow;

// Take top 8 bits of 12-bit ADC data
always @(posedge adc_clk or posedge rst) begin
    if (rst)
        adc_data_narrow <= 8'd0;
    else
        adc_data_narrow <= adc_data[11:4];
end

// Sampling state machine
always @(posedge adc_clk or posedge rst) begin
    if (rst) begin
        state      <= S_IDLE;
        wait_cnt   <= 32'd0;
        sample_cnt <= 11'd0;
        adc_buf_wr <= 1'b0;
    end else begin
        case (state)
            S_IDLE: begin
                state <= S_SAMPLE;
            end
            S_SAMPLE: begin
                if (sample_cnt == 11'd1279) begin
                    sample_cnt <= 11'd0;
                    adc_buf_wr <= 1'b0;
                    state      <= S_WAIT;
                end else begin
                    sample_cnt <= sample_cnt + 11'd1;
                    adc_buf_wr <= 1'b1;
                end
            end
            S_WAIT: begin
                if (wait_cnt == 32'd25_000_000) begin
                    state    <= S_SAMPLE;
                    wait_cnt <= 32'd0;
                end else begin
                    wait_cnt <= wait_cnt + 32'd1;
                end
            end
            default: state <= S_IDLE;
        endcase
    end
end

endmodule

// =========================================================================
// DAC Sine Wave Generator
// Uses 1024-sample 14-bit ROM from sin1024.mem (loaded via $readmemh)
// Frequency: 65 MHz / 1024 * ADDR_STEP = ~127 kHz (ADDR_STEP=2)
// ~2.5 complete sine cycles visible on 1280-sample display
// =========================================================================
module dac_square_gen(
    input               clk,        // DAC clock (~65 MHz)
    input               rst,
    output reg [13:0]   dac_data
);

// Sine wave ROM: 1024 entries x 14 bits
reg [13:0] sin_rom [0:1023];
initial $readmemh("sin1024.mem", sin_rom);

// Address counter - increment by 4 for ~5 visible cycles
reg [9:0] rom_addr;

always @(posedge clk or posedge rst) begin
    if (rst) begin
        rom_addr <= 10'd0;
        dac_data <= 14'h2000;
    end else begin
        rom_addr <= rom_addr + 10'd4;
        dac_data <= sin_rom[rom_addr];
    end
end

endmodule
