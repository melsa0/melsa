# Force reload project and implementation
puts "Loading project..."
open_project vivado_gui/oscilloscope_test.xpr -quiet
set_property board_part "" [current_project] -quiet

puts "Opening implementation run..."
open_run impl_1 -name impl_1

puts "\n========================================="
puts "✅ Project and Implementation Loaded!"
puts "========================================="
puts "\nYou can now:"
puts "  1. View schematic (Flow Navigator → Open Elaborated/Implemented Design)"
puts "  2. Open Hardware Manager (Flow Navigator → PROGRAM AND DEBUG)"
puts "  3. View timing reports (Reports → Timing)"
puts "========================================="
