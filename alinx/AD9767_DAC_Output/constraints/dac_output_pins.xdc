##############################################################################
## AD9767 DAC Sine Wave Output - Pin Constraints
## Board: ALINX AX7010 (XC7Z010CLG400-1)
## AN9767 DAC module on J10 expansion header
##############################################################################

############## Clock (50 MHz) and Reset ##################
create_clock -period 20.000 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports {sys_clk}]
set_property PACKAGE_PIN U18 [get_ports {sys_clk}]

set_property IOSTANDARD LVCMOS33 [get_ports {rst_n}]
set_property PACKAGE_PIN N15 [get_ports {rst_n}]

############## AD9767 DAC - Channel 1 (J10) ##################
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
