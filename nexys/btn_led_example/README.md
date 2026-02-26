## Claude Code Prompt

Bu projeyi sifirdan olusturmak, derlemek ve karta yuklemek icin asagidaki prompt'u kullanabilirsiniz:

```
[ISTERLER.md dosya yolu] dosyasini oku. Masaustume bu isterlere gore
Nexys Video FPGA projesi olustur (btn_led_top.v, nexys_video_btn_led.xdc,
build_and_program.tcl, README.md). Sonra Vivado ile sentez, implementation ve
bitstream uret. Bitstream hazir olunca Vivado GUI'yi Hardware Manager acik
sekilde baslat ki karti programlayabileyim.
```

---

# Buton ile LED Kontrol Sistemi - Nexys Video

## Proje Bilgileri

| Ozellik | Deger |
|---------|-------|
| Proje Adi | Buton ile LED Kontrol (3 Modlu) |
| Kart | Digilent Nexys Video (Artix-7 XC7A200T-1SBG484C) |
| Arac | Xilinx Vivado 2025.1 |
| Dil | Verilog |
| Tarih | 23 Subat 2026 |
| Durum | Tamamlandi - Kartta Test Edildi |

---

## 1. Projenin Amaci

Nexys Video karti uzerindeki 5 buton (BTNU, BTND, BTNL, BTNR, BTNC) kullanilarak 8 LED'in 3 farkli modda kontrol edilmesini saglayan interaktif bir dijital sistemdir.

### Gereksinim Listesi (Requirements)

#### Fonksiyonel Gereksinimler

| ID | Gereksinim | Oncelik | Durum |
|----|-----------|---------|-------|
| FR-01 | Sistem 3 farkli modda calisabilmeli | Zorunlu | Tamamlandi |
| FR-02 | BTNU butonuna basildiginda Pozisyon Moduna gecilmeli | Zorunlu | Tamamlandi |
| FR-03 | BTND butonuna basildiginda Volume Moduna gecilmeli | Zorunlu | Tamamlandi |
| FR-04 | BTNC butonuna basildiginda tum LED'ler yanmali | Zorunlu | Tamamlandi |
| FR-05 | Pozisyon Modunda BTNL ile LED sola kaymali | Zorunlu | Tamamlandi |
| FR-06 | Pozisyon Modunda BTNR ile LED saga kaymali | Zorunlu | Tamamlandi |
| FR-07 | Volume Modunda BTNL ile LED sayisi artmali | Zorunlu | Tamamlandi |
| FR-08 | Volume Modunda BTNR ile LED sayisi azalmali | Zorunlu | Tamamlandi |
| FR-09 | Pozisyon degeri 0-7 arasinda sinirlandirilmali (clamp) | Zorunlu | Tamamlandi |
| FR-10 | Volume degeri 1-8 arasinda sinirlandirilmali (clamp) | Zorunlu | Tamamlandi |
| FR-11 | "Tumunu Yak" modunda BTNL/BTNR etkisiz olmali | Zorunlu | Tamamlandi |
| FR-12 | CPU Reset butonu sistemi baslangic durumuna getirmeli | Zorunlu | Tamamlandi |

#### Teknik Gereksinimler

| ID | Gereksinim | Oncelik | Durum |
|----|-----------|---------|-------|
| TR-01 | Buton sinyalleri 2-FF ile senkronize edilmeli (metastabilite onleme) | Zorunlu | Tamamlandi |
| TR-02 | ~10ms debounce suresi uygulanmali (2^20 clock dongusu @ 100 MHz) | Zorunlu | Tamamlandi |
| TR-03 | Yukselen kenar algilama ile tek pulse uretilmeli | Zorunlu | Tamamlandi |
| TR-04 | 100 MHz sistem saati kullanilmali | Zorunlu | Tamamlandi |
| TR-05 | Timing constraint'ler karsilanmali (WNS > 0) | Zorunlu | Tamamlandi |

---

## 2. Sistem Mimarisi

```
  +--------------------------------------------------------------+
  |                      btn_led_top                              |
  |                                                               |
  |  +---------+    +--------------+    +-------------------+    |
  |  |  BTNU   +--->|  Debounce +  +--->|                   |    |
  |  |  BTND   +--->|  Edge Detect +--->|   Mod Secim       |    |
  |  |  BTNL   +--->|  (5 adet)    +--->|   State Machine   |    |
  |  |  BTNR   +--->|              +--->|                   |    |
  |  |  BTNC   +--->|  ~10ms       +--->|  +-----------+   |    |
  |  +---------+    |  debounce    |    |  | Pozisyon  |   |    |
  |                 +--------------+    |  | Sayaci    |   |    |
  |                                     |  | (pos:0-7) |   |    |
  |                                     |  +-----------+   |    |
  |                                     |  | Volume    |   |    |
  |                                     |  | Sayaci    |   |    |
  |                                     |  | (vol:1-8) |   |    |
  |                                     |  +-----+-----+   |    |
  |                                     +--------+----------+    |
  |                                              |               |
  |                                              v               |
  |                                     +-------------------+    |
  |                                     |   LED Cikis       |    |
  |                                     |   Mantigi         |    |
  |                                     |                   |    |
  |                                     | Pozisyon: 1<<pos  |    |
  |                                     | Volume: FF>>(8-v) |    |
  |                                     | Hepsi: 0xFF       |    |
  |                                     +--------+----------+    |
  |                                              |               |
  |                                              v               |
  |                                        +----------+          |
  |                                        | LED[7:0] |          |
  |                                        +----------+          |
  +--------------------------------------------------------------+
```

### Modullerin Aciklamasi

#### 2.1 Debounce + Edge Detect Modulu (`debounce_edge`)

Her buton icin ayri bir instance olusturulur (toplam 5 adet).

**3 asamali islem:**
1. **Senkronizasyon (2-FF):** Buton sinyali iki flip-flop ile saat alanina senkronize edilir. Metastabilite onlenir.
2. **Debounce:** Sinyal 10ms boyunca kararli kalmazsa sayac sifirlanir. Kararli kalirsa yeni deger kabul edilir. Sayac genisligi: 20-bit (2^20 = 1,048,576 clock ~ 10.5ms @ 100 MHz)
3. **Edge Detection:** Onceki ve simdiki kararli deger karsilastirilir. Yukselen kenar (0->1) algilandiginda tek bir clock pulse uretilir.

```
  Fiziksel Buton:   ---+  +-+-+------+  +-+---
                       +--+ + +      +--+ +
                       <-bounce->     <bounce>

  Debounce Sonrasi: -----+                +------
                         +----------------+

  Edge Detect:      -----+-----------------+------
                          # (tek pulse)     #
```

#### 2.2 Mod State Machine

3 durum arasinda gecis:

```
         BTNU                    BTND                   BTNC
          |                       |                      |
          v                       v                      v
  +---------------+      +---------------+      +---------------+
  |   POZISYON    |<---->|    VOLUME     |<---->|   HEPSI YAK   |
  |   MODU        |      |    MODU       |      |               |
  |  pos: 0-7     |      |  vol: 1-8     |      |  LED = 0xFF   |
  |  BTNL: pos+1  |      |  BTNL: vol+1  |      |  (BTNL/BTNR   |
  |  BTNR: pos-1  |      |  BTNR: vol-1  |      |   etkisiz)    |
  +---------------+      +---------------+      +---------------+
```

#### 2.3 LED Cikis Mantigi (Combinational)

| Mod | Formul | Ornek |
|-----|--------|-------|
| Pozisyon | `1 << pos` | pos=3 -> `00001000` |
| Volume | `0xFF >> (8 - vol)` | vol=4 -> `00001111` |
| Hepsi Yak | `0xFF` | `11111111` |

---

## 3. Pin Atamalari (FPGA I/O)

### Girisler

| Sinyal | FPGA Pini | I/O Standardi | Aciklama |
|--------|-----------|---------------|----------|
| `clk` | R4 | LVCMOS33 | 100 MHz sistem saati |
| `cpu_resetn` | G4 | LVCMOS15 | Active-low reset butonu |
| `btnu` | F15 | LVCMOS12 | Yukari - Pozisyon moduna gec |
| `btnd` | D22 | LVCMOS12 | Asagi - Volume moduna gec |
| `btnl` | C22 | LVCMOS12 | Sol - Sola hareket / Artir |
| `btnr` | D14 | LVCMOS12 | Sag - Saga hareket / Azalt |
| `btnc` | B22 | LVCMOS12 | Orta - Tum LED'leri yak |

### Cikislar

| Sinyal | FPGA Pini | I/O Standardi | Aciklama |
|--------|-----------|---------------|----------|
| `led[0]` | T14 | LVCMOS25 | LD0 |
| `led[1]` | T15 | LVCMOS25 | LD1 |
| `led[2]` | T16 | LVCMOS25 | LD2 |
| `led[3]` | U16 | LVCMOS25 | LD3 |
| `led[4]` | V15 | LVCMOS25 | LD4 |
| `led[5]` | W16 | LVCMOS25 | LD5 |
| `led[6]` | W15 | LVCMOS25 | LD6 |
| `led[7]` | Y13 | LVCMOS25 | LD7 |

### Konfigurasyon

```
CONFIG_VOLTAGE = 3.3V
CFGBVS = VCCO
```

---

## 4. Kullanim Kilavuzu

### 4.1 Pozisyon Modu (BTNU)

Tek bir LED yanar. BTNL/BTNR ile pozisyonu kaydirilir.

```
  Baslangic:  *ooooooo  (LD0 yanar)
  BTNL:       o*oooooo  (LD1'e kayar)
  BTNL:       oo*ooooo  (LD2'ye kayar)
  BTNR:       o*oooooo  (LD1'e geri doner)
  ...
  BTNL x6:   ooooooo*  (LD7'de - sinir)
  BTNL:       ooooooo*  (LD7'de kalir, daha fazla kaymaz)
```

### 4.2 Volume Modu (BTND)

LED'ler sagdan sola bar seklinde dolar (ses seviyesi kontrolu gibi).

```
  Baslangic:  *ooooooo  (1 LED, vol=1)
  BTNL:       **oooooo  (2 LED, vol=2)
  BTNL:       ***ooooo  (3 LED, vol=3)
  BTNL:       ****oooo  (4 LED, vol=4)
  BTNR:       ***ooooo  (3 LED, vol=3)
  ...
  BTNL x5:   ********  (8 LED - sinir, max)
  BTNR x7:   *ooooooo  (1 LED - sinir, min)
```

### 4.3 Tumunu Yak Modu (BTNC)

BTNC'ye basildiginda 8 LED birden yanar. BTNL ve BTNR bu modda etkisizdir.

```
  BTNC:       ********  (tum LED'ler yanar)
```

### 4.4 Sinir Korumasi (Clamping)

| Mod | Sinir | BTNL | BTNR |
|-----|-------|------|------|
| Pozisyon | pos=7 (LD7) | Degismez | Saga kayar |
| Pozisyon | pos=0 (LD0) | Sola kayar | Degismez |
| Volume | vol=8 (hepsi) | Degismez | Bir LED azalir |
| Volume | vol=1 (min) | Bir LED artar | Degismez |

---

## 5. Derleme Sonuclari

### 5.1 Asamalar

| Asama | Durum | Hata | Uyari |
|-------|-------|------|-------|
| Sentez (Synthesis) | Basarili | 0 | 0 |
| Yerlestirme (Implementation) | Basarili | 0 | 0 |
| Bitstream Uretimi | Basarili | 0 | 0 |
| Karta Yukleme (Programming) | Basarili | 0 | 0 |

### 5.2 Kaynak Kullanimi (Post-Implementation)

| Kaynak | Kullanim | Mevcut | Oran |
|--------|----------|--------|------|
| Slice LUT | 78 | 134,600 | %0.06 |
| Slice Register (FF) | 129 | 269,200 | %0.05 |
| Slice | 52 | 33,650 | %0.15 |
| Bonded IOB | 15 | 285 | %5.26 |
| BUFG (Clock) | 1 | 32 | %3.13 |
| Block RAM | 0 | 365 | %0.00 |
| DSP | 0 | 740 | %0.00 |

### 5.3 Primitive Kullanimi

| Primitive | Adet | Kategori |
|-----------|------|----------|
| FDRE | 128 | Flip-Flop |
| FDSE | 1 | Flip-Flop |
| LUT1 | 7 | LUT |
| LUT2 | 3 | LUT |
| LUT3 | 7 | LUT |
| LUT4 | 31 | LUT |
| LUT5 | 9 | LUT |
| LUT6 | 27 | LUT |
| CARRY4 | 25 | Carry Logic |
| IBUF | 7 | I/O |
| OBUF | 8 | I/O |
| BUFG | 1 | Clock |

### 5.4 Zamanlama (Timing) - Post-Route

| Metrik | Deger | Durum |
|--------|-------|-------|
| Saat Frekansi | 100 MHz (10 ns period) | |
| WNS (Worst Negative Slack) | **5.144 ns** | MET |
| WHS (Worst Hold Slack) | **0.166 ns** | MET |
| WPWS (Worst Pulse Width Slack) | **4.500 ns** | MET |
| Toplam Failing Endpoint | **0** | BASARILI |

**Kritik Yol:** `u_deb_btnr/btn_stable_reg` -> `pos_reg[2]` (4.904 ns, 3 logic level)

---

## 6. Dosya Yapisi

```
btn_led_example/
|
|-- README.md                     # Bu dokuman
|-- btn_led_top.v                 # Ana Verilog modulu (btn_led_top + debounce_edge)
|-- nexys_video_btn_led.xdc       # FPGA pin atamalari (constraint dosyasi)
|-- build_and_program.tcl         # Vivado otomasyon scripti (sentez -> bitstream)
|
|-- output/
|   |-- btn_led_top.bit           # Hazir bitstream dosyasi (karta yuklenebilir)
|   |-- utilization_impl.rpt      # Kaynak kullanim raporu
|   +-- timing_impl.rpt           # Zamanlama raporu
|
+-- docs/
    +-- RAPOR_Button_LED.pdf      # Detayli proje raporu (diyagramli)
```

---

## 7. Hizli Baslangic

### Yontem 1: Hazir Bitstream ile (onerilen)

1. Vivado'yu ac
2. **Flow Navigator** > **Open Hardware Manager**
3. **Open Target** > **Auto Connect**
4. **Program Device** > `output/btn_led_top.bit` sec
5. **Program** butonuna bas

### Yontem 2: Sifirdan Derleme

```
vivado -mode batch -source build_and_program.tcl
```

Bu komut sirasiyla:
1. Proje olusturur (`C:/btn_led_build/`)
2. Kaynak dosyalari ekler
3. Sentez calistirir
4. Implementation calistirir
5. Bitstream uretir

Derleme tamamlandiginda bitstream dosyasi:
`C:/btn_led_build/btn_led_project.runs/impl_1/btn_led_top.bit`

---

## 8. Teknik Detaylar

### 8.1 Debounce Mekanizmasi

- **Senkronizasyon:** 2 kademeli flip-flop zinciri (async -> sync)
- **Sayac:** 20-bit (2^20 = 1,048,576 clock cycle)
- **Debounce suresi:** 1,048,576 / 100,000,000 = ~10.5 ms
- **Calisma:** Sinyal degistiginde sayac baslar. 10ms boyunca kararli kalirsa yeni deger kabul edilir. Aksi halde sayac sifirlanir.

### 8.2 Edge Detection

- Onceki kararli deger (`btn_prev`) ile simdiki (`btn_stable`) karsilastirilir
- `btn_pulse = btn_stable & ~btn_prev` (yukselen kenar -> tek clock pulse)

### 8.3 Mod Gecisleri

- Mod degistirme butonlari (BTNU/BTND/BTNC) hareket butonlarindan (BTNL/BTNR) onceliklidir
- Mod degistiginde ilgili sayac sifirlanir (pos=0, vol=1)
- Reset (cpu_resetn=0): mode=POSITION, pos=0, vol=1

---

## 9. Ogrenilen Kavramlar

| Kavram | Aciklama |
|--------|----------|
| Debouncing | Mekanik butonlarin guvenilir kullanimi icin sinyal filtreleme |
| Metastabilite Onleme | 2-FF senkronizasyon zinciri ile asenkron sinyallerin guvenli alinmasi |
| Edge Detection | Olay tabanli tetikleme - buton basildiginda tek pulse uretme |
| State Machine | Coklu mod yonetimi - durumlar arasi gecis |
| Bit Manipulasyonu | Shift (<<) ve mask (>>) islemleri ile LED kontrol |
| Sinir Korumasi (Clamping) | Gecersiz durumlarin onlenmesi |
| Combinational vs Sequential | LED cikis mantigi (combinational) vs durum mantigi (sequential) |

---

## 10. Kart Bilgisi

- **Kart:** Digilent Nexys Video Rev. A
- **FPGA:** Xilinx Artix-7 XC7A200T-1SBG484C
- **Sistem Saati:** 100 MHz (R4 pini)
- **Butonlar:** 5 adet push-button (LVCMOS12)
- **LED'ler:** 8 adet (LVCMOS25)
- **Programlama:** USB-JTAG (PROG portu)
