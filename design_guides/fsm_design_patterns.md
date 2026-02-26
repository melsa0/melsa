# FSM (Finite State Machine) Design Patterns for FPGA

## Overview

State machines are the backbone of digital design. This guide covers patterns used in the UART LED Controller project.

## Pattern 1: Simple Sequential FSM

Used in: UART RX/TX

```verilog
localparam IDLE  = 2'd0;
localparam START = 2'd1;
localparam DATA  = 2'd2;
localparam STOP  = 2'd3;

reg [1:0] state;

always @(posedge clk) begin
    if (rst)
        state <= IDLE;
    else begin
        case (state)
            IDLE:  if (trigger) state <= START;
            START: if (done)    state <= DATA;
            DATA:  if (done)    state <= STOP;
            STOP:  if (done)    state <= IDLE;
        endcase
    end
end
```

**Key Points:**
- Use `localparam` for state encoding (not `define`)
- Size the state register to match number of states
- Always have a reset path to IDLE

## Pattern 2: Nested State Machine

Used in: Game logic inside command parser

```verilog
// Outer FSM: Game states
localparam GAME_OFF  = 3'd0;
localparam GAME_WAIT = 3'd1;
localparam GAME_GO   = 3'd2;

// Inner logic: Command parsing (runs only in GAME_OFF)
case (game_state)
    GAME_OFF: begin
        if (rx_valid) begin
            case (rx_data)
                "g": game_state <= GAME_WAIT;  // start game
                "0": led[0] <= ~led[0];        // normal command
            endcase
        end
    end
    GAME_WAIT: begin
        // Game-specific logic, ignores normal commands
    end
endcase
```

**Key Points:**
- Outer FSM controls which inner logic runs
- Commands only processed in appropriate states
- Clear state transitions prevent conflicting behavior

## Pattern 3: String Transmitter (ROM + Counter)

Used in: Message transmission system

```verilog
// Message ROM (combinational)
always @(*) begin
    case (msg_id)
        MSG_WAIT: begin
            msg_length = 10;
            case (msg_idx)
                0: msg_char = 8'h0D;  // \r
                1: msg_char = 8'h0A;  // \n
                2: msg_char = "W";
                // ...
            endcase
        end
    endcase
end

// Sender FSM (sequential)
case (stx_state)
    STX_IDLE: if (msg_send) stx_state <= STX_LOAD;
    STX_LOAD: begin
        if (msg_idx >= msg_length)
            stx_state <= STX_IDLE;     // done
        else if (!tx_busy)
            stx_state <= STX_SEND;     // ready to send
    end
    STX_SEND: stx_state <= STX_WAIT;   // trigger TX
    STX_WAIT: begin
        if (!tx_busy) begin            // TX finished
            msg_idx <= msg_idx + 1;
            stx_state <= STX_LOAD;     // next character
        end
    end
endcase
```

**Key Points:**
- Separate ROM (combinational) from sender (sequential)
- Wait for `!tx_busy` before sending each character
- Index counter tracks position in message

## Pattern 4: Priority Arbiter

Used in: TX priority system (msg > num > echo)

```verilog
// Only one source can use TX per cycle
if (msg_sending && !tx_busy) begin
    tx_data  <= msg_char;
    tx_start <= 1;
end
else if (num_sending && !tx_busy && !msg_busy) begin
    tx_data  <= digit_ascii;
    tx_start <= 1;
end
else if (echo_pending && !tx_busy && !msg_busy && !num_busy) begin
    tx_data  <= echo_char;
    tx_start <= 1;
    echo_pending <= 0;
end
```

**Key Points:**
- Higher priority sources checked first
- Each level checks that higher-priority sources are idle
- Only one `tx_start` pulse per cycle

## Pattern 5: Registered BCD Conversion

Used in: Number-to-ASCII conversion

```verilog
// Each clock cycle: one subtract operation
case (bcd_step)
    0: begin // thousands
        if (remain >= 1000) begin
            remain <= remain - 1000;
            digit  <= digit + 1;
        end else begin
            out_thousands <= digit;
            digit <= 0;
            bcd_step <= 1;  // next digit
        end
    end
    // ... hundreds, tens, ones
endcase
```

**Why not use `/` and `%`?**
Division operators create long combinational paths:
- `value / 1000` requires ~16 levels of compare-subtract logic
- At 100 MHz (10 ns period), this exceeds timing
- Registered approach: 1 subtraction per clock, always meets timing

## Anti-Patterns to Avoid

### 1. Blocking assignments in sequential logic
```verilog
// BAD
always @(posedge clk) begin
    state = NEXT;  // blocking in sequential!
end

// GOOD
always @(posedge clk) begin
    state <= NEXT;  // non-blocking in sequential
end
```

### 2. Incomplete case without default
```verilog
// BAD: infers latch
always @(*) begin
    case (state)
        IDLE: out = 0;
        RUN:  out = 1;
        // missing default!
    endcase
end

// GOOD
always @(*) begin
    case (state)
        IDLE:    out = 0;
        RUN:     out = 1;
        default: out = 0;
    endcase
end
```

### 3. Multiple drivers
```verilog
// BAD: tx_start driven from two always blocks
always @(posedge clk) begin
    if (send_echo) tx_start <= 1;
end
always @(posedge clk) begin
    if (send_msg) tx_start <= 1;
end

// GOOD: single always block with priority
always @(posedge clk) begin
    tx_start <= 0;
    if (send_msg)       tx_start <= 1;
    else if (send_echo) tx_start <= 1;
end
```
