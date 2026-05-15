// CubeSat orta raf — ESP32 + MPU6050 silikonu için düz yüzey
// Gövde içine sürüklenir, ortada kalır; komponentler üstüne silikonlanır.

$fn = 32;

INNER   = 96;    // gövde iç kenar
TOL     =  0.6;  // her kenardan boşluk (toplam 1.2mm — rahat kayar)
THICK   =  3.0;  // raf kalınlığı
HOLE_D  = 12;    // kablo geçiş delikleri çapı
USB_W   = 11;    // USB-C pencere genişliği
USB_H   =  5;    // USB-C pencere yüksekliği

W = INNER - TOL * 2;   // 94.8 mm

difference() {
    cube([W, W, THICK], center = true);

    // kablo geçiş delikleri (4 köşe)
    for (sx = [-1, 1]) for (sy = [-1, 1])
        translate([sx * (W/2 - 18), sy * (W/2 - 18), 0])
            cylinder(d = HOLE_D, h = THICK + 1, center = true);

    // merkez büyük delik (hafifletme + hava sirkülasyonu)
    cylinder(d = 30, h = THICK + 1, center = true);

    // USB-C penceresi (bir kenarda, ESP32'yi çıkarmadan programlamak için)
    translate([0, W/2 - 0.1, 0])
        cube([USB_W, THICK, USB_H], center = true);
}
