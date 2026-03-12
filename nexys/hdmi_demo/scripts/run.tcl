set script_dir [file dirname [file normalize [info script]]]
set hw_dir [file join $script_dir ../hw]
exec updatemem -meminfo [file join $hw_dir hdmi_wrapper.mmi] -data [file join $hw_dir app.elf] -bit [file join $hw_dir hdmi_wrapper.bit] -proc hdmi_i/microblaze_0 -out [file join $hw_dir merged.bit] -force
