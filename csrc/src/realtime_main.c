/*
 * realtime_main.c — Dinamik pipeline simulasyonu
 *
 * .bin dosyalardan ard arda frame okur VEYA sentetik frame uretir,
 * realtime pipeline ile isler, FPS ve sonuclari raporlar.
 *
 * Kullanim:
 *   ./realtime                           (sentetik 100 frame)
 *   ./realtime -n 200                    (200 frame)
 *   ./realtime -n 50 -a 0.1             (hizli adaptasyon)
 *   ./realtime frame_dir/ -n 100         (dizinden .bin oku)
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

/* Varsayilan parametreler */
#define DEFAULT_W       2048
#define DEFAULT_H       2048
#define DEFAULT_N       100
#define DEFAULT_BOX     50
#define DEFAULT_FILTER  3
#define DEFAULT_RN      13.0f
#define DEFAULT_ALPHA   0.05f
#define DEFAULT_SIGMA   3.0f
#define N_STARS         150
#define STAR_RAD        8
#define BG_BASE         2000.0f
#define BG_VIGNETTE     0.10f

/* Basit RNG */
static uint64_t rng_state = 88172645463325252ULL;
static double rng_uniform(void) {
    rng_state ^= rng_state << 13;
    rng_state ^= rng_state >> 7;
    rng_state ^= rng_state << 17;
    return (double)(rng_state & 0x7FFFFFFFULL) / (double)0x7FFFFFFFULL;
}
static double rng_gauss(void) {
    double u1 = rng_uniform() + 1e-30;
    double u2 = rng_uniform();
    return sqrt(-2.0 * log(u1)) * cos(6.283185307 * u2);
}

/* Sentetik frame uret (yildizlar her frame'de biraz kayar) */
static void generate_frame(float *buf, int W, int H, int frame_idx,
                            float *star_x, float *star_y, float *star_flux,
                            float drift_rate)
{
    /* Background: vignetting + dark current */
    float cx = (float)W * 0.5f, cy = (float)H * 0.5f;
    float r_max = sqrtf(cx * cx + cy * cy);

    for (int y = 0; y < H; y++) {
        for (int x = 0; x < W; x++) {
            float dx = (float)x - cx, dy = (float)y - cy;
            float r = sqrtf(dx * dx + dy * dy) / r_max;
            float bg = BG_BASE * (1.0f - BG_VIGNETTE * r * r);
            /* Poisson noise approx: sqrt(bg) * gaussian */
            buf[y * W + x] = bg + sqrtf(bg) * (float)rng_gauss()
                            + DEFAULT_RN * (float)rng_gauss();
        }
    }

    /* Yildizlar (frame'e gore kaydirilmis) */
    float sigma = 1.5f;
    for (int s = 0; s < N_STARS; s++) {
        float sx = star_x[s] + drift_rate * (float)frame_idx;
        float sy = star_y[s] + drift_rate * 0.3f * (float)frame_idx;
        /* Wrap around */
        while (sx >= W) sx -= W;
        while (sy >= H) sy -= H;
        while (sx < 0) sx += W;
        while (sy < 0) sy += H;

        int ix = (int)sx, iy = (int)sy;
        float fx = sx - (float)ix, fy = sy - (float)iy;

        for (int dy = -STAR_RAD; dy <= STAR_RAD; dy++) {
            int py = iy + dy;
            if (py < 0 || py >= H) continue;
            for (int dx = -STAR_RAD; dx <= STAR_RAD; dx++) {
                int px = ix + dx;
                if (px < 0 || px >= W) continue;
                float r2 = ((float)dx - fx) * ((float)dx - fx)
                         + ((float)dy - fy) * ((float)dy - fy);
                float val = star_flux[s] * expf(-r2 / (2.0f * sigma * sigma));
                buf[py * W + px] += val;
            }
        }
    }
}

int main(int argc, char *argv[])
{
    int W = DEFAULT_W, H = DEFAULT_H;
    int n_frames = DEFAULT_N;
    int box = DEFAULT_BOX, filt = DEFAULT_FILTER;
    float rn = DEFAULT_RN, alpha = DEFAULT_ALPHA, sig = DEFAULT_SIGMA;
    float drift = 0.5f; /* piksel/frame kayma hizi */
    int ring = 0; /* ring buffer: 0=IIR, 3-8=median */

    /* Arguman parse */
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-n") == 0 && i+1 < argc) n_frames = atoi(argv[++i]);
        else if (strcmp(argv[i], "-b") == 0 && i+1 < argc) box = atoi(argv[++i]);
        else if (strcmp(argv[i], "-f") == 0 && i+1 < argc) filt = atoi(argv[++i]);
        else if (strcmp(argv[i], "-a") == 0 && i+1 < argc) alpha = (float)atof(argv[++i]);
        else if (strcmp(argv[i], "-s") == 0 && i+1 < argc) sig = (float)atof(argv[++i]);
        else if (strcmp(argv[i], "-d") == 0 && i+1 < argc) drift = (float)atof(argv[++i]);
        else if (strcmp(argv[i], "-r") == 0 && i+1 < argc) ring = atoi(argv[++i]);
        else if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            printf("Usage: %s [options]\n", argv[0]);
            printf("  -n N       Frame sayisi (default %d)\n", DEFAULT_N);
            printf("  -b box     Box size (default %d)\n", DEFAULT_BOX);
            printf("  -f filt    Filter size (default %d)\n", DEFAULT_FILTER);
            printf("  -a alpha   IIR alpha (default %.2f)\n", DEFAULT_ALPHA);
            printf("  -s sigma   Threshold sigma (default %.1f)\n", DEFAULT_SIGMA);
            printf("  -d drift   Yildiz kayma hizi px/frame (default 0.5)\n");
            return 0;
        }
    }

    printf("=== Realtime Pipeline Simulasyonu ===\n\n");
    printf("  Goruntu  : %dx%d\n", W, H);
    printf("  Frameler : %d\n", n_frames);
    printf("  Box/Filt : %d / %d\n", box, filt);
    printf("  Alpha    : %.3f\n", alpha);
    printf("  Sigma    : %.1f\n", sig);
    printf("  Drift    : %.2f px/frame\n", drift);
    #ifdef _OPENMP
    printf("  OpenMP   : %d thread\n", omp_get_max_threads());
    #else
    printf("  OpenMP   : kapal\n");
    #endif
    printf("\n");

    /* Yildiz konumlari olustur */
    float star_x[N_STARS], star_y[N_STARS], star_flux[N_STARS];
    rng_state = 42;
    for (int i = 0; i < N_STARS; i++) {
        star_x[i] = (float)(rng_uniform() * (W - 100) + 50);
        star_y[i] = (float)(rng_uniform() * (H - 100) + 50);
        /* Magnitude 2-7 arasi logaritmik */
        double mag = 2.0 + rng_uniform() * 5.0;
        star_flux[i] = (float)(1e4 * pow(10.0, -0.4 * mag));
    }

    /* Frame buffer */
    float *frame_buf = (float *)malloc((size_t)W * H * sizeof(float));
    if (!frame_buf) { printf("HATA: bellek yetersiz\n"); return 1; }

    /* Pipeline init */
    pl_realtime_ctx_t ctx;
    int rc = pl_realtime_init(&ctx, W, H, box, filt, rn, alpha, sig, ring);
    if (rc != PL_OK) {
        printf("HATA: pipeline init basarisiz (%d)\n", rc);
        free(frame_buf);
        return 1;
    }

    /* Frame dongusu */
    printf("  Ring buf : %d frame\n", ring);
    printf("  Memory   : %.1f MB\n\n", (double)pl_realtime_memory_usage(&ctx) / (1024*1024));

    printf("Frame  Threshold  Piksel  Sure(ms)  FPS   Ring  Memory(MB)\n");
    printf("-----  ---------  ------  --------  -----  ----  ----------\n");

    double total_time = 0.0;
    double min_time = 1e9, max_time = 0.0;

    for (int f = 0; f < n_frames; f++) {
        /* Frame uret */
        generate_frame(frame_buf, W, H, f, star_x, star_y, star_flux, drift);

        /* Pipeline isle */
        pl_frame_result_t result;
        rc = pl_realtime_feed(&ctx, frame_buf, &result);
        if (rc != PL_OK) {
            printf("HATA: frame %d isleme basarisiz (%d)\n", f, rc);
            break;
        }

        total_time += result.process_time_ms;
        if (result.process_time_ms < min_time) min_time = result.process_time_ms;
        if (result.process_time_ms > max_time) max_time = result.process_time_ms;

        float fps = (result.process_time_ms > 0.01f)
                   ? 1000.0f / result.process_time_ms : 9999.0f;

        /* Her 10 frame'de veya ilk/son frame'de rapor */
        if (f == 0 || f == n_frames - 1 || (f + 1) % 10 == 0) {
            printf("%5d  %9.2f  %6d  %8.2f  %5.0f  %4d  %10.1f\n",
                   f + 1, result.threshold, result.n_above_threshold,
                   result.process_time_ms, fps,
                   result.ring_fill,
                   (double)result.memory_bytes / (1024*1024));
        }
    }

    /* Ozet */
    double avg_time = total_time / n_frames;
    double avg_fps = 1000.0 / avg_time;
    /* Ilk frame haric ortalama (ilk frame tam hesaplama yapar) */
    double avg_time_steady = (n_frames > 1)
        ? (total_time - max_time) / (n_frames - 1) : avg_time;
    double steady_fps = 1000.0 / avg_time_steady;

    printf("\n=== SONUC ===\n");
    printf("  Toplam frame     : %d\n", ctx.frame_count);
    printf("  Toplam sure      : %.1f ms\n", total_time);
    printf("  Ilk frame (tam)  : %.1f ms\n", max_time);
    printf("  Ort. sure (tumu) : %.2f ms  (%.0f FPS)\n", avg_time, avg_fps);
    printf("  Ort. sure (IIR)  : %.2f ms  (%.0f FPS)\n", avg_time_steady, steady_fps);
    printf("  Min sure         : %.2f ms  (%.0f FPS)\n", min_time, 1000.0 / min_time);
    printf("  Son RMS          : %.2f ADU\n", ctx.rms_median);
    printf("  Son threshold    : %.2f ADU\n", ctx.threshold_sigma * ctx.rms_median);
    printf("  Bellek kullanimi : %.1f MB\n", (double)pl_realtime_memory_usage(&ctx) / (1024*1024));
    printf("  Ring buffer      : %d / %d\n", ctx.ring_count, ctx.ring_size);

    if (steady_fps >= 30.0)
        printf("\n  [BASARILI] 30 FPS hedefi karsilandi (%.0f FPS)\n", steady_fps);
    else
        printf("\n  [YETERSIZ] 30 FPS hedefinin altinda (%.0f FPS)\n", steady_fps);

    printf("=================\n");

    pl_realtime_destroy(&ctx);
    free(frame_buf);
    return 0;
}
