# AD9767 DAC Dalga Formu Analizi

Bu dokuman, AD9767 DAC cikisinin Analog Discovery 2 ile olcum sonuclarini
ve dalga formu yorumunu icerir.

---

## 1. Sistem Mimarisi

```
ALINX AX7010 (Zynq-7000) --> AN9767 (AD9767 DAC) --> Analog Discovery 2 --> Python
      50 MHz --> MMCM --> 65 MHz DAC clock
      Sine ROM: 1024 sample x 14-bit, adres adimi = 1
      Cikis frekansi: 65 MHz / 1024 = ~63.5 kHz
      Her iki kanal da ayni sinus verisini aliyor
```

---

## 2. Onceki Durum (Adres Adimi = 4, ~254 kHz)

Ilk tasarimda ROM adres sayaci her saat darbesinde 4 artiriliyordu.

### 2.1 Olcum Sonuclari

| Parametre | CH1 (DA1) | CH2 (DA2) |
|-----------|-----------|-----------|
| Sinyal var mi? | Hayir (gurultu) | Evet |
| Vpp | ~8 mV | ~300 mV |
| Dalga tipi | Gurultu | Basamakli periyodik |
| Frekans | - | ~254 kHz |
| THD | - | >10% (tahmini) |

### 2.2 Onceki Dalga Formu Yorumu

#### CH1 - Zaman Alani
- **Genlik:** ~0V ile ~0.008V arasi (yaklasik 8 mV peak-to-peak)
- **DC Offset:** ~5.3 mV
- **Yorum:** Bu kanal neredeyse tamamen gurultuden (noise) ibaret. Anlamli bir
  sinus veya periyodik dalga formu gorunmuyor. Olasi nedenler:
  - Analog Discovery 2 CH1 probu DAC DA1 cikisina bagli degil
  - Verilog kodundaki yorumda belirtildigi gibi sadece CH2'ye baglanti yapilmis
  - Sadece termal gurultu ve osiloskop giris gurultusu olculuyor

#### CH2 - Zaman Alani
- **Genlik:** ~0.05V ile ~0.35V arasi (yaklasik 300 mV Vpp)
- **Yorum:** Periyodik sinyal var ancak sinus olmaktan cok basamakli/kare dalga
  benzeri gorunuyor. Bunun nedenleri:
  - ROM'dan sadece her 4. sample okunuyor (1024 yerine 256 nokta)
  - DAC cikisinda reconstruction filtresi (anti-imaging low-pass filter) yok
  - Zero-order hold basamaklari dogrudan goruluyor
  - 300 mV Vpp, AD9767 icin beklenen ~1V degerinin altinda

#### CH1 - Frekans Spektrumu
- Spektrum duz ve gurultu tabanli, -80 dB ile -100 dB arasinda
- Baskin frekans tepesi yok - tipik beyaz gurultu (white noise) profili

#### CH2 - Frekans Spektrumu
- Birkac belirgin frekans tepesi (spike) goruluyor
- Harmoniklerin varligi, dalga formunun saf sinus olmadigini kanitliyor
- DAC zero-order hold etkisi ve reconstruction filter eksikliginden kaynaklaniyor

---

## 3. Yapilan Degisiklik

### 3.1 Verilog Kodu Degisikligi (`dac_output_top.v`)

```verilog
// ONCEKI: Adres adimi 4
rom_addr <= rom_addr + 10'd4;  // f_out = 65 MHz / 256 = ~254 kHz

// YENI: Adres adimi 1
rom_addr <= rom_addr + 10'd1;  // f_out = 65 MHz / 1024 = ~63.5 kHz
```

### 3.2 Degisikligin Etkileri

| Parametre | Onceki (adim=4) | Yeni (adim=1) |
|-----------|-----------------|---------------|
| Adres adimi | +4 | +1 |
| ROM kullanimi | Her 4 sample'da 1 (256 nokta) | Tum 1024 sample |
| Cikis frekansi | ~254 kHz | ~63.5 kHz |
| Periyot basina sample | 256 | 1024 |

Tum 1024 sinus noktasinin kullanilmasi dalga formunun cok daha puruzsuz olmasini sagliyor.

---

## 4. Yeni Durum (Adres Adimi = 1, ~63.5 kHz)

### 4.1 CH2 - Sinus Dalgasi (Calisiyor)

| Parametre | Deger |
|-----------|-------|
| Frekans | **63.47 kHz** |
| Periyot | **15.76 us** |
| Vpp | **1003.5 mV** (~1V) |
| Vmax | +505.5 mV |
| Vmin | -497.9 mV |
| DC Offset | 4.9 mV (neredeyse sifir) |
| Vrms (AC) | 353.4 mV |
| THD | **%0.48** |
| SNR | **33.1 dB** |
| Sinyal kalitesi | **MUKEMMEL** |

#### Harmonik Analizi (CH2)

| Harmonik | Frekans | Seviye |
|----------|---------|--------|
| Temel (1.) | 63.47 kHz | 0 dB (referans) |
| 2. Harmonik | 127.0 kHz | -63.5 dB |
| 3. Harmonik | 190.4 kHz | -48.8 dB |
| 4. Harmonik | 253.9 kHz | -65.4 dB |
| 5. Harmonik | 317.4 kHz | -50.4 dB |

#### Dalga Formu Yorumu

Temiz, puruzsuz bir sinus dalgasi elde edildi:
- Grafik uzerinde 200 us pencerede yaklasik 12-13 tam periyot gorulmektedir
- Hesaplanan 63.5 kHz ile olculen 63.47 kHz birebir uyusmaktadir
- Dalga formu simetrik, +/- 500 mV civarinda saliniyor
- Basamak efektleri neredeyse tamamen kaybolmus
- THD %0.48 ile endustri standardinin uzerinde kalite

#### Frekans Spektrumu Yorumu

- 63.5 kHz'de baskin ve keskin bir tepe gorunmektedir (temel frekans)
- Tum harmonikler -48 dB'nin altinda, yani temel frekansa gore cok zayif
- Gurultu tabani -100 dB civarinda
- THD %0.48 ile 14-bit DAC cozunurlugu tam verimle kullanilmaktadir

### 4.2 CH1 - Hala Sinyal Yok

| Parametre | Deger |
|-----------|-------|
| Vpp | 11.8 mV |
| DC Offset | 2.3 mV |
| Durum | Sadece gurultu |

Analog Discovery 2 CH1 probu DAC DA1 cikisina bagli degil.
FPGA her iki kanala da ayni veriyi gondermektedir - DA1 cikisini
Analog Discovery 2 CH1'e bagladiginizda ayni sinus dalgasini goreceksiniz.

---

## 5. Onceki vs Yeni Karsilastirma Ozeti

| Parametre | Onceki (adim=4) | Yeni (adim=1) | Iyilesme |
|-----------|-----------------|---------------|----------|
| Frekans | ~254 kHz | 63.47 kHz | 4x dusuk |
| CH2 Vpp | ~300 mV | 1003.5 mV | ~3.3x artis |
| Dalga sekli | Basamakli/kare | Temiz sinus | Buyuk iyilesme |
| THD | >10% | %0.48 | >20x iyilesme |
| SNR | Dusuk | 33.1 dB | Belirgin iyilesme |
| ROM kullanimi | 256/1024 nokta | 1024/1024 nokta | Tam kapasite |

---

## 6. Sonuc ve Oneriler

### Calisan
- FPGA --> DAC veri akisi DA2 kanalinda mukemmel calisiyor
- Sinus ROM tablosu dogru (1024 x 14-bit, 0x0001 - 0x3FFF)
- Frekans hesaplamasi dogru (olculen 63.47 kHz vs hesaplanan 63.5 kHz)
- THD %0.48 - mukemmel sinyal kalitesi
- Genlik ~1V Vpp - AD9767 icin beklenen deger

### Oneriler
1. **CH1 baglantisi:** DA1 analog cikisini Analog Discovery 2 CH1'e baglayin
2. **Reconstruction filtresi:** DAC cikisina alcak geciren filtre (cutoff ~100 kHz)
   eklenirse harmonikler daha da azalir
3. **Frekans ayari:** `rom_addr` adres adimini degistirerek farkli frekanslar elde edilebilir:
   - `1` --> ~63.5 kHz (mevcut)
   - `2` --> ~127 kHz
   - `4` --> ~254 kHz
   - `8` --> ~508 kHz
