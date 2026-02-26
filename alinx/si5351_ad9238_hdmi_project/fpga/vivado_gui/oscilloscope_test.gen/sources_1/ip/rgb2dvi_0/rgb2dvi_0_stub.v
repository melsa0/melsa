// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2025 Advanced Micro Devices, Inc. All Rights Reserved.
// --------------------------------------------------------------------------------
// Tool Version: Vivado v.2025.1 (lin64) Build 6140274 Wed May 21 22:58:25 MDT 2025
// Date        : Mon Feb 16 15:10:19 2026
// Host        : testpc-MS-7D98 running 64-bit Ubuntu 22.04.5 LTS
// Command     : write_verilog -force -mode synth_stub
//               /home/testpc/fpga_asist_dev/validation_test/si5351_ad9238_hdmi_project/fpga/vivado_gui/oscilloscope_test.gen/sources_1/ip/rgb2dvi_0/rgb2dvi_0_stub.v
// Design      : rgb2dvi_0
// Purpose     : Stub declaration of top-level module interface
// Device      : xc7z010clg400-1
// --------------------------------------------------------------------------------

// This empty module with port declaration file causes synthesis tools to infer a black box for IP.
// The synthesis directives are for Synopsys Synplify support to prevent IO buffer insertion.
// Please paste the declaration into a Verilog source file or add the file as an additional source.
(* CHECK_LICENSE_TYPE = "rgb2dvi_0,rgb2dvi,{}" *) (* downgradeipidentifiedwarnings = "yes" *) (* x_core_info = "rgb2dvi,Vivado 2025.1" *) 
module rgb2dvi_0(TMDS_Clk_p, TMDS_Clk_n, TMDS_Data_p, 
  TMDS_Data_n, oen, aRst_n, vid_pData, vid_pVDE, vid_pHSync, vid_pVSync, PixelClk, SerialClk)
/* synthesis syn_black_box black_box_pad_pin="TMDS_Clk_p,TMDS_Clk_n,TMDS_Data_p[2:0],TMDS_Data_n[2:0],oen,aRst_n,vid_pData[23:0],vid_pVDE,vid_pHSync,vid_pVSync" */
/* synthesis syn_force_seq_prim="PixelClk" */
/* synthesis syn_force_seq_prim="SerialClk" */;
  (* x_interface_info = "digilentinc.com:interface:tmds:1.0 TMDS CLK_P" *) (* x_interface_mode = "master TMDS" *) output TMDS_Clk_p;
  (* x_interface_info = "digilentinc.com:interface:tmds:1.0 TMDS CLK_N" *) output TMDS_Clk_n;
  (* x_interface_info = "digilentinc.com:interface:tmds:1.0 TMDS DATA_P" *) output [2:0]TMDS_Data_p;
  (* x_interface_info = "digilentinc.com:interface:tmds:1.0 TMDS DATA_N" *) output [2:0]TMDS_Data_n;
  output oen;
  (* x_interface_info = "xilinx.com:signal:reset:1.0 AsyncRst_n RST" *) (* x_interface_mode = "slave AsyncRst_n" *) (* x_interface_parameter = "XIL_INTERFACENAME AsyncRst_n, POLARITY ACTIVE_LOW, INSERT_VIP 0" *) input aRst_n;
  (* x_interface_info = "xilinx.com:interface:vid_io:1.0 RGB DATA" *) (* x_interface_mode = "slave RGB" *) input [23:0]vid_pData;
  (* x_interface_info = "xilinx.com:interface:vid_io:1.0 RGB ACTIVE_VIDEO" *) input vid_pVDE;
  (* x_interface_info = "xilinx.com:interface:vid_io:1.0 RGB HSYNC" *) input vid_pHSync;
  (* x_interface_info = "xilinx.com:interface:vid_io:1.0 RGB VSYNC" *) input vid_pVSync;
  (* x_interface_info = "xilinx.com:signal:clock:1.0 PixelClk CLK" *) (* x_interface_mode = "slave PixelClk" *) (* x_interface_parameter = "XIL_INTERFACENAME PixelClk, FREQ_HZ 100000000, FREQ_TOLERANCE_HZ 0, PHASE 0.0, INSERT_VIP 0" *) input PixelClk /* synthesis syn_isclock = 1 */;
  (* x_interface_info = "xilinx.com:signal:clock:1.0 SerialClk CLK" *) (* x_interface_mode = "slave SerialClk" *) (* x_interface_parameter = "XIL_INTERFACENAME SerialClk, ASSOCIATED_RESET aRst:aRst_n:pRst:pRst_n, FREQ_HZ 100000000, FREQ_TOLERANCE_HZ 0, PHASE 0.0, INSERT_VIP 0" *) input SerialClk /* synthesis syn_isclock = 1 */;
endmodule
