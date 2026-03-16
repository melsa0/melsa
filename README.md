# Star Tracker C Pipeline

CMV4000 sensor (2048×2048, 5.5µm) + PolarFire SoC üzerinde çalışacak
star tracker centroid pipeline'ının C implementasyonu.

**Golden reference:** [psfPhotometry](https://github.com/Meto423/photutilsPSFAnalysis) (Python/photutils)

## Hedef

- Centroid doğruluğu: ≤ 0.04 piksel (SNR > 100, ω ≤ 2°/s)
- Platform: PolarFire SoC VideoKit (RISC-V RV64GC + FPGA)

## Dizin Yapısı

```
src/                    ← Python golden reference (READ-ONLY)
csrc/
├── include/            ← Public header'lar
├── src/                ← C implementasyonları
├── tests/              ← Unit testler
└── benchmark/          ← Algoritma karşılaştırma
test_vectors/           ← Binary test vektörleri
data/                   ← PSF kütüphanesi (FITS)
docs/
├── algorithms/         ← Algoritma açıklamaları
└── benchmark_results/  ← Karşılaştırma CSV'leri
papers/                 ← Referans makaleler (PDF)
```

## Derleme & Test

```bash
sudo apt-get install gcc make libcfitsio-dev
cd csrc && make all && make test
```

## Katkıda Bulunma

1. `dev` branch'inden kendi branch'ini oluştur (`feature/module-<isim>` veya `feature/algo-<isim>`)
2. Çalış, test et (`make test` yeşil olmalı)
3. `dev`'e PR aç — CI geçmeli, review bekle
4. Detaylar: [STUDENT_GUIDE.md](STUDENT_GUIDE.md)

## Dokümanlar

- [ROADMAP.md](ROADMAP.md) — Milestone'lar ve issue listesi
- [STUDENT_GUIDE.md](STUDENT_GUIDE.md) — Çalışma rehberi
- [docs/algorithms/TEMPLATE.md](docs/algorithms/TEMPLATE.md) — Algoritma belgeleme şablonu

## Sensor Parametreleri

| Parametre | Değer |
|-----------|-------|
| Sensor | CMV4000, 2048×2048, 5.5 µm piksel |
| Optik | EFL = 42.86 mm, F/1.59 |
| Plate scale | 26.47 arcsec/piksel |
| Read noise | 13 e⁻ RMS (CDS) |
| Dark current | 125 e⁻/px/s @ 25°C |
| Exposure | 10 ms (default) |
