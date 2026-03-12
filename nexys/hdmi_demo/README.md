# Nexys Video HDMI Demo

Digilent Nexys Video (Artix-7 XC7A200T) FPGA kartı üzerinde HDMI giriş/çıkış demo projesi.

## Proje Hakkinda

Bu proje, Nexys Video kartının HDMI TX (çıkış) ve HDMI RX (giriş) yeteneklerini gösteren tam bir demo uygulamasıdır. MicroBlaze soft-processor üzerinde çalışan C yazılımı ile UART üzerinden interaktif bir menü arayüzü sunar.

### Sistem Mimarisi

```
                    ┌─────────────────────────────────────┐
                    │          Nexys Video FPGA            │
                    │         (Artix-7 XC7A200T)          │
                    │                                     │
  HDMI Kaynak ──────┤► HDMI RX ──► Video Capture          │
  (PC/RPi)          │              (VTC + GPIO)           │
                    │                  │                   │
                    │            AXI VDMA                  │
                    │          (Frame Buffers)             │
                    │                  │                   │
                    │           MicroBlaze                 │
                    │         (İşleme & Kontrol)           │
                    │                  │                   │
                    │            AXI VDMA                  │
                    │                  │                   │
                    │         Display Controller           │
  Monitör ◄─────────┤◄ HDMI TX ◄── (VTC + DynClk)        │
                    │                                     │
                    │    UART ◄──► Seri Terminal           │
                    └─────────────────────────────────────┘
```

### IP Blokları

| IP Bloğu | Açıklama |
|-----------|----------|
| **MicroBlaze** | Soft-processor, menü ve frame işleme kontrolü |
| **AXI VDMA** | Video DMA - frame buffer'lar arası veri transferi |
| **VTC (Video Timing Controller)** | Display ve capture zamanlama sinyalleri |
| **AXI DynClk** | Dinamik piksel clock üretimi (çözünürlük değişimi) |
| **AXI GPIO** | HDMI RX hotplug algılama |
| **AXI Interrupt Controller** | Video detect ve VTC interrupt yönetimi |
| **AXI UARTLite** | Seri terminal iletişimi (115200 baud) |

## Desteklenen Özellikler

| Menü | Özellik | Açıklama |
|------|---------|----------|
| **1** | Çözünürlük Değiştir | 640x480, 800x600, 1280x720, 1280x1024, 1920x1080 |
| **2** | Display Framebuffer Değiştir | 3 frame buffer arasında geçiş |
| **3** | Blended Test Pattern | Gradient renk deseni |
| **4** | Color Bar Test Pattern | 7 renkli çubuk deseni |
| **5** | Video Stream Başlat/Durdur | HDMI girişinden canlı video akışı |
| **6** | Video Framebuffer Değiştir | Capture buffer seçimi |
| **7** | Renk Ters Çevirme | HDMI girişini yakalar, renkleri tersler |
| **8** | Ölçekleme | HDMI girişini yakalar, display çözünürlüğüne ölçekler (bilinear interpolation) |

## Dosya Yapısı

```
hdmi_demo/
├── hw/
│   ├── hdmi_wrapper.bit          # FPGA bitstream
│   ├── hdmi_wrapper.mmi          # Memory map (ELF merge için)
│   └── app.elf                   # MicroBlaze uygulama binary
├── sw/
│   └── src/
│       ├── video_demo.c          # Ana uygulama (menü, frame işleme)
│       ├── video_demo.h          # Header dosyası
│       ├── lscript.ld            # Linker script
│       ├── display_ctrl/         # HDMI TX display controller driver
│       │   ├── display_ctrl.c
│       │   ├── display_ctrl.h
│       │   └── vga_modes.h       # Çözünürlük zamanlama parametreleri
│       ├── video_capture/        # HDMI RX video capture driver
│       │   ├── video_capture.c
│       │   └── video_capture.h
│       ├── dynclk/               # Dinamik clock driver
│       │   ├── dynclk.c
│       │   └── dynclk.h
│       ├── intc/                 # Interrupt controller driver
│       │   ├── intc.c
│       │   └── intc.h
│       └── timer_ps/             # Timer driver
│           ├── timer_ps.c
│           └── timer_ps.h
├── scripts/
│   ├── program.tcl               # FPGA programlama scripti (xsdb)
│   └── run.tcl                   # ELF merge scripti (updatemem)
└── README.md
```

## Kurulum ve Çalıştırma

### Gereksinimler

- **Donanım:** Digilent Nexys Video (Artix-7 XC7A200T)
- **Yazılım:** Xilinx Vivado 2025.1 (veya uyumlu sürüm)
- **Kablolar:** USB (JTAG/UART), HDMI kablosu, Monitör
- **Terminal:** TeraTerm veya PuTTY (115200 baud, 8N1)

### Adım 1: FPGA Programlama

```bash
# Vivado'nun xsdb aracıyla programla
C:\Xilinx\2025.1\Vivado\bin\xsdb.bat scripts/program.tcl
```

> **Not:** `program.tcl` içindeki dosya yollarını kendi ortamınıza göre güncelleyin.

### Adım 2: Seri Terminal Bağlantısı

1. TeraTerm'i açın
2. Serial port seçin (USB Serial Port)
3. Ayarlar: **115200 baud, 8 data bits, no parity, 1 stop bit**
4. Terminal > New-line: Receive = **AUTO**

### Adım 3: HDMI Giriş Bağlantısı

HDMI kaynağını (PC, Raspberry Pi, vb.) Nexys Video'nun **HDMI IN** portuna bağlayın.

- Windows PC bağlarken: **Win + P** → **Çoğalt** (Duplicate) veya **Genişlet** (Extend)
- Menüde `Video Capture Resolution` satırında çözünürlük görünmeli

### Adım 4: Demo Kullanımı

Terminal'den menü seçeneklerini kullanın:
1. **5** ile video akışını başlatın
2. **1** ile çıkış çözünürlüğünü değiştirin
3. **7** ile renk ters çevirme deneyin
4. **8** ile ölçekleme deneyin (giriş/çıkış çözünürlükleri farklı olmalı)

## Teknik Detaylar

### Frame Buffer Yapısı

- **3 adet frame buffer** (display ve capture paylaşımlı)
- **Maksimum frame boyutu:** 1920 x 1080 x 3 byte (RGB) = ~5.9 MB
- **Stride:** 5760 byte (1920 x 3)
- **128-byte aligned** (DMA uyumluluğu)

### Bilinear Interpolation (Ölçekleme)

Seçenek 8, yazılımsal bilinear interpolation kullanarak HDMI girişini display çözünürlüğüne ölçekler. MicroBlaze üzerinde float işlem yaptığı için büyük çözünürlük farkları yavaş olabilir.

### Renk Ters Çevirme

Seçenek 7, her pikselin RGB değerlerini bitwise NOT (~) ile tersler. Basit ama etkili bir görüntü işleme demonstrasyonu.

## Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| `!HDMI UNPLUGGED!` | HDMI kaynağının açık ve bağlı olduğunu kontrol edin |
| Monitörde görüntü yok | HDMI OUT kablosunu kontrol edin, **5** ile video stream başlatın |
| Terminal'de menü yok | COM port ve baud rate (115200) ayarlarını kontrol edin |
| Ölçekleme çok yavaş | Giriş/çıkış çözünürlük farkını azaltın |

## Kaynak

Bu proje [Digilent Nexys Video HDMI Demo](https://digilent.com/reference/programmable-logic/nexys-video/demos/hdmi) referans tasarımına dayanmaktadır.

- **Orijinal Yazar:** Sam Bobrowicz (Digilent)
- **Platform:** Nexys Video, Artix-7 XC7A200T
- **Araçlar:** Xilinx Vivado 2025.1, Vitis
