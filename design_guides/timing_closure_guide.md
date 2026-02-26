# Timing Closure Guide for FPGA Designs

## Understanding Timing Reports

### Key Metrics
- **WNS (Worst Negative Slack):** Must be >= 0 for timing closure
  - Positive = timing met (good)
  - Negative = timing violation (bad)
- **WHS (Worst Hold Slack):** Must be >= 0
- **WPWS (Worst Pulse Width Slack):** Must be >= 0

### Reading Vivado Timing Summary
```
Timing Summary:
  WNS(ns)  TNS(ns)  WHS(ns)  THS(ns)
  +4.307   0.000    +0.054   0.000
```
- WNS = +4.307 ns means 4.307 ns of margin on a 10 ns clock period
- TNS = 0.000 means no total negative slack (all paths pass)

## Common Timing Violations and Fixes

### 1. Combinational Division Operators

**Problem:**
```verilog
// BAD: Creates very long combinational path
wire [3:0] thousands = value / 1000;
wire [3:0] hundreds  = (value % 1000) / 100;
wire [3:0] tens      = (value % 100) / 10;
wire [3:0] ones      = value % 10;
```

Verilog `/` and `%` operators synthesize into iterative subtraction circuits. For 16-bit values, this creates chains of comparators and subtractors that cannot meet timing at 100 MHz.

**Real Example:** WNS dropped from +5 ns to **-2.320 ns** when division was added.

**Solution: Registered Shift-and-Subtract BCD**
```verilog
// GOOD: One subtraction per clock cycle
always @(posedge clk) begin
    case (bcd_step)
        0: begin // thousands
            if (remain >= 16'd1000) begin
                remain <= remain - 16'd1000;
                digit  <= digit + 1;
            end else begin
                thousands_out <= digit;
                digit  <= 0;
                bcd_step <= 1; // move to hundreds
            end
        end
        // ... similar for hundreds, tens
    endcase
end
```

**Result:** WNS improved from **-2.320 ns** to **+4.307 ns**.

### 2. Large Multiplexers

**Problem:** Wide case statements with many options create deep MUX trees.

**Solution:** Pipeline or register intermediate results.

### 3. Long Counter Chains

**Problem:** 32-bit counter comparison creates long carry chain.

**Solution:** Use hierarchical comparison or pipeline the comparison.

### 4. Cross-Clock Domain Paths

**Problem:** Signals crossing between clock domains create false or difficult timing paths.

**Solution:** Use proper CDC techniques:
- Double-FF synchronizer for single-bit signals
- Gray-code FIFO for multi-bit data
- Handshake protocols for control signals

## Vivado Build Optimization Tips

### Use -jobs 1 for Small Designs
```tcl
launch_runs synth_1 -jobs 1
```
Avoids `[Synth 8-7080] Parallel synthesis criteria is not met` warning for designs under ~50K LUTs.

### Check Implementation Status Robustly
```tcl
# BAD: Exact match fails when timing is not met
if {$status == "route_design Complete!"} ...

# GOOD: Partial match handles "Complete, Failed Timing!"
if {[string match "*Complete*" $status]} ...
```

### Generate Reports
```tcl
report_utilization -file utilization.txt
report_timing_summary -file timing.txt
report_power -file power.txt
```

## Timing Closure Checklist

1. Check WNS after synthesis - if negative, fix before implementation
2. Identify the critical path (longest combinational delay)
3. Register combinational outputs that span multiple operations
4. Avoid division, modulo, and multiplication in combinational logic
5. Pipeline deep logic (> 4 levels of LUTs)
6. Use proper CDC for cross-domain signals
7. Constrain all clocks with `create_clock`
8. Set appropriate I/O delays with `set_input_delay` / `set_output_delay`
