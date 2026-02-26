# AD9767 -> AD9238 Loopback Proje Rehberi

Bu rehber, ALINX AX7010 uzerinde DAC-ADC loopback test projesinin mimarisini, modullerin calisma prensiplerini ve projeyi adim adim nasil kuracaginizi aciklar.

---

## 1. Proje Mimarisi

### 1.1 Sinyal Akisi

```
                     Analog Kablo
  FPGA (Sinus ROM)                      FPGA (HDMI Goruntu)
       |                                      ^
       v                                      |
  +----------+    +---------+    +----------+  |  +-----------+
  | DAC Gen  |--->| AD9767  |--->| AD9238   |--+->| Waveform  |---> HDMI 720p
  | (14-bit) |    | DAC     |    | ADC      |     | Display   |
  +----------+    | (J10)   |    | (J11)    |     +-----------+
                  +---------+    +----------+
```

### 1.2 Saat Dagitimi

Projede tek bir MMCM (Mixed-Mode Clock Manager) kullanilir. XC7Z010 cipinde toplam 2 MMCM bulunur, bu proje 1 tanesini kullanir.

```
                +-------------------+
  50 MHz ------>|                   |---> clk_out1: ~74.25 MHz  (HDMI Pixel)
  (U18)        |    clk_wiz_0      |---> clk_out2: ~371.25 MHz (TMDS 5x Serial)
               |    (MMCM)         |---> clk_out3: ~65 MHz     (ADC/DAC)
               +-------------------+
```

**MMCM Parametreleri:**
- Giris: 50 MHz (periyot = 20 ns)
- CLKFBOUT_MULT_F = 14.875
- CLKOUT0_DIVIDE_F = 10.000 -> 74.375 MHz (hedef: 74.25 MHz)
- CLKOUT1_DIVIDE = 2 -> 371.875 MHz (hedef: 371.25 MHz)
- CLKOUT2_DIVIDE = 11 -> 67.61 MHz (hedef: 65 MHz)

### 1.3 Video Pipeline

Video sinyali asagidaki sirayla islenir:

```
video_timing_720p -> grid_overlay -> waveform_display(CH0) -> waveform_display(CH1) -> hdmi_tx
     |                   |                    |                         |                  |
  Siyah arkaplan   Osiloskop       Yesil dalga formu        Mavi dalga formu      TMDS cikis
  + zamanlama      izgarasi             (CH0)                     (CH1)           HDMI'ya
```

---

## 2. Modul Detaylari

### 2.1 loopback_top (Top Modul)

Top modul, tum alt modulleri birbirine baglar. Onemli atamalar:

```verilog
// ADC ve DAC ayni saat ile calisir
assign ad9238_clk_ch0 = adc_dac_clk;  // ~65 MHz
assign ad9238_clk_ch1 = adc_dac_clk;
assign da1_clk = adc_dac_clk;
assign da1_wrt = adc_dac_clk;         // Write sinyali = clock
assign da1_data = dac_data;            // Her iki DAC kanali ayni veriyi alir
assign da2_data = dac_data;
```

**Reset mekanizmasi:** `sys_rst = ~rst_n | ~pll_locked`
- Buton birakildiginda VEYA MMCM kilitlenmediginde sistem resetlenir.

### 2.2 dac_square_gen (Sinus Dalga Ureteci)

Isme ragmen (eski isim korunmustur), bu modul ROM tabanli sinus dalga uretir.

**Calisma prensibi:**
1. `sin1024.mem` dosyasindan 1024 adet 14-bit hex deger BRAM'e yuklenir
2. Her saat darbesinde adres 4 artirilir (rom_addr += 4)
3. ROM'dan okunan deger dogrudan DAC verisine atanir

**Frekans hesabi:**
```
f_out = f_clk / (ROM_BOYUTU / ADRES_ADIMI)
f_out = 65 MHz / (1024 / 4) = 65 MHz / 256 = ~254 kHz
```

**Gorunen dalga sayisi (1280 orneklik pencerede):**
```
Gorunen periyot = 1280 / 256 = 5 tam dalga
```

**Frekans ayarlama:** `rom_addr + 10'd4` satirindaki `4` degerini degistirin:
- `1` -> ~63.5 kHz (~1.25 dalga)
- `2` -> ~127 kHz (~2.5 dalga)
- `4` -> ~254 kHz (~5 dalga)  [mevcut]
- `8` -> ~508 kHz (~10 dalga)

### 2.3 adc_sampler (ADC Ornekleyici)

3 durumlu bir FSM (Sonlu Durum Makinesi) ile calisir:

```
S_IDLE -> S_SAMPLE -> S_WAIT -> S_SAMPLE -> S_WAIT -> ...
```

- **S_IDLE:** Baslangic durumu, hemen S_SAMPLE'a gecer
- **S_SAMPLE:** 1280 adet ADC ornegi toplar (12-bit -> ust 8 bit alinir)
- **S_WAIT:** 25 milyon saat darbe bekler (~385 ms @ 65 MHz), sonra tekrar ornekler

Her ADC ornegi 12-bit olarak gelir, `adc_data[11:4]` ile ust 8 bite daraltilir ve RAM'e yazilir.

### 2.4 waveform_display (Dalga Formu Goruntuleyici)

**Cift portlu RAM:**
- Yazma portu: ADC saat alaninda (65 MHz), ornekleri depolar
- Okuma portu: Piksel saat alaninda (74.25 MHz), goruntu icin okur

**Goruntuleme bolges:** x=[9..1018], y=[9..308] (1010x300 piksel)

**Dalga cizimi:** 3 piksel kalinlikta cizgi
```verilog
wire wave_hit = (y_diff == 0) || (y_diff == 1) || (y_diff == -1);
```

**Renkler:**
- CH0 (loopback): Yesil (24'h00FF00)
- CH1: Acik Mavi (24'h0080FF)

### 2.5 video_timing_720p (720p Zamanlama Ureteci)

1280x720 @ ~74.25 MHz icin standart zamanlama parametreleri:

| Parametre | Yatay | Dikey |
|-----------|-------|-------|
| Active | 1280 | 720 |
| Front Porch | 110 | 5 |
| Sync | 40 | 5 |
| Back Porch | 220 | 20 |
| **Toplam** | **1650** | **750** |

Arkaplan rengi: Siyah (00, 00, 00) - osiloskop tarzi.

### 2.6 grid_overlay (Osiloskop Izgarasi)

Aktif bolge uzerinde izgaralar cizer:
- **Yatay cizgiler:** y=32 (ust), y=159 (orta), y=287 (alt/referans)
- **Dikey noktalar:** Her 10 pikselde bir, yalnizca tek satirlarda (noktali cizgi efekti)
- **Renk:** Koyu sari (RGB: 139, 129, 29)

### 2.7 hdmi_tx (HDMI/DVI Verici)

IP bagimliligi olmayan saf Verilog HDMI vericisi. Uc alt katmandan olusur:

**a) TMDS Encoder (8b/10b):**
- DVI standartina gore 8-bit video verisini 10-bit TMDS koduna donusturur
- Blanking periyodlarinda kontrol tokenlarini gonderir (hsync/vsync)
- DC dengesi icin running disparity takibi

**b) TMDS Serializer:**
- OSERDESE2 primitifini kullanarak 10-bit paralel veriyi seri hale getirir
- Master/Slave cascade modunda 10:1 DDR serilestirme
- 371.25 MHz seri saat ile 74.25 MHz piksel hizinda veri cikarimi

**c) Diferansiyel Cikis:**
- OBUFDS ile tek uclu sinyali TMDS diferansiyel ciftine donusturur
- Saat kanali icin 10'b0000011111 sabiti kullanilir (5x frekans olusturur)

---

## 3. Pin Atamalari

### 3.1 Sistem

| Sinyal | Pin | IO Standardi | Aciklama |
|--------|-----|-------------|----------|
| sys_clk | U18 | LVCMOS33 | 50 MHz sistem saati |
| rst_n | N15 | LVCMOS33 | Aktif-dusuk reset butonu |

### 3.2 HDMI

| Sinyal | Pin | IO Standardi |
|--------|-----|-------------|
| TMDS_clk_p | N18 | TMDS_33 |
| TMDS_data_p[0] | V20 | TMDS_33 |
| TMDS_data_p[1] | T20 | TMDS_33 |
| TMDS_data_p[2] | N20 | TMDS_33 |
| hdmi_oen | V16 | LVCMOS33 |

### 3.3 AD9238 ADC (J11 Header)

**Kanal 0:**

| Sinyal | Pin | J11 Header |
|--------|-----|-----------|
| clk_ch0 | H17 | PIN31 |
| data[0] | J20 | PIN19 |
| data[1] | H20 | - |
| data[2] | L16 | PIN22 |
| data[3] | L17 | PIN21 |
| data[4] | M17 | PIN24 |
| data[5] | M18 | PIN23 |
| data[6] | D19 | PIN26 |
| data[7] | D20 | PIN25 |
| data[8] | E18 | PIN28 |
| data[9] | E19 | PIN27 |
| data[10] | G17 | PIN30 |
| data[11] | G18 | PIN29 |

### 3.4 AD9767 DAC (J10 Header)

**DA1 (Kanal 1):**

| Sinyal | Pin | J10 Header |
|--------|-----|-----------|
| da1_clk | W19 | PIN3 |
| da1_wrt | W18 | PIN4 |
| da1_data[13] | R14 | PIN5 |
| da1_data[12] | P14 | PIN6 |
| ... | ... | ... |
| da1_data[0] | P15 | PIN18 |

### 3.5 Zamanlama Kisitlamalari

```tcl
# ADC/DAC ve piksel saat alanlari arasinda false path
set_false_path -from [get_clocks clk_out3] -to [get_clocks clk_out1]
set_false_path -from [get_clocks clk_out1] -to [get_clocks clk_out3]
```

Bu false path'ler, ADC/DAC saat alanindaki sinyallerin piksel saat alanina gecisinde zamanlama analizi yapmamasi gerektigini belirtir. Clock domain crossing dual-port RAM tarafindan yonetilir.

---

## 4. Adim Adim Kurulum

### 4.1 Donanim Kurulumu

1. ALINX AX7010 kartini hazirlayin
2. AN9767 DAC modulunu J10 header'a takin
3. AN9238 ADC modulunu J11 header'a takin
4. DAC Channel 1 (DA1) analog cikisini ADC Channel 0 (CH0) girisiyle BNC/jumper kablo ile baglayinbirr
5. HDMI kablosuyla monitore baglayin
6. USB-JTAG kablosuyla bilgisayara baglayin

### 4.2 Hizli Baslangic (Hazir Bitstream)

```tcl
# Vivado Tcl Console'da:
source <proje_yolu>/scripts/program_fpga.tcl
```

### 4.3 Sifirdan Derleme

**Yontem 1 - Batch Mod:**
```bash
"C:\Xilinx\2025.1\Vivado\bin\vivado.bat" -mode batch -source scripts/create_project.tcl
```

**Yontem 2 - GUI:**
1. Vivado'yu acin
2. Tools -> Run Tcl Script
3. `scripts/create_project.tcl` dosyasini secin
4. Script otomatik olarak projeyi olusturur, sentezler ve bitstream uretir

**Yontem 3 - Tcl Console:**
```bash
vivado -mode tcl -source scripts/create_project.tcl
```

### 4.4 FPGA Programlama

1. Vivado'da Hardware Manager'i acin
2. "Open Target" -> "Auto Connect"
3. Cihaza sag tiklayin -> "Program Device"
4. `output/loopback_top.bit` dosyasini secin
5. "Program" butonuna basin

Veya Tcl Console'da:
```tcl
source scripts/program_fpga.tcl
```

---

## 5. Beklenen Sonuc

HDMI ekranda asagidaki goruntu olusur:

```
+--------------------------------------------------+
|  Siyah arkaplan                                   |
|  +--------------------------------------------+  |
|  | Koyu sari izgarali osiloskop bolges         |  |
|  |                                             |  |
|  |  ~~~~ Yesil sinus dalgasi (CH0) ~~~~       |  |
|  |  - - - - - (referans cizgisi) - - - - -     |  |
|  |  ~~~~ Mavi sinus dalgasi (CH1) ~~~~        |  |
|  |                                             |  |
|  +--------------------------------------------+  |
|                                                   |
+--------------------------------------------------+
```

- **Yesil dalga (CH0):** DAC'dan cikip ADC'ye giren loopback sinyali
- **Mavi dalga (CH1):** ADC kanal 1 (bagli degilse duz cizgi veya gurultu)
- Ekranda ~5 tam sinus periyodu gorunur
- Ornekleme her ~385 ms'de bir yenilenir

---

## 6. Sorun Giderme

| Sorun | Olasi Neden | Cozum |
|-------|-------------|-------|
| Ekranda hic goruntu yok | HDMI baglantisi veya MMCM kilitlenmemis | Reset butonuna basin, HDMI kablosunu kontrol edin |
| Duz cizgi gorunuyor | DAC-ADC kablo baglantisi yanlis | Kablo baglantilarini kontrol edin, DA1 cikisi -> CH0 girisi |
| Dalga cok kucuk/buyuk | ADC giris seviyesi uygun degil | Analog sinyal seviyesini kontrol edin (0-3.3V arasi) |
| Dalga bozuk/gurultulu | Topraklama sorunu | GND baglantilarini kontrol edin, kisa kablo kullanin |
| Sentez hatasi | Dosya yolunda ozel karakter | Proje yolunda bosluk veya ozel karakter olmamali |

---

## 7. Kod Degisiklikleri Rehberi

### Frekans Degistirme
`loopback_top.v` icinde `dac_square_gen` modulunde:
```verilog
rom_addr <= rom_addr + 10'd4;  // Bu degeri degistirin
```

### Dalga Rengi Degistirme
`loopback_top.v` icinde waveform_display orneklemelerinde:
```verilog
.wave_color(24'h00FF00),  // CH0: Yesil -> istediginiz RGB degeri
.wave_color(24'h0080FF),  // CH1: Mavi -> istediginiz RGB degeri
```

### Farkli Dalga Formu Kullanma
`sin1024.mem` dosyasini degistirin. Format:
- Her satirda bir 14-bit hex deger
- 1024 satir
- Deger araligi: 0000 - 3FFF (orta nokta: 2000)
