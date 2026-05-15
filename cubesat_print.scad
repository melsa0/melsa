// ═══════════════════════════════════════════════════════════════
//  1U CubeSat — 3D Baskı Modeli
//  Gövde: 100 × 100 × 100 mm  (standart 1U)
//  Kanatlar: ayrı parça, hinge pini ile takılır
//  Anten:  ayrı parça (ince, ayrı bas)
//
//  KULLANIM:
//    OpenSCAD → Render (F6) → Export as STL (F7)
//    PART değişkenini değiştirerek istediğin parçayı export et:
//      "body"   → Gövde (BODY_ONLY = false → kapak da dahil / true → sadece kutu)
//      "lid"    → Kapak (alt kapak, ESP32 erişimi için)
//      "panel"  → Solar kanat (2 adet bas, ayna simetrik)
//      "all"    → Hepsini bir arada gör (bas için ayrı ayrı export et)
// ═══════════════════════════════════════════════════════════════

PART = "all";   // "body" | "lid" | "panel" | "all"

$fn = 48;

// ── Boyutlar (mm) ──────────────────────────────────────────────
BODY     = 100;   // kenar uzunluğu
WALL     =   2;   // et kalınlığı
LID_H    =  12;   // alt kapak yüksekliği  (açıkta kalır, vida ile tutturulur)
LID_SLOT =   0.3; // kapak boşluk toleransı

PANEL_W  = 140;   // kanat genişliği (gövdeden dışa uzanan kısım)
PANEL_H  =  88;   // kanat yüksekliği
PANEL_T  =   3;   // kanat kalınlığı
CELL_C   =   4;   // yatay hücre sayısı
CELL_R   =   3;   // dikey hücre sayısı
GROOVE   =   0.8; // hücre çizgisi derinliği
GROOVE_W =   0.8; // hücre çizgisi genişliği

HINGE_D  =   3;   // hinge pim çapı
HINGE_L  =  20;   // hinge pim uzunluğu
HINGE_CL =   0.3; // hinge tolerans

ANT_D    =   3;   // anten çap (kök)
ANT_L    =  70;   // anten uzunluğu

// ── Yerleşim ofseti (all modunda parçaları ayır) ───────────────
SPREAD = 30;

// ═══════════════════════════════════════════════════════════════
//  GÖVDE  (hollow cube + kapak yuvası)
// ═══════════════════════════════════════════════════════════════
module body_shell() {
    difference() {
        // Dış kutu
        cube([BODY, BODY, BODY], center=true);

        // İç boşluk  (alt kapak yüksekliği kadar daha geniş)
        translate([0, 0, LID_H/2])
            cube([BODY - WALL*2,
                  BODY - WALL*2,
                  BODY - WALL*2 + LID_H], center=true);

        // Alt kapak yuvası (toleranslı)
        translate([0, 0, -(BODY/2 - LID_H/2)])
            cube([BODY - WALL*2 + LID_SLOT*2,
                  BODY - WALL*2 + LID_SLOT*2,
                  LID_H + 0.1], center=true);
    }

    // Hinge braketleri (kanatlar için, her iki yanda 2'şer adet)
    for (side = [-1, 1]) {
        for (h_pos = [-1, 1]) {
            translate([side * BODY/2,
                       h_pos * (PANEL_H/4),
                       0])
                rotate([0, 90, 0])
                    hinge_bracket(side);
        }
    }

    // Anten çıkışı (üst yüz köşeleri)
    for (sx = [-1, 1]) for (sz = [-1, 1]) {
        translate([sx * 42, BODY/2 - 1, sz * 42])
            cylinder(d = ANT_D + 1, h = 3, center=true);
    }
}

// ── Hinge braketi (gövde tarafı) ──────────────────────────────
module hinge_bracket(side) {
    // Pim için delik dahil
    difference() {
        cube([8, PANEL_T + 2, 8], center=true);
        cylinder(d = HINGE_D + HINGE_CL, h = 10, center=true);
    }
}

// ═══════════════════════════════════════════════════════════════
//  KAPAK  (alt, vida delikleri köşelerde)
// ═══════════════════════════════════════════════════════════════
module lid() {
    inner = BODY - WALL*2;
    difference() {
        union() {
            // Dış çerçeve
            difference() {
                cube([BODY, BODY, LID_H], center=true);
                cube([inner, inner, LID_H + 1], center=true);
            }
            // Alt plaka
            translate([0, 0, -LID_H/2 + WALL/2])
                cube([BODY, BODY, WALL], center=true);
        }
        // Köşe vida delikleri (M3)
        for (sx = [-1,1]) for (sy = [-1,1])
            translate([sx*(BODY/2 - 5), sy*(BODY/2 - 5), 0])
                cylinder(d=3.2, h=LID_H + 1, center=true);
    }
}

// ═══════════════════════════════════════════════════════════════
//  SOLAR KANAT  (hinge tarafı sol — sağ için mirror bas)
// ═══════════════════════════════════════════════════════════════
module solar_panel() {
    difference() {
        // Panel gövdesi
        cube([PANEL_W, PANEL_H, PANEL_T], center=true);

        // Ön yüz hücre çizgileri (dikey)
        for (c = [1 : CELL_C - 1]) {
            x = -PANEL_W/2 + c * (PANEL_W / CELL_C);
            translate([x, 0, PANEL_T/2 - GROOVE/2])
                cube([GROOVE_W, PANEL_H, GROOVE + 0.01], center=true);
        }
        // Ön yüz hücre çizgileri (yatay)
        for (r = [1 : CELL_R - 1]) {
            y = -PANEL_H/2 + r * (PANEL_H / CELL_R);
            translate([0, y, PANEL_T/2 - GROOVE/2])
                cube([PANEL_W, GROOVE_W, GROOVE + 0.01], center=true);
        }
    }

    // Hinge kulakları (gövdeye takılan taraf)
    for (h_pos = [-1, 1]) {
        translate([-PANEL_W/2 - 5,
                    h_pos * (PANEL_H/4),
                    0]) {
            difference() {
                cube([10, PANEL_T + 2, 8], center=true);
                cylinder(d = HINGE_D, h = 10, center=true);
            }
        }
    }
}

// ═══════════════════════════════════════════════════════════════
//  ANTEN  (köşe whip — 4 adet bas)
// ═══════════════════════════════════════════════════════════════
module antenna() {
    union() {
        // Gövdeye sokulacak kök
        cylinder(d = ANT_D + 1, h = 5);
        // İnce çubuk
        translate([0, 0, 5])
            cylinder(d1 = ANT_D, d2 = ANT_D * 0.4, h = ANT_L);
    }
}

// ═══════════════════════════════════════════════════════════════
//  RENDER SEÇİMİ
// ═══════════════════════════════════════════════════════════════
if (PART == "body") {
    body_shell();

} else if (PART == "lid") {
    lid();

} else if (PART == "panel") {
    solar_panel();

} else {   // "all" — görsel inceleme için
    // Gövde
    body_shell();

    // Kanatlar
    translate([ BODY/2 + PANEL_W/2 + SPREAD, 0, 0])
        rotate([0, 0, 0]) solar_panel();
    translate([-(BODY/2 + PANEL_W/2 + SPREAD), 0, 0])
        rotate([0, 0, 180]) solar_panel();

    // Kapak (gövdenin altında)
    translate([0, 0, -(BODY/2 + LID_H/2 + SPREAD)])
        lid();

    // Antenler
    for (sx = [-1,1]) for (sz = [-1,1])
        translate([sx*42, BODY/2 + 2, sz*42])
            rotate([-90, 0, 0])
                antenna();
}
