/*
 * bkg2d.h — 2D Background Subtraction Library
 *
 * Public API for background estimation, error map computation,
 * and image I/O (binary + BMP).
 */

#ifndef BKG2D_H
#define BKG2D_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Error codes */
#define BKG2D_OK         0
#define BKG2D_ERR_PARAM -1
#define BKG2D_ERR_ALLOC -2
#define BKG2D_ERR_IO    -3

/* ---- Types ---- */

typedef struct {
    float *data;
    int    width;
    int    height;
} image_t;

typedef struct {
    image_t background;
    float   rms_median;
} bkg_result_t;

/* Colormap callback: maps t in [0,1] to RGB */
typedef void (*cmap_fn)(float t, uint8_t *r, uint8_t *g, uint8_t *b);

/* ---- Image lifecycle ---- */

image_t image_alloc(int w, int h);
void    image_free(image_t *img);

/* ---- Core pipeline ---- */

int v3_background_estimate(const image_t *input,
                           int box_size,
                           int filter_size,
                           bkg_result_t *result);

int v3_compute_error_map(const image_t *data_sub,
                         float read_noise,
                         image_t *error_out);

void v3_bkg_result_free(bkg_result_t *r);

/* ---- Image I/O: binary format ---- */
/*  Format: [int32 width][int32 height][float32 * w*h], little-endian */

int image_read_bin(const char *path, image_t *img);
int image_write_bin(const char *path, const image_t *img);

/* ---- Image I/O: BMP format ---- */

/* Read 24-bit uncompressed BMP -> float grayscale (luminance) */
int image_read_bmp(const char *path, image_t *img);

/* Write BMP with colormap, mapping [vmin, vmax] to [0,1] */
int write_bmp(const char *path, const image_t *img,
              float vmin, float vmax, cmap_fn cm);

/* ---- Built-in colormaps ---- */

void cmap_gray(float t, uint8_t *r, uint8_t *g, uint8_t *b);
void cmap_viridis(float t, uint8_t *r, uint8_t *g, uint8_t *b);
void cmap_redblue(float t, uint8_t *r, uint8_t *g, uint8_t *b);

/* ---- Utilities ---- */

void image_find_minmax(const image_t *img, float *mn, float *mx);
image_t image_log_stretch(const image_t *img);

#ifdef __cplusplus
}
#endif

#endif /* BKG2D_H */
