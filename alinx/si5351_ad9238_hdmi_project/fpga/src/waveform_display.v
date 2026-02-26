`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Waveform Display Module
// - Inferred dual-port RAM (replaces dpram2048x8 IP)
// - Pixel position tracking (replaces timing_gen_xy)
// - Waveform overlay on video stream
//////////////////////////////////////////////////////////////////////////////////
module waveform_display(
    input                       rst_n,
    input                       pclk,           // Pixel clock
    input  [23:0]               wave_color,     // Waveform color (RGB)
    // ADC buffer write port
    input                       adc_clk,
    input                       adc_buf_wr,
    input  [10:0]               adc_buf_addr,
    input  [7:0]                adc_buf_data,
    // Video input
    input                       i_hs,
    input                       i_vs,
    input                       i_de,
    input  [23:0]               i_data,
    // Video output
    output                      o_hs,
    output                      o_vs,
    output                      o_de,
    output [23:0]               o_data
);

// =========================================================================
// Pixel position tracking (replaces timing_gen_xy)
// =========================================================================
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

// =========================================================================
// Inferred Dual-Port RAM (replaces dpram2048x8 IP)
// Write port: ADC clock domain
// Read port: Pixel clock domain
// =========================================================================
(* ram_style = "block" *) reg [7:0] sample_ram [0:2047];

// Write port
always @(posedge adc_clk) begin
    if (adc_buf_wr)
        sample_ram[adc_buf_addr] <= adc_buf_data;
end

// Read port
reg [7:0]   q;
reg [10:0]  rdaddress;

always @(posedge pclk) begin
    q <= sample_ram[rdaddress];
end

// =========================================================================
// Waveform overlay logic
// =========================================================================
reg [23:0]  v_data;
reg         region_active;

assign o_data = v_data;

// Active waveform region: x=[9..1018], y=[9..308]
always @(posedge pclk) begin
    if (pos_y >= 12'd9 && pos_y <= 12'd308 &&
        pos_x >= 12'd9 && pos_x <= 12'd1018)
        region_active <= 1'b1;
    else
        region_active <= 1'b0;
end

// RAM read address: increments across active region per line
always @(posedge pclk) begin
    if (region_active && de_d1)
        rdaddress <= rdaddress + 11'd1;
    else
        rdaddress <= 11'd0;
end

// Waveform drawing: draw 3-pixel thick line for visibility
// if |287 - pos_y - q| <= 1, draw in wave_color
wire [11:0] wave_y_pos = {4'd0, q};
wire [11:0] screen_y   = 12'd287 - pos_y;
wire signed [12:0] y_diff = {1'b0, screen_y} - {1'b0, wave_y_pos};
wire wave_hit = (y_diff == 0) || (y_diff == 1) || (y_diff == -1);

always @(posedge pclk) begin
    if (region_active)
        if (wave_hit)
            v_data <= wave_color;
        else
            v_data <= data_d1;
    else
        v_data <= data_d1;
end

endmodule
