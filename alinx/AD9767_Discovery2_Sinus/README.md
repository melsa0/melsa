# AD9767 DAC Sinus Dalga Cikisi + Analog Discovery 2 Olcum

ALINX AX7010 (XC7Z010CLG400-1) uzerinde ROM tabanli sinus dalga uretimi,
AD9767 DAC ile analog cikis ve Analog Discovery 2 ile canli olcum/kayit sistemi.

## Genel Bakis

```
FPGA (Sinus ROM) --> AD9767 DAC (J10) --> Analog Cikis --> Analog Discovery 2
                                                                    |
                                                              Python ile
                                                           canli izleme/kayit
```

FPGA icinde 1024 noktali sinus tablosu ROM'dan okunarak 14-bit DAC verisine donusturulur.
AD9767 DAC modulu bu dijital veriyi analog sinyale cevirir. Analog Discovery 2 ile
sinyal yakalanir, analiz edilir ve CSV formatinda kaydedilir.

## Donanim Gereksinimleri

| Bilesen | Aciklama |
|---------|----------|
| FPGA Karti | ALINX AX7010 (XC7Z010CLG400-1) |
| DAC Modulu | AN9767 (AD9767, 14-bit, J10 header) |
| Olcum Cihazi | Digilent Analog Discovery 2 |
| Yazilim | Vivado 2025.1+, WaveForms, Python 3 |
| Kablo | DAC analog cikisindan Discovery 2 CH1/CH2 girisi |

## Saat Yapisi

Tek MMCM ile 50 MHz -> ~65 MHz DAC clock.

## Sinyal Ozellikleri

| Parametre | Deger |
|-----------|-------|
| Dalga formu | Sinus (1024 noktali ROM) |
| DAC cozunurluk | 14-bit |
| Cikis frekansi | ~254 kHz |
| Vpp (olculen) | ~665 mV |
| THD (olculen) | ~2.85% |
| DC offset | ~5 mV |

## Proje Dosyalari

```
AD9767_Discovery2_Sinus/
├── src/
│   ├── dac_output_top.v       # Top modul + sinus ureteci
│   └── sin1024.mem            # 1024 noktali 14-bit sinus ROM verisi
├── constraints/
│   └── dac_output_pins.xdc    # AX7010 J10 pin atamalari
├── scripts/
│   ├── create_project.tcl     # Vivado proje + sentez + bitstream
│   └── program_fpga.tcl       # FPGA programlama
├── python/
│   ├── view_waveform.py       # Canli osiloskop (matplotlib grafik)
│   ├── capture_analyze.py     # Tek sefer yakalama + analiz + FFT
│   └── live_monitor.py        # Terminal canli monitor + CSV kayit
├── output/
│   └── dac_output_top.bit     # Hazir bitstream
├── docs/
│   └── proje_rehberi.md       # Detayli proje rehberi
└── README.md
```

## Hizli Baslangic

### 1. FPGA Programlama

```bash
# Hazir bitstream ile
vivado -mode tcl -source scripts/program_fpga.tcl

# veya sifirdan derleme
vivado -mode batch -source scripts/create_project.tcl
```

### 2. Baglanti

- AN9767 DAC modulunu J10 header'a takin
- DA1 analog cikisini Analog Discovery 2 CH1 girisi (1+) ile baglayinr
- GND baglantilarini yapinn

### 3. Olcum (3 farkli yontem)

**a) Canli Osiloskop Grafigi:**
```bash
python python/view_waveform.py
```
Matplotlib penceresi acilir, CH1 ve CH2 canli guncellenir.

**b) Tek Sefer Yakalama + Analiz:**
```bash
python python/capture_analyze.py
```
Vpp, frekans, THD, SNR ve harmonik analizi yapar. FFT grafigi kaydeder.

**c) Terminal Canli Monitor + CSV Kayit:**
```bash
python python/live_monitor.py
```
0.5 saniye arayla olcum yapar, terminalde gosterir, CSV dosyasina kaydeder.
Genlikle oynarken degisimleri anlik takip edebilirsiniz. Ctrl+C ile durdurun.

## Python Bagimliliklari

```bash
pip install numpy matplotlib
```

WaveForms SDK (`dwf.dll`) WaveForms kurulumu ile birlikte gelir.

## Olcum Sonuclari ve Sinyal Analizi

Proje test edilip Analog Discovery 2 ile olcum yapildiginda asagidaki sonuclar elde edilmistir:

### CH2 - DAC Cikisi (Analog Discovery 2 CH2'ye bagli)

| Parametre | Olcum | Yorum |
|-----------|-------|-------|
| Frekans | 253.91 kHz | Beklenen ~254 kHz ile birebir uyumlu. `65 MHz / (1024/4) = 253.9 kHz` hesabi dogrulanmistir. |
| Vpp | 665.5 mV | AD9767 DAC'in tipik analog cikis seviyesi. |
| Vrms (AC) | 231.4 mV | Saf sinus icin beklenen Vpp/(2*sqrt(2)) = 235 mV'a yakin. |
| DC Offset | 4.7 mV | Ihmal edilebilir seviyede, DAC cikisi iyi dengelenmis. |
| THD | 2.85% | Direkt DAC cikisi icin iyi kalite. Rekonstrüksiyon filtresi olmadan elde edilmistir. |
| SNR | 22.3 dB | Kabul edilebilir. Ortam gurultusu ve filtre eksikligi etkili. |
| 2. Harmonik | -36.0 dB | Temel frekansin cok altinda, iyi bastirilmis. |
| 3. Harmonik | -40.2 dB | Iyi bastirilmis. |
| 4. Harmonik | -44.6 dB | Cok iyi. |
| 5. Harmonik | -33.6 dB | Nispeten yuksek, DAC cikisindaki merdiven etkisinden kaynaklanir. |

### CH1 - Bagli Degil

| Parametre | Olcum |
|-----------|-------|
| Vpp | 7.8 mV |
| Yorum | Sadece gurultu. CH1'e kablo baglanmamisti. |

### Genel Degerlendirme

- **DAC dogru calisiyor.** Sinus frekansi ve dalga formu tasarimla birebir uyumlu.
- **THD %2.85** rekonstrüksiyon filtresi olmadan elde edilen iyi bir deger. DAC cikisinda
  merdiven seklindeki basamaklar (quantization noise) harmonik bozulmaya neden olur.
  Basit bir RC alcak geciren filtre (ornegin R=100 ohm, C=1nF, kesim ~1.6 MHz) eklenirse
  THD %1'in altina dusurulebilir.
- **Zaman domaininde** temiz sinus dalgasi gorulmektedir. ~20 us'lik pencerede ~5 tam
  periyot gorunur, bu da 254 kHz ile uyumludur.
- **FFT spektrumunda** 254 kHz'de belirgin temel frekans tepesi, harmoniklerin hepsi
  -30 dB'nin altinda gorulmektedir.
- **Sinyal stabilitesi** iyi: 60 saniyelik canli monitor kayitlarinda frekans 253.90-253.92 kHz
  araliginda, Vpp 663.5-666.2 mV araliginda kalmistir (dalgalanma < %0.5).
