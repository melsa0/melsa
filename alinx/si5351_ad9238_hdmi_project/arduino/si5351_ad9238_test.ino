/*
 * Si5351 Test Signal Generator for AD9238 + HDMI Oscilloscope
 *
 * Baglanti:
 *   Arduino SDA -> Si5351 SDA
 *   Arduino SCL -> Si5351 SCL
 *   Arduino 3.3V -> Si5351 VIN
 *   Arduino GND -> Si5351 GND
 *   Si5351 CLK0 -> AN9238 CH0 SMA input
 *   Si5351 CLK1 -> AN9238 CH1 SMA input
 *
 * NOT: Si5351 cikislari 3.3V kare dalga uretir.
 *      AN9238 modulu -5V..+5V analog giris araligina sahip.
 *      3.3V kare dalga, ADC araliginin yaklasik %33'unu kaplar - gorunur olmali.
 *
 * Kutuphane: Adafruit Si5351 (Arduino Library Manager'dan yukleyin)
 */

#include <Wire.h>
#include <Adafruit_SI5351.h>

Adafruit_SI5351 clockgen = Adafruit_SI5351();

void setup() {
  Serial.begin(9600);
  Serial.println("Si5351 AD9238 HDMI Test Signal Generator");

  // Si5351 baslatma
  if (clockgen.begin() != ERROR_NONE) {
    Serial.println("HATA: Si5351 bulunamadi! Baglantiyi kontrol edin.");
    while(1);
  }
  Serial.println("Si5351 bulundu ve basladi.");

  /*
   * Si5351 frekans ayari:
   * setupPLL(pll, multiplier, numerator, denominator)
   *   PLL freq = 25MHz * (multiplier + numerator/denominator)
   *
   * setupMultisynth(output, pll, divider, numerator, denominator)
   *   Output freq = PLL freq / (divider + numerator/denominator)
   *
   * Ornek: 100 kHz cikis
   *   PLL_A = 25MHz * 24 = 600 MHz
   *   CLK0 = 600 MHz / 6000 = 100 kHz
   *   (6000 = divider olarak max 900 oldugu icin multisynth + R divider kullanilir)
   *
   * Daha kolay yol: Dusuk frekanslar icin R divider kullanmak
   *   CLK0 = PLL / divider / R_divider
   */

  // =====================================================
  // CLK0: 200 kHz kare dalga (CH0 icin)
  // PLL_A = 25 MHz * 32 = 800 MHz
  // Multisynth0 = 800 MHz / 50 = 16 MHz
  // R divider = 64 -> 16 MHz / 64 = 250 kHz  (yakin deger)
  // =====================================================

  // Yontem: Daha basit - dogrudan bolucu kullan
  // PLL_A = 25MHz * 36 = 900 MHz
  clockgen.setupPLL(SI5351_PLL_A, 36, 0, 1);

  // CLK0 = 900 MHz / 900 = 1 MHz, sonra /64 = ~15.6 kHz
  // Veya: CLK0 = 900 MHz / 100 = 9 MHz, sonra /64 = ~140 kHz
  // En iyisi: CLK0 = 900 MHz / 56 = ~16 MHz, /64 = 250 kHz

  // DAHA BASIT YAKLASIM - Orta frekans (gorunur olacak):
  // PLL_A = 25 MHz * 24 = 600 MHz
  clockgen.setupPLL(SI5351_PLL_A, 24, 0, 1);

  // CLK0 = 600 MHz / 750 = 800 kHz (R div /8 kullanarak)
  // setupMultisynth(output, pll, div, num, denom)
  // Gercek cikis = 600MHz / (div) / R_div

  // 600 MHz / 100 = 6 MHz -> ekranda cok hizli
  // 600 MHz / 600 = 1 MHz -> 65MSPS ile orneklemede ~65 sample/periyot, iyi!
  // 600 MHz / 300 = 2 MHz -> ~32 sample/periyot, gorunur

  // CLK0 = 600 MHz / 600 = 1 MHz  (iyi gorunecek)
  clockgen.setupMultisynth(0, SI5351_PLL_A, 600, 0, 1);

  // CLK1: Farkli frekans (CH1 icin)
  // CLK1 = 600 MHz / 300 = 2 MHz
  clockgen.setupMultisynth(1, SI5351_PLL_A, 300, 0, 1);

  // CLK2: Kapatildi
  clockgen.enableOutputs(true);

  Serial.println("Cikislar aktif:");
  Serial.println("  CLK0 = 1 MHz   -> AN9238 CH0");
  Serial.println("  CLK1 = 2 MHz   -> AN9238 CH1");
  Serial.println("");
  Serial.println("HDMI ekraninda kare dalga gorunmeli.");
  Serial.println("");
  Serial.println("Frekans degistirmek icin Serial Monitor'e yazin:");
  Serial.println("  '1' -> CLK0 = 500 kHz");
  Serial.println("  '2' -> CLK0 = 1 MHz");
  Serial.println("  '3' -> CLK0 = 2 MHz");
  Serial.println("  '4' -> CLK0 = 5 MHz");
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    switch(c) {
      case '1':
        // 500 kHz: 600 MHz / 1200
        clockgen.setupPLL(SI5351_PLL_A, 24, 0, 1);  // 600 MHz
        clockgen.setupMultisynth(0, SI5351_PLL_A, 900, 0, 1);
        Serial.println("CLK0 = ~667 kHz");
        break;
      case '2':
        // 1 MHz: 600 MHz / 600
        clockgen.setupPLL(SI5351_PLL_A, 24, 0, 1);
        clockgen.setupMultisynth(0, SI5351_PLL_A, 600, 0, 1);
        Serial.println("CLK0 = 1 MHz");
        break;
      case '3':
        // 2 MHz: 600 MHz / 300
        clockgen.setupPLL(SI5351_PLL_A, 24, 0, 1);
        clockgen.setupMultisynth(0, SI5351_PLL_A, 300, 0, 1);
        Serial.println("CLK0 = 2 MHz");
        break;
      case '4':
        // 5 MHz: 600 MHz / 120
        clockgen.setupPLL(SI5351_PLL_A, 24, 0, 1);
        clockgen.setupMultisynth(0, SI5351_PLL_A, 120, 0, 1);
        Serial.println("CLK0 = 5 MHz");
        break;
    }
  }
  delay(100);
}
