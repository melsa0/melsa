###############################################################################
# SI5351 + AD9238 + HDMI Oscilloscope - Rebuild (thicker waveform)
###############################################################################

puts "\n====================================================================="
puts "SI5351 + AD9238 + HDMI Oscilloscope Build v2"
puts "====================================================================="

set base_dir "C:/vivado_builds"
set project_name "oscilloscope_v2"
set project_dir "$base_dir/project_v2"
set fpga_part "xc7z010clg400-1"
set src_dir "$base_dir/src"
set constr_dir "$base_dir/constraints"
set ip_repo_path "$base_dir/ip_repo"

if {[file exists $project_dir]} {
    file delete -force $project_dir
}

puts "\[1/7\] Creating project..."
create_project $project_name $project_dir -part $fpga_part -force
set_property ip_repo_paths $ip_repo_path [current_project]
update_ip_catalog

puts "\[2/7\] Adding sources..."
add_files -norecurse "$src_dir/top_simplified.v"
add_files -norecurse "$src_dir/waveform_display.v"
add_files -norecurse "$src_dir/test_square_wave_gen.v"

puts "\[3/7\] Adding constraints..."
add_files -fileset constrs_1 -norecurse "$constr_dir/pins.xdc"
set_property top si5351_ad9238_hdmi_top_test [current_fileset]

puts "\[4/7\] Creating IPs..."
set ip_dir "$project_dir/$project_name.srcs/sources_1/ip"
file mkdir $ip_dir

create_ip -name clk_wiz -vendor xilinx.com -library ip -version 6.0 -module_name clk_wiz_0 -dir $ip_dir
set_property -dict [list \
    CONFIG.PRIM_IN_FREQ {50.000} \
    CONFIG.CLKOUT1_REQUESTED_OUT_FREQ {74.25} \
    CONFIG.CLKOUT2_REQUESTED_OUT_FREQ {371.25} \
    CONFIG.CLKOUT3_REQUESTED_OUT_FREQ {65.00} \
    CONFIG.CLKOUT2_USED {true} \
    CONFIG.CLKOUT3_USED {true} \
    CONFIG.NUM_OUT_CLKS {3} \
    CONFIG.RESET_TYPE {ACTIVE_HIGH} \
    CONFIG.RESET_PORT {reset} \
    CONFIG.LOCKED_PORT {locked} \
] [get_ips clk_wiz_0]
generate_target all [get_ips clk_wiz_0]

create_ip -name rgb2dvi -vendor digilentinc.com -library ip -version 1.3 -module_name rgb2dvi_0 -dir $ip_dir
generate_target all [get_ips rgb2dvi_0]

puts "\[5/7\] Synthesis..."
reset_run synth_1
launch_runs synth_1 -jobs 4
wait_on_run synth_1
puts "  Status: [get_property STATUS [get_runs synth_1]]"

puts "\[6/7\] Implementation..."
launch_runs impl_1 -jobs 4
wait_on_run impl_1
puts "  Status: [get_property STATUS [get_runs impl_1]]"

puts "\[7/7\] Bitstream..."
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1

set bit_file "$project_dir/$project_name.runs/impl_1/si5351_ad9238_hdmi_top_test.bit"
if {[file exists $bit_file]} {
    puts "\nBUILD COMPLETE! Bitstream: $bit_file ([file size $bit_file] bytes)"
} else {
    puts "\nWARNING: Bitstream not found. Check logs."
}
