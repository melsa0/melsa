##############################################################################
## AD9767 DAC - Rebuild Script
## Opens existing project and reruns synthesis + implementation + bitstream
##############################################################################

set project_dir [file normalize [file dirname [info script]]/..]
set proj_path "$project_dir/vivado_project/dac_output.xpr"

puts "============================================"
puts " AD9767 DAC - Rebuild"
puts " Project: $proj_path"
puts "============================================"

# Open existing project
puts "\n>>> Opening project..."
open_project $proj_path

# Update source files (in case they changed)
update_compile_order -fileset sources_1

# =========================================================================
# Reset and rerun synthesis
# =========================================================================
puts "\n>>> Resetting synthesis..."
reset_run synth_1
puts ">>> Running synthesis..."
launch_runs synth_1 -jobs 4
wait_on_run synth_1

set synth_status [get_property STATUS [get_runs synth_1]]
puts "   Synthesis status: $synth_status"
if {$synth_status != "synth_design Complete!"} {
    puts "ERROR: Synthesis failed!"
    exit 1
}
puts "   Synthesis OK!"

# =========================================================================
# Reset and rerun implementation
# =========================================================================
puts "\n>>> Resetting implementation..."
reset_run impl_1
puts ">>> Running implementation..."
launch_runs impl_1 -jobs 4
wait_on_run impl_1

set impl_status [get_property STATUS [get_runs impl_1]]
puts "   Implementation status: $impl_status"
if {$impl_status != "route_design Complete!"} {
    puts "ERROR: Implementation failed!"
    exit 1
}
puts "   Implementation OK!"

# =========================================================================
# Generate bitstream
# =========================================================================
puts "\n>>> Generating bitstream..."
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1

# Copy bitstream to output
set bit_file "$project_dir/vivado_project/dac_output.runs/impl_1/dac_output_top.bit"
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
    puts "ERROR: Bitstream not found!"
    exit 1
}

close_project
