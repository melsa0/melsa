# Buton ile LED Kontrol Sistemi - Proje Isterleri

## Proje Tanimi

Nexys Video (Artix-7 XC7A200T) karti uzerinde 5 buton ile 8 LED'in 3 farkli modda kontrol edilmesi.

---

## 1. Donanim Isterleri

| ID | Ister | Kabul Kriteri |
|----|-------|---------------|
| HW-01 | Hedef kart Digilent Nexys Video Rev. A olmalidir | Part: xc7a200tsbg484-1 |
| HW-02 | Sistem saati 100 MHz olmalidir | R4 pini, LVCMOS33 |
| HW-03 | 5 adet buton girisi kullanilmalidir (BTNU, BTND, BTNL, BTNR, BTNC) | LVCMOS12 standardinda |
| HW-04 | 8 adet LED cikisi kullanilmalidir (LD0-LD7) | LVCMOS25 standardinda |
| HW-05 | CPU Reset butonu (active-low) desteklenmelidir | G4 pini, LVCMOS15 |
| HW-06 | FPGA konfigurasyon voltaji 3.3V, CFGBVS=VCCO olmalidir | XDC'de tanimli |

---

## 2. Fonksiyonel Isterler

### 2.1 Mod Yonetimi

| ID | Ister | Kabul Kriteri |
|----|-------|---------------|
| FN-01 | Sistem 3 modda calisabilmelidir: Pozisyon, Volume, Tumunu Yak | Her mod bagimsiz calisir |
| FN-02 | BTNU'ya basildiginda Pozisyon Moduna gecilmelidir | Pozisyon sayaci 0'a sifirlanir |
| FN-03 | BTND'ye basildiginda Volume Moduna gecilmelidir | Volume sayaci 1'e sifirlanir |
| FN-04 | BTNC'ye basildiginda Tumunu Yak Moduna gecilmelidir | 8 LED birden yanar (0xFF) |
| FN-05 | Herhangi bir moddan diger herhangi bir moda gecis mumkun olmalidir | BTNU/BTND/BTNC ile anlik gecis |
| FN-06 | Sistem acilista Pozisyon Modunda baslamalidir | pos=0, LD0 yanik |

### 2.2 Pozisyon Modu

| ID | Ister | Kabul Kriteri |
|----|-------|---------------|
| FN-10 | Ayni anda yalnizca 1 LED yanmalidir | LED = 1 << pos |
| FN-11 | BTNL'ye basildiginda LED bir pozisyon sola (ust bite dogru) kaymalidir | pos = pos + 1 |
| FN-12 | BTNR'ye basildiginda LED bir pozisyon saga (alt bite dogru) kaymalidir | pos = pos - 1 |
| FN-13 | Pozisyon degeri 0'dan asagi dusmemelidir | pos >= 0 (clamp) |
| FN-14 | Pozisyon degeri 7'den yukari cikmamalidir | pos <= 7 (clamp) |
| FN-15 | Sinir degerinde buton basildiginda LED konumu degismemelidir | Tasma yok |

### 2.3 Volume Modu

| ID | Ister | Kabul Kriteri |
|----|-------|---------------|
| FN-20 | LED'ler sagdan sola bar seklinde dolmalidir | LED = 0xFF >> (8 - vol) |
| FN-21 | BTNL'ye basildiginda bir LED daha yanmalidir | vol = vol + 1 |
| FN-22 | BTNR'ye basildiginda bir LED sonmelidir | vol = vol - 1 |
| FN-23 | Minimum 1 LED yanik kalmalidir | vol >= 1 (clamp) |
| FN-24 | Maksimum 8 LED yanabilmelidir | vol <= 8 (clamp) |
| FN-25 | Sinir degerinde buton basildiginda LED sayisi degismemelidir | Tasma yok |

### 2.4 Tumunu Yak Modu

| ID | Ister | Kabul Kriteri |
|----|-------|---------------|
| FN-30 | BTNC'ye basildiginda 8 LED birden yanmalidir | LED = 0xFF |
| FN-31 | Bu modda BTNL ve BTNR etkisiz olmalidir | Buton basilsa bile LED durumu degismez |

### 2.5 Reset

| ID | Ister | Kabul Kriteri |
|----|-------|---------------|
| FN-40 | CPU Reset basildiginda sistem baslangic durumuna donmelidir | mode=POZISYON, pos=0, vol=1 |
| FN-41 | Reset active-low olmalidir (cpu_resetn) | 0 = reset aktif, 1 = normal calisma |

---

## 3. Teknik Isterler

### 3.1 Buton Isleme

| ID | Ister | Kabul Kriteri |
|----|-------|---------------|
| TK-01 | Her buton sinyali 2 kademeli flip-flop ile senkronize edilmelidir | Metastabilite riski onlenir |
| TK-02 | Her butona en az 10ms debounce uygulanmalidir | 20-bit sayac @ 100 MHz (~10.5 ms) |
| TK-03 | Debounce sirasinda sinyal kararli degilse sayac sifirlanmalidir | Bouncing suresince yeni deger kabul edilmez |
| TK-04 | Her buton basiminda yalnizca tek bir clock-pulse uretilmelidir | Yukselen kenar algilama (edge detect) |
| TK-05 | Buton birakildiginda herhangi bir islem tetiklenmemelidir | Sadece 0->1 gecisi gecerli |

### 3.2 State Machine

| ID | Ister | Kabul Kriteri |
|----|-------|---------------|
| TK-10 | Mod degistirme butonlari (BTNU/BTND/BTNC) hareket butonlarindan (BTNL/BTNR) oncelikli olmalidir | Ayni anda basilirsa mod gecisi uygulanir |
| TK-11 | Mod degistiginde ilgili sayac baslangic degerine sifirlanmalidir | Pozisyon: pos=0, Volume: vol=1 |
| TK-12 | Tum durum degisiklikleri saat'in yukselen kenarinda gerceklesmelidir | Senkron tasarim |
| TK-13 | LED cikis mantigi kombinasyonel olmalidir | always @(*) blogu |

---

## 4. Performans Isterleri

| ID | Ister | Kabul Kriteri |
|----|-------|---------------|
| PF-01 | Tasarim 100 MHz'de timing constraint'leri karsilamalidir | WNS > 0 ns |
| PF-02 | Hold violation olmamalidir | WHS > 0 ns |
| PF-03 | Sentez ve implementation hatasiz tamamlanmalidir | 0 error |
| PF-04 | Buton basimina tepki suresi < 15 ms olmalidir | Debounce (~10ms) + 1 clock |

---

## 5. Tasarim Kisitlari

| ID | Kisit | Gerekce |
|----|-------|---------|
| KS-01 | Tek bir Verilog dosyasinda tum moduller tanimlanmalidir | Basitlik, tasinabilirlik |
| KS-02 | PLL/MMCM kullanilmamalidir, dogrudan 100 MHz BUFG ile calisilmalidir | Gereksiz karmasiklik onleme |
| KS-03 | Block RAM / DSP kullanilmamalidir | Sadece LUT ve FF yeterlidir |
| KS-04 | Vivado TCL scripti ile sifirdan derlenebilir olmalidir | Tekrarlanabilir build |
| KS-05 | Harici IP veya kutuphane bagimililigi olmamalidir | Saf Verilog RTL |

---

## 6. Test ve Dogrulama Isterleri

| ID | Ister | Yontem |
|----|-------|--------|
| TV-01 | Pozisyon Modunda LED'in 0'dan 7'ye kaydigini dogrulayin | Kart uzerinde BTNL ile test |
| TV-02 | Pozisyon Modunda LED'in 7'den 0'a geri dondugunu dogrulayin | Kart uzerinde BTNR ile test |
| TV-03 | Pozisyon sinirlarinda (0 ve 7) LED'in sabit kaldigini dogrulayin | Sinir degerinde ek basim |
| TV-04 | Volume Modunda bar'in 1'den 8'e doldugunu dogrulayin | Kart uzerinde BTNL ile test |
| TV-05 | Volume Modunda bar'in 8'den 1'e bosaldigini dogrulayin | Kart uzerinde BTNR ile test |
| TV-06 | Volume sinirlarinda (1 ve 8) LED sayisinin sabit kaldigini dogrulayin | Sinir degerinde ek basim |
| TV-07 | BTNC ile 8 LED'in birden yandigini dogrulayin | Kart uzerinde gorsel kontrol |
| TV-08 | Tumunu Yak modunda BTNL/BTNR'nin etkisiz oldugunu dogrulayin | Butonlara basildiginda degisim yok |
| TV-09 | Modlar arasi geciste sayaclarin sifirlandigini dogrulayin | Mod degistirip LED durumunu kontrol |
| TV-10 | CPU Reset ile sistemin baslangica dondugunu dogrulayin | Reset sonrasi LD0 yanik, Pozisyon Modu |
| TV-11 | Hizli buton basimlarinda bounce etkisi olmamalidir | Arka arkaya hizli basimlar |
| TV-12 | Timing raporunda violation olmamalidir | WNS > 0, WHS > 0 |

---

## 7. Teslimat Listesi

| # | Teslimat | Dosya |
|---|----------|-------|
| 1 | Verilog kaynak kodu | `btn_led_top.v` |
| 2 | Pin constraint dosyasi | `nexys_video_btn_led.xdc` |
| 3 | Build otomasyon scripti | `build_and_program.tcl` |
| 4 | Hazir bitstream | `output/btn_led_top.bit` |
| 5 | Kaynak kullanim raporu | `output/utilization_impl.rpt` |
| 6 | Zamanlama raporu | `output/timing_impl.rpt` |
| 7 | Proje raporu (PDF) | `RAPOR_Button_LED.pdf` |
| 8 | Proje dokumantasyonu | `README.md` |
| 9 | Ister dokumani | `ISTERLER.md` |
