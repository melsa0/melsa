# 1U CubeSat IMU Görselleştirici

ESP32 + MPU6050 ile gerçek zamanlı 3D yönelim takibi.  
ESP32 kendi WiFi ağını açar (Access Point), PC ona bağlanır, tarayıcıda canlı görselleştirme yapar.

```
MPU6050 ──I2C──> ESP32 ──WiFi AP/TCP──> Python Server ──HTTP──> Tarayıcı / Three.js
```

---

## Donanım

| Parça | Adet |
|-------|------|
| ESP32 (WROOM-32D veya muadili) | 1 |
| MPU6050 breakout (GY-521) | 1 |
| Jumper kablo | 4 |
| USB kablo (data destekli) | 1 |

### Kablolama

```
MPU6050        ESP32
──────────     ──────────
VCC     ──→   3.3V   (5V bağlama!)
GND     ──→   GND
SDA     ──→   GPIO 21
SCL     ──→   GPIO 22
AD0     ──→   GND    (I2C adresi 0x68)
INT     ──    (bağlanmaz)
```

---

## Kurulum

### 1. Arduino IDE — ESP32 board paketi

File → Preferences → Additional boards manager URLs:
```
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
```
Tools → Board → Boards Manager → `esp32 by Espressif Systems` → Install

Tools → Board → **ESP32 Dev Module**

### 2. Kütüphane

Tools → Manage Libraries → `MPU6050 by Electronic Cats` → Install

### 3. CP2102 USB sürücüsü (ilk kurulumda)

ESP32 COM portunda görünmüyorsa yönetici PowerShell'de:
```powershell
pnputil /add-driver "C:\...\silabser.inf" /install
```
veya SiLabs sitesinden `CP210x Universal Windows Driver` indir ve kur.

---

## Çalıştırma (her seferinde)

### Adım 1 — ESP32'yi flash'la (ilk kurulumda veya değişiklik olunca)

`esp32_imu_udp/esp32_imu_udp.ino` dosyasını Arduino IDE ile aç → Upload.

Serial Monitor'da (115200 baud) şunu bekle:
```
MPU6050 hazir
Kalibrasyon (sabit tutun)..........tamam!
AP acildi: IMU-SENSOR
ESP32 IP: 192.168.4.1
TCP sunucu port 4210 bekleniyor...
```
> Kalibrasyon sırasında cihazı sabit tutun (~2 saniye).

### Adım 2 — PC'yi ESP32'nin WiFi'sine bağla

- WiFi listesinde **IMU-SENSOR** ağını seç
- Şifre: `imu12345`

### Adım 3 — Python sunucuyu başlat

```bash
python imu_server.py
```

### Adım 4 — Tarayıcıda aç

```
http://localhost:8765/imu_view.html
```

Sol üstte `● esp32:192.168.4.1` yazınca bağlantı kurulmuştur.  
ESP32 bağlı değilse 3 saniye sonra otomatik DEMO animasyonu başlar.

---

## Dosyalar

| Dosya | Açıklama |
|-------|----------|
| `esp32_imu_udp/esp32_imu_udp.ino` | ESP32 firmware — WiFi AP, TCP sunucu, MPU6050 |
| `imu_server.py` | Python sunucu — TCP client, Mahony filtresi, HTTP API |
| `imu_view.html` | 3D görselleştirici — Three.js, MPU6050 board modeli |
| `cubesat_stickers.html` | A4 baskıya hazır CubeSat sticker paketi |
| `cubesat_print.scad` | 1U CubeSat gövdesi OpenSCAD modeli |
| `cubesat_shelf.scad` | ESP32+MPU6050 montaj rafı (94.8×94.8×3mm) |

---

## Sistem Mimarisi

### Veri akışı

```
MPU6050
  │ I2C 21/22, 50 Hz
ESP32 (Access Point: 192.168.4.1)
  │ TCP :4210 — "ax ay az gx gy gz\n"
imu_server.py
  │ Mahony filtresi → quaternion [w,x,y,z]
  │ HTTP :8765
imu_view.html (Three.js)
  │ /data endpoint → quaternion → 3D model
Tarayıcı
```

### Mahony Filtresi

Gyro + ivmeölçer birleştirilerek drift-free quaternion üretilir:

```
hata  = cross(accel_ölçüm, accel_tahmini)
gyro_düzeltilmiş = gyro + Kp×hata + Ki×∫hata·dt
quaternion += gyro_düzeltilmiş × dt
```

- **Kp = 2.0** — sert düzeltme
- **Ki = 0.005** — yavaş integral birikimi
- Frekans: 50 Hz

### HTTP API

| Endpoint | Açıklama |
|----------|----------|
| `GET /data` | Quaternion + sensör verisi (JSON) |
| `GET /reset` | Yönelimi sıfırla |
| `GET /imu_view.html` | Görselleştirici |

`/data` format:
```json
{"q":[w,x,y,z], "gx":0.0,"gy":0.0,"gz":0.0, "ax":0.0,"ay":0.0,"az":0.0, "source":"esp32:192.168.4.1"}
```

---

## 3D Baskı

### CubeSat Gövdesi (`cubesat_print.scad`)

OpenSCAD'de `PART` değişkenini ayarlayıp STL export et:

```scad
PART = "body";   // ana gövde
PART = "lid";    // kapak
PART = "panel";  // güneş paneli
PART = "all";    // hepsi
```

### Montaj Rafı (`cubesat_shelf.scad`)

94.8 × 94.8 × 3 mm. Gövde ortasına yerleştirilir, ESP32 + MPU6050 silikon ile sabitlenir.

### Sticker Paketi (`cubesat_stickers.html`)

Tarayıcıda açıp **Ctrl+P** — A4, 2 sayfa:
- Sayfa 1: ÜST, ALT, ÖN, ARKA yüzler (100×100mm)
- Sayfa 2: SOL, SAĞ yüzler + 2 güneş paneli (140×88mm)

---

## Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| ESP32 COM portunda görünmüyor | CP2102 sürücüsünü kur |
| "MPU6050 bulunamadı" | SDA→21, SCL→22, VCC→3.3V kontrol et |
| WiFi ağı listede yok | ESP32'nin upload'u tamamlandı mı? Güçlü mü? |
| `imu_server.py` bağlanamıyor | PC `IMU-SENSOR` ağında mı? `ping 192.168.4.1` çalışıyor mu? |
| Model ters görünüyor | RESET butonuna bas, sensörü düz tut |
