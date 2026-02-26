# Quick Synthesis and Implementation
puts "========================================="
puts "Starting Synthesis..."
puts "========================================="

open_project vivado_gui/oscilloscope_test.xpr
set_property board_part "" [current_project]

# Run synthesis
reset_run synth_1
launch_runs synth_1 -jobs 8
wait_on_run synth_1

if {[get_property PROGRESS [get_runs synth_1]] != "100%"} {
    puts "ERROR: Synthesis failed!"
    exit 1
}

puts "\n✅ SYNTHESIS COMPLETE"

# Run implementation
reset_run impl_1
launch_runs impl_1 -jobs 8
wait_on_run impl_1

if {[get_property PROGRESS [get_runs impl_1]] != "100%"} {
    puts "ERROR: Implementation failed!"
    exit 1
}

puts "\n✅ IMPLEMENTATION COMPLETE"

# Generate bitstream
launch_runs impl_1 -to_step write_bitstream -jobs 8
wait_on_run impl_1

puts "\n========================================="
puts "✅ BITSTREAM GENERATED"
puts "========================================="

# Report timing
open_run impl_1
set wns [get_property SLACK [get_timing_paths -max_paths 1 -nworst 1]]
set whs [get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 -hold]]

puts "\nTiming Results:"
puts "  WNS: $wns ns"
puts "  WHS: $whs ns"

if {$wns < 0} {
    puts "\n⚠️  WARNING: Negative WNS - Timing not met!"
} else {
    puts "\n✅ Timing constraints met!"
}

puts "\nBitstream location:"
puts "  vivado_gui/oscilloscope_test.runs/impl_1/si5351_ad9238_hdmi_top_test.bit"
puts "========================================="

close_project
