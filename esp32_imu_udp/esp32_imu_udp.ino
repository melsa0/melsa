/*
  ESP32 + MPU6050 → UDP  (Mahony fusion ready)
  ──────────────────────────────────────────────────────────────────
  Gönderilen format:  "ax ay az gx gy gz\n"
    ax/ay/az : ivmeölçer   (g cinsinden, ±2g range)
    gx/gy/gz : jiroskop    (rad/s,        ±250°/s range)

  Kablolama (MPU6050 → ESP32):
    VCC  → 3.3V
    GND  → GND
    SDA  → GPIO 21
    SCL  → GPIO 22
    AD0  → GND   (I2C adresi 0x68 olur)
    INT  → bağlanmaz

  Gerekli kütüphaneler (Arduino Library Manager):
    - "MPU6050" by Electronic Cats
    - WiFi (ESP32 için built-in gelir)

  ★ Değiştirmen gereken 3 satır:
    WIFI_SSID, WIFI_PASS, SERVER_IP
*/

#include <WiFi.h>
#include <WiFiUdp.h>
#include <Wire.h>
#include <MPU6050.h>

// ── AYARLAR ───────────────────────────────────────────────────────
const char*    WIFI_SSID = "WIFI_ADINIZ";
const char*    WIFI_PASS = "WIFI_SIFRENIZ";
const char*    SERVER_IP = "172.28.x.x";   // WSL IP — terminalde: hostname -I
const uint16_t UDP_PORT  = 4210;
const int      SEND_HZ   = 50;             // gönderme frekansı (Hz)
// ─────────────────────────────────────────────────────────────────

MPU6050 mpu;
WiFiUDP udp;

// Kalibrasyon offset (setup'ta doldurulur)
float gx_off = 0, gy_off = 0, gz_off = 0;
float ax_off = 0, ay_off = 0;   // Z ekseni offset'i yok (1g kalır)

void calibrate() {
  const int N = 500;
  double sgx=0, sgy=0, sgz=0, sax=0, say=0;
  int16_t ax, ay, az, gx, gy, gz;

  Serial.print("Kalibrasyon (sabit tutun)");
  for (int i = 0; i < N; i++) {
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
    sgx += gx; sgy += gy; sgz += gz;
    sax += ax; say += ay;
    if (i % 50 == 0) Serial.print(".");
    delay(4);
  }
  gx_off = sgx/N;  gy_off = sgy/N;  gz_off = sgz/N;
  ax_off = sax/N;  ay_off = say/N;
  Serial.println(" tamam!");
  Serial.printf("  gyro offset: %.1f %.1f %.1f\n", gx_off, gy_off, gz_off);
  Serial.printf("  accel offset (XY): %.1f %.1f\n", ax_off, ay_off);
}

void setup() {
  Serial.begin(115200);
  Wire.begin();

  mpu.initialize();
  if (!mpu.testConnection()) {
    Serial.println("MPU6050 bulunamadı! Kablo bağlantısını kontrol et.");
    while (1) delay(1000);
  }
  mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_250);   // ±250°/s
  mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_2);   // ±2g
  Serial.println("MPU6050 hazır");

  calibrate();

  Serial.printf("WiFi bağlanıyor: %s", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.printf("\nBağlandı! ESP32 IP: %s\n", WiFi.localIP().toString().c_str());
  Serial.printf("UDP → %s:%d\n", SERVER_IP, UDP_PORT);

  udp.begin(4211);
}

void loop() {
  static uint32_t last = 0;
  const int interval = 1000 / SEND_HZ;
  if (millis() - last < interval) return;
  last = millis();

  int16_t ax_r, ay_r, az_r, gx_r, gy_r, gz_r;
  mpu.getMotion6(&ax_r, &ay_r, &az_r, &gx_r, &gy_r, &gz_r);

  // Jiroskop: raw → rad/s
  //   ±250°/s range → 131 LSB/(°/s)
  const float G_SCALE = (1.0f / 131.0f) * (M_PI / 180.0f);
  float gx = (gx_r - gx_off) * G_SCALE;
  float gy = (gy_r - gy_off) * G_SCALE;
  float gz = (gz_r - gz_off) * G_SCALE;

  // İvmeölçer: raw → g
  //   ±2g range → 16384 LSB/g
  const float A_SCALE = 1.0f / 16384.0f;
  float ax = (ax_r - ax_off) * A_SCALE;
  float ay = (ay_r - ay_off) * A_SCALE;
  float az =  az_r            * A_SCALE;   // Z'de 1g kalır, offset yok

  char buf[96];
  snprintf(buf, sizeof(buf),
    "%.5f %.5f %.5f %.5f %.5f %.5f",
    ax, ay, az, gx, gy, gz);

  udp.beginPacket(SERVER_IP, UDP_PORT);
  udp.print(buf);
  udp.endPacket();

  // Serial debug (her 25 pakette bir)
  static int dbg = 0;
  if (++dbg % 25 == 0)
    Serial.printf("a=[%.3f %.3f %.3f]g  g=[%.4f %.4f %.4f]r/s\n",
                  ax, ay, az, gx, gy, gz);
}
