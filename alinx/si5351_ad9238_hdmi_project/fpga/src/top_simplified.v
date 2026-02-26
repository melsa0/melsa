`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// SI5351 + AD9238 + HDMI Oscilloscope - Project 2
// Board: Alinx AX7010 (XC7Z010CLG400-1)
// Description: Reads AD9238 dual-channel ADC data and displays waveforms on HDMI
//              Si5351 provides external test signal via Arduino
//////////////////////////////////////////////////////////////////////////////////
module si5351_ad9238_hdmi_top_test(
    input                       sys_clk,            // 50 MHz system clock
    input                       rst_n,              // Active-low reset
    // AD9238 ADC interface
    output                      ad9238_clk_ch0,     // ADC channel 0 clock
    output                      ad9238_clk_ch1,     // ADC channel 1 clock
    input  [11:0]               ad9238_data_ch0,    // ADC channel 0 data
    input  [11:0]               ad9238_data_ch1,    // ADC channel 1 data
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
wire            video_clk;      // 74.25 MHz pixel clock
wire            video_clk5x;    // 371.25 MHz TMDS serial clock
wire            adc_clk;        // ~65 MHz ADC sampling clock
wire            pll_locked;

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

// ADC clock assignment
assign ad9238_clk_ch0 = adc_clk;
assign ad9238_clk_ch1 = adc_clk;

// =========================================================================
// Clock Generation - clk_wiz_0
// 50 MHz -> 74.25 MHz (pixel), 371.25 MHz (5x serial), 65 MHz (ADC)
// =========================================================================
clk_wiz_0 clk_wiz_inst (
    .clk_in1    (sys_clk),
    .clk_out1   (video_clk),       // ~74.17 MHz
    .clk_out2   (video_clk5x),     // ~370.83 MHz
    .clk_out3   (adc_clk),         // ~65.44 MHz
    .reset      (~rst_n),
    .locked     (pll_locked)
);

// =========================================================================
// HDMI Output - rgb2dvi_0
// =========================================================================
rgb2dvi_0 rgb2dvi_inst (
    .TMDS_Clk_p     (TMDS_clk_p),
    .TMDS_Clk_n     (TMDS_clk_n),
    .TMDS_Data_p    (TMDS_data_p),
    .TMDS_Data_n    (TMDS_data_n),
    .oen            (hdmi_oen),
    .aRst_n         (1'b1),
    .vid_pData      ({wave1_r, wave1_g, wave1_b}),
    .vid_pVDE       (wave1_de),
    .vid_pHSync     (wave1_hs),
    .vid_pVSync     (wave1_vs),
    .PixelClk       (video_clk),
    .SerialClk      (video_clk5x)
);

// =========================================================================
// Video Timing Generator (1280x720 @ 74.25 MHz)
// =========================================================================
video_timing_720p video_timing_inst (
    .clk    (video_clk),
    .rst    (~rst_n),
    .hs     (vid_hs),
    .vs     (vid_vs),
    .de     (vid_de),
    .rgb_r  (vid_r),
    .rgb_g  (vid_g),
    .rgb_b  (vid_b)
);

// =========================================================================
// Grid Display Overlay
// =========================================================================
grid_overlay grid_inst (
    .rst_n      (rst_n),
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
// ADC Sampling - Channel 0
// =========================================================================
adc_sampler adc_sample_ch0 (
    .adc_clk        (adc_clk),
    .rst            (~rst_n),
    .adc_data       (ad9238_data_ch0),
    .adc_buf_wr     (adc0_buf_wr),
    .adc_buf_addr   (adc0_buf_addr),
    .adc_buf_data   (adc0_buf_data)
);

// =========================================================================
// ADC Sampling - Channel 1
// =========================================================================
adc_sampler adc_sample_ch1 (
    .adc_clk        (adc_clk),
    .rst            (~rst_n),
    .adc_data       (ad9238_data_ch1),
    .adc_buf_wr     (adc1_buf_wr),
    .adc_buf_addr   (adc1_buf_addr),
    .adc_buf_data   (adc1_buf_data)
);

// =========================================================================
// Waveform Display - Channel 0 (Red)
// =========================================================================
waveform_display wav_display_ch0 (
    .rst_n          (rst_n),
    .pclk           (video_clk),
    .wave_color     (24'hFF0000),       // Red
    .adc_clk        (adc_clk),
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
    .rst_n          (rst_n),
    .pclk           (video_clk),
    .wave_color     (24'h0000FF),       // Blue
    .adc_clk        (adc_clk),
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

endmodule

// =========================================================================
// Video Timing Generator - 1280x720p @ 74.25 MHz
// Generates color bar background
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
    end else if (video_active) begin
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

// Pixel position tracking (timing_gen_xy)
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
