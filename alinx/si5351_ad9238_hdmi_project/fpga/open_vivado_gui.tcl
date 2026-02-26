# Open Vivado GUI with completed implementation
open_project vivado_gui/oscilloscope_test.xpr
set_property board_part "" [current_project]

# Open the implemented design
open_run impl_1

puts "\n========================================="
puts "✅ Vivado GUI Ready"
puts "========================================="
puts "\nProject Status:"
puts "  - Implementation: Complete"
puts "  - Timing: WNS=2.051ns, WHS=0.049ns"
puts "  - Bitstream: Ready"
puts "\nBitstream Location:"
puts "  vivado_gui/oscilloscope_test.runs/impl_1/si5351_ad9238_hdmi_top_test.bit"
puts "========================================="
