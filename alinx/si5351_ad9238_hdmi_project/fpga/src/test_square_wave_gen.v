`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Test Square Wave Generator (optional)
// Generates internal square wave for testing without external Si5351/AD9238
// Not used in normal operation - the real ADC path is in adc_sampler
//////////////////////////////////////////////////////////////////////////////////
module test_square_wave_gen(
    input               clk,
    input               rst,
    output reg          buf_wr,
    output reg [10:0]   buf_addr,
    output reg [7:0]    buf_data
);

localparam S_IDLE   = 2'd0;
localparam S_FILL   = 2'd1;
localparam S_WAIT   = 2'd2;

localparam SAMPLES    = 11'd1280;
localparam HALF_PER   = 11'd64;
localparam WAIT_COUNT = 32'd5_000_000;

reg [1:0]   state;
reg [10:0]  sample_cnt;
reg [31:0]  wait_cnt;
reg [10:0]  phase_cnt;

always @(posedge clk or posedge rst) begin
    if (rst) begin
        state      <= S_IDLE;
        sample_cnt <= 11'd0;
        wait_cnt   <= 32'd0;
        phase_cnt  <= 11'd0;
        buf_wr     <= 1'b0;
        buf_addr   <= 11'd0;
        buf_data   <= 8'd0;
    end else begin
        case (state)
            S_IDLE: begin
                state      <= S_FILL;
                sample_cnt <= 11'd0;
                phase_cnt  <= 11'd0;
            end
            S_FILL: begin
                buf_wr   <= 1'b1;
                buf_addr <= sample_cnt;
                buf_data <= (phase_cnt < HALF_PER) ? 8'd200 : 8'd55;

                if (phase_cnt == (HALF_PER * 2 - 1))
                    phase_cnt <= 11'd0;
                else
                    phase_cnt <= phase_cnt + 11'd1;

                if (sample_cnt == SAMPLES - 1) begin
                    sample_cnt <= 11'd0;
                    buf_wr     <= 1'b0;
                    state      <= S_WAIT;
                end else begin
                    sample_cnt <= sample_cnt + 11'd1;
                end
            end
            S_WAIT: begin
                buf_wr <= 1'b0;
                if (wait_cnt == WAIT_COUNT) begin
                    state    <= S_FILL;
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
