# VGA Timing Guide for FPGA

## VGA 640x480 @ 60Hz Standard

### Timing Parameters

| Parameter | Pixels/Lines | Time |
|-----------|-------------|------|
| **Horizontal** | | |
| Visible area | 640 px | 25.6 us |
| Front porch | 16 px | 0.64 us |
| Sync pulse | 96 px | 3.84 us |
| Back porch | 48 px | 1.92 us |
| **Total** | **800 px** | **32.0 us** |
| **Vertical** | | |
| Visible area | 480 lines | 15.36 ms |
| Front porch | 10 lines | 0.32 ms |
| Sync pulse | 2 lines | 0.064 ms |
| Back porch | 33 lines | 1.056 ms |
| **Total** | **525 lines** | **16.8 ms** |

### Pixel Clock
- Required: 25.175 MHz
- From 100 MHz: divide by 4 = **25 MHz** (0.7% error, acceptable)
- Frame rate: 25 MHz / (800 * 525) = **59.52 Hz**

## Implementation

### Pixel Clock Generation
```verilog
reg [1:0] clk_div;
always @(posedge clk) begin  // 100 MHz
    clk_div <= clk_div + 1;
end
wire pixel_en = (clk_div == 0);  // 25 MHz tick
```

### Sync Signal Generation
```verilog
// Horizontal counter (0-799)
always @(posedge clk) begin
    if (pixel_en) begin
        if (h_count == 799)
            h_count <= 0;
        else
            h_count <= h_count + 1;
    end
end

// HSYNC active during sync pulse region
hsync <= ~(h_count >= 656 && h_count < 752);
```

### Text Mode Display

For 80x60 character text display with 8x8 font:
```
Columns: 640 / 8 = 80 characters
Rows:    480 / 8 = 60 characters
Total:   80 * 60 = 4,800 characters (fits in single BRAM)
```

### Pipeline Architecture

VGA display requires a read pipeline because BRAM and ROM have 1-cycle latency:

```
Cycle 0: Compute BRAM address from pixel coordinates
Cycle 1: BRAM outputs character code -> feed to char ROM
Cycle 2: Char ROM outputs pixel bitmap -> select bit for current pixel
```

```verilog
// Stage 0: address
assign buf_addr = vga_row * 80 + vga_col;

// Stage 1: BRAM -> ROM
always @(posedge clk) begin
    font_char <= buf_dout[6:0];
    font_row  <= pixel_y[2:0];
end

// Stage 2: ROM -> pixel
wire pixel_on = font_pixels[7 - pixel_x_delayed[2:0]];
```

## Common Issues

### 1. Pipeline Delay Mismatch
The 2-cycle pipeline means `video_active` and `pixel_x` must be delayed by 2 cycles to match the pixel data.

### 2. Multiplication in Address Calculation
`row * 80` creates a multiplier. For better timing:
- Use `row * 64 + row * 16` (shift and add)
- Or register the multiplication result

### 3. BRAM Port Conflict
Text buffer uses Port A for UART writes and Port B for VGA reads. Both can operate simultaneously on a true dual-port BRAM without conflict.

## See Also
- `rtl_archive/common/video/vga_sync.v` - VGA timing generator module
- `rtl_archive/common/video/char_rom.v` - 8x8 ASCII font ROM
- `validation_test/NexysVideo-VGA-Terminal/` - Complete working example
