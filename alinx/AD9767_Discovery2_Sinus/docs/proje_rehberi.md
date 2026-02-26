# AD9767 Discovery2 Sinus - Proje Rehberi

Bu rehber, ALINX AX7010 uzerinde DAC sinus dalga cikisi ve Analog Discovery 2 ile
olcum sisteminin mimarisini, kodlarin calisma prensiplerini ve kullanimi aciklar.

---

## 1. Proje Mimarisi

### 1.1 Sinyal Akisi

```
  +-------------+     +----------+     +---------+     +------------------+
  | FPGA        |     | AD9767   |     | Analog  |     | PC               |
  | Sinus ROM   |---->| DAC      |---->| Disc. 2 |---->| Python/WaveForms |
  | (1024x14bit)|     | (J10)    |     | CH1/CH2 |     | Olcum + Kayit    |
  +-------------+     +----------+     +---------+     +------------------+
```

### 1.2 Saat Dagitimi

```
  50 MHz (U18) ----> MMCM (clk_wiz_0) ----> ~65 MHz DAC clock
```

Tek bir MMCM, tek bir cikis saati. XC7Z010'daki 2 MMCM'den sadece 1'i kullanilir.

---

## 2. FPGA Tasarimi

### 2.1 dac_output_top (Top Modul)

Minimal tasarim: sadece saat ureteci + sinus ureteci + DAC cikis atamalari.

```verilog
// Her iki DAC kanali ayni saat ve veriyi alir
assign da1_clk  = dac_clk;    // ~65 MHz
assign da1_wrt  = dac_clk;
assign da1_data = sine_data;   // 14-bit sinus
assign da2_clk  = dac_clk;
assign da2_wrt  = dac_clk;
assign da2_data = sine_data;
```

### 2.2 sine_gen (Sinus Ureteci)

ROM tabanli sinus dalga ureteci:

1. `sin1024.mem` dosyasindan 1024 adet 14-bit hex deger BRAM'e yuklenir
2. Her saat darbesinde adres 1 artirilir (tum 1024 sample kullanilir)
3. ROM cikisi dogrudan DAC verisine atanir

**Frekans hesabi:**
```
f_out = f_clk / (ROM_boyutu / adres_adimi)
f_out = 65 MHz / (1024 / 1) = 65 MHz / 1024 = ~63.5 kHz
```

**Frekans degistirme:** `dac_output_top.v` icinde `sine_gen` modulunde:
```verilog
rom_addr <= rom_addr + 10'd1;  // Bu degeri degistirin
```
- `1` -> ~63.5 kHz (mevcut)
- `2` -> ~127 kHz
- `4` -> ~254 kHz
- `8` -> ~508 kHz
- `16` -> ~1.016 MHz

### 2.3 sin1024.mem Format

- Her satirda bir 14-bit hexadecimal deger
- 1024 satir
- Deger araligi: 0001 - 3FFF
- Orta nokta (sifir gecisi): 2000
- sin1024.coe dosyasindan donusturulmustur

---

## 3. Pin Atamalari (J10 Header)

### Sistem

| Sinyal | Pin | Aciklama |
|--------|-----|----------|
| sys_clk | U18 | 50 MHz sistem saati |
| rst_n | N15 | Reset butonu (aktif-dusuk) |

### DAC Kanal 1 (DA1)

| Sinyal | Pin | J10 |
|--------|-----|-----|
| da1_clk | W19 | PIN3 |
| da1_wrt | W18 | PIN4 |
| da1_data[13..0] | R14..P15 | PIN5-PIN18 |

### DAC Kanal 2 (DA2)

| Sinyal | Pin | J10 |
|--------|-----|-----|
| da2_clk | U17 | PIN19 |
| da2_wrt | T16 | PIN20 |
| da2_data[13..0] | V18..B19 | PIN21-PIN34 |

Tum pinler LVCMOS33 IO standardi kullanir.

---

## 4. Python Araclari

### 4.1 view_waveform.py - Canli Osiloskop

Matplotlib ile canli osiloskop penceresi acar.

- CH1 (yesil) ve CH2 (mavi) zaman domaini grafigi
- Frekans ve Vpp olcumleri grafik uzerinde
- 100ms arayla guncellenir
- Pencereyi kapatarak durdurulur

**Ayarlar (script icinde):**
```python
SAMPLE_RATE = 10_000_000.0   # 10 MHz ornekleme
BUFFER_SIZE = 8192            # ornek sayisi
VOLTAGE_RANGE = 5.0           # +/- 2.5V
```

### 4.2 capture_analyze.py - Tek Sefer Analiz

Tek bir yakalama yapar ve detayli analiz cikarir:

- DC Offset, Vmin, Vmax, Vpp, Vrms
- Frekans (sifir gecisi yontemi)
- THD (Total Harmonic Distortion)
- SNR (Signal-to-Noise Ratio)
- 2. - 5. harmonik seviyeleri (dB)
- Sinus benzerligi (korelasyon)
- Zaman domaini + FFT spektrum grafigi (PNG olarak kaydeder)

### 4.3 live_monitor.py - Terminal Monitor + CSV Kayit

Terminal uzerinden canli olcum tablosu gosterir:

```
   # |      Zaman |    CH1 Vpp  CH1 Vrms    CH1 DC   CH1 Freq    THD |    CH2 Vpp  CH2 Vrms    CH2 DC   CH2 Freq    THD
   1 |   11:13:30 |     8.1 mV     1.1 mV    4.1 mV  2062.35 kHz 19.8% |   665.5 mV   231.4 mV    4.8 mV   253.91 kHz  2.9%
```

- 0.5 saniye arayla olcum
- CSV dosyasina otomatik kayit (`log_YYYYMMDD_HHMMSS.csv`)
- Ctrl+C ile durdurulur
- Excel veya Python ile sonradan analiz edilebilir

---

## 5. Adim Adim Kullanim

### 5.1 Donanim Kurulumu

1. AN9767 DAC modulunu AX7010 J10 header'a takin
2. Analog Discovery 2'yi USB ile PC'ye baglayin
3. DAC DA1 analog cikisini Discovery 2 **CH1 (1+)** girisiyle baglayin
4. DAC DA2 analog cikisini Discovery 2 **CH2 (2+)** girisiyle baglayin (istege bagli)
5. GND baglantilarini yapin

### 5.2 FPGA Programlama

```bash
# Hazir bitstream
vivado -mode tcl -source scripts/program_fpga.tcl

# veya sifirdan derleme (sentez + implementation + bitstream)
vivado -mode batch -source scripts/create_project.tcl
```

### 5.3 Olcum

```bash
# Canli grafik
python python/view_waveform.py

# Detayli analiz
python python/capture_analyze.py

# Terminal monitor (genlikle oynarken)
python python/live_monitor.py
```

---

## 6. Olcum Sonuclari

Proje test edildiginde elde edilen tipik degerler:

| Parametre | CH2 (DAC cikisi) |
|-----------|-------------------|
| Frekans | 63.47 kHz |
| Vpp | 1003.5 mV |
| Vrms (AC) | 353.4 mV |
| DC Offset | 4.9 mV |
| THD | 0.48% |
| SNR | 33.1 dB |
| 2. Harmonik | -63.5 dB |
| 3. Harmonik | -48.8 dB |
| 4. Harmonik | -65.4 dB |
| 5. Harmonik | -50.4 dB |
| Sinyal kalitesi | MUKEMMEL |

Detayli dalga formu analizi: [dalga_formu_analizi.md](dalga_formu_analizi.md)

---

## 7. Sorun Giderme

| Sorun | Cozum |
|-------|-------|
| Discovery 2 acilamiyor | WaveForms SDK kurulu mu kontrol edin, USB baglantisini kontrol edin |
| "Devices are busy" hatasi | WaveForms GUI veya baska Python scripti aciksa kapatin |
| CH1'de sinyal yok | Kabloyu CH1 (1+) girisiyle baglayinn, GND'yi kontrol edin |
| Dusuk Vpp | DAC analog cikisinin dogru pininden aldiginizdan emin olun |
| Frekans yanlis | FPGA programlanmis mi kontrol edin, reset butonuna basin |
