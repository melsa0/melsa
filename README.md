# CubeSat 1U — IMU & Sun Sensor HIL Sistemi

Gerçek zamanlı 3D yönelim takibi ve güneş sensörü için NASA NOS3 tabanlı
Hardware-in-the-Loop (HIL) + Software-in-the-Loop (SIL) test ortamı.

```
MPU6050 + LDR ──I²C/analog──► Arduino Uno ──USB serial──► imu_server.py
                                                               │
                                              ┌────────────────┼────────────────┐
                                              ▼                ▼                ▼
                                        NOS3 Bridge      HTTP :8765       HTTP :8765
                                        (nos3/         /data  API      /imu_view.html
                                     hardware_provider.py)                Three.js 3D
                                              │
                                     ┌────────┴────────┐
                                     ▼                  ▼
                              GENERIC_IMU          GENERIC_CSS
                              cFS app              cFS app
                                     └────────┬────────┘
                                              ▼
                                      COSMOS Ground
                                      Station :2006
```

---

## Donanım

### HIL (Gerçek Proje Donanımı) — Arduino Uno

| Parça | Adet | Açıklama |
|-------|------|----------|
| Arduino Uno (Rev3) | 1 | USB-serial köprü, 115200 baud |
| MPU6050 (GY-521) | 1 | 6-DOF IMU: ivmeölçer ±2g, jiroskop ±250°/s |
| LDR fotodiod | 4 | Kaba güneş sensörü (coarse sun sensor) |
| 10 kΩ direnç | 4 | LDR voltaj bölücü |
| USB-B kablosu | 1 | Arduino ↔ PC |

### ESP32 (Sadece Sergi / Exhibition Display)

| Parça | Adet | Açıklama |
|-------|------|----------|
| ESP32 WROOM-32D | 1 | WiFi AP + TCP sunucu (exhibition only) |
| MPU6050 (GY-521) | 1 | 6-DOF IMU |
| Jumper kablo | 4 | |

---

## Kablolama / Wiring

### Arduino Uno + MPU6050

```
MPU6050              Arduino Uno
───────────          ─────────────────
VCC     ──────────►  3.3V   ← 3.3V zorunlu, 5V bağlama!
GND     ──────────►  GND
SDA     ──────────►  A4     (pin 18, I²C data)
SCL     ──────────►  A5     (pin 19, I²C clock)
AD0     ──────────►  GND    → I²C adresi: 0x68
INT     ──            (bağlanmaz)
```

### LDR Güneş Sensörü (×4, her yüz için)

```
5V ──[ LDR ]──┬── A0 (+X yüzü)
              └──[ 10kΩ ]── GND

5V ──[ LDR ]──┬── A1 (-X yüzü)
              └──[ 10kΩ ]── GND

5V ──[ LDR ]──┬── A2 (+Y yüzü)
              └──[ 10kΩ ]── GND

5V ──[ LDR ]──┬── A3 (-Y yüzü)
              └──[ 10kΩ ]── GND

Devre: 5V → LDR → ADC pini → 10kΩ → GND
       Işık artınca LDR direnci düşer → ADC voltajı artar → ADC değeri artar
```

### ESP32 + MPU6050 (Sergi modu)

```
MPU6050              ESP32
───────────          ─────────────────
VCC     ──────────►  3.3V
GND     ──────────►  GND
SDA     ──────────►  GPIO 21
SCL     ──────────►  GPIO 22
AD0     ──────────►  GND    → 0x68
```

---

## Değer Aralıkları / Value Ranges

### MPU6050 — İvmeölçer (Accelerometer)

| Parametre | Değer |
|-----------|-------|
| Ölçüm aralığı | ±2 g |
| Hassasiyet | 16384 LSB/g |
| Ham → g | `raw / 16384.0` |
| Çıkış birimi | g (imu_server.py'de) / m/s² (NOS3'te ×9.80665) |
| Kalibre hata | ax_off, ay_off: 500 örnek ortalaması |

### MPU6050 — Jiroskop (Gyroscope)

| Parametre | Değer |
|-----------|-------|
| Ölçüm aralığı | ±250 °/s |
| Hassasiyet | 131 LSB/(°/s) |
| Ham → rad/s | `raw / 131.0 × (π/180)` |
| Çıkış birimi | rad/s |
| Drift | Mahony filtresinde integral terimi ile giderilir |

### LDR — Lux Hesaplama

**Devre:** `5V → LDR → ADC_pin → 10kΩ (R_fixed) → GND`

```
R_ldr (Ω)  = R_fixed × (1023 − ADC) / ADC      [R_fixed = 10000 Ω]

Lux        = 500000 / R_ldr
```

| ADC Değeri | R_LDR | Lux | Ortam |
|------------|-------|-----|-------|
| 50 | ~190 kΩ | ~3 | Karanlık oda |
| 200 | ~40 kΩ | ~13 | Loş oda |
| 500 | 10 kΩ | 50 | Ofis ışığı |
| 700 | ~4.4 kΩ | 114 | Aydınlık oda |
| 850 | ~1.8 kΩ | 278 | Pencere yanı |
| 950 | ~540 Ω | 926 | Açık gölge |
| 1000 | ~230 Ω | ~2170 | Simüle güneş |

Pin başına en yüksek lux değeri → güneş yönü tahmini (+X, -X, +Y, -Y yüzü).

### Seri Port Çıktısı Formatı

```
ax ay az gx gy gz ldr0 ldr1 ldr2 ldr3\n
│   │   │   │   │   │   │    │    │    └── -Y yüzü lux (A3)
│   │   │   │   │   │   │    │    └─────── +Y yüzü lux (A2)
│   │   │   │   │   │   │    └──────────── -X yüzü lux (A1)
│   │   │   │   │   │   └───────────────── +X yüzü lux (A0)
│   │   │   │   │   └──────────────────── gz [rad/s]
│   │   │   │   └──────────────────────── gy [rad/s]
│   │   │   └──────────────────────────── gx [rad/s]
│   │   └──────────────────────────────── az [g]
│   └──────────────────────────────────── ay [g]
└──────────────────────────────────────── ax [g]

Hız: 50 Hz  |  Baud: 115200  |  '#' ile başlayan satırlar yorum
```

---

## Mahony Filtresi

Jiroskop + ivmeölçer birleştirilerek drift-free quaternion üretilir.

**Referans:** Mahony et al., "Nonlinear Complementary Filters on the Special Orthogonal Group", *IEEE Transactions on Automatic Control*, 2008.

```
1. Ölçülen ivmeyi normalleştir:  a_norm = a / |a|
2. Quaternion'dan yerçekimi tahmini:
   g_est = [2(xz−wy),  2(yz+wx),  w²−x²−y²+z²]
3. Hata: e = cross(a_norm, g_est)
4. İntegral: eInt += Ki × e × dt
5. Düzeltilmiş gyro: gyro_corr = gyro + Kp×e + eInt
6. Delta quaternion: dq = gyro_corr → küçük açı dönüşümü × dt
7. Güncelleme: q = normalise(q ⊗ dq)
```

| Parametre | Değer | Etki |
|-----------|-------|------|
| Kp | 2.0 | Hızlı düzeltme (ivmeölçer ağırlığı) |
| Ki | 0.005 | Yavaş gyro drift giderimi |
| Frekans | 50 Hz | Arduino çıkış hızıyla eşleşik |

---

## Faz Yapısı / Project Phases

### SIL — Software-in-the-Loop

NOS3 sanal sensör modelleri, gerçek donanım olmadan cFS uygulamalarını test eder.

```
NOS3 generate_template.sh
  → GENERIC_IMU  (sanal IMU modeli)
  → GENERIC_CSS  (sanal güneş sensörü)
  → GENERIC_THERMAL (sanal termal sensör)
        │
        ▼
   cFS uygulamaları
        │
        ▼
   COSMOS Packet Viewer (:2006)
```

CCSDS paket yapısı:
```
┌────────────────────────────┐
│ Primary Header    6 byte   │ APID | seq_flags | seq_count | data_len
├────────────────────────────┤
│ Secondary Header  10 byte  │ MET_seconds (4B) | MET_sub (2B) | pad (4B)
├────────────────────────────┤
│ Payload           N byte   │ Sensor data
└────────────────────────────┘

Telemetri portu: 2006
Komut portu:     2005
```

### HIL — Hardware-in-the-Loop

Gerçek Arduino Uno sensör verisi NOS3 middleware'ine beslenir.

```
Arduino Uno ──USB──► imu_server.py  ──HTTP──►  nos3/hardware_provider.py
  MPU6050                 │                           │
  LDR ×4             HTTP :8765                 UDP :5013 → GENERIC_IMU
                     /data API                  UDP :5020 → GENERIC_CSS
                          │
                    imu_view.html
                    Three.js 3D
```

---

## Kurulum

### 1. Arduino IDE — Arduino Uno

Board Manager URL:
```
https://www.arduino.cc/en/software
```

Tools → Board → **Arduino Uno**  
Tools → Port → COM3 (veya aktif COM portu)

Kütüphane gerekmez — Wire.h built-in.

`arduino_uno/arduino_uno_imu.ino` dosyasını aç → Upload.

Serial Monitor'da (115200 baud) çıktı:
```
# MPU6050 hazir (WHO_AM_I=0x68)
# Kalibrasyon basliyor — hareketsiz tutun...
#..........tamam!
# ax(g) ay(g) az(g) gx(r/s) gy(r/s) gz(r/s) ldr0(lx) ldr1(lx) ldr2(lx) ldr3(lx)
0.00124 -0.00087 0.99812 0.00001 -0.00003 0.00002 45 12 823 67
...
```

### 2. Python sunucu (imu_server.py)

```bash
pip install pyserial          # Arduino modu için zorunlu
pip install requests          # NOS3 bridge için gerekli

# Arduino modu (HIL — gerçek proje):
python imu_server.py --mode arduino --port COM3

# ESP32 modu (sergi):
python imu_server.py --mode esp32
```

### 3. NOS3 HIL Bridge (opsiyonel)

```bash
# imu_server.py çalışırken ayrı terminalde:
python nos3/hardware_provider.py
```

### 4. 3D Görselleştirici

```
http://localhost:8765/imu_view.html
```

Sol üstte kaynak etiketi:
- `● arduino:COM3` — Arduino bağlı
- `● esp32:192.168.4.1` — ESP32 bağlı
- `◌ DEMO` — Donanım yok, demo animasyon

---

## ESP32 Kurulumu (Sergi Modu)

Arduino IDE → File → Preferences → Additional boards manager URLs:
```
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
```
Tools → Board → Boards Manager → `esp32 by Espressif Systems` → Install  
Tools → Board → **ESP32 Dev Module**  
Tools → Manage Libraries → `MPU6050 by Electronic Cats` → Install

`esp32_imu_udp/esp32_imu_udp.ino` dosyasını aç → Upload.

Serial Monitor'da (115200 baud):
```
MPU6050 hazir
Kalibrasyon (sabit tutun)..........tamam!
AP acildi: IMU-SENSOR
ESP32 IP: 192.168.4.1
TCP sunucu port 4210 bekleniyor...
```

WiFi → **IMU-SENSOR** ağına bağlan (şifre: `imu12345`)  
Sonra: `python imu_server.py --mode esp32`

---

## HTTP API

| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/data` | GET | Tüm sensör verisi (JSON) |
| `/reset` | GET | Quaternion'ı sıfırla |
| `/config` | GET | Eksen eşleme ayarları |
| `/config` | POST | Eksen eşleme güncelle |
| `/imu_view.html` | GET | Three.js 3D görselleştirici |

### GET /data — Örnek Yanıt

```json
{
  "q":   [0.9971, 0.0523, 0.0349, 0.0175],
  "ax":   0.03241,
  "ay":  -0.01876,
  "az":   0.99812,
  "gx":   0.00231,
  "gy":  -0.00087,
  "gz":   0.00145,
  "ldr": [823, 145, 612, 89],
  "lux":  823,
  "source": "arduino:COM3",
  "t":   42.5
}
```

`ldr[0..3]` = lux değeri (+X, -X, +Y, -Y yüzleri)  
`lux` = max(ldr) — baskın güneş yönü

---

## 3D Görselleştirici (imu_view.html)

Three.js / WebGL tabanlı gerçek zamanlı CubeSat görünümü.

- `GET /data` her **30 ms**'de bir sorgulanır (~33 Hz)
- Quaternion SLERP interpolasyonu ile 60 fps akıcı dönüş
- CubeSat 3D modeli: ana gövde + güneş paneli + anten
- Renkli eksen yardımcısı: X=kırmızı, Y=yeşil, Z=mavi
- HUD: anlık roll, pitch, yaw (derece)
- Demo modu: seri/TCP bağlantı yoksa 3 saniye sonra otomatik başlar

> **Not:** 42 Spacecraft Simulation Tool lab bilgisayarlarında yapılandırılamadı;
> onun yerine bu özel Three.js görselleştiricisi geliştirildi.

---

## Dosya Yapısı

```
bitirme/
├── README.md
├── arduino_uno/
│   └── arduino_uno_imu.ino     HIL firmware — MPU6050 + LDR sun sensor
├── esp32_imu_udp/
│   └── esp32_imu_udp.ino       ESP32 exhibition display (WiFi AP + TCP)
├── imu_server.py               Python server — Mahony filter, HTTP API
├── imu_view.html               Three.js 3D visualizer
├── nos3/
│   └── hardware_provider.py    NOS3 HIL bridge (imu_server → NOS3 UDP)
├── sample_data/
│   └── imu_data.json           /data API örnek çıktısı + açıklamalar
├── cubesat_print.scad          1U CubeSat gövdesi (OpenSCAD)
├── cubesat_shelf.scad          Arduino+MPU6050 montaj rafı (94.8×94.8×3mm)
└── cubesat_stickers.html       A4 baskıya hazır yüz etiketleri
```

---

## Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| Arduino COM portunda görünmüyor | CH340/CP2102 sürücüsünü kur |
| `WHO_AM_I=0x00` veya hata | SDA→A4, SCL→A5, VCC→3.3V kontrol et |
| `ModuleNotFoundError: serial` | `pip install pyserial` çalıştır |
| LDR değerleri hep 0 | LDR devre bağlantısını kontrol et (10kΩ GND'ye) |
| LDR değerleri hep ~1023 | LDR'nin ışığa maruz olup olmadığını kontrol et |
| Model ters görünüyor | `/reset` endpointini çağır veya sensörü düz tut |
| NOS3 veri almıyor | `hardware_provider.py` çalışıyor mu? Port: 5013/5020 |
| COSMOS'ta paket yok | cFS'in GENERIC_IMU uygulamasının aktif olduğunu doğrula |
