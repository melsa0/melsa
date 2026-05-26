/*
  Arduino Uno — CubeSat HIL Sensor Bridge
  =========================================
  Sensors:
    MPU6050  IMU       → I²C: SDA=A4 (pin 18), SCL=A5 (pin 19)
                          VCC=3.3V, GND=GND, AD0→GND (address 0x68)
    LDR ×4   Sun sensor → A0=+X face, A1=-X face, A2=+Y face, A3=-Y face
                          Circuit: 5V → LDR → pin → 10kΩ → GND

  Output (USB serial, 115200 baud, 50 Hz):
    ax ay az gx gy gz ldr0 ldr1 ldr2 ldr3 CRC16
    ├── ax/ay/az  : acceleration [g],  float, 5 decimal places
    ├── gx/gy/gz  : angular rate [rad/s], float, 5 decimal places
    ├── ldr0-3    : lux estimate per face (5-sample moving average), integer
    └── CRC16     : CRC-16/XMODEM over first 10 fields, 4 hex digits

  Lines starting with '#' are comments — imu_server.py skips them.

  Wiring diagram:
    MPU6050                Arduino Uno
    ───────────            ─────────────
    VCC       ──────────→  3.3V  (NOT 5V!)
    GND       ──────────→  GND
    SDA       ──────────→  A4    (pin 18)
    SCL       ──────────→  A5    (pin 19)
    AD0       ──────────→  GND   (I²C address 0x68)
    INT       ──          (not connected)

    LDR circuit (×4, one per face):
    5V ──[ LDR ]──┬── A0/A1/A2/A3
                  └──[ 10kΩ ]── GND

  Value ranges:
    Accel:  ±2g       → LSB = 16384 counts/g
    Gyro:   ±250°/s   → LSB = 131 counts/(°/s) → ×(π/180) for rad/s
    ADC:    0–1023    → lux via voltage divider + LDR resistance formula
*/

#include <Wire.h>

// ── MPU6050 register map ──────────────────────────────────────────────────────
#define MPU_ADDR      0x68
#define REG_PWR_MGMT  0x6B   // write 0x00 to wake up
#define REG_GYRO_CFG  0x1B   // 0x00 = ±250°/s
#define REG_ACCEL_CFG 0x1C   // 0x00 = ±2g
#define REG_ACCEL_OUT 0x3B   // 14-byte block: AX AY AZ TEMP GX GY GZ (big-endian)
#define REG_WHO_AM_I  0x75   // should read 0x68

// ── Scale factors ─────────────────────────────────────────────────────────────
const float A_SCALE = 1.0f / 16384.0f;                 // raw → g
const float G_SCALE = (1.0f / 131.0f) * (PI / 180.0f); // raw → rad/s

// ── LDR (GL5528-type): 5V → LDR → pin → R_FIXED → GND ───────────────────────
// V_pin = 5 * R_FIXED / (R_LDR + R_FIXED)
// ADC/1023 = R_FIXED / (R_LDR + R_FIXED)
// R_LDR = R_FIXED * (1023 - ADC) / ADC
// Lux ≈ 500000 / R_LDR   (empirical for GL5528, R_FIXED=10kΩ)
//   ADC=50  → R_LDR≈190kΩ → ~3 lux   (dim room)
//   ADC=200 → R_LDR≈40kΩ  → ~12 lux  (office)
//   ADC=500 → R_LDR=10kΩ  → 50 lux   (bright room)
//   ADC=800 → R_LDR≈2.6kΩ → 192 lux  (near window)
//   ADC=950 → R_LDR≈540Ω  → 926 lux  (sunlight)
const long   R_FIXED = 10000L;  // Ω

const uint8_t LDR_PINS[4] = { A0, A1, A2, A3 };
// Face mapping:  [0]=+X  [1]=-X  [2]=+Y  [3]=-Y
// Dominant face with highest lux = approximate sun direction

// ── LDR moving average (5-sample ring buffer, averages ADC before lux conversion) ──
const int LDR_MA_N = 5;
int _ldr_raw[4][LDR_MA_N];
int _ldr_idx  = 0;
bool _ldr_full = false;

// ── Calibration ───────────────────────────────────────────────────────────────
const int CALIB_N = 500;
float gx_off = 0, gy_off = 0, gz_off = 0;
float ax_off = 0, ay_off = 0;  // Z not offset — keeps gravity reference

// ── Timing ───────────────────────────────────────────────────────────────────
const int SEND_HZ = 50;        // 50 Hz → 20 ms/sample

// ── MPU6050 I/O helpers ───────────────────────────────────────────────────────
void mpu_write(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  Wire.write(val);
  Wire.endTransmission();
}

void mpu_read6(int16_t &ax, int16_t &ay, int16_t &az,
               int16_t &gx, int16_t &gy, int16_t &gz) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(REG_ACCEL_OUT);
  Wire.endTransmission(false);
  Wire.requestFrom((uint8_t)MPU_ADDR, (uint8_t)14, (uint8_t)true);
  ax = (int16_t)((Wire.read() << 8) | Wire.read());
  ay = (int16_t)((Wire.read() << 8) | Wire.read());
  az = (int16_t)((Wire.read() << 8) | Wire.read());
  Wire.read(); Wire.read();   // temperature — discard
  gx = (int16_t)((Wire.read() << 8) | Wire.read());
  gy = (int16_t)((Wire.read() << 8) | Wire.read());
  gz = (int16_t)((Wire.read() << 8) | Wire.read());
}

// ── Lux calculation ───────────────────────────────────────────────────────────
int adc_to_lux(int adc) {
  if (adc <= 0)    return 0;
  if (adc >= 1023) return 99999;
  long r_ldr = R_FIXED * (long)(1023 - adc) / (long)adc;  // Ω
  if (r_ldr == 0) return 99999;
  return (int)(500000L / r_ldr);
}

// ── Calibration routine ───────────────────────────────────────────────────────
void calibrate() {
  Serial.println(F("# Kalibrasyon basliyor — hareketsiz tutun..."));
  double sgx=0, sgy=0, sgz=0, sax=0, say=0;
  int16_t ax, ay, az, gx, gy, gz;
  for (int i = 0; i < CALIB_N; i++) {
    mpu_read6(ax, ay, az, gx, gy, gz);
    sax += ax;  say += ay;
    sgx += gx;  sgy += gy;  sgz += gz;
    if (i % 50 == 0) Serial.print(F("#."));
    delay(4);
  }
  ax_off = (float)(sax / CALIB_N);
  ay_off = (float)(say / CALIB_N);
  gx_off = (float)(sgx / CALIB_N);
  gy_off = (float)(sgy / CALIB_N);
  gz_off = (float)(sgz / CALIB_N);
  Serial.println(F(" tamam!"));
  Serial.print(F("# Gyro offsets (raw): "));
  Serial.print(gx_off,1); Serial.print(F(" "));
  Serial.print(gy_off,1); Serial.print(F(" "));
  Serial.println(gz_off,1);
}

// ── CRC-16/XMODEM (poly 0x1021, init 0xFFFF) ─────────────────────────────────
uint16_t crc16_xmodem(const char *s, int len) {
  uint16_t crc = 0xFFFF;
  while (len--) {
    crc ^= (uint8_t)(*s++) << 8;
    for (int i = 0; i < 8; i++)
      crc = (crc & 0x8000) ? (crc << 1) ^ 0x1021 : crc << 1;
  }
  return crc;
}

// ─────────────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Wire.begin();
  delay(200);

  // Wake MPU6050 and configure ranges
  mpu_write(REG_PWR_MGMT,  0x00);   // clear SLEEP bit
  mpu_write(REG_GYRO_CFG,  0x00);   // FS_SEL=0 → ±250°/s
  mpu_write(REG_ACCEL_CFG, 0x00);   // AFS_SEL=0 → ±2g
  delay(100);

  // Verify chip identity
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(REG_WHO_AM_I);
  Wire.endTransmission(false);
  Wire.requestFrom((uint8_t)MPU_ADDR, (uint8_t)1, (uint8_t)true);
  uint8_t who = Wire.read();
  if (who != 0x68 && who != 0x72) {
    Serial.print(F("# HATA: WHO_AM_I=0x"));
    Serial.print(who, HEX);
    Serial.println(F(" — MPU6050 bulunamadi! Kablolari kontrol et."));
    while (true) delay(1000);
  }
  Serial.println(F("# MPU6050 hazir (WHO_AM_I=0x68)"));

  calibrate();

  Serial.println(F("# ax(g) ay(g) az(g) gx(r/s) gy(r/s) gz(r/s) ldr0(lx) ldr1(lx) ldr2(lx) ldr3(lx)"));
  Serial.println(F("# Faces: ldr0=+X ldr1=-X ldr2=+Y ldr3=-Y"));
}

void loop() {
  static uint32_t last_ms = 0;
  uint32_t now = millis();
  if (now - last_ms < (1000UL / SEND_HZ)) return;
  last_ms = now;

  // ── IMU read ──────────────────────────────────────────────────────────────
  int16_t ax_r, ay_r, az_r, gx_r, gy_r, gz_r;
  mpu_read6(ax_r, ay_r, az_r, gx_r, gy_r, gz_r);

  float ax = (ax_r - ax_off) * A_SCALE;
  float ay = (ay_r - ay_off) * A_SCALE;
  float az =  az_r            * A_SCALE;   // Z: gravity reference preserved
  float gx = (gx_r - gx_off) * G_SCALE;
  float gy = (gy_r - gy_off) * G_SCALE;
  float gz = (gz_r - gz_off) * G_SCALE;

  // ── LDR sun sensor read (5-sample moving average on ADC, then lux) ─────────
  for (int i = 0; i < 4; i++)
    _ldr_raw[i][_ldr_idx] = analogRead(LDR_PINS[i]);
  _ldr_idx++;
  if (_ldr_idx >= LDR_MA_N) { _ldr_idx = 0; _ldr_full = true; }
  int n_avg = _ldr_full ? LDR_MA_N : _ldr_idx;
  int lux[4];
  for (int i = 0; i < 4; i++) {
    long sum = 0;
    for (int j = 0; j < n_avg; j++) sum += _ldr_raw[i][j];
    lux[i] = adc_to_lux((int)(sum / n_avg));
  }

  // ── Serial output — Format: "ax ay az gx gy gz ldr0 ldr1 ldr2 ldr3 CRC16\n"
  char buf[100];
  int n = snprintf(buf, sizeof(buf),
    "%.5f %.5f %.5f %.5f %.5f %.5f %d %d %d %d",
    ax, ay, az, gx, gy, gz,
    lux[0], lux[1], lux[2], lux[3]);
  uint16_t crc = crc16_xmodem(buf, n);
  char out[120];
  snprintf(out, sizeof(out), "%s %04X", buf, crc);
  Serial.println(out);
}
