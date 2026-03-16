# Öğrenci Rehberi: Star Tracker C Pipeline

Bu belgede projeye nasıl katkı yapacağın, issue nasıl alacağın ve
algoritma implementasyonuna nasıl başlayacağın anlatılıyor.

---

## Genel Bakış

Python'da yazılmış bir star tracker centroid pipeline'ı var.
Senin görevin:
- Python kodunu C'ye çevirmek (baseline modüller), **veya**
- Literatürdeki alternatif bir algoritmayı C'de implement etmek

Her iki durumda da aynı test vektörleri kullanılıyor ve benchmark ile doğrulama yapılıyor.

---

## Başlamadan Önce

### Repo'yu kur

```bash
git clone <repo_url>
cd startracker-c-pipeline
cd csrc && make all    # derleme çalışıyor mu
make test              # mevcut testler geçiyor mu
```

**Bağımlılıklar:**
```bash
sudo apt-get install gcc make libcfitsio-dev
```

### Python referansını anla

`src/` altındaki Python kodu golden reference. C'nin üretmesi gereken sonuçlar
buradan geliyor. Kodun ne yaptığını anlamadan C yazmaya başlama.

---

## Issue Alma & Çalışma Akışı

1. **Kanban'dan bir issue al** — "In Progress"'e taşı, kendine ata
2. **Branch oluştur:**
   ```bash
   git checkout dev
   git pull
   git checkout -b feature/module-<isim>   # baseline modül için
   git checkout -b feature/algo-<isim>     # literatür algoritması için
   ```
3. **Çalış** (aşağıdaki rehbere bak)
4. **Test et** — `make test` yeşil olmalı
5. **PR aç** `dev` branch'ine — CI geçmeli, review bekle
6. **Merge sonrası** issue'yu "Done"'a taşı

---

## Baseline Modül Yazma (Milestone 2)

Python kodunu C'ye çevirirken:

1. **Python fonksiyonunu oku** — ne aldığını, ne döndürdüğünü anla
2. **Mevcut header'a bak** — `csrc/include/pst_<isim>.h` API tanımı
3. **`csrc/src/pst_<isim>.c` yaz** — header'daki imzaları implement et
4. **Test vektörü üret** — Python ile referans çıktı üret, `test_vectors/` altına koy
5. **C testini yaz:** `csrc/tests/test_<isim>.c` — Python çıktısıyla karşılaştır
6. **Kabul kriteri:** Python ile fark < 0.01 piksel (centroid), < 0.1 ADU (background)

### Örnek: pst_centroid (Issue #7)

Python referans: `src/main.py` — centroid hesaplama

```python
# Python'da ne oluyor:
# 1. detection pozisyonunu al (x0, y0)
# 2. box_size x box_size pencerede COM hesapla
# 3. COM sonucundan quadratic refine
```

C'de yapman gereken: `pst_centroid_com()` ve `pst_centroid_quadratic()`.

---

## Literatür Algoritması Yazma (Milestone 3-4)

### Adım 1: Makaleyi bul ve oku

- NASA ADS: [ui.adsabs.harvard.edu](https://ui.adsabs.harvard.edu)
- arXiv: [arxiv.org](https://arxiv.org)
- IEEE Xplore, Google Scholar

Algoritmanın matematiksel adımlarını kağıda yaz. Anlamadan kod yazma.

### Adım 2: `docs/algorithms/<isim>.md` yaz

Template: [docs/algorithms/TEMPLATE.md](docs/algorithms/TEMPLATE.md)

Şunları mutlaka yaz:
- Algoritmanın ne yaptığı (2-3 cümle)
- Matematiksel formüller
- Parametrelerin ne anlama geldiği
- Avantaj ve dezavantajlar

### Adım 3: Python'da hızlıca dene (opsiyonel ama tavsiye edilir)

```python
# src/prototype_<isim>.py
import numpy as np
from scipy import ndimage
# Algoritmayı burada dene, sonuçları DAOFind ile karşılaştır
```

### Adım 4: C'yi yaz

```
csrc/include/pst_<tip>_<isim>.h   ← API tanımı
csrc/src/pst_<tip>_<isim>.c       ← implementasyon
csrc/tests/test_<isim>.c          ← unit test
```

`<tip>`: `detection` veya `centroid`

### Adım 5: Benchmark çalıştır

```bash
cd csrc && make benchmark
# Çıktı: docs/benchmark_results/benchmark_latest.csv
```

Sonuçları issue'ya yorum olarak ekle ve `docs/benchmark_results/` altına commit'le.

---

## Test Vektörleri

| Dizin | İçerik |
|-------|--------|
| `test_vectors/background/` | Background estimation (512×512) |
| `test_vectors/detection/` | DAOFind detection |
| `test_vectors/catalog/` | Benchmark için tam katalog |
| `test_vectors/fullsky_noiseless/` | 5 pointing, noiseless |
| `test_vectors/fullsky_noisy/` | 10 pointing, RN=13, BG=62.5 |

Binary format: `float32`, row-major, `width × height`

---

## AI Agent Kullanımı

Takıldığında şunu kullan:

```
psfPhotometry projesinde <algoritma_adı> C implementasyonu yapıyorum.

Referans: <makale_adı> (<yıl>)
Test vektörleri: test_vectors/catalog/
Mevcut baseline: csrc/src/pst_detection.c (DAOFind)

<spesifik sorum>
```

AI çıktısını direkt commit'leme — önce anla, test et, sonra merge et.

---

## Kodlama Kuralları

- **Dil:** C11 (`-std=c11`)
- **Uyarılar:** `-Wall -Wextra -Wpedantic` ile sıfır uyarı
- **Return kodları:** `PST_OK`, `PST_ERR_ALLOC`, `PST_ERR_PARAM`, `PST_ERR_IO`
- **Bellek:** `malloc` ettiklerini `free`'le, leak bırakma
- **Yorum:** Neden yaptığını yaz, ne yaptığını değil
- **Threshold:** Her zaman `data_sub` piksel değerine uygula (convolved'a değil)

---

## Sık Yapılan Hatalar

**1. Threshold'u yanlış yere uygulamak**

```c
// YANLIŞ — convolved görüntüde threshold
if (convolved[y][x] < threshold) continue;

// DOĞRU — data_sub'da threshold
if (data_sub[y][x] < threshold) continue;
```

**2. PSF'i PRF'e çevirmemek**

Görüntü render'larken PSF'i doğrudan kullanma. `pst_psf_model`
PRF dönüşümünü (pixel integration) yapıyor.

**3. Centroid hedefi**

0.04 px hedefi yalnızca SNR > 100 ve ω ≤ 2°/s için geçerli.
5°/s'de bu hedefi yakalamak fiziksel olarak imkânsız — bu bir hata değil.

---

## Yardım & İletişim

- Takıldığında önce `docs/algorithms/` belgelerine bak
- Python referans kodunu oku: `src/`
- Issue'ya yorum yaz — review sırasında konuşuruz
- Kanban'da "Blocked" kolonu var, oraya taşı ve neden bloklu olduğunu yaz
