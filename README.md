# Star Tracker C Pipeline

CMV4000 sensor (2048×2048, 5.5µm) + PolarFire SoC üzerinde çalışacak
star tracker centroid pipeline'ının C implementasyonu.

**Golden reference:** [psfPhotometry](https://github.com/Meto423/photutilsPSFAnalysis) (Python/photutils)

## Hedef

- Centroid doğruluğu: ≤ 0.04 piksel (SNR > 100, ω ≤ 2°/s)
- Platform: PolarFire SoC VideoKit (RISC-V RV64GC + FPGA)

## Pipeline Aşamaları

```
Girdi (2048×2048 float32)
    ↓
[1] Background Estimation (sigma-clipped block median + bilinear interpolation)
    ↓
[2] Background Subtraction + Error Map (fused, tek geçiş)
    ↓
[3] 3-Sigma Thresholding (gürültü altı pikselleri sıfırla)
    ↓
Çıktı: subtracted, thresholded, background, error map (.bin + .bmp)
```

## Benchmark Sonuçları (15 senaryo, 2048×2048)

| Metrik | Değer |
|--------|-------|
| Ort. MAE% | 0.079% (ground truth'a göre) |
| Max MAE% | 0.16% |
| Flux koruma | ≥ 99.99% |
| Ort. süre | 38 ms/frame (OpenMP, çok çekirdek) |
| Tahmini FPS | ~27 FPS |

## Dizin Yapısı

```
csrc/
├── include/
│   └── pipeline.h              ← Public API
├── src/
│   ├── pipeline.c              ← Background extraction kütüphanesi (V3 optimized)
│   ├── pipeline_main.c         ← CLI frontend
│   ├── generate_catalog_image.py  ← Hipparcos katalog görüntü üretici
│   ├── run_test.py             ← Tek test üretici (otomatik numaralama)
│   ├── batch_test.py           ← Çoklu senaryo test
│   ├── benchmark.py            ← 15 senaryo benchmark
│   ├── bin2fits.py             ← .bin → FITS dönüştürücü (AstroImageJ için)
│   └── visualize.py            ← .bin → PNG görselleştirme
├── tests/                      ← Unit testler
└── benchmark/                  ← Karşılaştırma sonuçları
test_vectors/                   ← Binary test vektörleri
data/                           ← PSF kütüphanesi
docs/                           ← Dokümanlar
```

## Derleme

```bash
cd csrc/src

# OpenMP ile (önerilen):
gcc -std=c11 -O3 -Wall -Wextra -I../include -fopenmp -o pipeline.exe pipeline.c pipeline_main.c -lm

# OpenMP olmadan:
gcc -std=c11 -O3 -Wall -Wextra -I../include -o pipeline.exe pipeline.c pipeline_main.c -lm
```

## Kullanım

### C Pipeline

```bash
# Sentetik test görüntüsü ile:
./pipeline.exe test_image.bin -b 50 -f 3 -o output_prefix

# Parametreler:
#   -b  box_size     Block boyutu (default: 32)
#   -f  filter_size  Median filtre boyutu, tek sayı (default: 3)
#   -r  read_noise   Read noise e- RMS (default: 13.0)
#   -o  prefix       Çıktı prefix (default: "out")
```

### Test Görüntüsü Üretme

```bash
# Hipparcos kataloğundan gerçek yıldız konumlarıyla (photutils kullanmaz):
python generate_catalog_image.py --ra 83.6 --dec -5.4 --exp 0.05

# Farklı gökyüzü yönleri:
python generate_catalog_image.py --ra 0 --dec 90 --roll 15      # Kuzey kutbu
python generate_catalog_image.py --ra 266.4 --dec -29.0          # Samanyolu merkezi

# Otomatik numaralı test:
python run_test.py                          # Varsayılan parametreler
python run_test.py --stars 500 --sky 60     # Çok yıldız
python run_test.py --rn 30 --sky 80         # Yüksek gürültü
```

### AstroImageJ ile İnceleme

```bash
# .bin → FITS dönüştür (AstroImageJ float32 destekler):
python bin2fits.py tests/catalog_001/catalog_001

# AstroImageJ'de aç:
# File > Open > tests/catalog_001/catalog_001_subtracted.fits
# File > Open > tests/catalog_001/catalog_001_thresholded.fits
```

### Benchmark

```bash
python benchmark.py    # 15 farklı senaryo, sonuç tablosu + CSV
```

## Optimizasyonlar

- **Sigma clipping**: 2 iterasyon, 3-sigma — yıldız piksellerini block median'dan çıkarır
- **Quickselect**: O(n) median, median-of-3 pivot + insertion sort fallback
- **LUT bilinear interpolation**: Önceden hesaplanmış grid indeksleri
- **Fused subtract + error**: Tek geçişte çıkarma + hata haritası
- **OpenMP**: Paralel block median + paralel interpolation
- **Percentile BMP contrast**: Log stretch + %1–%99.5 clipping

## Katkıda Bulunma

1. `dev` branch'inden kendi branch'ini oluştur
2. Çalış, test et
3. `dev`'e PR aç — CI geçmeli, review bekle
4. Detaylar: [STUDENT_GUIDE.md](STUDENT_GUIDE.md)

## Dokümanlar

- [ROADMAP.md](ROADMAP.md) — Milestone'lar ve issue listesi
- [STUDENT_GUIDE.md](STUDENT_GUIDE.md) — Çalışma rehberi

## Sensor Parametreleri

| Parametre | Değer |
|-----------|-------|
| Sensor | CMV4000, 2048×2048, 5.5 µm piksel |
| Optik | EFL = 42.86 mm, F/1.59 |
| Plate scale | 26.47 arcsec/piksel |
| Read noise | 13 e⁻ RMS (CDS) |
| Dark current | 125 e⁻/px/s @ 25°C |
| Zero point flux | 2.1M e⁻/s (mag=0) |
| Exposure | 10 ms (default) |
