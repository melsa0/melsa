# Proje 2: Si5351 + AD9238 HDMI Osiloskop

## Proje Amaci

Bu proje, harici bir saat/sinyal kaynagi olan **Si5351** ile laboratuvar seviyesinde bir test dalgasi uretir; bu sinyal **AN9238** modulu uzerindeki **AD9238** (12-bit, iki kanalli, 65 MSPS) ADC'ye uygulanir ve orneklenen veri FPGA icinde islenerek **HDMI** uzerinden gercek zamanli dalga formu olarak goruntulenir.

## Donanim

| Birim | Aciklama |
|-------|----------|
| **AX7010** | Zynq-7000 XC7Z010CLG400-1 FPGA gelistirme karti |
| **AN9238** | AD9238 cift kanalli 12-bit 65MSPS ADC modulu |
| **Si5351** | I2C ile kontrol edilen coklu saat ureticisi |
| **Arduino** | Si5351'i kontrol eden mikrodenetleyici |
| **HDMI Monitor** | Dalga formlarini goruntulemek icin |

## Blok Diyagram

```
Arduino (I2C) --> Si5351 --> CLK0 --> AN9238 CH0 SMA --> AD9238 CH0 --+
                         --> CLK1 --> AN9238 CH1 SMA --> AD9238 CH1 --+
                                                                      |
           HDMI Monitor <-- rgb2dvi <-- Video Pipeline <-- FPGA <-----+
```

## Baglanti

### Arduino -> Si5351
| Arduino | Si5351 |
|---------|--------|
| SDA     | SDA    |
| SCL     | SCL    |
| 3.3V    | VIN    |
| GND     | GND    |

### Si5351 -> AN9238
| Si5351 | AN9238      |
|--------|-------------|
| CLK0   | CH0 SMA In  |
| CLK1   | CH1 SMA In  |

### AN9238 -> FPGA
AN9238 modulu AX7010 kartinin **J11** expansion soketine takilir.

### FPGA -> HDMI
AX7010 kartinin yerlesik HDMI cikisi kullanilir.

## Dosya Yapisi

```
si5351_ad9238_hdmi_project/
├── README.md                          # Bu dosya
├── arduino/
│   └── si5351_ad9238_test.ino         # Arduino Si5351 kontrol kodu
├── fpga/
│   ├── src/
│   │   ├── top_simplified.v           # FPGA top modul (si5351_ad9238_hdmi_top_test)
│   │   ├── waveform_display.v         # Dalga formu gosterim modulu (inferred BRAM)
│   │   └── test_square_wave_gen.v     # Opsiyonel dahili test sinyal ureteci
│   ├── constraints/
│   │   └── pins.xdc                   # Pin atama dosyasi (J11, HDMI, Clock, Reset)
│   ├── output/
│   │   └── si5351_ad9238_hdmi_top_test.bit  # Hazir bitstream dosyasi
│   ├── build_project.tcl              # Vivado otomatik build scripti
│   └── ...
└── docs/
```

## FPGA Tasarim Detaylari

### IP Coreleri
| IP | Aciklama |
|----|----------|
| **clk_wiz_0** | 50 MHz -> 74.25 MHz (piksel), 371.25 MHz (TMDS 5x), 65 MHz (ADC) |
| **rgb2dvi_0** | Digilent RGB-to-DVI HDMI encoder (TMDS serializer) |

### Moduller
| Modul | Dosya | Aciklama |
|-------|-------|----------|
| `si5351_ad9238_hdmi_top_test` | top_simplified.v | Ust seviye modul, tum bilesenleri baglar |
| `video_timing_720p` | top_simplified.v | 1280x720 @ 74.25 MHz video zamanlama ureteci |
| `grid_overlay` | top_simplified.v | Osiloskop izgarasi cizimi |
| `adc_sampler` | top_simplified.v | ADC ornekleme (1280 ornek, sonra bekleme) |
| `waveform_display` | waveform_display.v | Dalga formu bindirme (inferred dual-port BRAM) |
| `test_square_wave_gen` | test_square_wave_gen.v | Opsiyonel dahili test sinyali |

### Pin Atamalari
- **sys_clk**: U18 (50 MHz)
- **rst_n**: N15 (aktif dusuk reset)
- **HDMI**: N18 (CLK), V20/T20/N20 (DATA)
- **AD9238 CH0**: H17 (CLK), J20-G18 (DATA[11:0]) - J11
- **AD9238 CH1**: F17 (CLK), F16-K18 (DATA[11:0]) - J11
- **hdmi_oen**: V16

## Kullanim

### 1. FPGA Programlama
1. Vivado'yu acin
2. Hardware Manager -> Open Target -> Program Device
3. `fpga/output/si5351_ad9238_hdmi_top_test.bit` dosyasini secin
4. Program butonuna basin

### 2. Arduino Yukleme
1. Arduino IDE'yi acin
2. Library Manager'dan **Adafruit SI5351** kutuphanesini yukleyin
3. `arduino/si5351_ad9238_test.ino` dosyasini acin
4. Board ve Port secimini yapin
5. Upload butonuna basin
6. Serial Monitor'den frekans degistirebilirsiniz:
   - `1` -> ~667 kHz
   - `2` -> 1 MHz
   - `3` -> 2 MHz
   - `4` -> 5 MHz

### 3. Gozlem
- HDMI monitor'de siyah arka plan uzerinde:
  - **Koyu sari izgara** cizgileri
  - **Kirmizi dalga** (CH0 - Si5351 CLK0)
  - **Mavi dalga** (CH1 - Si5351 CLK1)

## Sifirdan Build Etme

Vivado 2025.1 yukluyse, `build_project.tcl` scriptini calistirarak projeyi sifirdan olusturabilirsiniz. Scriptteki `base_dir`, `src_dir`, `constr_dir` ve `ip_repo_path` yollarini kendi sisteminize gore duzenleyin.

```tcl
vivado -mode batch -source build_project.tcl
```

## Notlar

- XC7Z010'da sadece **2 MMCM** vardir. Bu tasarim 1 adet MMCM (clk_wiz_0 icinde) kullanir.
- AN9238 analog giris araligi: **-5V ... +5V** (op-amp on-uc ile)
- Si5351 cikisi **3.3V CMOS kare dalga** - ADC araliginin ~%33'unu kaplar
- ADC ornekleme hizi: ~65 MSPS (clk_wiz_0 clk_out3)
- Ekran goruntusu 1280x720 @ ~74.25 MHz
- Dalga formu aktif bolge: X=[9..1018], Y=[9..308] piksel
