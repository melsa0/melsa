# SPI Protocol Implementation Guide

## Overview

SPI (Serial Peripheral Interface) is a synchronous full-duplex protocol used for short-distance communication with sensors, ADCs, DACs, flash memory, and displays.

## SPI Signals

| Signal | Direction | Description |
|--------|-----------|-------------|
| SCLK | Master -> Slave | Serial clock |
| MOSI | Master -> Slave | Master Out, Slave In (data) |
| MISO | Slave -> Master | Master In, Slave Out (data) |
| CS_N | Master -> Slave | Chip Select (active low) |

## SPI Modes

| Mode | CPOL | CPHA | Clock Idle | Data Sampled | Data Shifted |
|------|------|------|------------|--------------|--------------|
| 0 | 0 | 0 | LOW | Rising edge | Falling edge |
| 1 | 0 | 1 | LOW | Falling edge | Rising edge |
| 2 | 1 | 0 | HIGH | Falling edge | Rising edge |
| 3 | 1 | 1 | HIGH | Rising edge | Falling edge |

**Mode 0** is the most common (used by most sensors and flash chips).

## SPI Master Implementation

### Clock Generation
```verilog
parameter CLK_DIV = 50;  // 100 MHz / (2*50) = 1 MHz SPI clock

reg [15:0] clk_cnt;
always @(posedge clk) begin
    if (clk_cnt >= CLK_DIV - 1) begin
        clk_cnt <= 0;
        sclk <= ~sclk;  // toggle SPI clock
    end else
        clk_cnt <= clk_cnt + 1;
end
```

### Data Transfer (Mode 0)
```
CS_N:  _____|_________________________________|_____
SCLK:  _____|__|-|__|-|__|-|__|-|__|-|__|-|__|-|__|-|_____
MOSI:  _____|D7|D6|D5|D4|D3|D2|D1|D0|_____
MISO:  _____|D7|D6|D5|D4|D3|D2|D1|D0|_____
         CS    8 clock cycles              CS
       setup                             hold
```

### State Machine
```
IDLE -> CS_SETUP -> SHIFT (x16 half-clocks) -> CS_HOLD -> DONE -> IDLE
```

1. **IDLE:** CS high, SCLK low, wait for start
2. **CS_SETUP:** CS goes low, wait setup time
3. **SHIFT:** Toggle SCLK, shift data MSB first
   - Rising edge: sample MISO
   - Falling edge: output next MOSI bit
4. **CS_HOLD:** Hold CS low briefly after last clock
5. **DONE:** CS goes high, assert done pulse

## SPI Clock Speed Considerations

| Application | Typical Speed | CLK_DIV @ 100MHz |
|-------------|--------------|-------------------|
| Temperature sensor | 1 MHz | 50 |
| ADC (12-bit) | 5 MHz | 10 |
| Flash memory | 10 MHz | 5 |
| Display (SPI LCD) | 20 MHz | 2-3 |

## Common Pitfalls

### 1. CS Timing
Some devices need minimum CS setup/hold time before/after clock edges. Always add a small delay.

### 2. MSB vs LSB First
Most SPI devices use **MSB first**. Check the datasheet!

### 3. Clock Polarity on CS Transitions
In Mode 0, SCLK must be LOW when CS transitions. Starting SCLK high during CS setup will confuse the slave.

### 4. Full-Duplex
SPI is full-duplex: data is simultaneously sent and received. Even if you only want to read, you must send dummy data (usually 0x00 or 0xFF).

## Verified Implementation

See `rtl_archive/common/spi/spi_master.v` for a production-ready SPI master module.
See `validation_test/NexysVideo-VGA-Terminal/` for SPI integration example.
