/*
 * pst_background.h — 2D Background Estimation Module
 *
 * Algorithm: block-median + MAD sigma + median grid filter + bilinear interpolation
 * Matches photutils.Background2D behaviour within < 0.1 ADU.
 *
 * Part of: startracker-c-pipeline
 */

#ifndef PST_BACKGROUND_H
#define PST_BACKGROUND_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ---- Return codes ---- */
#define PST_OK          0
#define PST_ERR_ALLOC  -1
#define PST_ERR_PARAM  -2
#define PST_ERR_IO     -3

/* ---- Types ---- */

/** Row-major float32 image buffer */
typedef struct {
    float *data;
    int    width;
    int    height;
} pst_image_t;

/** Configuration for background estimation */
typedef struct {
    int box_size;       /* block size in pixels (default: 64) */
    int filter_size;    /* median filter window, must be odd (default: 3) */
} pst_bkg_config_t;

/** Result of background estimation */
typedef struct {
    pst_image_t background;   /* estimated background map */
    float       rms_median;   /* median of per-block RMS values */
} pst_bkg_result_t;

/* ---- Image lifecycle ---- */

pst_image_t pst_image_alloc(int width, int height);
void        pst_image_free(pst_image_t *img);

/* ---- Core pipeline ---- */

/**
 * Estimate 2D background from input image.
 *
 * Steps:
 *   1. Divide into box_size x box_size blocks
 *   2. Per-block median (O(N) quickselect)
 *   3. Per-block MAD * 1.4826 as RMS
 *   4. Median filter on coarse grid
 *   5. Bilinear interpolation to full resolution
 */
int pst_background_estimate(
    const pst_image_t      *input,
    const pst_bkg_config_t *cfg,
    pst_bkg_result_t       *result);

/** Subtract background from input */
int pst_background_subtract(
    const pst_image_t *input,
    const pst_image_t *background,
    pst_image_t       *data_sub);

void pst_bkg_result_free(pst_bkg_result_t *r);

/* ---- I/O: raw float32 binary ---- */
/*  Format: [int32 width][int32 height][float32 * w*h], little-endian, row-major */

int pst_image_write_f32(const char *path, const pst_image_t *img);
int pst_image_read_f32(const char *path, pst_image_t *img);

#ifdef __cplusplus
}
#endif

#endif /* PST_BACKGROUND_H */
