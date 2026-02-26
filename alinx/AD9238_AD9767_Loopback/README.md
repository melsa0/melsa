# AD9767 -> AD9238 Loopback Test

ALINX AX7010 (XC7Z010CLG400-1) uzerinde DAC-ADC loopback testi ve HDMI osiloskop goruntusu.

## Genel Bakis

FPGA'dan uretilen sinus sinyali **AN9767 DAC** modulu uzerinden analog cikisa verilir, kablo ile **AN9238 ADC** modulune baglanarak geri okunur ve **HDMI 720p** ekranda dalga formu olarak gosterilir.

```
FPGA --> AD9767 DAC (J10) --> Analog Kablo --> AD9238 ADC (J11) --> FPGA --> HDMI 720p
```

## Donanim Gereksinimleri

| Bilesen | Aciklama |
|---------|----------|
| FPGA Karti | ALINX AX7010 (XC7Z010CLG400-1) |
| DAC Modulu | AN9767 (AD9767, 14-bit, J10 header) |
| ADC Modulu | AN9238 (AD9238, 12-bit, J11 header) |
| Ekran | HDMI destekli monitor (720p) |
| Kablo | DAC cikisindan ADC girisine analog baglanti |

## Saat Yapisi

Tek bir MMCM (clk_wiz_0) ile 50 MHz giris saatinden 3 saat uretilir:

| Saat | Frekans | Kullanim |
|------|---------|----------|
| clk_out1 | ~74.25 MHz | HDMI pixel clock (720p) |
| clk_out2 | ~371.25 MHz | TMDS 5x serial clock |
| clk_out3 | ~65 MHz | ADC/DAC ortak clock |

## Fiziksel Baglanti

- **AN9767 DAC** modulunu **J10** header'a takin
- **AN9238 ADC** modulunu **J11** header'a takin
- DAC Channel 1 (DA1) analog cikisini ADC Channel 0 (CH0) girisine kablo ile baglayin
- HDMI kablosu ile monitore baglayin

## Proje Dosyalari

```
AD9238_AD9767_Loopback/
├── src/
│   ├── loopback_top.v       # Top modul + alt moduller (sinus ureteci, zamanlama, grid)
│   ├── hdmi_tx.v            # Saf Verilog HDMI/DVI verici (TMDS + OSERDESE2)
│   ├── waveform_display.v   # Dalga formu goruntuleme (RAM + overlay)
│   └── sin1024.mem          # 1024 noktali sinus dalga ROM verisi (14-bit hex)
├── constraints/
│   └── loopback_pins.xdc    # Pin atamalari ve zamanlama kisitlamalari
├── scripts/
│   ├── create_project.tcl   # Vivado proje olusturma + sentez + bitstream
│   └── program_fpga.tcl     # FPGA programlama scripti
├── output/
│   └── loopback_top.bit     # Hazir bitstream dosyasi
└── README.md
```

## Kullanim

### Bitstream'den Programlama (Hizli)

Hazir bitstream dosyasi `output/loopback_top.bit` icindedir. Vivado Hardware Manager ile programlamak icin:

```tcl
source scripts/program_fpga.tcl
```

### Sifirdan Derleme

Vivado 2025.1 veya ustu gereklidir:

```bash
# Batch modda
vivado -mode batch -source scripts/create_project.tcl

# veya GUI'den: Tools -> Run Tcl Script -> create_project.tcl secin
```

Script otomatik olarak:
1. Vivado projesi olusturur
2. RTL kaynak dosyalarini ekler
3. clk_wiz_0 IP'sini olusturur ve yapilandirir
4. Kisitlama dosyasini ekler
5. Sentez calistirir
6. Implementasyon calistirir
7. Bitstream uretir

## Modul Aciklamalari

### loopback_top
Ana modul. Tum alt modulleri birbirine baglar. Sinus dalga uretecini, ADC ornekleyicisini, HDMI video zamanlamasini ve dalga formu goruntulecisini entegre eder.

### dac_square_gen (Sinus Ureteci)
ROM tabanli sinus dalga ureteci. `sin1024.mem` dosyasindan 1024 noktali tabloyu okur. Adres adimi 4 olarak ayarlanmistir (~254 kHz cikis frekansi).

### hdmi_tx
IP bagimliligi olmayan saf Verilog HDMI/DVI verici. TMDS 8b/10b kodlama, OSERDESE2 10:1 DDR serilestirme ve OBUFDS diferansiyel cikis kullanir.

### waveform_display
ADC'den okunan ornekleri cift portlu RAM'de depolar ve video akisi uzerine dalga formu cizer. CH0 yesil, CH1 acik mavi renkte gosterilir.

## Kaynak Kullanimi (XC7Z010)

| Kaynak | Kullanim |
|--------|----------|
| LUT | ~2% |
| Register | ~1% |
| BRAM | ~2% |
| MMCM | 1/2 (50%) |
| IOB | 61/100 (61%) |
