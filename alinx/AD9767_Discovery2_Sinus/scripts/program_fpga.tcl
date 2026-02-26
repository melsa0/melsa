##############################################################################
## FPGA Programming Script
## Opens Hardware Manager, connects, and programs the device
##
## Usage: In Vivado Tcl Console, run:
##   source <path_to_this_script>/program_fpga.tcl
##############################################################################

set script_dir [file dirname [file normalize [info script]]]
set project_dir [file normalize "$script_dir/.."]
set bit_file "$project_dir/output/dac_output_top.bit"

# Open Hardware Manager
open_hw_manager

# Connect to hardware server (local)
connect_hw_server -allow_non_jtag

# Open the first available hardware target
open_hw_target

# Get the FPGA device (skip arm_dap on Zynq)
set hw_device [get_hw_devices xc7z*]
if {$hw_device eq ""} {
    set hw_device [lindex [get_hw_devices] 1]
}
current_hw_device $hw_device

# Set the bitstream file
set_property PROGRAM.FILE $bit_file $hw_device

# Program the device
program_hw_devices $hw_device

puts ""
puts "============================================"
puts " FPGA PROGRAMMED SUCCESSFULLY!"
puts " Bitstream: $bit_file"
puts "============================================"
