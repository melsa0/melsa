##############################################################################
## AD9767 -> AD9238 Loopback Test Pin Constraints
## Board: ALINX AX7010 (XC7Z010CLG400-1)
## AN9767 DAC module on J10 | AN9238 ADC module on J11 | HDMI output
##############################################################################

############## Clock (50 MHz) and Reset ##################
create_clock -period 20.000 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports {sys_clk}]
set_property PACKAGE_PIN U18 [get_ports {sys_clk}]

set_property IOSTANDARD LVCMOS33 [get_ports {rst_n}]
set_property PACKAGE_PIN N15 [get_ports {rst_n}]

############## HDMI Output ###########################
set_property PACKAGE_PIN N18 [get_ports TMDS_clk_p]
set_property IOSTANDARD TMDS_33 [get_ports TMDS_clk_p]
set_property IOSTANDARD TMDS_33 [get_ports TMDS_clk_n]

set_property PACKAGE_PIN V20 [get_ports {TMDS_data_p[0]}]
set_property IOSTANDARD TMDS_33 [get_ports {TMDS_data_p[0]}]
set_property IOSTANDARD TMDS_33 [get_ports {TMDS_data_n[0]}]

set_property PACKAGE_PIN T20 [get_ports {TMDS_data_p[1]}]
set_property IOSTANDARD TMDS_33 [get_ports {TMDS_data_p[1]}]
set_property IOSTANDARD TMDS_33 [get_ports {TMDS_data_n[1]}]

set_property PACKAGE_PIN N20 [get_ports {TMDS_data_p[2]}]
set_property IOSTANDARD TMDS_33 [get_ports {TMDS_data_p[2]}]
set_property IOSTANDARD TMDS_33 [get_ports {TMDS_data_n[2]}]

set_property PACKAGE_PIN V16 [get_ports hdmi_oen]
set_property IOSTANDARD LVCMOS33 [get_ports hdmi_oen]

############## AD9238 ADC - Channel 0 (J11) ##################
## ADC CH0 Clock output
set_property PACKAGE_PIN H17 [get_ports ad9238_clk_ch0]
set_property IOSTANDARD LVCMOS33 [get_ports ad9238_clk_ch0]

## ADC CH0 Data input [11:0]
set_property PACKAGE_PIN J20 [get_ports {ad9238_data_ch0[0]}]
set_property PACKAGE_PIN H20 [get_ports {ad9238_data_ch0[1]}]
set_property PACKAGE_PIN L16 [get_ports {ad9238_data_ch0[2]}]
set_property PACKAGE_PIN L17 [get_ports {ad9238_data_ch0[3]}]
set_property PACKAGE_PIN M17 [get_ports {ad9238_data_ch0[4]}]
set_property PACKAGE_PIN M18 [get_ports {ad9238_data_ch0[5]}]
set_property PACKAGE_PIN D19 [get_ports {ad9238_data_ch0[6]}]
set_property PACKAGE_PIN D20 [get_ports {ad9238_data_ch0[7]}]
set_property PACKAGE_PIN E18 [get_ports {ad9238_data_ch0[8]}]
set_property PACKAGE_PIN E19 [get_ports {ad9238_data_ch0[9]}]
set_property PACKAGE_PIN G17 [get_ports {ad9238_data_ch0[10]}]
set_property PACKAGE_PIN G18 [get_ports {ad9238_data_ch0[11]}]
set_property IOSTANDARD LVCMOS33 [get_ports {ad9238_data_ch0[*]}]
set_property IOB true [get_ports {ad9238_data_ch0[*]}]

############## AD9238 ADC - Channel 1 (J11) ##################
## ADC CH1 Clock output
set_property PACKAGE_PIN F17 [get_ports ad9238_clk_ch1]
set_property IOSTANDARD LVCMOS33 [get_ports ad9238_clk_ch1]

## ADC CH1 Data input [11:0]
set_property PACKAGE_PIN F16 [get_ports {ad9238_data_ch1[0]}]
set_property PACKAGE_PIN F20 [get_ports {ad9238_data_ch1[1]}]
set_property PACKAGE_PIN F19 [get_ports {ad9238_data_ch1[2]}]
set_property PACKAGE_PIN G20 [get_ports {ad9238_data_ch1[3]}]
set_property PACKAGE_PIN G19 [get_ports {ad9238_data_ch1[4]}]
set_property PACKAGE_PIN H18 [get_ports {ad9238_data_ch1[5]}]
set_property PACKAGE_PIN J18 [get_ports {ad9238_data_ch1[6]}]
set_property PACKAGE_PIN L20 [get_ports {ad9238_data_ch1[7]}]
set_property PACKAGE_PIN L19 [get_ports {ad9238_data_ch1[8]}]
set_property PACKAGE_PIN M20 [get_ports {ad9238_data_ch1[9]}]
set_property PACKAGE_PIN M19 [get_ports {ad9238_data_ch1[10]}]
set_property PACKAGE_PIN K18 [get_ports {ad9238_data_ch1[11]}]
set_property IOSTANDARD LVCMOS33 [get_ports {ad9238_data_ch1[*]}]
set_property IOB true [get_ports {ad9238_data_ch1[*]}]

############## AD9767 DAC - Channel 1 (J10) ##################
## AN9767 module connected to J10 expansion header
## Pin mapping: J10 header pins -> FPGA Bank 34/35 pins
##
## DA1 Clock and Write (J10 PIN3/PIN4)
set_property PACKAGE_PIN W19 [get_ports {da1_clk}]
set_property PACKAGE_PIN W18 [get_ports {da1_wrt}]
set_property IOSTANDARD LVCMOS33 [get_ports {da1_clk}]
set_property IOSTANDARD LVCMOS33 [get_ports {da1_wrt}]

## DA1 Data [13:0] (J10 PIN5-PIN18)
set_property PACKAGE_PIN R14 [get_ports {da1_data[13]}]
set_property PACKAGE_PIN P14 [get_ports {da1_data[12]}]
set_property PACKAGE_PIN Y17 [get_ports {da1_data[11]}]
set_property PACKAGE_PIN Y16 [get_ports {da1_data[10]}]
set_property PACKAGE_PIN W15 [get_ports {da1_data[9]}]
set_property PACKAGE_PIN V15 [get_ports {da1_data[8]}]
set_property PACKAGE_PIN Y14 [get_ports {da1_data[7]}]
set_property PACKAGE_PIN W14 [get_ports {da1_data[6]}]
set_property PACKAGE_PIN P18 [get_ports {da1_data[5]}]
set_property PACKAGE_PIN N17 [get_ports {da1_data[4]}]
set_property PACKAGE_PIN U15 [get_ports {da1_data[3]}]
set_property PACKAGE_PIN U14 [get_ports {da1_data[2]}]
set_property PACKAGE_PIN P16 [get_ports {da1_data[1]}]
set_property PACKAGE_PIN P15 [get_ports {da1_data[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {da1_data[*]}]

############## AD9767 DAC - Channel 2 (J10) ##################
## DA2 Clock and Write (J10 PIN19/PIN20)
set_property PACKAGE_PIN U17 [get_ports {da2_clk}]
set_property PACKAGE_PIN T16 [get_ports {da2_wrt}]
set_property IOSTANDARD LVCMOS33 [get_ports {da2_clk}]
set_property IOSTANDARD LVCMOS33 [get_ports {da2_wrt}]

## DA2 Data [13:0] (J10 PIN21-PIN34)
set_property PACKAGE_PIN V18 [get_ports {da2_data[13]}]
set_property PACKAGE_PIN V17 [get_ports {da2_data[12]}]
set_property PACKAGE_PIN T15 [get_ports {da2_data[11]}]
set_property PACKAGE_PIN T14 [get_ports {da2_data[10]}]
set_property PACKAGE_PIN V13 [get_ports {da2_data[9]}]
set_property PACKAGE_PIN U13 [get_ports {da2_data[8]}]
set_property PACKAGE_PIN W13 [get_ports {da2_data[7]}]
set_property PACKAGE_PIN V12 [get_ports {da2_data[6]}]
set_property PACKAGE_PIN U12 [get_ports {da2_data[5]}]
set_property PACKAGE_PIN T12 [get_ports {da2_data[4]}]
set_property PACKAGE_PIN T10 [get_ports {da2_data[3]}]
set_property PACKAGE_PIN T11 [get_ports {da2_data[2]}]
set_property PACKAGE_PIN A20 [get_ports {da2_data[1]}]
set_property PACKAGE_PIN B19 [get_ports {da2_data[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {da2_data[*]}]

############## Timing Constraints ##################
## False path for async clock domain crossing (ADC/DAC clock -> pixel clock)
set_false_path -from [get_clocks -of_objects [get_pins clk_wiz_inst/clk_out3]] \
               -to   [get_clocks -of_objects [get_pins clk_wiz_inst/clk_out1]]
set_false_path -from [get_clocks -of_objects [get_pins clk_wiz_inst/clk_out1]] \
               -to   [get_clocks -of_objects [get_pins clk_wiz_inst/clk_out3]]
