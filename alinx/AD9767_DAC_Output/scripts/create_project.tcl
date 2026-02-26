##############################################################################
## AD9767 DAC Sine Wave Output - Vivado Build Script
## Board: ALINX AX7010 (XC7Z010CLG400-1)
##
## Usage:
##   Option 1 (GUI):  Open Vivado -> Tools -> Run Tcl Script -> select this file
##   Option 2 (Batch): vivado -mode batch -source create_project.tcl
##   Option 3 (Tcl):   vivado -mode tcl -source create_project.tcl
##############################################################################

# Get the directory where this script is located
set script_dir [file dirname [file normalize [info script]]]
set project_dir [file normalize "$script_dir/.."]

puts "============================================"
puts " AD9767 DAC Sine Wave Output Builder"
puts " Project directory: $project_dir"
puts "============================================"

# =========================================================================
# Step 1: Create Project
# =========================================================================
puts "\n>>> Step 1: Creating Vivado project..."
set proj_name "dac_output"
set proj_path "$project_dir/vivado_project"

# Remove existing project if present
if {[file exists $proj_path]} {
    file delete -force $proj_path
}

create_project $proj_name $proj_path -part xc7z010clg400-1 -force
set_property target_language Verilog [current_project]

# =========================================================================
# Step 2: Add RTL Source Files
# =========================================================================
puts "\n>>> Step 2: Adding RTL source files..."
add_files -norecurse [list \
    "$project_dir/src/dac_output_top.v" \
    "$project_dir/src/sin1024.mem" \
]

# Set top module
set_property top dac_output_top [current_fileset]

# =========================================================================
# Step 3: Create and Configure clk_wiz_0 IP (MMCM)
# Input:  50 MHz single-ended
# Output: 65 MHz (DAC clock)
# =========================================================================
puts "\n>>> Step 3: Creating clk_wiz_0 IP..."
create_ip -name clk_wiz -vendor xilinx.com -library ip -module_name clk_wiz_0

set_property -dict [list \
    CONFIG.PRIM_IN_FREQ {50.000} \
    CONFIG.PRIM_SOURCE {Single_ended_clock_capable_pin} \
    CONFIG.CLKOUT1_REQUESTED_OUT_FREQ {65.000} \
    CONFIG.NUM_OUT_CLKS {1} \
    CONFIG.RESET_TYPE {ACTIVE_HIGH} \
    CONFIG.RESET_PORT {reset} \
    CONFIG.LOCKED_PORT {locked} \
    CONFIG.CLK_IN1_BOARD_INTERFACE {Custom} \
    CONFIG.USE_BOARD_FLOW {false} \
    CONFIG.CLKIN1_JITTER_PS {200.0} \
    CONFIG.MMCM_CLKIN1_PERIOD {20.000} \
] [get_ips clk_wiz_0]

generate_target all [get_ips clk_wiz_0]
synth_ip [get_ips clk_wiz_0]

# =========================================================================
# Step 4: Add Constraint File
# =========================================================================
puts "\n>>> Step 4: Adding constraint file..."
add_files -fileset constrs_1 -norecurse "$project_dir/constraints/dac_output_pins.xdc"

# =========================================================================
# Step 5: Run Synthesis
# =========================================================================
puts "\n>>> Step 5: Running synthesis..."
puts "   This may take several minutes..."

# Update compile order
update_compile_order -fileset sources_1
update_compile_order -fileset constrs_1

launch_runs synth_1 -jobs 4
wait_on_run synth_1

# Check synthesis result
set synth_status [get_property STATUS [get_runs synth_1]]
puts "   Synthesis status: $synth_status"

if {$synth_status != "synth_design Complete!"} {
    puts "ERROR: Synthesis failed!"
    puts "Check the synthesis log for details."
    open_run synth_1
    report_utilization -file "$proj_path/synth_utilization.rpt"
    return -code error "Synthesis failed"
}

puts "   Synthesis completed successfully!"

# Report utilization after synthesis
open_run synth_1
report_utilization -file "$proj_path/synth_utilization.rpt"
report_timing_summary -file "$proj_path/synth_timing.rpt"
puts "   Utilization report: $proj_path/synth_utilization.rpt"
puts "   Timing report: $proj_path/synth_timing.rpt"

# =========================================================================
# Step 6: Run Implementation
# =========================================================================
puts "\n>>> Step 6: Running implementation..."
puts "   This may take several minutes..."

launch_runs impl_1 -jobs 4
wait_on_run impl_1

# Check implementation result
set impl_status [get_property STATUS [get_runs impl_1]]
puts "   Implementation status: $impl_status"

if {$impl_status != "route_design Complete!"} {
    puts "ERROR: Implementation failed!"
    puts "Check the implementation log for details."
    open_run impl_1
    report_utilization -file "$proj_path/impl_utilization.rpt"
    report_timing_summary -file "$proj_path/impl_timing.rpt"
    return -code error "Implementation failed"
}

puts "   Implementation completed successfully!"

# Report implementation results
open_run impl_1
report_utilization -file "$proj_path/impl_utilization.rpt"
report_timing_summary -file "$proj_path/impl_timing.rpt"
report_power -file "$proj_path/impl_power.rpt"
puts "   Utilization report: $proj_path/impl_utilization.rpt"
puts "   Timing report: $proj_path/impl_timing.rpt"
puts "   Power report: $proj_path/impl_power.rpt"

# =========================================================================
# Step 7: Generate Bitstream
# =========================================================================
puts "\n>>> Step 7: Generating bitstream..."
puts "   This may take a few minutes..."

launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1

# Copy bitstream to output directory
set bit_file "$proj_path/${proj_name}.runs/impl_1/dac_output_top.bit"
set output_dir "$project_dir/output"

if {![file exists $output_dir]} {
    file mkdir $output_dir
}

if {[file exists $bit_file]} {
    file copy -force $bit_file "$output_dir/dac_output_top.bit"
    puts "\n============================================"
    puts " BUILD SUCCESSFUL!"
    puts " Bitstream: $output_dir/dac_output_top.bit"
    puts "============================================"
} else {
    puts "\nWARNING: Bitstream file not found at expected location."
    puts "Check: $bit_file"
    set alt_bit [glob -nocomplain "$proj_path/${proj_name}.runs/impl_1/*.bit"]
    if {[llength $alt_bit] > 0} {
        set actual_bit [lindex $alt_bit 0]
        file copy -force $actual_bit "$output_dir/dac_output_top.bit"
        puts " Found bitstream at: $actual_bit"
        puts " Copied to: $output_dir/dac_output_top.bit"
        puts "============================================"
    } else {
        puts "ERROR: No bitstream file generated!"
        return -code error "Bitstream generation failed"
    }
}

puts "\n>>> Done! You can now program the FPGA using:"
puts "    source scripts/program_fpga.tcl"
