// ═══════════════════════════════════════════════════════════════
//  CubeSat İç Montaj Tepsisi
//  ESP32 DevKit (38-pin, 55×28 mm) + MPU6050 GY-521 (21×16 mm)
//
//  Tasarım kararları:
//   • ESP32  → ray klipsleri (vidaya gerek yok, PCB kenarından tutulur)
//   • MPU6050 → merkeze yerleştirilmiş platform + pimler
//   • USB-C girişi için yan duvarda pencere (programlarken çıkarmak gerekmez)
//   • Tepsi gövde içine kayar, alt kapak ile kilitlenir
//
//  PARÇA SEÇİMİ (PART değişkeni):
//    "tray"    → ESP32 + MPU6050 tepsisi  (1 adet bas)
//    "preview" → ESP32 ve MPU6050 ile birlikte önizleme
// ═══════════════════════════════════════════════════════════════

PART = "tray";

$fn = 32;

// ── CubeSat gövde iç boyutu ───────────────────────────────────
INNER = 96;       // gövde iç kenar (100mm - 2×2mm et)
TOL   =  0.4;     // tepsi-gövde toleransı
TRAY_W = INNER - TOL*2;   // 95.2 mm
TRAY_H = INNER - TOL*2;
TRAY_T =  3.0;    // taban plaka kalınlığı

// ── ESP32 DevKit v1 (38-pin) ──────────────────────────────────
// PCB boyutu — yaygın clone değerleri
E32_L   = 55.0;   // uzun kenar
E32_W   = 28.0;   // kısa kenar
E32_PCB =  1.6;   // PCB kalınlığı (standart FR4)
E32_PIN =  3.0;   // pin uzunluğu (PCB altında)
CLIP_H  =  5.0;   // klips yüksekliği (PCB + biraz fazla)
CLIP_LIP = 1.2;   // PCB üstünü tutan dudak
CLIP_W  =  8.0;   // her klipsin genişliği

// ── MPU6050 GY-521 ────────────────────────────────────────────
MPU_L   = 21.0;
MPU_W   = 16.0;
MPU_PCB =  1.6;
MPU_POST_H = 3.0; // platform yüksekliği (MPU altındaki boşluk)
MPU_PEG_D  = 1.8; // pim çapı (≈ 2mm deliğe girecek, biraz baskılı)
MPU_PEG_SX = 15.0; // delik açıklığı — kısa kenar
MPU_PEG_SY = 11.0; // delik açıklığı — uzun kenar

// ── Kablo bağı yuvaları ───────────────────────────────────────
TIE_W = 3.5;
TIE_H = 2.0;

// ── USB-C pencere boyutu ──────────────────────────────────────
USB_W = 10;   // USB-C konnektör genişliği + pay
USB_H =  5;

// ═══════════════════════════════════════════════════════════════
//  YARDIMCI MODÜLLER
// ═══════════════════════════════════════════════════════════════

// ESP32 klips (PCB kenarını tutan L-profil)
// origin: klipsin alt-sol köşesi, PCB bu profilin içine girer
module esp32_clip() {
    difference() {
        cube([CLIP_W, E32_PCB + CLIP_LIP + 1.5, CLIP_H]);
        // PCB yuvası
        translate([-0.1, 0, E32_PIN])
            cube([CLIP_W + 0.2, E32_PCB + 0.2, CLIP_H]);
        // alt girişi aç (PCB kayarken girmesi için)
        translate([-0.1, -0.1, -0.1])
            cube([CLIP_W + 0.2, E32_PCB + 0.2 + 0.1, E32_PIN + 0.1]);
    }
    // dudak (PCB üstüne basan kısım)
    translate([0, E32_PCB, E32_PIN + E32_PCB])
        cube([CLIP_W, CLIP_LIP, CLIP_H - E32_PIN - E32_PCB]);
}

// Kablo bağı yuvası
module cable_tie_slot(l = 20) {
    cube([l, TIE_W, TIE_H], center=true);
}

// MPU6050 montaj platformu (PCB'nin altı, ortada)
module mpu_platform() {
    // platform tabanı
    translate([-MPU_L/2, -MPU_W/2, 0])
        cube([MPU_L, MPU_W, MPU_POST_H]);

    // 4 köşe pimi (MPU PCB deliklerine girer, baskılı geçme)
    peg_positions = [
        [ MPU_PEG_SX/2,  MPU_PEG_SY/2],
        [ MPU_PEG_SX/2, -MPU_PEG_SY/2],
        [-MPU_PEG_SX/2,  MPU_PEG_SY/2],
        [-MPU_PEG_SX/2, -MPU_PEG_SY/2],
    ];
    for (p = peg_positions)
        translate([p[0], p[1], MPU_POST_H])
            cylinder(d = MPU_PEG_D, h = 3.5);
}

// ═══════════════════════════════════════════════════════════════
//  ANA TEPSİ
// ═══════════════════════════════════════════════════════════════
module tray() {

    difference() {
        union() {
            // ── Taban plaka ───────────────────────────────────
            cube([TRAY_W, TRAY_H, TRAY_T]);

            // ── ESP32 klipsleri ───────────────────────────────
            // ESP32, tepsinin ortasına yerleştirilmiş
            // Uzun kenar Y eksenine paralel
            esp32_cx = TRAY_W/2;   // orta X
            esp32_cy = TRAY_H/2;   // orta Y

            // Uzun kenar sol (−X)  → 2 klips
            // PCB sol kenarı: esp32_cx - E32_W/2
            left_x = esp32_cx - E32_W/2 - (E32_PCB + CLIP_LIP + 1.5);
            for (y_off = [-E32_L/4, E32_L/4]) {
                translate([left_x,
                           esp32_cy + y_off - CLIP_W/2,
                           TRAY_T])
                    esp32_clip();
            }

            // Uzun kenar sağ (+X) → 2 klips (aynalı)
            right_x = esp32_cx + E32_W/2;
            for (y_off = [-E32_L/4, E32_L/4]) {
                translate([right_x + E32_PCB + CLIP_LIP + 1.5,
                           esp32_cy + y_off - CLIP_W/2,
                           TRAY_T])
                    mirror([1,0,0]) esp32_clip();
            }

            // ── MPU6050 platformu (ESP32'nin üstünde, ortada) ─
            // ESP32 yüzeyi: TRAY_T + E32_PIN + E32_PCB ≈ 8.6 mm
            // MPU platformu bunun üstünde + 1mm ara
            mpu_z = TRAY_T + E32_PIN + E32_PCB + 1.0;
            translate([esp32_cx, esp32_cy, mpu_z])
                mpu_platform();

            // ── Kablo bağı zincirleri (tepsinin köşelerinde) ──
            // kablo bağı için çubuk + delik çifti
            for (cx = [15, TRAY_W-15]) {
                for (cy = [8, TRAY_H-8]) {
                    translate([cx, cy, TRAY_T/2])
                        cable_tie_slot(12);
                }
            }
        }

        // ── Taban delik boşaltma (hafifletme + havalandırma) ──
        for (hx = [1:3]) for (hy = [1:3]) {
            translate([hx * TRAY_W/4 - 5,
                       hy * TRAY_H/4 - 5,
                       -0.1])
                cube([10, 10, TRAY_T + 0.2]);
        }

        // ── USB-C penceresi (kısa kenar duvara gelecek yer) ───
        // ESP32 USB-C'si kısa kenarın ortasında
        // → tepsinin +Y yüzünde pencere aç (ESP32'nin kısa kenarı bu tarafa bakacak)
        esp32_cy2 = TRAY_H/2;
        usb_z = TRAY_T + E32_PIN;  // USB konnektör altı buradan başlıyor yaklaşık
        translate([TRAY_W/2 - USB_W/2,
                   TRAY_H - 0.1,
                   usb_z])
            cube([USB_W, TRAY_T + 0.2, USB_H]);
    }
}

// ═══════════════════════════════════════════════════════════════
//  ESP32 + MPU6050 TEMSİLİ (preview için, baskı için değil)
// ═══════════════════════════════════════════════════════════════
module preview_esp32() {
    color("green", 0.7)
        translate([TRAY_W/2 - E32_W/2, TRAY_H/2 - E32_L/2, TRAY_T + E32_PIN])
            cube([E32_W, E32_L, E32_PCB]);
}

module preview_mpu() {
    mpu_z = TRAY_T + E32_PIN + E32_PCB + 1.0 + MPU_POST_H;
    color("blue", 0.7)
        translate([TRAY_W/2 - MPU_L/2, TRAY_H/2 - MPU_W/2, mpu_z])
            cube([MPU_L, MPU_W, MPU_PCB]);
}

// ═══════════════════════════════════════════════════════════════
//  RENDER
// ═══════════════════════════════════════════════════════════════
if (PART == "tray") {
    tray();
} else {
    tray();
    preview_esp32();
    preview_mpu();
}
