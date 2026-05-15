/*
  ESP32 + MPU6050 → WiFi Access Point + TCP Server
  ESP32 kendi WiFi'sini açar, PC ona bağlanır.
  PC'de: WiFi → "IMU-SENSOR" ağına bağlan, şifre: imu12345
  Sonra: python imu_server.py

  Kablolama:
    VCC → 3.3V  |  GND → GND
    SDA → GPIO 21  |  SCL → GPIO 22
    AD0 → GND
*/

#include <WiFi.h>
#include <Wire.h>
#include <MPU6050.h>

const char* AP_SSID = "IMU-SENSOR";
const char* AP_PASS = "imu12345";
const int   TCP_PORT = 4210;
const int   SEND_HZ  = 50;

MPU6050 mpu(0x68);
WiFiServer server(TCP_PORT);
WiFiClient client;

float gx_off = 0, gy_off = 0, gz_off = 0;
float ax_off = 0, ay_off = 0;

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
  gx_off = sgx/N; gy_off = sgy/N; gz_off = sgz/N;
  ax_off = sax/N; ay_off = say/N;
  Serial.println(" tamam!");
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  delay(200);

  mpu.initialize();
  mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_250);
  mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_2);
  Serial.println("MPU6050 hazir");

  calibrate();

  WiFi.softAP(AP_SSID, AP_PASS);
  Serial.printf("AP acildi: %s\n", AP_SSID);
  Serial.printf("ESP32 IP: %s\n", WiFi.softAPIP().toString().c_str());

  server.begin();
  Serial.printf("TCP sunucu port %d bekleniyor...\n", TCP_PORT);
}

void loop() {
  // Yeni bağlantı kabul et
  if (!client || !client.connected()) {
    client = server.accept();
    if (client) Serial.println("PC baglandi!");
  }

  static uint32_t last = 0;
  if (millis() - last < 1000 / SEND_HZ) return;
  last = millis();

  if (!client || !client.connected()) return;

  int16_t ax_r, ay_r, az_r, gx_r, gy_r, gz_r;
  mpu.getMotion6(&ax_r, &ay_r, &az_r, &gx_r, &gy_r, &gz_r);

  const float G_SCALE = (1.0f / 131.0f) * (3.14159265f / 180.0f);
  float gx = (gx_r - gx_off) * G_SCALE;
  float gy = (gy_r - gy_off) * G_SCALE;
  float gz = (gz_r - gz_off) * G_SCALE;

  const float A_SCALE = 1.0f / 16384.0f;
  float ax = (ax_r - ax_off) * A_SCALE;
  float ay = (ay_r - ay_off) * A_SCALE;
  float az =  az_r            * A_SCALE;

  char buf[96];
  snprintf(buf, sizeof(buf), "%.5f %.5f %.5f %.5f %.5f %.5f\n", ax, ay, az, gx, gy, gz);
  client.print(buf);
}
