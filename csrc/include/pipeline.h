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

#ifdef __cplusplus
}
#endif

#endif /* PIPELINE_H */
