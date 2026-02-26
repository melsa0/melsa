###############################################################################
# Open project in Vivado GUI and run full build flow
###############################################################################
set script_dir [file dirname [file normalize [info script]]]
source "$script_dir/build_project.tcl"
# After build, open GUI
start_gui
