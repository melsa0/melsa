# ==============================================================================
# Vivado Otomasyon Scripti - Buton LED Kontrol Sistemi
# Nexys Video (Artix-7 XC7A200T-1SBG484C)
#
# Kullanim:
#   vivado -mode batch -source build_and_program.tcl
#
# Bu script sirasiyla:
#   1. Proje olusturur
#   2. Kaynak dosyalari ekler
#   3. Sentez (Synthesis) calistirir
#   4. Yerlestirme ve Yonlendirme (Implementation) calistirir
#   5. Bitstream uretir
# ==============================================================================

# --- Proje ayarlari ---
set project_name "btn_led_project"
set project_dir  "C:/btn_led_build"
set part         "xc7a200tsbg484-1"

# --- Kaynak dosya yollarini belirle ---
set script_dir [file dirname [file normalize [info script]]]
set rtl_file   [file join $script_dir "btn_led_top.v"]
set xdc_file   [file join $script_dir "nexys_video_btn_led.xdc"]

# --- Temiz baslangic ---
if {[file exists $project_dir]} {
    file delete -force $project_dir
}

puts "============================================"
puts " Proje Olusturuluyor..."
puts "============================================"

create_project $project_name $project_dir -part $part -force
set_property target_language Verilog [current_project]

# --- Dosyalari ekle ---
add_files -norecurse $rtl_file
add_files -fileset constrs_1 -norecurse $xdc_file

# Top modul ayarla
set_property top btn_led_top [current_fileset]
update_compile_order -fileset sources_1

puts "============================================"
puts " Sentez (Synthesis) Basliyor..."
puts "============================================"

launch_runs synth_1 -jobs 4
wait_on_run synth_1

# Sentez sonucunu kontrol et
if {[get_property STATUS [get_runs synth_1]] != "synth_design Complete!"} {
    puts "HATA: Sentez basarisiz!"
    exit 1
}
puts " Sentez tamamlandi."

# --- Sentez raporu ---
open_run synth_1
report_utilization -file [file join $project_dir "utilization_synth.rpt"]
report_timing_summary -file [file join $project_dir "timing_synth.rpt"]

puts "============================================"
puts " Implementation Basliyor..."
puts "============================================"

launch_runs impl_1 -jobs 4
wait_on_run impl_1

if {[get_property STATUS [get_runs impl_1]] != "route_design Complete!"} {
    puts "HATA: Implementation basarisiz!"
    exit 1
}
puts " Implementation tamamlandi."

# --- Implementation raporu ---
open_run impl_1
report_utilization -file [file join $project_dir "utilization_impl.rpt"]
report_timing_summary -file [file join $project_dir "timing_impl.rpt"]

puts "============================================"
puts " Bitstream Uretiliyor..."
puts "============================================"

launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1

puts "============================================"
puts " TAMAMLANDI!"
puts "============================================"
puts ""
puts " Proje dizini : $project_dir"
puts " Bitstream     : $project_dir/${project_name}.runs/impl_1/btn_led_top.bit"
puts ""
puts " Karta yuklemek icin:"
puts "   1. Vivado GUI'yi ac:  vivado $project_dir/${project_name}.xpr"
puts "   2. Flow Navigator > Open Hardware Manager"
puts "   3. Open Target > Auto Connect"
puts "   4. Program Device > btn_led_top.bit sec"
puts ""
