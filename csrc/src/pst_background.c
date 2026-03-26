/*
 * pst_background.c — 2D Background Estimation (photutils.Background2D equivalent)
 *
 * Algorithm:
 *   1. Divide image into box_size x box_size blocks
 *   2. Per-block median  (O(N) quickselect)
 *   3. Per-block MAD * 1.4826 as RMS estimate
 *   4. Median filter on the coarse grid
 *   5. Bilinear interpolation to full resolution
 *
 * Acceptance: background values must match Python photutils output within < 0.1 ADU.
 *
 * Compile: gcc -std=c11 -Wall -Wextra -Wpedantic -O2 -c pst_background.c -lm
 */

#include "pst_background.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* =================================================================
 *  IMAGE LIFECYCLE
 * ================================================================= */

pst_image_t pst_image_alloc(int width, int height)
{
    pst_image_t img = { NULL, width, height };
    if (width > 0 && height > 0) {
        img.data = (float *)calloc((size_t)width * (size_t)height, sizeof(float));
    }
    return img;
}

void pst_image_free(pst_image_t *img)
{
    if (img && img->data) {
        free(img->data);
        img->data   = NULL;
        img->width  = 0;
        img->height = 0;
    }
}

/* =================================================================
 *  QUICKSELECT — O(N) MEDIAN
 * ================================================================= */

static void swap_f(float *a, float *b)
{
    float t = *a;
    *a = *b;
    *b = t;
}

static float quickselect(float *arr, int n, int k)
{
    int lo = 0, hi = n - 1;
    while (lo < hi) {
        float pivot = arr[(lo + hi) / 2];
        int i = lo, j = hi;
        while (i <= j) {
            while (arr[i] < pivot) { i++; }
            while (arr[j] > pivot) { j--; }
            if (i <= j) {
                swap_f(&arr[i], &arr[j]);
                i++;
                j--;
            }
        }
        if (j < k) { lo = i; }
        if (i > k) { hi = j; }
    }
    return arr[k];
}

static float fast_median(float *arr, int n)
{
    if (n <= 0) { return 0.0f; }
    if (n == 1) { return arr[0]; }
    if (n == 2) { return 0.5f * (arr[0] + arr[1]); }

    if (n % 2 == 1) {
        return quickselect(arr, n, n / 2);
    }
    float lo = quickselect(arr, n, n / 2 - 1);
    float hi = quickselect(arr, n, n / 2);
    return 0.5f * (lo + hi);
}

/* =================================================================
 *  BACKGROUND ESTIMATION
 * ================================================================= */

int pst_background_estimate(
    const pst_image_t      *input,
    const pst_bkg_config_t *cfg,
    pst_bkg_result_t       *result)
{
    /* --- Parameter validation --- */
    if (!input || !input->data || !cfg || !result) {
        return PST_ERR_PARAM;
    }
    int box_size    = cfg->box_size;
    int filter_size = cfg->filter_size;

    if (box_size < 2 || filter_size < 1 || filter_size % 2 == 0) {
        return PST_ERR_PARAM;
    }

    int W = input->width;
    int H = input->height;

    /* Number of grid cells */
    int gw = (W + box_size - 1) / box_size;
    int gh = (H + box_size - 1) / box_size;
    int blk_max = box_size * box_size;

    /* Allocate grid arrays */
    float *med_grid = (float *)calloc((size_t)gw * (size_t)gh, sizeof(float));
    float *rms_grid = (float *)calloc((size_t)gw * (size_t)gh, sizeof(float));

    /* Working buffer: [0..blk_max-1] = pixel values, [blk_max..2*blk_max-1] = MAD copy */
    float *buf = (float *)malloc((size_t)blk_max * 2 * sizeof(float));

    if (!med_grid || !rms_grid || !buf) {
        free(med_grid);
        free(rms_grid);
        free(buf);
        return PST_ERR_ALLOC;
    }

    /* --- Step 1-3: Block median + MAD --- */
    for (int gy = 0; gy < gh; gy++) {
        for (int gx = 0; gx < gw; gx++) {
            int x0 = gx * box_size;
            int y0 = gy * box_size;
            int x1 = (x0 + box_size < W) ? x0 + box_size : W;
            int y1 = (y0 + box_size < H) ? y0 + box_size : H;

            int n = 0;
            for (int y = y0; y < y1; y++) {
                for (int x = x0; x < x1; x++) {
                    buf[n++] = input->data[y * W + x];
                }
            }

            /* Keep a copy for MAD computation */
            memcpy(buf + blk_max, buf, (size_t)n * sizeof(float));

            float med = fast_median(buf, n);
            med_grid[gy * gw + gx] = med;

            /* MAD = median(|x_i - median|), sigma ~ MAD * 1.4826 */
            float *dev = buf + blk_max;
            for (int i = 0; i < n; i++) {
                dev[i] = fabsf(dev[i] - med);
            }
            float mad = fast_median(dev, n);
            rms_grid[gy * gw + gx] = mad * 1.4826f;
        }
    }
    free(buf);

    /* --- Step 4: Median filter on coarse grid --- */
    int fhalf = filter_size / 2;
    float *med_filtered = (float *)calloc((size_t)gw * (size_t)gh, sizeof(float));
    if (!med_filtered) {
        free(med_grid);
        free(rms_grid);
        return PST_ERR_ALLOC;
    }

    /* Stack buffer for filter window (supports up to 9x9 filter) */
    float filt_buf[81];

    for (int gy = 0; gy < gh; gy++) {
        for (int gx = 0; gx < gw; gx++) {
            int n = 0;
            for (int dy = -fhalf; dy <= fhalf; dy++) {
                for (int dx = -fhalf; dx <= fhalf; dx++) {
                    int nx = gx + dx;
                    int ny = gy + dy;
                    /* Clamp to grid boundaries */
                    if (nx < 0)   { nx = 0; }
                    if (nx >= gw) { nx = gw - 1; }
                    if (ny < 0)   { ny = 0; }
                    if (ny >= gh) { ny = gh - 1; }
                    filt_buf[n++] = med_grid[ny * gw + nx];
                }
            }
            med_filtered[gy * gw + gx] = fast_median(filt_buf, n);
        }
    }
    free(med_grid);

    /* --- Step 5: Bilinear interpolation to full resolution --- */
    result->background = pst_image_alloc(W, H);
    if (!result->background.data) {
        free(med_filtered);
        free(rms_grid);
        return PST_ERR_ALLOC;
    }

    for (int py = 0; py < H; py++) {
        float gy_f = ((float)py + 0.5f) / (float)box_size - 0.5f;
        int gy0 = (int)floorf(gy_f);
        int gy1 = gy0 + 1;
        float ty = gy_f - (float)gy0;

        if (gy0 < 0)  { gy0 = 0;      gy1 = 0;      ty = 0.0f; }
        if (gy1 >= gh) { gy1 = gh - 1; if (gy0 >= gh) { gy0 = gh - 1; } ty = 0.0f; }

        for (int px = 0; px < W; px++) {
            float gx_f = ((float)px + 0.5f) / (float)box_size - 0.5f;
            int gx0 = (int)floorf(gx_f);
            int gx1 = gx0 + 1;
            float tx = gx_f - (float)gx0;

            if (gx0 < 0)  { gx0 = 0;      gx1 = 0;      tx = 0.0f; }
            if (gx1 >= gw) { gx1 = gw - 1; if (gx0 >= gw) { gx0 = gw - 1; } tx = 0.0f; }

            float v00 = med_filtered[gy0 * gw + gx0];
            float v10 = med_filtered[gy0 * gw + gx1];
            float v01 = med_filtered[gy1 * gw + gx0];
            float v11 = med_filtered[gy1 * gw + gx1];

            result->background.data[py * W + px] =
                v00 * (1.0f - tx) * (1.0f - ty)
              + v10 * tx          * (1.0f - ty)
              + v01 * (1.0f - tx) * ty
              + v11 * tx          * ty;
        }
    }
    free(med_filtered);

    /* --- RMS median (global) --- */
    result->rms_median = fast_median(rms_grid, gw * gh);
    free(rms_grid);

    return PST_OK;
}

/* =================================================================
 *  BACKGROUND SUBTRACTION
 * ================================================================= */

int pst_background_subtract(
    const pst_image_t *input,
    const pst_image_t *background,
    pst_image_t       *data_sub)
{
    if (!input || !input->data || !background || !background->data || !data_sub) {
        return PST_ERR_PARAM;
    }
    if (input->width != background->width || input->height != background->height) {
        return PST_ERR_PARAM;
    }

    int W = input->width;
    int H = input->height;

    *data_sub = pst_image_alloc(W, H);
    if (!data_sub->data) {
        return PST_ERR_ALLOC;
    }

    size_t n = (size_t)W * (size_t)H;
    for (size_t i = 0; i < n; i++) {
        data_sub->data[i] = input->data[i] - background->data[i];
    }

    return PST_OK;
}

/* =================================================================
 *  CLEANUP
 * ================================================================= */

void pst_bkg_result_free(pst_bkg_result_t *r)
{
    if (r) {
        pst_image_free(&r->background);
        r->rms_median = 0.0f;
    }
}

/* =================================================================
 *  I/O: RAW FLOAT32 BINARY
 *  Format: [int32 width][int32 height][float32 * w*h], little-endian, row-major
 *  Compatible with test_vectors/ in startracker-c-pipeline.
 * ================================================================= */

int pst_image_write_f32(const char *path, const pst_image_t *img)
{
    if (!path || !img || !img->data) {
        return PST_ERR_PARAM;
    }
    FILE *f = fopen(path, "wb");
    if (!f) { return PST_ERR_IO; }

    int32_t hdr[2] = { (int32_t)img->width, (int32_t)img->height };
    fwrite(hdr, sizeof(int32_t), 2, f);
    fwrite(img->data, sizeof(float), (size_t)img->width * (size_t)img->height, f);
    fclose(f);
    return PST_OK;
}

int pst_image_read_f32(const char *path, pst_image_t *img)
{
    if (!path || !img) {
        return PST_ERR_PARAM;
    }
    FILE *f = fopen(path, "rb");
    if (!f) { return PST_ERR_IO; }

    int32_t hdr[2];
    if (fread(hdr, sizeof(int32_t), 2, f) != 2) {
        fclose(f);
        return PST_ERR_IO;
    }
    if (hdr[0] <= 0 || hdr[1] <= 0 || hdr[0] > 65536 || hdr[1] > 65536) {
        fclose(f);
        return PST_ERR_PARAM;
    }

    *img = pst_image_alloc(hdr[0], hdr[1]);
    if (!img->data) {
        fclose(f);
        return PST_ERR_ALLOC;
    }

    size_t n = (size_t)hdr[0] * (size_t)hdr[1];
    if (fread(img->data, sizeof(float), n, f) != n) {
        pst_image_free(img);
        fclose(f);
        return PST_ERR_IO;
    }
    fclose(f);
    return PST_OK;
}
