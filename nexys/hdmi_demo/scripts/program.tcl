set script_dir [file dirname [file normalize [info script]]]
connect
puts "Connected to hw_server"
after 1000
puts "Programming FPGA..."
targets -set -filter {name =~ "*xc7a*"}
fpga [file join $script_dir ../hw/hdmi_wrapper.bit]
after 2000
puts "Downloading ELF to MicroBlaze..."
targets 3
rst -processor
after 1000
dow [file join $script_dir ../hw/app.elf]
after 1000
puts "Starting application..."
con
puts "Done! Check serial terminal for HDMI menu."
