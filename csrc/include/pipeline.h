/*
 * pipeline.h — 2D Background Subtraction Pipeline (V3 Optimized)
 *
 * Ece'nin performans optimizasyonlari + dinamik boyut + modular API:
 *   - Quickselect: median-of-3 pivot + insertion sort fallback (n<=16)
 *   - Arena buffer: tek malloc, tekrar tekrar kullanilir
 *   - LUT-accelerated bilinear interpolasyon
 *   - Fused subtract + error map (tek gecis)
 *   - Satir buffer'li BMP yazma
 */

#ifndef PIPELINE_H
#define PIPELINE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ---- Hata kodlari ---- */
#define PL_OK          0
#define PL_ERR_PARAM  -1
#define PL_ERR_ALLOC  -2
#define PL_ERR_IO     -3

/* ---- Tipler ---- */

typedef struct {
    float *data;
    int    width;
    int    height;
} pl_image_t;

typedef struct {
    pl_image_t background;
    float      rms_median;
} pl_bkg_result_t;

typedef void (*pl_cmap_fn)(float t, uint8_t *r, uint8_t *g, uint8_t *b);

/* ---- Image lifecycle ---- */

pl_image_t pl_image_alloc(int w, int h);
void       pl_image_free(pl_image_t *img);

/* ---- Core pipeline (ece optimizasyonlari) ---- */

/**
 * Background tahmini:
 *   1. block median (quickselect, median-of-3 pivot)
 *   2. MAD * 1.4826 RMS
 *   3. grid median filtre
 *   4. LUT-accelerated bilinear interpolasyon
 */
int pl_background_estimate(const pl_image_t *input,
                           int box_size, int filter_size,
                           pl_bkg_result_t *result);

/**
 * Fused subtract + error map (tek gecis):
 *   data_sub = raw - background
 *   error    = sqrt(max(sub,0) + rn^2) + 1e-6
 */
int pl_fused_subtract_error(const pl_image_t *raw,
                            const pl_image_t *background,
                            float read_noise,
                            pl_image_t *data_sub,
                            pl_image_t *error_map);

void pl_bkg_result_free(pl_bkg_result_t *r);

/* ---- Istatistik ---- */

typedef struct {
    float min, max, mean, rms;
} pl_stats_t;

pl_stats_t pl_compute_stats(const pl_image_t *img);

/* ---- I/O: binary ---- */

int pl_image_write_bin(const char *path, const pl_image_t *img);
int pl_image_read_bin(const char *path, pl_image_t *img);

/* ---- I/O: BMP ---- */

int pl_image_read_bmp(const char *path, pl_image_t *img);
int pl_write_bmp(const char *path, const pl_image_t *img,
                 float vmin, float vmax, pl_cmap_fn cm);

/* ---- Colormaps ---- */

void pl_cmap_gray(float t, uint8_t *r, uint8_t *g, uint8_t *b);
void pl_cmap_viridis(float t, uint8_t *r, uint8_t *g, uint8_t *b);

/* ---- Yardimci ---- */

void pl_image_minmax(const pl_image_t *img, float *mn, float *mx);
void pl_image_percentile_range(const pl_image_t *img, float lo_pct, float hi_pct,
                                float *vmin, float *vmax);
pl_image_t pl_image_log_stretch(const pl_image_t *img);
pl_image_t pl_image_sqrt_stretch(const pl_image_t *img);

/* =================================================================
 *  DINAMIK (REAL-TIME) PIPELINE
 *  - Baslangicta bir kez init, her frame'de feed, sonunda destroy
 *  - Feed sirasinda SIFIR malloc
 *  - IIR temporal background guncelleme
 *  - Ring buffer: son N frame'i tutar (median background icin)
 * ================================================================= */

#define PL_RING_MAX  8  /* Ring buffer'da max frame sayisi */

typedef struct {
    /* Parametreler */
    int width, height;
    int box_size, filter_size;
    float read_noise;
    float alpha;            /* IIR katsayi: 0.05 = yavas, 0.2 = hizli */
    float threshold_sigma;  /* 3.0 = 3-sigma */

    /* On-alloc bufferlar (init'te ayrilir, feed'de tekrar kullanilir) */
    pl_image_t background;  /* Guncel background tahmini */
    pl_image_t subtracted;  /* Son frame'in subtracted hali */
    pl_image_t thresholded; /* Threshold ustu piksel */
    pl_image_t error_map;   /* Hata haritasi */

    /* Ring buffer — son N frame'i tutar */
    pl_image_t ring[PL_RING_MAX];
    int   ring_size;        /* Kullanilacak ring boyutu (1..PL_RING_MAX) */
    int   ring_head;        /* Sonraki yazilacak slot */
    int   ring_count;       /* Dolu slot sayisi */

    /* Bellek izleme */
    size_t memory_bytes;    /* Toplam ayrilmis bellek (byte) */

    float rms_median;       /* Guncel RMS */
    int   frame_count;      /* Kac frame islendi */
    int   is_initialized;   /* Background ilk frame'de hesaplandi mi */
} pl_realtime_ctx_t;

/* Frame sonucu */
typedef struct {
    int   n_above_threshold;  /* Threshold ustu piksel sayisi */
    float rms_median;
    float threshold;          /* Kullanilan threshold degeri */
    float process_time_ms;    /* Bu frame'in isleme suresi */
    size_t memory_bytes;      /* Toplam bellek kullanimi */
    int   ring_fill;          /* Ring buffer dolulugu */
} pl_frame_result_t;

/**
 * Realtime pipeline baslat — tum bellegi ayir.
 * alpha: IIR katsayi (0.05 onerili, kucuk = yavas adaptasyon)
 * ring_size: ring buffer buyuklugu (1..PL_RING_MAX, 0=devre disi)
 */
int pl_realtime_init(pl_realtime_ctx_t *ctx,
                     int width, int height,
                     int box_size, int filter_size,
                     float read_noise, float alpha,
                     float threshold_sigma,
                     int ring_size);

/**
 * Bir frame isle — SIFIR malloc.
 * Ilk frame'de tam background hesaplar, sonrakilerinde IIR gunceller.
 * Ring buffer doluysa pixel-wise median background da hesaplanir.
 * raw_data: width*height float array (disaridan, kopyalanmaz)
 */
int pl_realtime_feed(pl_realtime_ctx_t *ctx,
                     const float *raw_data,
                     pl_frame_result_t *result);

/**
 * Tum bellegi serbest birak.
 */
void pl_realtime_destroy(pl_realtime_ctx_t *ctx);

/**
 * Bellek kullanim raporu.
 */
size_t pl_realtime_memory_usage(const pl_realtime_ctx_t *ctx);

#ifdef __cplusplus
}
#endif

#endif /* PIPELINE_H */
