# UART Protocol Implementation Guide

## Overview

UART (Universal Asynchronous Receiver/Transmitter) is the most common serial communication protocol for FPGA-PC communication. This guide covers implementing a robust UART module in Verilog.

## Protocol Specification

### 8N1 Format (most common)
```
IDLE  |START| D0 | D1 | D2 | D3 | D4 | D5 | D6 | D7 |STOP| IDLE
  1   |  0  | b0 | b1 | b2 | b3 | b4 | b5 | b6 | b7 |  1 |   1
```

- **Start bit:** Line goes LOW (1 -> 0)
- **Data bits:** 8 bits, LSB first
- **Stop bit:** Line goes HIGH (0 -> 1)
- **No parity** in 8N1 mode

### Baud Rate Calculation

```
CLKS_PER_BIT = Clock_Frequency / Baud_Rate

Example: 100 MHz / 115200 = 868 clocks per bit
Half-bit:  868 / 2 = 434 clocks (for mid-bit sampling)
```

### Common Baud Rates

| Baud Rate | Clocks @ 100 MHz | Error |
|-----------|-----------------|-------|
| 9600      | 10417           | 0.00% |
| 19200     | 5208            | 0.03% |
| 38400     | 2604            | 0.03% |
| 57600     | 1736            | 0.03% |
| 115200    | 868             | 0.06% |
| 230400    | 434             | 0.06% |
| 460800    | 217             | 0.06% |
| 921600    | 109             | 0.31% |

## UART Receiver Design

### State Machine
```
IDLE --> START --> DATA --> STOP --> IDLE
  |        |                          ^
  |        +-- false start (rx=1) ----+
  +-- rx=0 (start bit detected)
```

### Key Design Decisions

1. **Double-FF Synchronizer (Metastability Prevention)**
```verilog
reg rx_sync1, rx_sync2;
always @(posedge clk) begin
    rx_sync1 <= rx;
    rx_sync2 <= rx_sync1;
end
```
The RX signal is asynchronous. Sampling it directly can cause metastability. Two flip-flops reduce the probability to negligible levels.

2. **Mid-bit Sampling**
```
         |<--- CLKS_PER_BIT --->|
Start:   |       HALF_BIT       | <- sample here for start bit validation
Data:    |     CLKS_PER_BIT     | <- sample at center of each data bit
```
Sampling at the center of each bit provides maximum noise immunity.

3. **False Start Detection**
After detecting a falling edge (potential start bit), wait HALF_BIT clocks and re-check. If RX is still LOW, it's a real start bit. If HIGH, it was noise.

## UART Transmitter Design

### State Machine
```
IDLE --> START --> DATA --> STOP --> IDLE
  |                                   ^
  +-- tx_start pulse -----------------+
```

### Flow Control
- `tx_busy` output indicates transmission in progress
- New data should not be loaded while `tx_busy = 1`
- Check `!tx_busy && !tx_start` before starting new transmission

## Common Pitfalls

### 1. Clock Domain Crossing
**Problem:** RX signal comes from external source, not synchronized to FPGA clock.
**Solution:** Always use double-FF synchronizer on RX input.

### 2. Baud Rate Mismatch
**Problem:** Integer division of CLK_FREQ/BAUD_RATE introduces error.
**Solution:** Keep error below 2%. At 115200 baud with 100 MHz clock, error is 0.06% (acceptable).

### 3. TX Contention
**Problem:** Multiple sources trying to send simultaneously.
**Solution:** Implement priority-based TX arbitration:
```verilog
// Priority: message > number > echo
if (msg_sending && !tx_busy)
    // send message character
else if (num_sending && !tx_busy && !msg_busy)
    // send number digit
else if (echo_pending && !tx_busy && !msg_busy && !num_busy)
    // send echo
```

### 4. Missing Timescale
**Problem:** Simulation fails with "Module doesn't have a timescale" error.
**Solution:** Add `` `timescale 1ns / 1ps `` to ALL Verilog files, not just testbench.

## Verified Implementation

See `rtl_archive/common/uart/` for production-ready UART modules:
- `uart_rx.v` - Parameterized receiver
- `uart_tx.v` - Parameterized transmitter

See `validation_test/NexysVideo-UART-LED/` for complete working example.
