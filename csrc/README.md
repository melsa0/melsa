# bkg2d — 2D Background Subtraction Library

Astronomi goruntuleri icin modular 2D arka plan cikarma kutuphanesi.
Star tracker pipeline'inda ham sensor goruntusunden arka plan
gradyanini (vignetting, dark current, stray light) cikararak
yildiz sinyallerini ortaya cikarir.

## Dosya Yapisi

```
csrc/
  include/
    pst_background.h   — Production API (pst_ prefix, config struct)
    bkg2d.h             — Genisletilmis API (BMP I/O, colormap, error map)
  src/
    pst_background.c    — Core algoritma: quickselect, block median, MAD,
                           grid filter, bilinear interpolation, binary I/O
    bkg2d.c             — Tam kutuphane: background + error map + BMP + colormap
    bkg2d_main.c        — CLI frontend + sentetik test goruntu ureticisi
  Makefile              — GNU Make build
  CMakeLists.txt        — CMake build
  build.bat             — Windows build scripti
  build.sh              — Linux/macOS build scripti
```

## Hizli Baslangic

### Linux / macOS

```bash
cd csrc
make run
```

### Windows (MSYS2 / MinGW)

```bat
cd csrc
build.bat
```

### CMake

```bash
cd csrc
mkdir build && cd build
cmake ..
make
./bkg2d
```

## Kullanim

```bash
# Sentetik test goruntusu ile calistir (varsayilan 2048x2048, 80 yildiz)
./bkg2d

# BMP dosyasi yukle
./bkg2d input.bmp

# Binary dosya yukle
./bkg2d input.bin

# Parametreleri ayarla
./bkg2d input.bmp -b 128 -f 5 -r 10.0 -o result
```

### CLI Parametreleri

| Parametre | Varsayilan | Aciklama |
|-----------|-----------|----------|
| `-b size` | 64 | Block boyutu (piksel) |
| `-f size` | 3 | Median filtre penceresi (tek sayi) |
| `-r noise` | 13.0 | Okuma gurultusu (e- RMS) |
| `-o prefix` | "out" | Cikti dosya oneki |
| `-h` | — | Yardim mesaji |

## Algoritma

1. **Blok median**: Goruntu `box_size x box_size` bloklara bolunur, her blok icin O(n) quickselect ile median hesaplanir
2. **MAD (Median Absolute Deviation)**: `sigma = MAD * 1.4826` ile robust gurultu tahmini
3. **Grid median filtre**: Kaba grid uzerinde `filter_size x filter_size` median filtre
4. **Bilinear interpolasyon**: Grid'den tam cozunurluge yumusak gecis
5. **Subtract + Error**: `data_sub = raw - bkg`, `error = sqrt(max(sub,0) + rn^2)`

Photutils Background2D ile < 0.1 ADU uyumluluk.

## Ciktilar

| Dosya | Aciklama |
|-------|----------|
| `out_input.bmp` | Giris goruntusu (log-stretch, grayscale) |
| `out_background.bmp` | Arka plan haritasi (viridis) |
| `out_subtracted.bmp` | Temizlenmis goruntu (log-stretch, grayscale) |
| `out_errormap.bmp` | Hata haritasi (viridis) |
| `out_true_bkg.bmp` | Gercek arka plan — sadece sentetik modda (viridis) |
| `out_bkg_error.bmp` | Tahmin hatasi — sadece sentetik modda (redblue) |
| `out_input.bin` | Giris (binary float32) |
| `out_background.bin` | Arka plan (binary float32) |
| `out_subtracted.bin` | Temizlenmis veri (binary float32) |

## API Kullanimi (kutuphane olarak)

### pst_background (minimal API)

```c
#include "pst_background.h"

pst_image_t img = pst_image_alloc(2048, 2048);
// ... img.data'yi doldur ...

pst_bkg_config_t cfg = { .box_size = 64, .filter_size = 3 };
pst_bkg_result_t result;

int rc = pst_background_estimate(&img, &cfg, &result);
// result.background.data  -> arka plan haritasi
// result.rms_median       -> global RMS degeri

pst_image_t data_sub;
pst_background_subtract(&img, &result.background, &data_sub);

pst_image_free(&data_sub);
pst_bkg_result_free(&result);
pst_image_free(&img);
```

### bkg2d (genisletilmis API)

```c
#include "bkg2d.h"

image_t img;
image_read_bmp("input.bmp", &img);       // veya image_read_bin()

bkg_result_t result;
v3_background_estimate(&img, 64, 3, &result);

// BMP cikti
float mn, mx;
image_find_minmax(&result.background, &mn, &mx);
write_bmp("background.bmp", &result.background, mn, mx, cmap_viridis);

v3_bkg_result_free(&result);
image_free(&img);
```

## Binary Format

```
Offset  Boyut     Icerik
0       4 byte    width  (int32, little-endian)
4       4 byte    height (int32, little-endian)
8       w*h*4     piksel verileri (float32, row-major)
```
