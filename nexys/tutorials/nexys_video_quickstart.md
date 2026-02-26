# Nexys Video - FPGA Development Quick Start

## Board Overview

- **FPGA:** Artix-7 XC7A200T-1SBG484C
- **Clock:** 100 MHz system clock (pin R4)
- **LEDs:** 8x user LEDs (pins T14-Y13, LVCMOS25)
- **UART:** USB-UART bridge (TX: AA19, RX: V18, LVCMOS33)
- **Reset:** CPU reset button (pin G4, active-low, LVCMOS15)

## Development Environment Setup

### Prerequisites
- Xilinx Vivado 2025.1 (or compatible version)
- USB cable for JTAG programming
- Terminal software (PuTTY, Tera Term, or similar)

### Vivado Installation Path
```
C:\Xilinx\2025.1\Vivado\2025.1
```

## Workflow: CLI + GUI (Hybrid)

### Step 1: Write RTL
Create your Verilog modules. Minimum files needed:
- Top module (`.v`)
- Constraints (`.xdc`)

### Step 2: Build (CLI - Fast)
```batch
vivado -mode batch -source build_script.tcl
```
Runs synthesis, implementation, and bitstream generation in background.

### Step 3: Monitor (GUI - Visual)
```batch
vivado project.xpr
```
Open the project in GUI to see schematic, utilization, timing reports.

### Step 4: Simulate (CLI)
```batch
xvlog *.v
xelab top_tb -snapshot sim -debug all
xsim sim -runall
```

### Step 5: Program (GUI or CLI)
```tcl
# In Vivado TCL console:
open_hw_manager
connect_hw_server
open_hw_target
set_property PROGRAM.FILE {path/to/bitstream.bit} [current_hw_device]
program_hw_devices
```

## Pin Constraints Template (XDC)

```tcl
## Clock
set_property -dict { PACKAGE_PIN R4 IOSTANDARD LVCMOS33 } [get_ports clk]
create_clock -period 10.00 [get_ports clk]

## LEDs
set_property -dict { PACKAGE_PIN T14 IOSTANDARD LVCMOS25 } [get_ports {led[0]}]
set_property -dict { PACKAGE_PIN T15 IOSTANDARD LVCMOS25 } [get_ports {led[1]}]
set_property -dict { PACKAGE_PIN T16 IOSTANDARD LVCMOS25 } [get_ports {led[2]}]
set_property -dict { PACKAGE_PIN U16 IOSTANDARD LVCMOS25 } [get_ports {led[3]}]
set_property -dict { PACKAGE_PIN V15 IOSTANDARD LVCMOS25 } [get_ports {led[4]}]
set_property -dict { PACKAGE_PIN W16 IOSTANDARD LVCMOS25 } [get_ports {led[5]}]
set_property -dict { PACKAGE_PIN W15 IOSTANDARD LVCMOS25 } [get_ports {led[6]}]
set_property -dict { PACKAGE_PIN Y13 IOSTANDARD LVCMOS25 } [get_ports {led[7]}]

## Reset (active-low)
set_property -dict { PACKAGE_PIN G4 IOSTANDARD LVCMOS15 } [get_ports cpu_resetn]

## UART
set_property -dict { PACKAGE_PIN AA19 IOSTANDARD LVCMOS33 } [get_ports uart_rx_out]
set_property -dict { PACKAGE_PIN V18  IOSTANDARD LVCMOS33 } [get_ports uart_tx_in]

## Configuration
set_property CONFIG_VOLTAGE 3.3 [current_design]
set_property CFGBVS VCCO [current_design]
```

## Example Projects

### 1. LED Chaser (Beginner)
- Simple knight rider pattern
- Teaches: clock dividers, shift registers
- Files: `validation_test/led_chaser_example/`

### 2. UART LED Controller (Intermediate)
- UART RX/TX + LED control + Reaction Timer game
- Teaches: UART protocol, FSM design, BCD conversion
- Files: `validation_test/NexysVideo-UART-LED/`

## Common Issues

### Path Spaces in Vivado
Vivado TCL has issues with spaces in file paths. Use paths without spaces:
```
GOOD: C:\led_chaser_build\
BAD:  C:\Users\name\My Projects\
```

### Parallel Synthesis Warning
`[Synth 8-7080] Parallel synthesis criteria is not met`

Use `-jobs 1` for small designs (< 50K LUTs):
```tcl
launch_runs synth_1 -jobs 1
```

### Simulation Timescale Error
All Verilog files need `` `timescale `` directive, not just testbench:
```verilog
`timescale 1ns / 1ps
```

### PowerShell vs Bash
On Windows, use PowerShell for Vivado commands. Git Bash may not handle Windows paths correctly.
