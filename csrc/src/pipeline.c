/*
 * pipeline.c — 2D Background Subtraction Library (V3 Optimized)
 *
 * Ece optimizasyonlari + dinamik boyut + modular API:
 *   - Quickselect: median-of-3 pivot + insertion sort fallback
 *   - Arena buffer: tek malloc, tekrar kullanim
 *   - LUT-accelerated bilinear interpolasyon
 *   - Fused subtract + error map
 *   - Satir buffer'li BMP yazma
 *
 * Derleme (kutuphane + frontend):
 *   gcc -std=c11 -O3 -Wall -Iinclude -o pipeline pipeline.c pipeline_main.c -lm
 */

#include "pipeline.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#ifdef _OPENMP
#include <omp.h>
#endif

/* =================================================================
 *  IMAGE LIFECYCLE
 * ================================================================= */

pl_image_t pl_image_alloc(int w, int h)
{
    pl_image_t img = { NULL, w, h };
    if (w > 0 && h > 0)
        img.data = (float *)calloc((size_t)w * h, sizeof(float));
    return img;
}

void pl_image_free(pl_image_t *img)
{
    if (img && img->data) {
        free(img->data);
        img->data = NULL;
        img->width = img->height = 0;
    }
}

/* =================================================================
 *  QUICKSELECT — median-of-3 pivot + insertion sort fallback
 * ================================================================= */

static inline void swapf(float *a, float *b) { float t = *a; *a = *b; *b = t; }

static void insertion_sort(float *a, int n)
{
    for (int i = 1; i < n; i++) {
        float key = a[i];
        int j = i - 1;
        while (j >= 0 && a[j] > key) { a[j + 1] = a[j]; j--; }
        a[j + 1] = key;
    }
}

static float quickselect(float *a, int n, int k)
{
    while (n > 16) {
        /* median-of-3 pivot */
        int mid = n / 2;
        if (a[0] > a[mid])   swapf(&a[0], &a[mid]);
        if (a[0] > a[n - 1]) swapf(&a[0], &a[n - 1]);
        if (a[mid] > a[n - 1]) swapf(&a[mid], &a[n - 1]);
        float pivot = a[mid];
        swapf(&a[mid], &a[n - 2]);

        int lo = 0, hi = n - 2;
        for (;;) {
            while (a[++lo] < pivot) {}
            while (a[--hi] > pivot) {}
            if (lo >= hi) break;
            swapf(&a[lo], &a[hi]);
        }
        swapf(&a[lo], &a[n - 2]);

        if      (k < lo) n = lo;
        else if (k > lo) { a += lo + 1; n -= lo + 1; k -= lo + 1; }
        else return a[lo];
    }
    insertion_sort(a, n);
    return a[k];
}

static float fast_median(float *a, int n)
{
    if (n <= 0) return 0.0f;
    if (n == 1) return a[0];
    if (n == 2) return 0.5f * (a[0] + a[1]);
    if (n % 2 == 1) return quickselect(a, n, n / 2);
    /* Even: single quickselect + linear scan */
    float m1 = quickselect(a, n, n / 2 - 1);
    float m2 = a[n / 2];
    for (int i = n / 2 + 1; i < n; i++)
        if (a[i] < m2) m2 = a[i];
    return 0.5f * (m1 + m2);
}

/* =================================================================
 *  LUT for bilinear interpolation
 * ================================================================= */

typedef struct {
    int   idx0, idx1;
    float frac;
} interp_entry_t;

static void build_lut(interp_entry_t *lut, int pixel_count, int box, int grid_count)
{
    float inv_box = 1.0f / (float)box;
    for (int p = 0; p < pixel_count; p++) {
        float g = ((float)p + 0.5f) * inv_box - 0.5f;
        int g0 = (int)floorf(g), g1 = g0 + 1;
        float t = g - (float)g0;
        if (g0 < 0)            { g0 = 0; g1 = 0; t = 0.0f; }
        if (g1 >= grid_count)  { g1 = grid_count - 1; if (g0 >= grid_count) g0 = grid_count - 1; t = 0.0f; }
        lut[p].idx0 = g0;
        lut[p].idx1 = g1;
        lut[p].frac = t;
    }
}

/* =================================================================
 *  BACKGROUND ESTIMATE
 * ================================================================= */

int pl_background_estimate(
    const pl_image_t *input,
    int box_size, int filter_size,
    pl_bkg_result_t *result)
{
    if (!input || !input->data || !result)
        return PL_ERR_PARAM;
    if (box_size < 2 || filter_size < 1 || filter_size % 2 == 0)
        return PL_ERR_PARAM;

    int W = input->width, H = input->height;
    int gw = (W + box_size - 1) / box_size;
    int gh = (H + box_size - 1) / box_size;
    int blk_max = box_size * box_size;

    /* Grid arrays */
    int grid_n = gw * gh;
    float *med_grid     = (float *)malloc((size_t)grid_n * 3 * sizeof(float));
    if (!med_grid) return PL_ERR_ALLOC;
    float *rms_grid     = med_grid + grid_n;
    float *med_filtered = rms_grid + grid_n;

    /* Step 1-2: Block median + sigma-clipped MAD (OpenMP paralel) */
    int alloc_err = 0;
    #ifdef _OPENMP
    #pragma omp parallel
    #endif
    {
        /* Her thread kendi tamponuna sahip */
        float *tbuf = (float *)malloc((size_t)blk_max * sizeof(float));
        float *tdev = (float *)malloc((size_t)blk_max * sizeof(float));
        if (!tbuf || !tdev) alloc_err = 1;

        #ifdef _OPENMP
        #pragma omp for schedule(dynamic) collapse(2)
        #endif
        for (int gy = 0; gy < gh; gy++) {
            for (int gx = 0; gx < gw; gx++) {
                if (alloc_err) continue;
                int x0 = gx * box_size, y0 = gy * box_size;
                int x1 = (x0 + box_size < W) ? x0 + box_size : W;
                int y1 = (y0 + box_size < H) ? y0 + box_size : H;

                int n = 0;
                for (int y = y0; y < y1; y++) {
                    const float * restrict row = input->data + y * W;
                    for (int x = x0; x < x1; x++)
                        tbuf[n++] = row[x];
                }

                /* 3-sigma clipping: 2 iterasyon */
                int nc = n;
                for (int iter = 0; iter < 2; iter++) {
                    /* tbuf'u bozmadan median hesapla: tdev'e kopyala */
                    for (int i = 0; i < nc; i++) tdev[i] = tbuf[i];
                    float med = fast_median(tdev, nc);
                    /* MAD hesapla */
                    for (int i = 0; i < nc; i++) tdev[i] = fabsf(tbuf[i] - med);
                    float mad = fast_median(tdev, nc);
                    float sigma_est = mad * 1.4826f;
                    if (sigma_est < 1e-10f) break;
                    float lo_clip = med - 3.0f * sigma_est;
                    float hi_clip = med + 3.0f * sigma_est;
                    int kept = 0;
                    for (int i = 0; i < nc; i++) {
                        if (tbuf[i] >= lo_clip && tbuf[i] <= hi_clip)
                            tbuf[kept++] = tbuf[i];
                    }
                    if (kept < 3) break; /* minimum piksel */
                    nc = kept;
                }

                /* Clipped median & MAD */
                for (int i = 0; i < nc; i++) tdev[i] = tbuf[i];
                float med = fast_median(tdev, nc);
                med_grid[gy * gw + gx] = med;

                for (int i = 0; i < nc; i++) tdev[i] = fabsf(tbuf[i] - med);
                float mad = fast_median(tdev, nc);
                rms_grid[gy * gw + gx] = mad * 1.4826f;
            }
        }
        free(tbuf);
        free(tdev);
    }
    if (alloc_err) { free(med_grid); return PL_ERR_ALLOC; }

    /* Step 3: Grid median filter */
    int fhalf = filter_size / 2;
    #ifdef _OPENMP
    #pragma omp parallel for schedule(static) collapse(2)
    #endif
    for (int gy = 0; gy < gh; gy++) {
        for (int gx = 0; gx < gw; gx++) {
            float fbuf[81]; /* thread-local, stack'te */
            int fn = 0;
            for (int dy = -fhalf; dy <= fhalf; dy++) {
                for (int dx = -fhalf; dx <= fhalf; dx++) {
                    int nx = gx + dx, ny = gy + dy;
                    if (nx < 0) nx = 0; else if (nx >= gw) nx = gw - 1;
                    if (ny < 0) ny = 0; else if (ny >= gh) ny = gh - 1;
                    fbuf[fn++] = med_grid[ny * gw + nx];
                }
            }
            med_filtered[gy * gw + gx] = fast_median(fbuf, fn);
        }
    }

    /* Step 4: LUT-accelerated bilinear interpolation */
    result->background = pl_image_alloc(W, H);
    if (!result->background.data) { free(med_grid); return PL_ERR_ALLOC; }

    interp_entry_t *lut_x = (interp_entry_t *)malloc((size_t)W * sizeof(interp_entry_t));
    interp_entry_t *lut_y = (interp_entry_t *)malloc((size_t)H * sizeof(interp_entry_t));
    if (!lut_x || !lut_y) {
        free(lut_x); free(lut_y); free(med_grid);
        pl_image_free(&result->background);
        return PL_ERR_ALLOC;
    }
    build_lut(lut_x, W, box_size, gw);
    build_lut(lut_y, H, box_size, gh);

    #ifdef _OPENMP
    #pragma omp parallel for schedule(static)
    #endif
    for (int py = 0; py < H; py++) {
        const int   gy0 = lut_y[py].idx0, gy1 = lut_y[py].idx1;
        const float ty  = lut_y[py].frac, ty_inv = 1.0f - ty;

        const float * restrict row0 = med_filtered + gy0 * gw;
        const float * restrict row1 = med_filtered + gy1 * gw;
        float * restrict out = result->background.data + py * W;

        /* Pre-fetch row values for cache-friendly access */
        const interp_entry_t * restrict lx = lut_x;
        for (int px = 0; px < W; px++) {
            const float tx = lx[px].frac;
            const float tx_inv = 1.0f - tx;
            const int gx0 = lx[px].idx0, gx1 = lx[px].idx1;
            out[px] = (row0[gx0] * tx_inv + row0[gx1] * tx) * ty_inv
                    + (row1[gx0] * tx_inv + row1[gx1] * tx) * ty;
        }
    }
    free(lut_x);
    free(lut_y);

    /* RMS median */
    result->rms_median = fast_median(rms_grid, gw * gh);
    free(med_grid);

    return PL_OK;
}

/* =================================================================
 *  FUSED SUBTRACT + ERROR MAP
 * ================================================================= */

int pl_fused_subtract_error(
    const pl_image_t *raw,
    const pl_image_t *background,
    float read_noise,
    pl_image_t *data_sub,
    pl_image_t *error_map)
{
    if (!raw || !raw->data || !background || !background->data || !data_sub || !error_map)
        return PL_ERR_PARAM;
    if (raw->width != background->width || raw->height != background->height)
        return PL_ERR_PARAM;

    int W = raw->width, H = raw->height;
    *data_sub  = pl_image_alloc(W, H);
    *error_map = pl_image_alloc(W, H);
    if (!data_sub->data || !error_map->data) {
        pl_image_free(data_sub); pl_image_free(error_map);
        return PL_ERR_ALLOC;
    }

    float rn2 = read_noise * read_noise;
    size_t n = (size_t)W * H;
    #ifdef _OPENMP
    #pragma omp parallel for schedule(static)
    #endif
    for (size_t i = 0; i < n; i++) {
        float sub = raw->data[i] - background->data[i];
        data_sub->data[i] = sub;
        float v = (sub > 0.0f) ? sub : 0.0f;
        error_map->data[i] = sqrtf(v + rn2) + 1e-6f;
    }
    return PL_OK;
}

void pl_bkg_result_free(pl_bkg_result_t *r)
{
    if (r) { pl_image_free(&r->background); r->rms_median = 0.0f; }
}

/* =================================================================
 *  STATISTICS
 * ================================================================= */

pl_stats_t pl_compute_stats(const pl_image_t *img)
{
    pl_stats_t s = {0};
    if (!img || !img->data || img->width <= 0) return s;
    size_t n = (size_t)img->width * img->height;
    s.min = s.max = img->data[0];
    double sum = 0.0, sum2 = 0.0;
    for (size_t i = 0; i < n; i++) {
        float v = img->data[i];
        if (v < s.min) s.min = v;
        if (v > s.max) s.max = v;
        sum  += (double)v;
        sum2 += (double)v * (double)v;
    }
    s.mean = (float)(sum / (double)n);
    s.rms  = (float)sqrt(sum2 / (double)n);
    return s;
}

/* =================================================================
 *  BINARY I/O
 * ================================================================= */

int pl_image_write_bin(const char *path, const pl_image_t *img)
{
    if (!path || !img || !img->data) return PL_ERR_PARAM;
    FILE *f = fopen(path, "wb");
    if (!f) return PL_ERR_IO;
    int32_t hdr[2] = { (int32_t)img->width, (int32_t)img->height };
    size_t n = (size_t)img->width * img->height;
    if (fwrite(hdr, sizeof(int32_t), 2, f) != 2 ||
        fwrite(img->data, sizeof(float), n, f) != n) {
        fclose(f); return PL_ERR_IO;
    }
    fclose(f);
    return PL_OK;
}

int pl_image_read_bin(const char *path, pl_image_t *img)
{
    if (!path || !img) return PL_ERR_PARAM;
    FILE *f = fopen(path, "rb");
    if (!f) return PL_ERR_IO;
    int32_t hdr[2];
    if (fread(hdr, sizeof(int32_t), 2, f) != 2) { fclose(f); return PL_ERR_IO; }
    if (hdr[0] <= 0 || hdr[1] <= 0 || hdr[0] > 65536 || hdr[1] > 65536) {
        fclose(f); return PL_ERR_PARAM;
    }
    *img = pl_image_alloc(hdr[0], hdr[1]);
    if (!img->data) { fclose(f); return PL_ERR_ALLOC; }
    size_t n = (size_t)hdr[0] * hdr[1];
    if (fread(img->data, sizeof(float), n, f) != n) {
        pl_image_free(img); fclose(f); return PL_ERR_IO;
    }
    fclose(f);
    return PL_OK;
}

/* =================================================================
 *  BMP READ — 24-bit uncompressed -> float grayscale
 * ================================================================= */

int pl_image_read_bmp(const char *path, pl_image_t *img)
{
    if (!path || !img) return PL_ERR_PARAM;
    FILE *f = fopen(path, "rb");
    if (!f) return PL_ERR_IO;

    uint8_t bh[14];
    if (fread(bh, 1, 14, f) != 14) { fclose(f); return PL_ERR_IO; }
    if (bh[0] != 'B' || bh[1] != 'M') { fclose(f); return PL_ERR_PARAM; }

    uint32_t data_offset;
    memcpy(&data_offset, &bh[10], 4);

    uint8_t dh[40];
    if (fread(dh, 1, 40, f) != 40) { fclose(f); return PL_ERR_IO; }

    int32_t bw, bht;
    uint16_t bpp;
    uint32_t compression;
    memcpy(&bw, &dh[4], 4);
    memcpy(&bht, &dh[8], 4);
    memcpy(&bpp, &dh[14], 2);
    memcpy(&compression, &dh[16], 4);

    if (bpp != 24 || compression != 0) { fclose(f); return PL_ERR_PARAM; }
    if (bw <= 0 || bw > 65536) { fclose(f); return PL_ERR_PARAM; }

    int top_down = 0, h = bht;
    if (h < 0) { h = -h; top_down = 1; }
    if (h <= 0 || h > 65536) { fclose(f); return PL_ERR_PARAM; }

    *img = pl_image_alloc(bw, h);
    if (!img->data) { fclose(f); return PL_ERR_ALLOC; }

    fseek(f, (long)data_offset, SEEK_SET);
    int row_bytes = ((bw * 3 + 3) / 4) * 4;
    uint8_t *row_buf = (uint8_t *)malloc((size_t)row_bytes);
    if (!row_buf) { pl_image_free(img); fclose(f); return PL_ERR_ALLOC; }

    for (int row = 0; row < h; row++) {
        if (fread(row_buf, 1, (size_t)row_bytes, f) != (size_t)row_bytes) {
            free(row_buf); pl_image_free(img); fclose(f); return PL_ERR_IO;
        }
        int dest_y = top_down ? row : (h - 1 - row);
        for (int x = 0; x < bw; x++) {
            uint8_t b = row_buf[x * 3], g = row_buf[x * 3 + 1], r = row_buf[x * 3 + 2];
            img->data[dest_y * bw + x] = 0.299f * r + 0.587f * g + 0.114f * b;
        }
    }
    free(row_buf);
    fclose(f);
    return PL_OK;
}

/* =================================================================
 *  BMP WRITE — row-buffered + colormap
 * ================================================================= */

int pl_write_bmp(const char *path, const pl_image_t *img,
                 float vmin, float vmax, pl_cmap_fn cm)
{
    if (!path || !img || !img->data || !cm) return PL_ERR_PARAM;

    int W = img->width, H = img->height;
    int row_bytes = ((W * 3 + 3) / 4) * 4;
    uint32_t img_size = (uint32_t)row_bytes * H;
    uint32_t file_size = 54 + img_size;

    FILE *f = fopen(path, "wb");
    if (!f) return PL_ERR_IO;

    /* BMP header */
    uint8_t bh[14] = {0};
    bh[0] = 'B'; bh[1] = 'M';
    memcpy(&bh[2], &file_size, 4);
    uint32_t off = 54; memcpy(&bh[10], &off, 4);
    fwrite(bh, 1, 14, f);

    /* DIB header */
    uint8_t dh[40] = {0};
    uint32_t ds = 40; int32_t bw = W, bht = H; uint16_t pl = 1, bp = 24; uint32_t dpi = 2835;
    memcpy(&dh[0], &ds, 4); memcpy(&dh[4], &bw, 4); memcpy(&dh[8], &bht, 4);
    memcpy(&dh[12], &pl, 2); memcpy(&dh[14], &bp, 2);
    memcpy(&dh[20], &img_size, 4); memcpy(&dh[24], &dpi, 4); memcpy(&dh[28], &dpi, 4);
    fwrite(dh, 1, 40, f);

    float range = vmax - vmin;
    if (range < 1e-10f) range = 1.0f;
    float inv_range = 1.0f / range;

    uint8_t *row_buf = (uint8_t *)malloc((size_t)row_bytes);
    if (!row_buf) { fclose(f); return PL_ERR_ALLOC; }

    for (int y = 0; y < H; y++) {
        int sy = H - 1 - y;
        const float *src = img->data + sy * W;
        for (int x = 0; x < W; x++) {
            float t = (src[x] - vmin) * inv_range;
            if (t < 0.0f) t = 0.0f;
            if (t > 1.0f) t = 1.0f;
            uint8_t r, g, b;
            cm(t, &r, &g, &b);
            row_buf[x * 3] = b; row_buf[x * 3 + 1] = g; row_buf[x * 3 + 2] = r;
        }
        for (int p = W * 3; p < row_bytes; p++) row_buf[p] = 0;
        fwrite(row_buf, 1, (size_t)row_bytes, f);
    }
    free(row_buf);
    fclose(f);
    return PL_OK;
}

/* =================================================================
 *  COLORMAPS
 * ================================================================= */

void pl_cmap_gray(float t, uint8_t *r, uint8_t *g, uint8_t *b)
{
    uint8_t v = (uint8_t)(t * 255.0f);
    *r = v; *g = v; *b = v;
}

void pl_cmap_viridis(float t, uint8_t *r, uint8_t *g, uint8_t *b)
{
    static const uint8_t tbl[][3] = {
        {68,1,84},{72,24,106},{71,46,124},{64,67,135},{53,87,140},
        {41,106,141},{31,123,141},{23,140,137},{17,156,128},{25,172,112},
        {52,186,92},{94,199,67},{147,210,36},{205,216,26},{248,210,45},{253,231,37}
    };
    int N = 16;
    if (t <= 0.0f) { *r=tbl[0][0]; *g=tbl[0][1]; *b=tbl[0][2]; return; }
    if (t >= 1.0f) { *r=tbl[N-1][0]; *g=tbl[N-1][1]; *b=tbl[N-1][2]; return; }
    float idx = t * (N - 1);
    int i = (int)idx;
    float s = idx - (float)i;
    if (i >= N - 1) { *r=tbl[N-1][0]; *g=tbl[N-1][1]; *b=tbl[N-1][2]; return; }
    *r = (uint8_t)(tbl[i][0] + s * (tbl[i+1][0] - tbl[i][0]));
    *g = (uint8_t)(tbl[i][1] + s * (tbl[i+1][1] - tbl[i][1]));
    *b = (uint8_t)(tbl[i][2] + s * (tbl[i+1][2] - tbl[i][2]));
}

/* =================================================================
 *  UTILITIES
 * ================================================================= */

void pl_image_minmax(const pl_image_t *img, float *mn, float *mx)
{
    if (!img || !img->data) return;
    size_t n = (size_t)img->width * img->height;
    *mn = *mx = img->data[0];
    for (size_t i = 1; i < n; i++) {
        if (img->data[i] < *mn) *mn = img->data[i];
        if (img->data[i] > *mx) *mx = img->data[i];
    }
}

/* Percentile hesapla (partial quickselect) */
static float percentile_(const float *data, size_t n, float pct)
{
    float *tmp = (float *)malloc(n * sizeof(float));
    if (!tmp) return 0.0f;
    memcpy(tmp, data, n * sizeof(float));
    size_t k = (size_t)(pct / 100.0f * (float)(n - 1));
    if (k >= n) k = n - 1;
    /* partial sort: quickselect */
    size_t lo = 0, hi = n - 1;
    while (lo < hi) {
        float pivot = tmp[(lo + hi) / 2];
        size_t i = lo, j = hi;
        while (i <= j) {
            while (tmp[i] < pivot) i++;
            while (tmp[j] > pivot) j--;
            if (i <= j) { float t = tmp[i]; tmp[i] = tmp[j]; tmp[j] = t; i++; if (j == 0) break; j--; }
        }
        if (j < k) lo = i;
        if (k < i) hi = (j < n) ? j : 0;
    }
    float val = tmp[k];
    free(tmp);
    return val;
}

void pl_image_percentile_range(const pl_image_t *img, float lo_pct, float hi_pct,
                                float *vmin, float *vmax)
{
    if (!img || !img->data) return;
    size_t n = (size_t)img->width * img->height;
    *vmin = percentile_(img->data, n, lo_pct);
    *vmax = percentile_(img->data, n, hi_pct);
}

pl_image_t pl_image_log_stretch(const pl_image_t *img)
{
    pl_image_t out = pl_image_alloc(img->width, img->height);
    if (!out.data) return out;
    float mn = 0.0f, mx = 0.0f;
    pl_image_minmax(img, &mn, &mx);
    size_t n = (size_t)img->width * img->height;
    for (size_t i = 0; i < n; i++)
        out.data[i] = logf(1.0f + img->data[i] - mn);
    return out;
}

pl_image_t pl_image_sqrt_stretch(const pl_image_t *img)
{
    pl_image_t out = pl_image_alloc(img->width, img->height);
    if (!out.data) return out;
    size_t n = (size_t)img->width * img->height;
    for (size_t i = 0; i < n; i++) {
        float v = img->data[i];
        out.data[i] = (v > 0.0f) ? sqrtf(v) : 0.0f;
    }
    return out;
}

/* =================================================================
 *  BAD PIXEL MASK & SATURATION
 * ================================================================= */

int pl_bad_pixel_detect(const pl_image_t *dark_frame,
                        float dead_thresh, float hot_thresh,
                        pl_image_t *mask)
{
    if (!dark_frame || !dark_frame->data || !mask) return PL_ERR_PARAM;
    int W = dark_frame->width, H = dark_frame->height;
    *mask = pl_image_alloc(W, H);
    if (!mask->data) return PL_ERR_ALLOC;

    size_t npx = (size_t)W * H;
    int n_bad = 0;
    for (size_t i = 0; i < npx; i++) {
        float v = dark_frame->data[i];
        if (v <= dead_thresh || v >= hot_thresh) {
            mask->data[i] = 1.0f;
            n_bad++;
        } else {
            mask->data[i] = 0.0f;
        }
    }
    return n_bad;
}

int pl_bad_pixel_correct(pl_image_t *image, const pl_image_t *mask)
{
    if (!image || !image->data || !mask || !mask->data) return PL_ERR_PARAM;
    int W = image->width, H = image->height;
    int corrected = 0;

    for (int y = 0; y < H; y++) {
        for (int x = 0; x < W; x++) {
            if (mask->data[y * W + x] < 0.5f) continue;
            /* Komsu ortalamasi (3x3, sadece iyi pikseller) */
            float sum = 0.0f;
            int cnt = 0;
            for (int dy = -1; dy <= 1; dy++) {
                for (int dx = -1; dx <= 1; dx++) {
                    if (dx == 0 && dy == 0) continue;
                    int nx = x + dx, ny = y + dy;
                    if (nx < 0 || nx >= W || ny < 0 || ny >= H) continue;
                    if (mask->data[ny * W + nx] > 0.5f) continue;
                    sum += image->data[ny * W + nx];
                    cnt++;
                }
            }
            if (cnt > 0) {
                image->data[y * W + x] = sum / (float)cnt;
                corrected++;
            }
        }
    }
    return corrected;
}

int pl_saturation_flag(const pl_image_t *image, float sat_level,
                       pl_image_t *sat_mask, int *n_saturated)
{
    if (!image || !image->data || !sat_mask || !n_saturated) return PL_ERR_PARAM;
    int W = image->width, H = image->height;
    *sat_mask = pl_image_alloc(W, H);
    if (!sat_mask->data) return PL_ERR_ALLOC;

    size_t npx = (size_t)W * H;
    int nsat = 0;
    for (size_t i = 0; i < npx; i++) {
        if (image->data[i] >= sat_level) {
            sat_mask->data[i] = 1.0f;
            nsat++;
        } else {
            sat_mask->data[i] = 0.0f;
        }
    }
    *n_saturated = nsat;
    return PL_OK;
}

/* =================================================================
 *  REALTIME PIPELINE
 * ================================================================= */

int pl_realtime_init(pl_realtime_ctx_t *ctx,
                     int width, int height,
                     int box_size, int filter_size,
                     float read_noise, float alpha,
                     float threshold_sigma,
                     int ring_size)
{
    if (!ctx || width <= 0 || height <= 0) return PL_ERR_PARAM;
    if (box_size < 2 || filter_size < 1 || filter_size % 2 == 0) return PL_ERR_PARAM;
    if (ring_size < 0 || ring_size > PL_RING_MAX) return PL_ERR_PARAM;

    memset(ctx, 0, sizeof(*ctx));
    ctx->width = width;
    ctx->height = height;
    ctx->box_size = box_size;
    ctx->filter_size = filter_size;
    ctx->read_noise = read_noise;
    ctx->alpha = alpha;
    ctx->threshold_sigma = threshold_sigma;
    ctx->ring_size = (ring_size > 0) ? ring_size : 0;
    ctx->ring_head = 0;
    ctx->ring_count = 0;
    ctx->frame_count = 0;
    ctx->is_initialized = 0;
    ctx->memory_bytes = 0;
    ctx->has_bad_pixel_mask = 0;
    ctx->saturation_level = 0.0f;

    size_t img_bytes = (size_t)width * height * sizeof(float);

    /* Cikti bufferlari */
    ctx->background  = pl_image_alloc(width, height);
    ctx->subtracted   = pl_image_alloc(width, height);
    ctx->thresholded  = pl_image_alloc(width, height);
    ctx->error_map    = pl_image_alloc(width, height);
    ctx->memory_bytes += 4 * img_bytes;

    if (!ctx->background.data || !ctx->subtracted.data ||
        !ctx->thresholded.data || !ctx->error_map.data) {
        pl_realtime_destroy(ctx);
        return PL_ERR_ALLOC;
    }

    /* Ring buffer ayir */
    for (int i = 0; i < ctx->ring_size; i++) {
        ctx->ring[i] = pl_image_alloc(width, height);
        if (!ctx->ring[i].data) {
            pl_realtime_destroy(ctx);
            return PL_ERR_ALLOC;
        }
        ctx->memory_bytes += img_bytes;
    }

    return PL_OK;
}

/* Ring buffer'dan pixel-wise median hesapla (sifir malloc, stack buffer) */
static void ring_median_background(pl_realtime_ctx_t *ctx)
{
    int W = ctx->width, H = ctx->height;
    size_t npx = (size_t)W * H;
    int n = ctx->ring_count;
    if (n < 2) return;

    #ifdef _OPENMP
    #pragma omp parallel for schedule(static)
    #endif
    for (size_t i = 0; i < npx; i++) {
        float vals[PL_RING_MAX];
        for (int k = 0; k < n; k++)
            vals[k] = ctx->ring[k].data[i];

        /* Insertion sort (n <= PL_RING_MAX = 8, cok hizli) */
        for (int a = 1; a < n; a++) {
            float key = vals[a];
            int b = a - 1;
            while (b >= 0 && vals[b] > key) { vals[b+1] = vals[b]; b--; }
            vals[b+1] = key;
        }
        ctx->background.data[i] = (n % 2 == 1)
            ? vals[n/2]
            : 0.5f * (vals[n/2 - 1] + vals[n/2]);
    }
}

int pl_realtime_feed(pl_realtime_ctx_t *ctx,
                     const float *raw_data,
                     pl_frame_result_t *result)
{
    if (!ctx || !raw_data || !result) return PL_ERR_PARAM;
    if (!ctx->background.data) return PL_ERR_PARAM;

    int W = ctx->width, H = ctx->height;
    size_t npx = (size_t)W * H;

    clock_t t_start = clock();

    /* Bad pixel correction (mask varsa) */
    int n_bad_corrected = 0;
    if (ctx->has_bad_pixel_mask) {
        /* raw_data const, subtracted buffer'i gecici olarak kullan */
        memcpy(ctx->subtracted.data, raw_data, npx * sizeof(float));
        n_bad_corrected = pl_bad_pixel_correct(&ctx->subtracted, &ctx->bad_pixel_mask);
        raw_data = ctx->subtracted.data; /* duzeltilmis veriyi kullan */
    }

    /* Saturation tespiti */
    int n_saturated = 0;
    if (ctx->saturation_level > 0.0f) {
        for (size_t i = 0; i < npx; i++) {
            if (raw_data[i] >= ctx->saturation_level) n_saturated++;
        }
    }

    /* Ring buffer'a frame kopyala */
    if (ctx->ring_size > 0) {
        memcpy(ctx->ring[ctx->ring_head].data, raw_data, npx * sizeof(float));
        ctx->ring_head = (ctx->ring_head + 1) % ctx->ring_size;
        if (ctx->ring_count < ctx->ring_size) ctx->ring_count++;
    }

    if (!ctx->is_initialized) {
        /* ---- ILK FRAME: tam background hesapla ---- */
        pl_image_t input_wrap = { (float *)raw_data, W, H };
        pl_bkg_result_t bkg_result;
        int rc = pl_background_estimate(&input_wrap, ctx->box_size,
                                         ctx->filter_size, &bkg_result);
        if (rc != PL_OK) return rc;

        memcpy(ctx->background.data, bkg_result.background.data,
               npx * sizeof(float));
        ctx->rms_median = bkg_result.rms_median;
        pl_bkg_result_free(&bkg_result);
        ctx->is_initialized = 1;

    } else if (ctx->ring_size > 0 && ctx->ring_count >= 3) {
        /* ---- RING BUFFER MODU: pixel-wise median ---- */
        ring_median_background(ctx);

        /* RMS guncelle */
        double sum2 = 0.0; int cnt = 0;
        float old_thresh = ctx->threshold_sigma * ctx->rms_median;
        for (size_t i = 0; i < npx; i++) {
            float sub = raw_data[i] - ctx->background.data[i];
            if (sub < old_thresh) { sum2 += (double)sub * (double)sub; cnt++; }
        }
        if (cnt > 0) ctx->rms_median = (float)sqrt(sum2 / (double)cnt);

    } else {
        /* ---- IIR MODU: hizli guncelleme ---- */
        float alpha = ctx->alpha;
        float inv_alpha = 1.0f - alpha;
        float thresh = ctx->threshold_sigma * ctx->rms_median;

        #ifdef _OPENMP
        #pragma omp parallel for schedule(static)
        #endif
        for (size_t i = 0; i < npx; i++) {
            float raw_val = raw_data[i];
            float sub = raw_val - ctx->background.data[i];
            if (sub < thresh) {
                ctx->background.data[i] = inv_alpha * ctx->background.data[i]
                                        + alpha * raw_val;
            }
        }

        /* RMS guncelle */
        double sum_diff2 = 0.0; int count = 0;
        for (size_t i = 0; i < npx; i++) {
            float sub = raw_data[i] - ctx->background.data[i];
            if (sub < thresh) { sum_diff2 += (double)sub * (double)sub; count++; }
        }
        if (count > 0) ctx->rms_median = (float)sqrt(sum_diff2 / (double)count);
    }

    /* ---- Subtract + error + threshold (tek gecis, sifir malloc) ---- */
    float thresh = ctx->threshold_sigma * ctx->rms_median;
    float rn2 = ctx->read_noise * ctx->read_noise;
    int n_above = 0;

    #ifdef _OPENMP
    #pragma omp parallel for schedule(static) reduction(+:n_above)
    #endif
    for (size_t i = 0; i < npx; i++) {
        float sub = raw_data[i] - ctx->background.data[i];
        ctx->subtracted.data[i] = sub;
        float v = (sub > 0.0f) ? sub : 0.0f;
        ctx->error_map.data[i] = sqrtf(v + rn2) + 1e-6f;
        if (sub >= thresh) { ctx->thresholded.data[i] = sub; n_above++; }
        else               { ctx->thresholded.data[i] = 0.0f; }
    }

    clock_t t_end = clock();

    ctx->frame_count++;
    result->n_above_threshold = n_above;
    result->rms_median = ctx->rms_median;
    result->threshold = thresh;
    result->process_time_ms = (float)(t_end - t_start) / (float)CLOCKS_PER_SEC * 1000.0f;
    result->memory_bytes = ctx->memory_bytes;
    result->ring_fill = ctx->ring_count;
    result->n_saturated = n_saturated;
    result->n_bad_corrected = n_bad_corrected;

    return PL_OK;
}

int pl_realtime_set_bad_pixel_mask(pl_realtime_ctx_t *ctx,
                                    const float *dark_frame,
                                    float dead_thresh, float hot_thresh)
{
    if (!ctx || !dark_frame) return PL_ERR_PARAM;
    int W = ctx->width, H = ctx->height;
    size_t npx = (size_t)W * H;

    if (!ctx->has_bad_pixel_mask) {
        ctx->bad_pixel_mask = pl_image_alloc(W, H);
        if (!ctx->bad_pixel_mask.data) return PL_ERR_ALLOC;
        ctx->memory_bytes += npx * sizeof(float);
    }

    int n_bad = 0;
    for (size_t i = 0; i < npx; i++) {
        float v = dark_frame[i];
        if (v <= dead_thresh || v >= hot_thresh) {
            ctx->bad_pixel_mask.data[i] = 1.0f;
            n_bad++;
        } else {
            ctx->bad_pixel_mask.data[i] = 0.0f;
        }
    }
    ctx->has_bad_pixel_mask = 1;
    return n_bad;
}

void pl_realtime_set_saturation(pl_realtime_ctx_t *ctx, float sat_level)
{
    if (ctx) ctx->saturation_level = sat_level;
}

void pl_realtime_destroy(pl_realtime_ctx_t *ctx)
{
    if (!ctx) return;
    pl_image_free(&ctx->background);
    pl_image_free(&ctx->subtracted);
    pl_image_free(&ctx->thresholded);
    pl_image_free(&ctx->error_map);
    if (ctx->has_bad_pixel_mask) pl_image_free(&ctx->bad_pixel_mask);
    for (int i = 0; i < PL_RING_MAX; i++)
        pl_image_free(&ctx->ring[i]);
    memset(ctx, 0, sizeof(*ctx));
}

size_t pl_realtime_memory_usage(const pl_realtime_ctx_t *ctx)
{
    if (!ctx) return 0;
    return ctx->memory_bytes;
}
