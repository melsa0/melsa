`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////
// HDMI/DVI Transmitter - Pure Verilog (no IP dependency)
// Uses TMDS 8b/10b encoding + OSERDESE2 10:1 serialization + OBUFDS
// Target: Xilinx 7-series FPGA
//////////////////////////////////////////////////////////////////////////////

module hdmi_tx(
    input           pixel_clk,      // Pixel clock (~74.25 MHz for 720p)
    input           serial_clk,     // 5x pixel clock (~371.25 MHz)
    input           rst,            // Active-high reset
    input  [7:0]    vid_r,
    input  [7:0]    vid_g,
    input  [7:0]    vid_b,
    input           vid_de,         // Data enable (active region)
    input           vid_hsync,
    input           vid_vsync,
    output          TMDS_clk_p,
    output          TMDS_clk_n,
    output [2:0]    TMDS_data_p,
    output [2:0]    TMDS_data_n,
    output          hdmi_oen
);

assign hdmi_oen = 1'b1;

// TMDS encoded data for each channel
wire [9:0] tmds_red, tmds_green, tmds_blue;

// Channel 0 = Blue, c0 = hsync, c1 = vsync
tmds_encoder enc_blue (
    .clk    (pixel_clk),
    .rst    (rst),
    .din    (vid_b),
    .de     (vid_de),
    .c0     (vid_hsync),
    .c1     (vid_vsync),
    .dout   (tmds_blue)
);

// Channel 1 = Green, c0 = 0, c1 = 0
tmds_encoder enc_green (
    .clk    (pixel_clk),
    .rst    (rst),
    .din    (vid_g),
    .de     (vid_de),
    .c0     (1'b0),
    .c1     (1'b0),
    .dout   (tmds_green)
);

// Channel 2 = Red, c0 = 0, c1 = 0
tmds_encoder enc_red (
    .clk    (pixel_clk),
    .rst    (rst),
    .din    (vid_r),
    .de     (vid_de),
    .c0     (1'b0),
    .c1     (1'b0),
    .dout   (tmds_red)
);

// Serialize and output each TMDS data channel
wire [2:0] tmds_data_serial;

tmds_serializer ser_blue (
    .pixel_clk  (pixel_clk),
    .serial_clk (serial_clk),
    .rst        (rst),
    .tmds_data  (tmds_blue),
    .serial_out (tmds_data_serial[0])
);

tmds_serializer ser_green (
    .pixel_clk  (pixel_clk),
    .serial_clk (serial_clk),
    .rst        (rst),
    .tmds_data  (tmds_green),
    .serial_out (tmds_data_serial[1])
);

tmds_serializer ser_red (
    .pixel_clk  (pixel_clk),
    .serial_clk (serial_clk),
    .rst        (rst),
    .tmds_data  (tmds_red),
    .serial_out (tmds_data_serial[2])
);

// Serialize clock channel: pattern 1111100000 = pixel clock forwarding
wire tmds_clk_serial;
tmds_serializer ser_clk (
    .pixel_clk  (pixel_clk),
    .serial_clk (serial_clk),
    .rst        (rst),
    .tmds_data  (10'b0000011111),
    .serial_out (tmds_clk_serial)
);

// Differential output buffers
OBUFDS #(.IOSTANDARD("TMDS_33")) obuf_clk (
    .I  (tmds_clk_serial),
    .O  (TMDS_clk_p),
    .OB (TMDS_clk_n)
);

genvar i;
generate
    for (i = 0; i < 3; i = i + 1) begin : gen_obufds
        OBUFDS #(.IOSTANDARD("TMDS_33")) obuf_data (
            .I  (tmds_data_serial[i]),
            .O  (TMDS_data_p[i]),
            .OB (TMDS_data_n[i])
        );
    end
endgenerate

endmodule

//////////////////////////////////////////////////////////////////////////////
// TMDS 8b/10b Encoder (DVI 1.0 specification)
//////////////////////////////////////////////////////////////////////////////
module tmds_encoder(
    input               clk,
    input               rst,
    input      [7:0]    din,
    input               de,
    input               c0,
    input               c1,
    output reg [9:0]    dout
);

// Count number of 1s in input data
wire [3:0] n1_din = din[0] + din[1] + din[2] + din[3] +
                     din[4] + din[5] + din[6] + din[7];

// Choose XOR or XNOR path
wire use_xnor = (n1_din > 4'd4) || (n1_din == 4'd4 && din[0] == 1'b0);

// Stage 1: Transition minimization
wire [8:0] q_m;
assign q_m[0] = din[0];
assign q_m[1] = use_xnor ? ~(q_m[0] ^ din[1]) : (q_m[0] ^ din[1]);
assign q_m[2] = use_xnor ? ~(q_m[1] ^ din[2]) : (q_m[1] ^ din[2]);
assign q_m[3] = use_xnor ? ~(q_m[2] ^ din[3]) : (q_m[2] ^ din[3]);
assign q_m[4] = use_xnor ? ~(q_m[3] ^ din[4]) : (q_m[3] ^ din[4]);
assign q_m[5] = use_xnor ? ~(q_m[4] ^ din[5]) : (q_m[4] ^ din[5]);
assign q_m[6] = use_xnor ? ~(q_m[5] ^ din[6]) : (q_m[5] ^ din[6]);
assign q_m[7] = use_xnor ? ~(q_m[6] ^ din[7]) : (q_m[6] ^ din[7]);
assign q_m[8] = use_xnor ? 1'b0 : 1'b1;

// Count 1s and 0s in q_m[7:0]
wire [3:0] n1_qm = q_m[0] + q_m[1] + q_m[2] + q_m[3] +
                    q_m[4] + q_m[5] + q_m[6] + q_m[7];
wire [3:0] n0_qm = 4'd8 - n1_qm;

// Stage 2: DC balance with disparity counter
reg signed [4:0] cnt;

always @(posedge clk) begin
    if (rst) begin
        dout <= 10'd0;
        cnt  <= 5'sd0;
    end else begin
        if (de) begin
            if (cnt == 5'sd0 || n1_qm == 4'd4) begin
                // No disparity or balanced word
                dout[9]   <= ~q_m[8];
                dout[8]   <= q_m[8];
                dout[7:0] <= q_m[8] ? q_m[7:0] : ~q_m[7:0];
                if (q_m[8] == 1'b0)
                    cnt <= cnt + $signed({1'b0, n0_qm}) - $signed({1'b0, n1_qm});
                else
                    cnt <= cnt + $signed({1'b0, n1_qm}) - $signed({1'b0, n0_qm});
            end else begin
                if ((cnt > 5'sd0 && n1_qm > 4'd4) ||
                    (cnt < 5'sd0 && n1_qm < 4'd4)) begin
                    // Invert data to reduce disparity
                    dout[9]   <= 1'b1;
                    dout[8]   <= q_m[8];
                    dout[7:0] <= ~q_m[7:0];
                    cnt <= cnt + $signed({3'b000, q_m[8], 1'b0}) +
                           $signed({1'b0, n0_qm}) - $signed({1'b0, n1_qm});
                end else begin
                    // Keep data as is
                    dout[9]   <= 1'b0;
                    dout[8]   <= q_m[8];
                    dout[7:0] <= q_m[7:0];
                    cnt <= cnt - $signed({3'b000, ~q_m[8], 1'b0}) +
                           $signed({1'b0, n1_qm}) - $signed({1'b0, n0_qm});
                end
            end
        end else begin
            // Blanking period: send control tokens
            cnt <= 5'sd0;
            case ({c1, c0})
                2'b00: dout <= 10'b1101010100;
                2'b01: dout <= 10'b0010101011;
                2'b10: dout <= 10'b0101010100;
                2'b11: dout <= 10'b1010101011;
            endcase
        end
    end
end

endmodule

//////////////////////////////////////////////////////////////////////////////
// TMDS 10:1 Serializer using OSERDESE2 (master/slave cascade)
// Xilinx 7-series specific
//////////////////////////////////////////////////////////////////////////////
module tmds_serializer(
    input           pixel_clk,
    input           serial_clk,
    input           rst,
    input  [9:0]    tmds_data,
    output          serial_out
);

wire cascade1, cascade2;
wire serial_out_int;

OSERDESE2 #(
    .DATA_RATE_OQ   ("DDR"),
    .DATA_RATE_TQ   ("SDR"),
    .DATA_WIDTH     (10),
    .INIT_OQ        (1'b0),
    .INIT_TQ        (1'b0),
    .SERDES_MODE    ("MASTER"),
    .SRVAL_OQ       (1'b0),
    .SRVAL_TQ       (1'b0),
    .TBYTE_CTL      ("FALSE"),
    .TBYTE_SRC      ("FALSE"),
    .TRISTATE_WIDTH (1)
) oserdes_master (
    .OQ         (serial_out),
    .OFB        (),
    .TQ         (),
    .TFB        (),
    .SHIFTOUT1  (),
    .SHIFTOUT2  (),
    .TBYTEOUT   (),
    .CLK        (serial_clk),
    .CLKDIV     (pixel_clk),
    .D1         (tmds_data[0]),
    .D2         (tmds_data[1]),
    .D3         (tmds_data[2]),
    .D4         (tmds_data[3]),
    .D5         (tmds_data[4]),
    .D6         (tmds_data[5]),
    .D7         (tmds_data[6]),
    .D8         (tmds_data[7]),
    .TCE        (1'b0),
    .OCE        (1'b1),
    .TBYTEIN    (1'b0),
    .RST        (rst),
    .SHIFTIN1   (cascade1),
    .SHIFTIN2   (cascade2),
    .T1         (1'b0),
    .T2         (1'b0),
    .T3         (1'b0),
    .T4         (1'b0)
);

OSERDESE2 #(
    .DATA_RATE_OQ   ("DDR"),
    .DATA_RATE_TQ   ("SDR"),
    .DATA_WIDTH     (10),
    .INIT_OQ        (1'b0),
    .INIT_TQ        (1'b0),
    .SERDES_MODE    ("SLAVE"),
    .SRVAL_OQ       (1'b0),
    .SRVAL_TQ       (1'b0),
    .TBYTE_CTL      ("FALSE"),
    .TBYTE_SRC      ("FALSE"),
    .TRISTATE_WIDTH (1)
) oserdes_slave (
    .OQ         (),
    .OFB        (),
    .TQ         (),
    .TFB        (),
    .SHIFTOUT1  (cascade1),
    .SHIFTOUT2  (cascade2),
    .TBYTEOUT   (),
    .CLK        (serial_clk),
    .CLKDIV     (pixel_clk),
    .D1         (1'b0),
    .D2         (1'b0),
    .D3         (tmds_data[8]),
    .D4         (tmds_data[9]),
    .D5         (1'b0),
    .D6         (1'b0),
    .D7         (1'b0),
    .D8         (1'b0),
    .TCE        (1'b0),
    .OCE        (1'b1),
    .TBYTEIN    (1'b0),
    .RST        (rst),
    .SHIFTIN1   (1'b0),
    .SHIFTIN2   (1'b0),
    .T1         (1'b0),
    .T2         (1'b0),
    .T3         (1'b0),
    .T4         (1'b0)
);

endmodule
