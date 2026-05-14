# CubeSat IMU Visualizer

ESP32 + MPU6050 IMU sensörünü hareket ettirince ekranda 1U CubeSat 3D model gerçek zamanlı döner.  
WiFi üzerinden UDP ile veri iletimi, Mahony filtresi ile gyro drift'i düzeltilmiş attitude tahmini.

```
[MPU6050] ──I2C──> [ESP32] ──WiFi UDP──> [Python Server] ──HTTP──> [Browser / Three.js]
```

---

## Donanım Listesi

| Parça | Adet | Not |
|---|---|---|
| ESP32 DevKit (38-pin veya 30-pin) | 1 | Her ESP32 modeli çalışır |
| MPU6050 breakout kartı | 1 | GY-521 modülü yaygın |
| Jumper kablo (dişi-dişi) | 4 | |
| USB Micro/Type-C kablo | 1 | ESP32'yi programlamak için |

---

## Kablolama

```
MPU6050        ESP32
──────────     ──────────────
VCC     ──→   3.3V   (! 5V bağlama, bozulur)
GND     ──→   GND
SDA     ──→   GPIO 21
SCL     ──→   GPIO 22
AD0     ──→   GND    (I2C adresi 0x68 olur)
INT     ──    (bağlanmaz)
```

> **Dikkat:** MPU6050 breakout kartının üzerinde genellikle 3.3V regülatör vardır;
> bazı kartlara 5V da bağlayabilirsiniz. Kart üzerindeki "VCC" etiketine bakın.

---

## Bilgisayar Gereksinimleri

- **WSL2** (Windows Subsystem for Linux) — Ubuntu 20.04 veya 22.04
- **Python 3.8+** (WSL içinde, genellikle hazır gelir)
- **Arduino IDE 2.x** (Windows'ta)

---

## 1. Arduino IDE Kurulumu

### 1.1 ESP32 board desteği ekle

Arduino IDE → `File → Preferences → Additional boards manager URLs`:
```
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
```
Sonra `Tools → Board → Boards Manager` → **esp32** ara → **Espressif Systems** → Install.

### 1.2 MPU6050 kütüphanesi

`Tools → Manage Libraries` → `MPU6050` ara → **MPU6050 by Electronic Cats** → Install.

---

## 2. ESP32 Kodunu Yükle

### 2.1 WSL IP'ni öğren

WSL terminalinde çalıştır:
```bash
hostname -I
```
Çıktı örnek: `172.28.144.5 ...` — ilk IP'yi not al.

### 2.2 Kodu düzenle

`esp32_imu_udp/esp32_imu_udp.ino` dosyasını Arduino IDE ile aç.
En üstteki 3 satırı değiştir:

```cpp
const char* WIFI_SSID = "EV_WIFISI";          // WiFi adın
const char* WIFI_PASS = "WIFI_SIFRESI";        // WiFi şifren
const char* SERVER_IP = "172.28.144.5";        // hostname -I çıktısı
```

### 2.3 Board seç ve yükle

- `Tools → Board → ESP32 Arduino → ESP32 Dev Module`
- `Tools → Port` → ESP32'nin COM portunu seç (aygıt yöneticisinde görünür)
- `Upload` (→ ok butonu) tıkla

Yükleme bittikten sonra `Tools → Serial Monitor` aç, **115200 baud** seç.  
Şöyle bir çıktı görmelisin:
```
MPU6050 hazır
Kalibrasyon (sabit tutun)..........tamam!
WiFi bağlanıyor: EV_WIFISI......
Bağlandı! ESP32 IP: 192.168.1.42
UDP → 172.28.144.5:4210
```

> **Önemli:** Kalibrasyon sırasında ESP32'yi/IMU'yu sabit tutun (2 saniye).

---

## 3. Python Server'ı Başlat

WSL terminalinde:
```bash
cd ~/imu_vis
python3 imu_server.py
```

Çıktı:
```
====================================================
  IMU Visualizer — Mahony Filter (gyro + accel)
  UDP 4210   ← ESP32 sends 'ax ay az gx gy gz'
  HTTP 8765  → http://localhost:8765/imu_view.html
  WSL IP: 172.28.144.5
====================================================
```

---

## 4. Tarayıcıda Aç

Windows tarayıcısında (Chrome, Edge):
```
http://localhost:8765/imu_view.html
```

ESP32 bağlı değilse 3 saniye sonra **DEMO animasyonu** başlar.  
ESP32 bağlandığında sol üstte `● esp32:192.168.1.42` yazar.

---

## Nasıl Çalışır?

### Veri Akışı
```
MPU6050 → I2C → ESP32 → WiFi UDP (50 Hz) → Python → HTTP JSON → Browser
```

### Mahony Filtresi
Sadece jiroskop kullanılsaydı zaman içinde açısal kayma (drift) oluşurdu.  
İvmeölçer yerçekimi yönünü ölçer; Mahony filtresi bu iki kaynağı birleştirir:

```
hata  = cross(accel_ölçüm, accel_tahmin_quaternion'dan)
gyro_düzeltilmiş = gyro + Kp×hata + Ki×∫hata·dt
quaternion += gyro_düzeltilmiş × dt
```

Sonuç: hiç kayma olmayan, gerçek zamanlı attitude tahmini.

### Quaternion → 3D Rotasyon
Server `[w, x, y, z]` quaternion gönderir.  
Three.js tarayıcıda SLERP ile smooth interpolasyon yaparak modeli döndürür.

---

## Sorun Giderme

| Sorun | Çözüm |
|---|---|
| "MPU6050 bulunamadı" | SDA→GPIO21, SCL→GPIO22, VCC→3.3V kontrol et |
| WiFi bağlanmıyor | SSID/şifre doğru mu? ESP32 2.4GHz ağda mı? |
| UDP verisi gelmiyor | `hostname -I` ile WSL IP'ni tekrar kontrol et; Windows Firewall UDP 4210 portunu bloke ediyor olabilir |
| Tarayıcıda "disconnected" | `python3 imu_server.py` çalışıyor mu? |
| Model ters dönüyor | ESP32'yi IMU yönüne göre yerleştir veya SERVER'da eksen sıralamasını değiştir |
| Çok fazla drift | Kalibrasyonda ESP32'yi daha uzun süre sabit tut |

### Windows Firewall (UDP 4210 açma)
PowerShell (yönetici):
```powershell
New-NetFirewallRule -DisplayName "IMU UDP" -Direction Inbound -Protocol UDP -LocalPort 4210 -Action Allow
```

---

## Dosya Yapısı

```
imu_vis/
├── imu_server.py          # Python HTTP+UDP server, Mahony filtresi
├── imu_view.html          # Three.js 1U CubeSat görselleştirici
└── esp32_imu_udp/
    └── esp32_imu_udp.ino  # Arduino sketch (ESP32 + MPU6050)
```

---

## Geliştirme Fikirleri

- Magnetometre ekle (MPU9250 veya HMC5883L) → yaw drift de düzelir (Madgwick filtresi)
- NOS3 entegrasyonu → simülatörde spacecraft attitude güncelleme
- Accel verisinden linear hız entegrasyonu (dikkat: çok daha fazla drift)
