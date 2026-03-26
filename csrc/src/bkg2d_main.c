/*
 * bkg2d_main.c — CLI frontend for bkg2d library
 *
 * Usage:
 *   ./bkg2d input.bmp              (load 24-bit BMP)
 *   ./bkg2d input.bin              (load binary float image)
 *   ./bkg2d                        (generate synthetic test image)
 *   ./bkg2d input.bmp -b 128 -f 5 -r 10.0 -o result
 *
 * Options:
 *   -b box_size      Background block size (default 64)
 *   -f filter_size   Grid median filter size, odd (default 3)
 *   -r read_noise    Read noise in e- RMS (default 13.0)
 *   -o prefix        Output file prefix (default "out")
 *
 * Compile:
 *   gcc -Wall -O2 -o bkg2d bkg2d.c bkg2d_main.c -lm
 */

#include "bkg2d.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

/* ---- Defaults ---- */
#define DEFAULT_BOX_SIZE    64
#define DEFAULT_FILTER_SIZE 3
#define DEFAULT_READ_NOISE  13.0f
#define DEFAULT_PREFIX      "out"

/* Test image parameters */
#define SENSOR_W        2048
#define SENSOR_H        2048
#define DARK_CURRENT    125.0f
#define ZERO_POINT_FLUX 2100000.0f
#define DEFAULT_EXP     0.100f
#define MAG_LIMIT       6.0f
#define N_STARS         80
#define PI_F            3.14159265f
#define READ_NOISE_TEST 13.0f

/* =================================================================
 *  RNG + TEST IMAGE GENERATOR
 * ================================================================= */

static uint64_t rng_state = 88172645463325252ULL;

static double rng_uniform(void)
{
    rng_state ^= rng_state << 13;
    rng_state ^= rng_state >> 7;
    rng_state ^= rng_state << 17;
    return (double)(rng_state & 0x1FFFFFFFFFFFFFULL) / (double)0x1FFFFFFFFFFFFFULL;
}

static double rng_gauss(void)
{
    return sqrt(-2.0 * log(rng_uniform() + 1e-15)) * cos(2.0 * PI_F * rng_uniform());
}

static int rng_poisson(double lam)
{
    if (lam <= 0) return 0;
    if (lam > 500) {
        double v = lam + sqrt(lam) * rng_gauss();
        return v < 0 ? 0 : (int)(v + 0.5);
    }
    double L = exp(-lam); int k = 0; double p = 1.0;
    do { k++; p *= rng_uniform(); } while (p > L);
    return k - 1;
}

static void generate_test_image(image_t *img, image_t *true_bkg)
{
    int IW = img->width, IH = img->height;
    float cx = IW / 2.0f, cy = IH / 2.0f;
    float max_r = sqrtf(cx * cx + cy * cy);
    float base_bg = DARK_CURRENT * DEFAULT_EXP;

    for (int y = 0; y < IH; y++)
        for (int x = 0; x < IW; x++) {
            float dx = (float)x - cx, dy = (float)y - cy;
            float r = sqrtf(dx*dx + dy*dy) / max_r;
            float bg = base_bg * (1.0f - 0.10f * r * r);
            true_bkg->data[y * IW + x] = bg;
            img->data[y * IW + x] = bg;
        }

    float sigma = 1.7f, sig2 = 2.0f * sigma * sigma;
    int radius = (int)(5.0f * sigma);

    for (int s = 0; s < N_STARS; s++) {
        float sx = (float)(rng_uniform() * (IW - 20) + 10);
        float sy = (float)(rng_uniform() * (IH - 20) + 10);
        float mag = 2.0f + (float)(rng_uniform() * (MAG_LIMIT - 2.0f));
        float flux = ZERO_POINT_FLUX * powf(10.0f, -0.4f * mag) * DEFAULT_EXP;
        int icx = (int)sx, icy = (int)sy;
        float subx = sx - icx, suby = sy - icy;
        for (int dy = -radius; dy <= radius; dy++)
            for (int dx = -radius; dx <= radius; dx++) {
                int px = icx + dx, py = icy + dy;
                if (px < 0 || px >= IW || py < 0 || py >= IH) continue;
                float rx = (float)dx - subx, ry = (float)dy - suby;
                img->data[py * IW + px] += flux * expf(-(rx*rx + ry*ry) / sig2);
            }
    }

    size_t npix = (size_t)IW * IH;
    for (size_t i = 0; i < npix; i++)
        img->data[i] = (float)((double)rng_poisson((double)img->data[i])
                               + READ_NOISE_TEST * rng_gauss());
}

/* =================================================================
 *  HELPERS
 * ================================================================= */

static double timer_ms(clock_t s, clock_t e)
{
    return (double)(e - s) / CLOCKS_PER_SEC * 1000.0;
}

/* Check if string ends with given suffix (case-insensitive) */
static int ends_with_ci(const char *str, const char *suffix)
{
    size_t slen = strlen(str);
    size_t xlen = strlen(suffix);
    if (xlen > slen) return 0;
    const char *tail = str + slen - xlen;
    for (size_t i = 0; i < xlen; i++) {
        char a = tail[i], b = suffix[i];
        if (a >= 'A' && a <= 'Z') a += 32;
        if (b >= 'A' && b <= 'Z') b += 32;
        if (a != b) return 0;
    }
    return 1;
}

static void make_path(char *buf, size_t bufsize, const char *prefix, const char *suffix)
{
    snprintf(buf, bufsize, "%s_%s", prefix, suffix);
}

/* =================================================================
 *  USAGE
 * ================================================================= */

static void print_usage(const char *prog)
{
    printf("Usage: %s [input.bmp|input.bin] [options]\n\n", prog);
    printf("Options:\n");
    printf("  -b box_size      Block size (default %d)\n", DEFAULT_BOX_SIZE);
    printf("  -f filter_size   Median filter size, odd (default %d)\n", DEFAULT_FILTER_SIZE);
    printf("  -r read_noise    Read noise, e- RMS (default %.1f)\n", DEFAULT_READ_NOISE);
    printf("  -o prefix        Output file prefix (default \"%s\")\n", DEFAULT_PREFIX);
    printf("  -h               Show this help\n\n");
    printf("If no input file given, generates a synthetic test image.\n");
    printf("Format auto-detected by extension: .bmp or .bin\n");
}

/* =================================================================
 *  MAIN
 * ================================================================= */

int main(int argc, char *argv[])
{
    /* Defaults */
    const char *input_file = NULL;
    int box_size = DEFAULT_BOX_SIZE;
    int filter_size = DEFAULT_FILTER_SIZE;
    float read_noise = DEFAULT_READ_NOISE;
    const char *prefix = DEFAULT_PREFIX;

    /* Parse args */
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            print_usage(argv[0]);
            return 0;
        } else if (strcmp(argv[i], "-b") == 0 && i + 1 < argc) {
            box_size = atoi(argv[++i]);
        } else if (strcmp(argv[i], "-f") == 0 && i + 1 < argc) {
            filter_size = atoi(argv[++i]);
        } else if (strcmp(argv[i], "-r") == 0 && i + 1 < argc) {
            read_noise = (float)atof(argv[++i]);
        } else if (strcmp(argv[i], "-o") == 0 && i + 1 < argc) {
            prefix = argv[++i];
        } else if (argv[i][0] != '-') {
            input_file = argv[i];
        } else {
            fprintf(stderr, "Unknown option: %s\n", argv[i]);
            print_usage(argv[0]);
            return 1;
        }
    }

    printf("=== bkg2d — 2D Background Subtraction ===\n\n");

    image_t input = { NULL, 0, 0 };
    image_t true_bkg = { NULL, 0, 0 };
    int have_truth = 0;
    int rc;

    /* Step 1: Load or generate image */
    if (input_file) {
        printf("[1] Loading image: %s\n", input_file);

        if (ends_with_ci(input_file, ".bmp")) {
            rc = image_read_bmp(input_file, &input);
        } else if (ends_with_ci(input_file, ".bin")) {
            rc = image_read_bin(input_file, &input);
        } else {
            fprintf(stderr, "ERROR: Unknown format. Use .bmp or .bin\n");
            return 1;
        }

        if (rc != BKG2D_OK) {
            fprintf(stderr, "ERROR: Failed to read file (code=%d)\n", rc);
            return 1;
        }
        printf("    Size: %d x %d\n", input.width, input.height);
    } else {
        printf("[1] Generating test image (%dx%d, %d stars)\n",
               SENSOR_W, SENSOR_H, N_STARS);
        input    = image_alloc(SENSOR_W, SENSOR_H);
        true_bkg = image_alloc(SENSOR_W, SENSOR_H);
        if (!input.data || !true_bkg.data) {
            fprintf(stderr, "ERROR: Out of memory\n");
            return 1;
        }
        generate_test_image(&input, &true_bkg);
        have_truth = 1;
    }

    /* Step 2: Background estimate */
    printf("\n[2] Background estimation (box=%d, filter=%d)\n", box_size, filter_size);
    bkg_result_t result = { {NULL, 0, 0}, 0.0f };
    clock_t t0 = clock();
    rc = v3_background_estimate(&input, box_size, filter_size, &result);
    clock_t t1 = clock();
    if (rc != BKG2D_OK) {
        fprintf(stderr, "ERROR: Background estimation failed (code=%d)\n", rc);
        return 1;
    }
    printf("    Time: %.1f ms\n", timer_ms(t0, t1));
    printf("    RMS median: %.4f\n", result.rms_median);

    /* Step 3: Subtraction */
    printf("\n[3] Subtracting background\n");
    image_t data_sub = image_alloc(input.width, input.height);
    if (!data_sub.data) {
        fprintf(stderr, "ERROR: Out of memory\n");
        return 1;
    }
    size_t npix = (size_t)input.width * input.height;
    for (size_t i = 0; i < npix; i++)
        data_sub.data[i] = input.data[i] - result.background.data[i];

    /* Step 4: Error map */
    printf("[4] Computing error map (read_noise=%.1f)\n", read_noise);
    image_t error_map = { NULL, 0, 0 };
    rc = v3_compute_error_map(&data_sub, read_noise, &error_map);
    if (rc != BKG2D_OK) {
        fprintf(stderr, "ERROR: Error map failed (code=%d)\n", rc);
        return 1;
    }

    /* Step 5: Accuracy check (if ground truth available) */
    if (have_truth) {
        double sum2 = 0;
        for (size_t i = 0; i < npix; i++) {
            double e = (double)result.background.data[i] - (double)true_bkg.data[i];
            sum2 += e * e;
        }
        printf("\n[5] Accuracy: RMS = %.6f\n", sqrt(sum2 / npix));
    }

    /* Step 6: Save outputs */
    printf("\n[6] Saving outputs (prefix=\"%s\")\n", prefix);
    float mn, mx;
    char path[512];

    /* Input (log-stretch, grayscale) */
    image_t inp_log = image_log_stretch(&input);
    image_find_minmax(&inp_log, &mn, &mx);
    make_path(path, sizeof(path), prefix, "input.bmp");
    write_bmp(path, &inp_log, mn, mx, cmap_gray);
    image_free(&inp_log);
    printf("    %s\n", path);

    /* Background (viridis) */
    image_find_minmax(&result.background, &mn, &mx);
    make_path(path, sizeof(path), prefix, "background.bmp");
    write_bmp(path, &result.background, mn, mx, cmap_viridis);
    printf("    %s\n", path);

    /* Subtracted (log-stretch, grayscale) */
    image_t sub_log = image_log_stretch(&data_sub);
    image_find_minmax(&sub_log, &mn, &mx);
    make_path(path, sizeof(path), prefix, "subtracted.bmp");
    write_bmp(path, &sub_log, mn, mx, cmap_gray);
    image_free(&sub_log);
    printf("    %s\n", path);

    /* Error map (viridis) */
    image_find_minmax(&error_map, &mn, &mx);
    make_path(path, sizeof(path), prefix, "errormap.bmp");
    write_bmp(path, &error_map, mn, mx, cmap_viridis);
    printf("    %s\n", path);

    if (have_truth) {
        /* True background (viridis) */
        image_find_minmax(&true_bkg, &mn, &mx);
        make_path(path, sizeof(path), prefix, "true_bkg.bmp");
        write_bmp(path, &true_bkg, mn, mx, cmap_viridis);
        printf("    %s\n", path);

        /* Background error (redblue) */
        image_t diff = image_alloc(input.width, input.height);
        if (diff.data) {
            float max_err = 0;
            for (size_t i = 0; i < npix; i++) {
                diff.data[i] = result.background.data[i] - true_bkg.data[i];
                if (fabsf(diff.data[i]) > max_err) max_err = fabsf(diff.data[i]);
            }
            make_path(path, sizeof(path), prefix, "bkg_error.bmp");
            write_bmp(path, &diff, -max_err, max_err, cmap_redblue);
            printf("    %s\n", path);
            image_free(&diff);
        }
    }

    /* Binary outputs */
    make_path(path, sizeof(path), prefix, "input.bin");
    image_write_bin(path, &input);
    make_path(path, sizeof(path), prefix, "background.bin");
    image_write_bin(path, &result.background);
    make_path(path, sizeof(path), prefix, "subtracted.bin");
    image_write_bin(path, &data_sub);

    printf("\n=== Done ===\n");
    printf("    Threshold (3-sigma): %.2f ADU\n", 3.0f * result.rms_median);

    /* Cleanup */
    image_free(&input);
    image_free(&true_bkg);
    v3_bkg_result_free(&result);
    image_free(&data_sub);
    image_free(&error_map);

    return 0;
}
