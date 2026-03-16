# Roadmap: Star Tracker C Pipeline

CMV4000 sensor (2048×2048, 5.5µm) + PolarFire SoC star tracker için
Python golden reference'dan C'ye çeviri ve literatür algoritmaları karşılaştırması.

**Hedef doğruluk:** ≤ 0.04 px centroid scatter (SNR > 100, ω ≤ 2°/s)

---

## Milestone 1 — Altyapı & Kurulum

| # | Kapsam | Öğrenci |
|---|--------|---------|
| 1 | GitHub Actions CI (`make test`, her PR'da otomatik) | 1 |
| 2 | `pst_image_io`: libcfitsio ile FITS read/write | 1 |
| 3 | Benchmark framework: aynı test vektörleriyle N algoritma karşılaştır, CSV rapor | 1 |
| 4 | Dokümantasyon şablonu: `docs/algorithms/<isim>.md` (formüller + kaynak makale) | 1 |

---

## Milestone 2 — Baseline Pipeline (Python → C)

Mevcut Python kodunun birebir C çevirisi. Tüm unit testler geçmeli.

| # | Modül | Python Referans | Durum |
|---|-------|-----------------|-------|
| 5 | `pst_background` | `photutils.Background2D` | Yeni |
| 6 | `pst_detection` (DAOFind) | `DAOStarFinder` | Yeni |
| 7 | `pst_centroid` (COM + quadratic) | `src/main.py` | Yeni |
| 8 | `pst_error_map` | `src/sensor_params.py` | Yeni, küçük |
| 9 | `pst_psf_model` (libcfitsio) | `src/field_psf_loader.py` | Yeni |
| 10 | `pst_pipeline` orchestrator | `src/main.py` tam akış | M2 sonunda |

**Kritik not (#6):** DAOFind'da threshold `data_sub` piksel değerine uygulanır,
konvolüsyon çıktısına değil. Python referansa sadık kal.

---

## Milestone 3 — Alternatif Detection Algoritmaları (Literatür)

Her öğrenci bir makale okur, algoritmayı C'de implement eder, benchmark çalıştırır.

| # | Algoritma | Referans Makale |
|---|-----------|-----------------|
| 11 | **LoG (Laplacian of Gaussian)** | Marr & Hildreth 1980; Lindeberg 1998 |
| 12 | **Wavelet detection** (SExtractor tarzı) | Bertin & Arnouts 1996 |
| 13 | **Morphological top-hat** | Serra 1982; IRAF starfind |
| 14 | **Matched filter / optimal detection** | Alard & Lutz 1998 |

Her issue için deliverable:
1. `csrc/src/pst_detection_<isim>.c` — C implementasyonu
2. `docs/algorithms/detection_<isim>.md` — formüller + kaynak makale
3. Benchmark sonuçları (detection rate, false positive, hız)
4. `papers/<makale>.pdf` referans olarak

---

## Milestone 4 — Alternatif Centroid Algoritmaları (Literatür)

| # | Algoritma | Referans Makale |
|---|-----------|-----------------|
| 15 | **2D Gaussian fit** (iteratif LSQ) | Anderson & King 2000 |
| 16 | **Iterative windowed COM** (Irwin window) | Irwin 1985; Stone 1989 |
| 17 | **Sinc interpolation centroid** | Lauer 1999 |
| 18 | **Moment-based centroid** (flux-weighted, clipped) | Tody 1993 (IRAF) |

Her issue için deliverable:
1. `csrc/src/pst_centroid_<isim>.c` — C implementasyonu
2. `docs/algorithms/centroid_<isim>.md` — formüller + kaynak makale
3. Benchmark: centroid scatter (bias, std), hız karşılaştırması
4. Test: `test_vectors/catalog/` ile ≤ 0.04 px hedefi için SNR eşiği

---

## Milestone 5 — Karşılaştırmalı Analiz & Raporlama

| # | Kapsam |
|---|--------|
| 19 | Tüm detection algoritmaları benchmark (detection rate, FP, hız, SNR eşiği) |
| 20 | Tüm centroid algoritmaları benchmark (scatter, bias, hız, SNR eşiği) |
| 21 | Noisy full-sky validasyon (RN=13, BG=62.5 ile yeni test vektörleri) |
| 22 | Final rapor: en iyi kombinasyon önerisi, PolarFire hedefleri için değerlendirme |

---

## Milestone 6 — PolarFire Hazırlık (Uzun Vadeli)

| # | Kapsam |
|---|--------|
| 23 | `riscv64-linux-gnu-gcc` cross-compile CI |
| 24 | libcfitsio RISC-V için derleme |
| 25 | Performans profiling + hot-path optimizasyonu |

---

## Doğrulama Kriterleri

| Kriter | Hedef |
|--------|-------|
| Baseline unit testler | 100% PASS |
| Full-sky noiseless entegrasyon | 5/5 pointing PASS |
| Full-sky noisy validasyon | ≥ 8/10 pointing PASS |
| Baseline centroid scatter | < 0.04 px (SNR > 100, ω ≤ 2°/s) |
| Her literatür algoritması | Benchmark raporu + `docs/algorithms/<isim>.md` |
| CI | Her PR'da yeşil, merge öncesi zorunlu |

---

## Branch Stratejisi

```
main                         ← stable, korumalı
dev                          ← entegrasyon
feature/module-<isim>        ← baseline modüller
feature/algo-<isim>          ← literatür algoritmaları
benchmark/<isim>-vs-<isim>   ← karşılaştırma çalışmaları
```

## Öğrenci Atama Önerisi (10 öğrenci)

| Öğrenci | Milestone | Issue |
|---------|-----------|-------|
| 1 | M1 | #1 CI + #3 Benchmark framework |
| 2 | M1+M2 | #2 image_io + #4 Dokümantasyon |
| 3-4 | M2 | #5 pst_background |
| 5-6 | M2 | #6 pst_detection + #7 pst_centroid |
| 7 | M2+M3 | #8 error_map + #9 pst_psf_model |
| 8 | M3 | #11 LoG detection |
| 9 | M3 | #12 Wavelet detection |
| 10 | M4 | #15 veya #16 Centroid algoritması |

11-12. öğrenci: #10 pipeline, #13/#14 detection, #17/#18 centroid
