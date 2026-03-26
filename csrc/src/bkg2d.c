/*
 * bkg2d.c — 2D Background Subtraction Library Implementation
 *
 * Extracted from v3_background.c. Contains:
 *   - image_t allocation / free
 *   - quickselect-based median
 *   - v3_background_estimate  (block median + MAD + filter + interpolation)
 *   - v3_compute_error_map
 *   - Binary I/O  (read / write)
 *   - BMP I/O     (read 24-bit / write with colormap)
 *   - Built-in colormaps (gray, viridis, redblue)
 *   - Utility helpers (minmax, log stretch)
 *
 * Compile together with main.c:
 *   gcc -Wall -O2 -o bkg2d bkg2d.c main.c -lm
 */

#include "bkg2d.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* =================================================================
 *  IMAGE LIFECYCLE
 * ================================================================= */

image_t image_alloc(int w, int h)
{
    image_t img = { NULL, w, h };
    if (w > 0 && h > 0)
        img.data = (float *)calloc((size_t)w * h, sizeof(float));
    return img;
}

void image_free(image_t *img)
{
    if (img && img->data) {
        free(img->data);
        img->data = NULL;
        img->width = img->height = 0;
    }
}

/* =================================================================
 *  QUICKSELECT — O(N) median
 * ================================================================= */

static void swap_f(float *a, float *b)
{
    float t = *a; *a = *b; *b = t;
}

static float quickselect(float *arr, int n, int k)
{
    int lo = 0, hi = n - 1;
    while (lo < hi) {
        float pivot = arr[(lo + hi) / 2];
        int i = lo, j = hi;
        while (i <= j) {
            while (arr[i] < pivot) i++;
            while (arr[j] > pivot) j--;
            if (i <= j) {
                swap_f(&arr[i], &arr[j]);
                i++; j--;
            }
        }
        if (j < k) lo = i;
        if (i > k) hi = j;
    }
    return arr[k];
}

static float fast_median(float *arr, int n)
{
    if (n <= 0) return 0.0f;
    if (n == 1) return arr[0];
    if (n == 2) return 0.5f * (arr[0] + arr[1]);

    if (n % 2 == 1)
        return quickselect(arr, n, n / 2);

    /* Even count: find lower median, then scan for upper half minimum */
    float lo = quickselect(arr, n, n / 2 - 1);
    float hi = arr[n / 2];
    for (int i = n / 2 + 1; i < n; i++)
        if (arr[i] < hi) hi = arr[i];
    return 0.5f * (lo + hi);
}

/* =================================================================
 *  V3 BACKGROUND ESTIMATE
 * ================================================================= */

int v3_background_estimate(
    const image_t *input,
    int box_size,
    int filter_size,
    bkg_result_t *result)
{
    if (!input || !input->data || !result)
        return BKG2D_ERR_PARAM;
    if (box_size < 2 || filter_size < 1 || filter_size % 2 == 0)
        return BKG2D_ERR_PARAM;

    int W = input->width;
    int H = input->height;
    int gw = (W + box_size - 1) / box_size;
    int gh = (H + box_size - 1) / box_size;
    int blk_max = box_size * box_size;

    /* Grid arrays */
    float *med_grid = (float *)calloc((size_t)gw * gh, sizeof(float));
    float *rms_grid = (float *)calloc((size_t)gw * gh, sizeof(float));

    /* Single buffer: [0..blk_max-1] = pixels, [blk_max..2*blk_max-1] = MAD copy */
    float *buf = (float *)malloc((size_t)blk_max * 2 * sizeof(float));

    if (!med_grid || !rms_grid || !buf) {
        free(med_grid); free(rms_grid); free(buf);
        return BKG2D_ERR_ALLOC;
    }

    /* Step 1-3: Block median + MAD */
    for (int gy = 0; gy < gh; gy++) {
        for (int gx = 0; gx < gw; gx++) {
            int x0 = gx * box_size;
            int y0 = gy * box_size;
            int x1 = (x0 + box_size < W) ? x0 + box_size : W;
            int y1 = (y0 + box_size < H) ? y0 + box_size : H;

            int n = 0;
            for (int y = y0; y < y1; y++)
                for (int x = x0; x < x1; x++)
                    buf[n++] = input->data[y * W + x];

            memcpy(buf + blk_max, buf, (size_t)n * sizeof(float));

            float med = fast_median(buf, n);
            med_grid[gy * gw + gx] = med;

            float *dev = buf + blk_max;
            for (int i = 0; i < n; i++)
                dev[i] = fabsf(dev[i] - med);
            float mad = fast_median(dev, n);
            rms_grid[gy * gw + gx] = mad * 1.4826f;
        }
    }
    free(buf);

    /* Step 4: Grid median filter */
    int fhalf = filter_size / 2;
    float *med_filtered = (float *)calloc((size_t)gw * gh, sizeof(float));
    if (!med_filtered) {
        free(med_grid); free(rms_grid);
        return BKG2D_ERR_ALLOC;
    }

    /* Stack buffer for filter window (filter_size <= ~9 typically) */
    float filt_buf[81]; /* supports up to 9x9 filter */

    for (int gy = 0; gy < gh; gy++) {
        for (int gx = 0; gx < gw; gx++) {
            int n = 0;
            for (int dy = -fhalf; dy <= fhalf; dy++) {
                for (int dx = -fhalf; dx <= fhalf; dx++) {
                    int nx = gx + dx, ny = gy + dy;
                    if (nx < 0)   nx = 0;
                    if (nx >= gw) nx = gw - 1;
                    if (ny < 0)   ny = 0;
                    if (ny >= gh) ny = gh - 1;
                    filt_buf[n++] = med_grid[ny * gw + nx];
                }
            }
            med_filtered[gy * gw + gx] = fast_median(filt_buf, n);
        }
    }
    free(med_grid);

    /* Step 5: Bilinear interpolation */
    result->background = image_alloc(W, H);
    if (!result->background.data) {
        free(med_filtered); free(rms_grid);
        return BKG2D_ERR_ALLOC;
    }

    for (int py = 0; py < H; py++) {
        float gy_f = ((float)py + 0.5f) / (float)box_size - 0.5f;
        int gy0 = (int)floorf(gy_f), gy1 = gy0 + 1;
        float ty = gy_f - (float)gy0;

        if (gy0 < 0)   { gy0 = 0;      gy1 = 0;      ty = 0.0f; }
        if (gy1 >= gh)  { gy1 = gh - 1; if (gy0 >= gh) gy0 = gh - 1; ty = 0.0f; }

        for (int px = 0; px < W; px++) {
            float gx_f = ((float)px + 0.5f) / (float)box_size - 0.5f;
            int gx0 = (int)floorf(gx_f), gx1 = gx0 + 1;
            float tx = gx_f - (float)gx0;

            if (gx0 < 0)   { gx0 = 0;      gx1 = 0;      tx = 0.0f; }
            if (gx1 >= gw)  { gx1 = gw - 1; if (gx0 >= gw) gx0 = gw - 1; tx = 0.0f; }

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

    /* RMS median */
    result->rms_median = fast_median(rms_grid, gw * gh);
    free(rms_grid);

    return BKG2D_OK;
}

/* =================================================================
 *  ERROR MAP
 * ================================================================= */

int v3_compute_error_map(const image_t *data_sub, float read_noise, image_t *error_out)
{
    if (!data_sub || !data_sub->data || !error_out)
        return BKG2D_ERR_PARAM;

    *error_out = image_alloc(data_sub->width, data_sub->height);
    if (!error_out->data)
        return BKG2D_ERR_ALLOC;

    float rn2 = read_noise * read_noise;
    size_t n = (size_t)data_sub->width * data_sub->height;

    for (size_t i = 0; i < n; i++) {
        float v = data_sub->data[i];
        if (v < 0.0f) v = 0.0f;
        error_out->data[i] = sqrtf(v + rn2) + 1e-6f;
    }
    return BKG2D_OK;
}

void v3_bkg_result_free(bkg_result_t *r)
{
    if (r) { image_free(&r->background); r->rms_median = 0.0f; }
}

/* =================================================================
 *  BINARY I/O
 * ================================================================= */

int image_write_bin(const char *path, const image_t *img)
{
    if (!path || !img || !img->data)
        return BKG2D_ERR_PARAM;
    FILE *f = fopen(path, "wb");
    if (!f) return BKG2D_ERR_IO;
    int32_t hdr[2] = { (int32_t)img->width, (int32_t)img->height };
    size_t n = (size_t)img->width * img->height;
    if (fwrite(hdr, sizeof(int32_t), 2, f) != 2 ||
        fwrite(img->data, sizeof(float), n, f) != n) {
        fclose(f); return BKG2D_ERR_IO;
    }
    fclose(f);
    return BKG2D_OK;
}

int image_read_bin(const char *path, image_t *img)
{
    if (!path || !img)
        return BKG2D_ERR_PARAM;
    FILE *f = fopen(path, "rb");
    if (!f) return BKG2D_ERR_IO;
    int32_t hdr[2];
    if (fread(hdr, sizeof(int32_t), 2, f) != 2) { fclose(f); return BKG2D_ERR_IO; }
    if (hdr[0] <= 0 || hdr[1] <= 0 || hdr[0] > 65536 || hdr[1] > 65536) {
        fclose(f); return BKG2D_ERR_PARAM;
    }
    *img = image_alloc(hdr[0], hdr[1]);
    if (!img->data) { fclose(f); return BKG2D_ERR_ALLOC; }
    size_t n = (size_t)hdr[0] * hdr[1];
    if (fread(img->data, sizeof(float), n, f) != n) {
        image_free(img); fclose(f); return BKG2D_ERR_IO;
    }
    fclose(f);
    return BKG2D_OK;
}

/* =================================================================
 *  BMP READ — 24-bit uncompressed -> float grayscale
 * ================================================================= */

int image_read_bmp(const char *path, image_t *img)
{
    if (!path || !img)
        return BKG2D_ERR_PARAM;

    FILE *f = fopen(path, "rb");
    if (!f) return BKG2D_ERR_IO;

    /* Read BMP file header (14 bytes) */
    uint8_t bh[14];
    if (fread(bh, 1, 14, f) != 14) { fclose(f); return BKG2D_ERR_IO; }
    if (bh[0] != 'B' || bh[1] != 'M') { fclose(f); return BKG2D_ERR_PARAM; }

    uint32_t data_offset;
    memcpy(&data_offset, &bh[10], 4);

    /* Read DIB header (at least 40 bytes for BITMAPINFOHEADER) */
    uint8_t dh[40];
    if (fread(dh, 1, 40, f) != 40) { fclose(f); return BKG2D_ERR_IO; }

    int32_t bw, bht;
    uint16_t bpp;
    uint32_t compression;
    memcpy(&bw, &dh[4], 4);
    memcpy(&bht, &dh[8], 4);
    memcpy(&bpp, &dh[14], 2);
    memcpy(&compression, &dh[16], 4);

    /* Only support 24-bit uncompressed */
    if (bpp != 24 || compression != 0) { fclose(f); return BKG2D_ERR_PARAM; }
    if (bw <= 0 || bw > 65536) { fclose(f); return BKG2D_ERR_PARAM; }

    /* Height can be negative (top-down) or positive (bottom-up) */
    int top_down = 0;
    int h = bht;
    if (h < 0) { h = -h; top_down = 1; }
    if (h <= 0 || h > 65536) { fclose(f); return BKG2D_ERR_PARAM; }

    *img = image_alloc(bw, h);
    if (!img->data) { fclose(f); return BKG2D_ERR_ALLOC; }

    /* Seek to pixel data */
    fseek(f, (long)data_offset, SEEK_SET);

    int row_bytes = ((bw * 3 + 3) / 4) * 4;
    uint8_t *row_buf = (uint8_t *)malloc((size_t)row_bytes);
    if (!row_buf) { image_free(img); fclose(f); return BKG2D_ERR_ALLOC; }

    for (int row = 0; row < h; row++) {
        if (fread(row_buf, 1, (size_t)row_bytes, f) != (size_t)row_bytes) {
            free(row_buf); image_free(img); fclose(f);
            return BKG2D_ERR_IO;
        }

        /* BMP stores rows bottom-up by default */
        int dest_y = top_down ? row : (h - 1 - row);

        for (int x = 0; x < bw; x++) {
            uint8_t b = row_buf[x * 3 + 0];
            uint8_t g = row_buf[x * 3 + 1];
            uint8_t r = row_buf[x * 3 + 2];
            /* ITU-R BT.601 luminance */
            img->data[dest_y * bw + x] = 0.299f * r + 0.587f * g + 0.114f * b;
        }
    }

    free(row_buf);
    fclose(f);
    return BKG2D_OK;
}

/* =================================================================
 *  BMP WRITE — with colormap
 * ================================================================= */

int write_bmp(const char *path, const image_t *img,
              float vmin, float vmax, cmap_fn cm)
{
    if (!path || !img || !img->data || !cm)
        return BKG2D_ERR_PARAM;

    int W = img->width, H = img->height;
    int row_bytes = ((W * 3 + 3) / 4) * 4;
    uint32_t img_size = (uint32_t)row_bytes * H;
    uint32_t file_size = 54 + img_size;

    FILE *f = fopen(path, "wb");
    if (!f) return BKG2D_ERR_IO;

    uint8_t bh[14] = {0};
    bh[0] = 'B'; bh[1] = 'M';
    memcpy(&bh[2], &file_size, 4);
    uint32_t off = 54; memcpy(&bh[10], &off, 4);
    fwrite(bh, 1, 14, f);

    uint8_t dh[40] = {0};
    uint32_t ds = 40; int32_t bw = W, bht = H; uint16_t pl = 1, bp = 24; uint32_t dpi = 2835;
    memcpy(&dh[0], &ds, 4); memcpy(&dh[4], &bw, 4); memcpy(&dh[8], &bht, 4);
    memcpy(&dh[12], &pl, 2); memcpy(&dh[14], &bp, 2);
    memcpy(&dh[20], &img_size, 4); memcpy(&dh[24], &dpi, 4); memcpy(&dh[28], &dpi, 4);
    fwrite(dh, 1, 40, f);

    float range = vmax - vmin;
    if (range < 1e-10f) range = 1.0f;
    float inv_range = 1.0f / range;

    /* Row buffer: one fwrite per row instead of per pixel */
    uint8_t *row_buf = (uint8_t *)malloc((size_t)row_bytes);
    if (!row_buf) { fclose(f); return BKG2D_ERR_ALLOC; }

    for (int y = 0; y < H; y++) {
        int sy = H - 1 - y;
        const float *src = img->data + sy * W;
        for (int x = 0; x < W; x++) {
            float t = (src[x] - vmin) * inv_range;
            if (t < 0.0f) t = 0.0f;
            if (t > 1.0f) t = 1.0f;
            uint8_t r, g, b;
            cm(t, &r, &g, &b);
            row_buf[x * 3 + 0] = b;
            row_buf[x * 3 + 1] = g;
            row_buf[x * 3 + 2] = r;
        }
        /* Zero padding bytes */
        for (int p = W * 3; p < row_bytes; p++) row_buf[p] = 0;
        fwrite(row_buf, 1, (size_t)row_bytes, f);
    }
    free(row_buf);
    fclose(f);
    return BKG2D_OK;
}

/* =================================================================
 *  COLORMAPS
 * ================================================================= */

void cmap_gray(float t, uint8_t *r, uint8_t *g, uint8_t *b)
{
    uint8_t v = (uint8_t)(t * 255.0f);
    *r = v; *g = v; *b = v;
}

void cmap_viridis(float t, uint8_t *r, uint8_t *g, uint8_t *b)
{
    struct { float p; uint8_t r, g, b; } c[] = {
        {0.0f,68,1,84},{0.25f,59,82,139},{0.5f,33,145,140},{0.75f,94,201,98},{1.0f,253,231,37}
    };
    if (t <= 0) { *r=c[0].r; *g=c[0].g; *b=c[0].b; return; }
    if (t >= 1) { *r=c[4].r; *g=c[4].g; *b=c[4].b; return; }
    for (int i = 0; i < 4; i++) {
        if (t >= c[i].p && t <= c[i+1].p) {
            float s = (t - c[i].p) / (c[i+1].p - c[i].p);
            *r = (uint8_t)(c[i].r + s * (c[i+1].r - c[i].r));
            *g = (uint8_t)(c[i].g + s * (c[i+1].g - c[i].g));
            *b = (uint8_t)(c[i].b + s * (c[i+1].b - c[i].b));
            return;
        }
    }
}

void cmap_redblue(float t, uint8_t *r, uint8_t *g, uint8_t *b)
{
    if (t < 0.5f) {
        float s = t / 0.5f;
        *r = (uint8_t)(s * 255); *g = (uint8_t)(s * 255); *b = 255;
    } else {
        float s = (t - 0.5f) / 0.5f;
        *r = 255; *g = (uint8_t)((1 - s) * 255); *b = (uint8_t)((1 - s) * 255);
    }
}

/* =================================================================
 *  UTILITIES
 * ================================================================= */

void image_find_minmax(const image_t *img, float *mn, float *mx)
{
    if (!img || !img->data || img->width <= 0 || img->height <= 0) return;
    size_t n = (size_t)img->width * img->height;
    *mn = *mx = img->data[0];
    for (size_t i = 1; i < n; i++) {
        if (img->data[i] < *mn) *mn = img->data[i];
        if (img->data[i] > *mx) *mx = img->data[i];
    }
}

image_t image_log_stretch(const image_t *img)
{
    image_t out = image_alloc(img->width, img->height);
    if (!out.data) return out;
    float mn, mx;
    image_find_minmax(img, &mn, &mx);
    size_t n = (size_t)img->width * img->height;
    for (size_t i = 0; i < n; i++)
        out.data[i] = logf(1.0f + img->data[i] - mn);
    return out;
}
