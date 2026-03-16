# Algoritma: `pst_<tip>_<isim>`

## Özet
<!-- 2-3 cümle: ne yapar, ne zaman kullanılır -->

## Kaynak Makale
- **Yazar(lar):**
- **Yıl:**
- **Başlık:**
- **Dergi/Konferans:**
- **DOI:**
- PDF: `papers/<dosya>.pdf`

## Matematiksel Formülasyon

### Giriş
- `I[x,y]`: background çıkarılmış görüntü (float32)
- `σ`: gürültü RMS
- (diğer parametreler)

### Adımlar
1. **Adım 1:** ...

   $$formül$$

2. **Adım 2:** ...

3. ...

### Çıkış
- `(x₀, y₀)`: sub-pixel centroid / detection pozisyonu
- (diğer çıkışlar)

## C Implementasyonu

- Header: `csrc/include/pst_<tip>_<isim>.h`
- Kaynak: `csrc/src/pst_<tip>_<isim>.c`
- Test: `csrc/tests/test_<isim>.c`

### Parametre Seçimi
<!-- Hangi değerleri ne zaman kullanmalısınız? -->

## Benchmark Sonuçları

| Metrik | Bu Algoritma | DAOFind (baseline) | Not |
|--------|-------------|-------------------|-----|
| Detection rate | | | |
| False positive | | | |
| Centroid scatter X | | | |
| Centroid scatter Y | | | |
| Hız (ms/frame) | | | |

Detay: `docs/benchmark_results/<isim>_<tarih>.csv`

## Avantajlar & Dezavantajlar

**Avantajlar:**
-

**Dezavantajlar:**
-

## Ne Zaman Tercih Edilmeli?
<!-- DAOFind'a göre ne fark yaratır? Hangi koşullarda daha iyi/kötü? -->
