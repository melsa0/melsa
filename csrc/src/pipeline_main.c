/*
 * pipeline_main.c — CLI frontend for pipeline library
 *
 * Usage:
 *   ./pipeline                          (sentetik test goruntusu)
 *   ./pipeline input.bmp                (BMP yukle)
 *   ./pipeline input.bin                (binary yukle)
 *   ./pipeline input.bmp -b 64 -f 5 -r 10.0 -o result
 *
 * Derleme:
 *   gcc -std=c11 -O3 -Wall -Iinclude -o pipeline pipeline.c pipeline_main.c -lm
 */

#include "pipeline.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <sys/stat.h>
#include <sys/types.h>

#ifdef _WIN32
  #include <direct.h>
  #define MKDIR(d) _mkdir(d)
#else
  #define MKDIR(d) mkdir(d, 0755)
#endif

/* ---- Defaults ---- */
#define DEFAULT_BOX      32
#define DEFAULT_FILTER   3
#define DEFAULT_RN       13.0f
#define DEFAULT_PREFIX   "out"

/* ---- Sentetik goruntu parametreleri ---- */
#define SYNTH_W   256
#define SYNTH_H   256
#define N_STARS   5
#define STAR_RAD  8

/* =================================================================
 *  RNG (Xorshift) + sentetik goruntu
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
    return sqrt(-2.0 * log(rng_uniform() + 1e-15)) * cos(6.2831853 * rng_uniform());
}

static void generate_synthetic(pl_image_t *img)
{
    int W = img->width, H = img->height;

    /* Gradient background + Gaussian noise */
    for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++) {
            float bkg = 100.0f + 20.0f * (float)x / W + 10.0f * (float)y / H;
            img->data[y * W + x] = bkg + 13.0f * (float)rng_gauss();
        }

    /* 5 yildiz */
    const int   sx[] = { 64, 180,  30, 200, 128};
    const int   sy[] = { 64,  50, 200, 190, 128};
    const float sf[] = {5000, 8000, 3000, 10000, 6000};
    const float sg[] = {2.0f, 2.5f, 1.8f, 3.0f, 2.2f};

    for (int s = 0; s < N_STARS; s++) {
        float sig2 = sg[s] * sg[s];
        for (int dy = -STAR_RAD; dy <= STAR_RAD; dy++)
            for (int dx = -STAR_RAD; dx <= STAR_RAD; dx++) {
                int px = sx[s] + dx, py = sy[s] + dy;
                if (px >= 0 && px < W && py >= 0 && py < H)
                    img->data[py * W + px] += sf[s] * expf(-(float)(dx*dx + dy*dy) / (2.0f * sig2));
            }
    }
}

/* =================================================================
 *  HELPERS
 * ================================================================= */

static double timer_ms(clock_t s, clock_t e) {
    return (double)(e - s) / CLOCKS_PER_SEC * 1000.0;
}

static int ends_with_ci(const char *str, const char *suffix)
{
    size_t slen = strlen(str), xlen = strlen(suffix);
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

static void make_path(char *buf, size_t sz, const char *prefix, const char *suffix) {
    snprintf(buf, sz, "%s_%s", prefix, suffix);
}

static void print_usage(const char *prog) {
    printf("Usage: %s [input.bmp|input.bin] [options]\n\n", prog);
    printf("  -b box_size      Block size (default %d)\n", DEFAULT_BOX);
    printf("  -f filter_size   Median filter, odd (default %d)\n", DEFAULT_FILTER);
    printf("  -r read_noise    Read noise e- RMS (default %.1f)\n", DEFAULT_RN);
    printf("  -o prefix        Output prefix (default \"%s\")\n", DEFAULT_PREFIX);
    printf("  -h               Help\n\n");
    printf("No input file => synthetic %dx%d test image.\n", SYNTH_W, SYNTH_H);
}

/* =================================================================
 *  MAIN
 * ================================================================= */

int main(int argc, char *argv[])
{
    const char *input_file = NULL;
    int box_size = DEFAULT_BOX, filter_size = DEFAULT_FILTER;
    float read_noise = DEFAULT_RN;
    const char *prefix = DEFAULT_PREFIX;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) { print_usage(argv[0]); return 0; }
        else if (strcmp(argv[i], "-b") == 0 && i+1 < argc) box_size = atoi(argv[++i]);
        else if (strcmp(argv[i], "-f") == 0 && i+1 < argc) filter_size = atoi(argv[++i]);
        else if (strcmp(argv[i], "-r") == 0 && i+1 < argc) read_noise = (float)atof(argv[++i]);
        else if (strcmp(argv[i], "-o") == 0 && i+1 < argc) prefix = argv[++i];
        else if (argv[i][0] != '-') input_file = argv[i];
        else { fprintf(stderr, "Unknown: %s\n", argv[i]); print_usage(argv[0]); return 1; }
    }

    printf("\n=== Pipeline V3 Optimized ===\n\n");

    pl_image_t input = {NULL, 0, 0};
    int rc;

    /* Step 1: Load or generate */
    if (input_file) {
        printf("[1] Loading: %s\n", input_file);
        if (ends_with_ci(input_file, ".bmp"))
            rc = pl_image_read_bmp(input_file, &input);
        else if (ends_with_ci(input_file, ".bin"))
            rc = pl_image_read_bin(input_file, &input);
        else { fprintf(stderr, "ERROR: use .bmp or .bin\n"); return 1; }
        if (rc != PL_OK) { fprintf(stderr, "ERROR: read failed (%d)\n", rc); return 1; }
        printf("    Size: %dx%d\n", input.width, input.height);
    } else {
        printf("[1] Generating synthetic (%dx%d, %d stars)\n", SYNTH_W, SYNTH_H, N_STARS);
        input = pl_image_alloc(SYNTH_W, SYNTH_H);
        if (!input.data) { fprintf(stderr, "OOM\n"); return 1; }
        generate_synthetic(&input);
    }

    /* Step 2: Background estimate */
    printf("\n[2] Background (box=%d, filter=%d)\n", box_size, filter_size);
    pl_bkg_result_t result = { {NULL,0,0}, 0.0f };
    clock_t t0 = clock();
    rc = pl_background_estimate(&input, box_size, filter_size, &result);
    clock_t t1 = clock();
    if (rc != PL_OK) { fprintf(stderr, "ERROR: estimate failed (%d)\n", rc); return 1; }
    printf("    Time: %.1f ms\n", timer_ms(t0, t1));
    printf("    RMS median: %.4f ADU\n", result.rms_median);

    /* Step 3: Fused subtract + error */
    printf("\n[3] Fused subtract + error (read_noise=%.1f)\n", read_noise);
    pl_image_t data_sub, error_map;
    clock_t t2 = clock();
    rc = pl_fused_subtract_error(&input, &result.background, read_noise, &data_sub, &error_map);
    clock_t t3 = clock();
    if (rc != PL_OK) { fprintf(stderr, "ERROR: subtract failed (%d)\n", rc); return 1; }
    printf("    Time: %.1f ms\n", timer_ms(t2, t3));

    /* Step 4: Stats */
    printf("\n[4] Statistics\n");
    pl_stats_t sr = pl_compute_stats(&input);
    pl_stats_t sb = pl_compute_stats(&result.background);
    pl_stats_t sd = pl_compute_stats(&data_sub);
    pl_stats_t se = pl_compute_stats(&error_map);
    printf("    %-18s %10s %10s %10s %10s\n", "", "Min", "Max", "Mean", "RMS");
    printf("    %-18s %10.2f %10.2f %10.2f %10.2f\n", "Raw",        sr.min, sr.max, sr.mean, sr.rms);
    printf("    %-18s %10.2f %10.2f %10.2f %10.2f\n", "Background", sb.min, sb.max, sb.mean, sb.rms);
    printf("    %-18s %10.2f %10.2f %10.2f %10.2f\n", "Subtracted", sd.min, sd.max, sd.mean, sd.rms);
    printf("    %-18s %10.2f %10.2f %10.2f %10.2f\n", "Error",      se.min, se.max, se.mean, se.rms);

    /* Step 5: Save */
    printf("\n[5] Saving (prefix=\"%s\")\n", prefix);
    char path[512];
    float mn, mx;

    /* BMP outputs */
    pl_image_t inp_log = pl_image_log_stretch(&input);
    pl_image_minmax(&inp_log, &mn, &mx);
    make_path(path, sizeof(path), prefix, "input.bmp");
    pl_write_bmp(path, &inp_log, mn, mx, pl_cmap_gray);
    pl_image_free(&inp_log);
    printf("    %s\n", path);

    pl_image_minmax(&result.background, &mn, &mx);
    make_path(path, sizeof(path), prefix, "background.bmp");
    pl_write_bmp(path, &result.background, mn, mx, pl_cmap_viridis);
    printf("    %s\n", path);

    pl_image_t sub_log = pl_image_log_stretch(&data_sub);
    pl_image_percentile_range(&sub_log, 1.0f, 99.5f, &mn, &mx);
    make_path(path, sizeof(path), prefix, "subtracted.bmp");
    pl_write_bmp(path, &sub_log, mn, mx, pl_cmap_gray);
    pl_image_free(&sub_log);
    printf("    %s\n", path);

    pl_image_minmax(&error_map, &mn, &mx);
    make_path(path, sizeof(path), prefix, "errormap.bmp");
    pl_write_bmp(path, &error_map, mn, mx, pl_cmap_viridis);
    printf("    %s\n", path);

    /* Binary outputs */
    make_path(path, sizeof(path), prefix, "input.bin");
    pl_image_write_bin(path, &input);
    make_path(path, sizeof(path), prefix, "background.bin");
    pl_image_write_bin(path, &result.background);
    make_path(path, sizeof(path), prefix, "subtracted.bin");
    pl_image_write_bin(path, &data_sub);
    make_path(path, sizeof(path), prefix, "errormap.bin");
    pl_image_write_bin(path, &error_map);

    /* 3-sigma thresholded output */
    float thresh = 3.0f * result.rms_median;
    pl_image_t thresholded = pl_image_alloc(input.width, input.height);
    if (thresholded.data) {
        size_t npx = (size_t)input.width * input.height;
        int n_above = 0;
        for (size_t i = 0; i < npx; i++) {
            if (data_sub.data[i] >= thresh) {
                thresholded.data[i] = data_sub.data[i];
                n_above++;
            } else {
                thresholded.data[i] = 0.0f;
            }
        }
        make_path(path, sizeof(path), prefix, "thresholded.bin");
        pl_image_write_bin(path, &thresholded);
        pl_image_percentile_range(&thresholded, 0.0f, 99.5f, &mn, &mx);
        if (mx < 1.0f) mx = 1.0f;
        make_path(path, sizeof(path), prefix, "thresholded.bmp");
        pl_write_bmp(path, &thresholded, 0.0f, mx, pl_cmap_gray);
        printf("    %s (%d pixels above threshold)\n", path, n_above);
        pl_image_free(&thresholded);
    }

    double total = timer_ms(t0, t3);
    printf("\n=== Done (%.1f ms) ===\n", total);
    printf("    Threshold (3-sigma): %.2f ADU\n", thresh);

    pl_image_free(&input);
    pl_bkg_result_free(&result);
    pl_image_free(&data_sub);
    pl_image_free(&error_map);
    return 0;
}
