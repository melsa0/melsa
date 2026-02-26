`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////
// Buton ile LED Kontrol Sistemi - Nexys Video (Artix-7 XC7A200T)
//
// 3 Mod:
//   BTNU -> Pozisyon Modu : Tek LED saga-sola kayar (pos 0-7)
//   BTND -> Volume Modu   : LED bar sagdan sola dolar (vol 1-8)
//   BTNC -> Tumunu Yak    : 8 LED birden yanar (0xFF)
//
// BTNL/BTNR -> Mod icinde saga/sola hareket veya artir/azalt
//////////////////////////////////////////////////////////////////////////////

module btn_led_top (
    input  wire       clk,          // 100 MHz sistem saati (R4)
    input  wire       cpu_resetn,   // Active-low reset (G4)
    input  wire       btnu,         // Yukari  - Pozisyon modu (F15)
    input  wire       btnd,         // Asagi   - Volume modu   (D22)
    input  wire       btnl,         // Sol     - Sola / Artir  (C22)
    input  wire       btnr,         // Sag     - Saga / Azalt  (D14)
    input  wire       btnc,         // Orta    - Tumunu yak    (B22)
    output reg  [7:0] led           // 8 LED cikisi (T14-Y13)
);

    // ====================================================================
    // Reset senkronizasyonu
    // ====================================================================
    wire rst = ~cpu_resetn;

    // ====================================================================
    // Debounce ve Edge Detect sinyalleri
    // ====================================================================
    wire btnu_pulse, btnd_pulse, btnl_pulse, btnr_pulse, btnc_pulse;

    debounce_edge u_deb_btnu (.clk(clk), .rst(rst), .btn_in(btnu), .btn_pulse(btnu_pulse));
    debounce_edge u_deb_btnd (.clk(clk), .rst(rst), .btn_in(btnd), .btn_pulse(btnd_pulse));
    debounce_edge u_deb_btnl (.clk(clk), .rst(rst), .btn_in(btnl), .btn_pulse(btnl_pulse));
    debounce_edge u_deb_btnr (.clk(clk), .rst(rst), .btn_in(btnr), .btn_pulse(btnr_pulse));
    debounce_edge u_deb_btnc (.clk(clk), .rst(rst), .btn_in(btnc), .btn_pulse(btnc_pulse));

    // ====================================================================
    // Mod State Machine
    // ====================================================================
    localparam MODE_POSITION = 2'd0;
    localparam MODE_VOLUME   = 2'd1;
    localparam MODE_ALL_ON   = 2'd2;

    reg [1:0] mode;
    reg [2:0] pos;   // Pozisyon: 0-7
    reg [3:0] vol;   // Volume:   1-8

    always @(posedge clk) begin
        if (rst) begin
            mode <= MODE_POSITION;
            pos  <= 3'd0;
            vol  <= 4'd1;
        end else begin
            // --- Mod degistirme (oncelikli) ---
            if (btnu_pulse) begin
                mode <= MODE_POSITION;
                pos  <= 3'd0;
            end else if (btnd_pulse) begin
                mode <= MODE_VOLUME;
                vol  <= 4'd1;
            end else if (btnc_pulse) begin
                mode <= MODE_ALL_ON;
            end else begin
                // --- Mod icindeki hareketler ---
                case (mode)
                    MODE_POSITION: begin
                        if (btnl_pulse && pos < 3'd7)
                            pos <= pos + 3'd1;
                        else if (btnr_pulse && pos > 3'd0)
                            pos <= pos - 3'd1;
                    end
                    MODE_VOLUME: begin
                        if (btnl_pulse && vol < 4'd8)
                            vol <= vol + 4'd1;
                        else if (btnr_pulse && vol > 4'd1)
                            vol <= vol - 4'd1;
                    end
                    MODE_ALL_ON: begin
                        // BTNL/BTNR etkisiz
                    end
                    default: mode <= MODE_POSITION;
                endcase
            end
        end
    end

    // ====================================================================
    // LED Cikis Mantigi
    // ====================================================================
    always @(*) begin
        case (mode)
            MODE_POSITION: led = 8'd1 << pos;          // Tek LED: 1<<pos
            MODE_VOLUME:   led = 8'hFF >> (4'd8 - vol); // Bar: (2^vol)-1
            MODE_ALL_ON:   led = 8'hFF;                 // Hepsi yank
            default:       led = 8'd0;
        endcase
    end

endmodule

//////////////////////////////////////////////////////////////////////////////
// Debounce + Edge Detect Modulu
//
// 1. 2-FF senkronizasyon (metastabilite onleme)
// 2. 20-bit sayac ile ~10ms debounce (100 MHz'de 2^20 ~ 10.5ms)
// 3. Yukselen kenar algilama -> tek clock pulse
//////////////////////////////////////////////////////////////////////////////

module debounce_edge (
    input  wire clk,
    input  wire rst,
    input  wire btn_in,
    output wire btn_pulse
);

    // --- Senkronizasyon (2-FF) ---
    reg sync_0, sync_1;
    always @(posedge clk) begin
        if (rst) begin
            sync_0 <= 1'b0;
            sync_1 <= 1'b0;
        end else begin
            sync_0 <= btn_in;
            sync_1 <= sync_0;
        end
    end

    // --- Debounce sayaci ---
    reg [19:0] counter;
    reg        btn_stable;

    always @(posedge clk) begin
        if (rst) begin
            counter    <= 20'd0;
            btn_stable <= 1'b0;
        end else begin
            if (sync_1 != btn_stable) begin
                // Sinyal degisti, sayaci artir
                if (counter == 20'hF_FFFF) begin
                    btn_stable <= sync_1;   // 10ms gecti, kabul et
                    counter    <= 20'd0;
                end else begin
                    counter <= counter + 20'd1;
                end
            end else begin
                counter <= 20'd0;           // Sinyal kararliysa sayaci sifirla
            end
        end
    end

    // --- Edge Detection (yukselen kenar -> tek pulse) ---
    reg btn_prev;
    always @(posedge clk) begin
        if (rst)
            btn_prev <= 1'b0;
        else
            btn_prev <= btn_stable;
    end

    assign btn_pulse = btn_stable & ~btn_prev;  // 0->1 gecisi

endmodule
