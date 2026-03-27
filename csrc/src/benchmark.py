"""
Kapsamli benchmark: 12 farkli senaryo ile C pipeline vs ground truth karsilastirmasi.
"""
import numpy as np
import struct
import subprocess
import os
import sys

W, H = 2048, 2048
DARK_CURRENT = 0.1
PIPELINE_EXE = "./pipeline.exe"

SCENARIOS = [
    # (isim, n_stars, sky_bg, read_noise, exposure, sigma, box, filter, seed)
    ("01_varsayilan",        200,  20.0,  13.0, 100.0, 1.5, 50, 3,  42),
    ("02_az_yildiz",          20,  20.0,  13.0, 100.0, 1.5, 50, 3,  10),
    ("03_cok_yildiz",        800,  20.0,  13.0, 100.0, 1.5, 50, 3,  11),
    ("04_dusuk_sky",         200,   3.0,  13.0, 100.0, 1.5, 50, 3,  12),
    ("05_yuksek_sky",        200, 100.0,  13.0, 100.0, 1.5, 50, 3,  13),
    ("06_dusuk_gurultu",     200,  20.0,   2.0, 100.0, 1.5, 50, 3,  14),
    ("07_yuksek_gurultu",    200,  20.0,  40.0, 100.0, 1.5, 50, 3,  15),
    ("08_kisa_pozlama",      200,  20.0,  13.0,   5.0, 1.5, 50, 3,  16),
    ("09_uzun_pozlama",      200,  20.0,  13.0, 800.0, 1.5, 50, 3,  17),
    ("10_genis_psf",         200,  20.0,  13.0, 100.0, 4.0, 50, 3,  18),
    ("11_dar_psf",           200,  20.0,  13.0, 100.0, 0.6, 50, 3,  19),
    ("12_kucuk_box",         200,  20.0,  13.0, 100.0, 1.5, 25, 3,  42),
    ("13_buyuk_box",         200,  20.0,  13.0, 100.0, 1.5,100, 3,  42),
    ("14_buyuk_filter",      200,  20.0,  13.0, 100.0, 1.5, 50, 7,  42),
    ("15_extreme",          1000, 150.0,  50.0,  10.0, 3.0, 50, 3,  99),
]

out_dir = "benchmark_results"
os.makedirs(out_dir, exist_ok=True)

results = []

for name, n_stars, sky_bg, rn, exp, sigma, box, filt, seed in SCENARIOS:
    np.random.seed(seed)
    sdir = os.path.join(out_dir, name)
    os.makedirs(sdir, exist_ok=True)

    # --- Goruntu uret ---
    y, x = np.mgrid[0:H, 0:W]
    cx, cy = W/2, H/2
    r = np.sqrt((x-cx)**2 + (y-cy)**2) / np.sqrt(cx**2 + cy**2)
    vignetting = 1.0 - 0.15 * r**2
    sky = sky_bg * exp * vignetting
    dark = DARK_CURRENT * exp
    background = sky + dark

    star_x = np.random.uniform(50, W-50, n_stars)
    star_y = np.random.uniform(50, H-50, n_stars)
    magnitudes = np.random.uniform(2.0, 8.0, n_stars)
    zero_point = 1e6 * exp
    fluxes = zero_point * 10**(-0.4 * magnitudes)

    star_image = np.zeros((H, W), dtype=np.float64)
    radius = int(5 * sigma)
    for i in range(n_stars):
        ix, iy = int(star_x[i]), int(star_y[i])
        for dy in range(-radius, radius+1):
            for dx in range(-radius, radius+1):
                px, py = ix+dx, iy+dy
                if 0 <= px < W and 0 <= py < H:
                    r2 = (dx-(star_x[i]-ix))**2 + (dy-(star_y[i]-iy))**2
                    star_image[py, px] += fluxes[i] * np.exp(-r2/(2*sigma**2))

    signal = background + star_image
    noisy = np.random.poisson(np.maximum(signal, 0)).astype(np.float64)
    noisy += np.random.normal(0, rn, (H, W))

    bin_path = os.path.join(sdir, f"{name}.bin")
    gt_path = os.path.join(sdir, f"{name}_truebkg.bin")

    with open(bin_path, "wb") as f:
        f.write(struct.pack("<ii", W, H))
        f.write(noisy.astype(np.float32).tobytes())
    with open(gt_path, "wb") as f:
        f.write(struct.pack("<ii", W, H))
        f.write(background.astype(np.float32).tobytes())

    # --- C pipeline calistir ---
    prefix = os.path.join(sdir, name)
    cmd = [PIPELINE_EXE, bin_path, "-b", str(box), "-f", str(filt), "-o", prefix]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode != 0:
        print(f"  HATA: {name}")
        results.append({"name": name, "status": "FAIL"})
        continue

    # --- Parse pipeline output ---
    time_ms = 0.0
    rms_med = 0.0
    for line in proc.stdout.splitlines():
        if "Time:" in line and "Background" not in line:
            pass
        if "RMS median" in line:
            try: rms_med = float(line.split(":")[1].strip().split()[0])
            except: pass
        if "Done" in line:
            try: time_ms = float(line.split("(")[1].split("ms")[0])
            except: pass

    # --- Karsilastir ---
    c_bkg_path = prefix + "_background.bin"
    with open(c_bkg_path, "rb") as f:
        cw, ch = struct.unpack("<ii", f.read(8))
        c_bkg = np.frombuffer(f.read(), dtype=np.float32).reshape(ch, cw)
    with open(gt_path, "rb") as f:
        gw, gh = struct.unpack("<ii", f.read(8))
        gt_bkg = np.frombuffer(f.read(), dtype=np.float32).reshape(gh, gw)

    diff = c_bkg - gt_bkg
    mae = np.mean(np.abs(diff))
    rmse = np.sqrt(np.mean(diff**2))
    max_err = np.max(np.abs(diff))
    bkg_mean = np.mean(gt_bkg)
    pct_err = mae / bkg_mean * 100

    # Background-subtracted'da yildiz korunma orani
    c_sub_path = prefix + "_subtracted.bin"
    with open(c_sub_path, "rb") as f:
        sw, sh = struct.unpack("<ii", f.read(8))
        c_sub = np.frombuffer(f.read(), dtype=np.float32).reshape(sh, sw)

    # Yildiz pikselleri (star_image > 0)
    star_mask = star_image > (rn * 3)
    n_star_px = star_mask.sum()
    if n_star_px > 0:
        star_flux_truth = star_image[star_mask].sum()
        star_flux_recov = c_sub[star_mask].sum()
        flux_recovery = star_flux_recov / star_flux_truth * 100
    else:
        flux_recovery = 0.0

    # Subtracted'da background bolgesinin std'si
    bg_mask = ~star_mask
    bg_std = np.std(c_sub[bg_mask])

    row = {
        "name": name,
        "stars": n_stars,
        "sky": sky_bg,
        "rn": rn,
        "exp": exp,
        "sigma": sigma,
        "box": box,
        "filt": filt,
        "time_ms": time_ms,
        "MAE": mae,
        "RMSE": rmse,
        "MaxErr": max_err,
        "MAE%": pct_err,
        "flux_recov%": flux_recovery,
        "bg_std": bg_std,
        "status": "OK",
    }
    results.append(row)

# --- Rapor ---
print()
print("=" * 100)
print("  BENCHMARK RAPORU: C Pipeline Background Extraction")
print("=" * 100)
print()

# Tablo 1: Dogruluk
print("TABLO 1: Background Tahmini Dogrulugu (C pipeline vs Ground Truth)")
print("-" * 95)
hdr = f"{'Senaryo':<25} {'MAE':>8} {'RMSE':>8} {'MaxErr':>10} {'MAE%':>8} {'Durum':>8}"
print(hdr)
print("-" * 95)
for r in results:
    if r["status"] == "FAIL":
        print(f"{r['name']:<25} {'FAIL':>50}")
        continue
    print(f"{r['name']:<25} {r['MAE']:>8.3f} {r['RMSE']:>8.3f} {r['MaxErr']:>10.3f} {r['MAE%']:>7.4f}% {'OK':>6}")

print()
print("TABLO 2: Yildiz Koruma & Performans")
print("-" * 85)
hdr2 = f"{'Senaryo':<25} {'Flux Kor.%':>10} {'BG Std':>10} {'Sure(ms)':>10} {'Yildiz':>8} {'SNR':>8}"
print(hdr2)
print("-" * 85)
for r in results:
    if r["status"] == "FAIL":
        continue
    snr = "-"
    if r["bg_std"] > 0:
        snr = f"{r['MAE'] / r['bg_std']:.4f}"
    print(f"{r['name']:<25} {r['flux_recov%']:>9.2f}% {r['bg_std']:>10.2f} {r['time_ms']:>10.1f} {r['stars']:>8} {snr:>8}")

# Ozet
ok = [r for r in results if r["status"] == "OK"]
if ok:
    avg_mae_pct = np.mean([r["MAE%"] for r in ok])
    avg_flux = np.mean([r["flux_recov%"] for r in ok])
    avg_time = np.mean([r["time_ms"] for r in ok])
    max_mae_pct = max([r["MAE%"] for r in ok])
    min_flux = min([r["flux_recov%"] for r in ok])

    print()
    print("=" * 60)
    print("  OZET")
    print("=" * 60)
    print(f"  Toplam test      : {len(ok)} / {len(results)}")
    print(f"  Ort. MAE%        : {avg_mae_pct:.4f}%")
    print(f"  Max MAE%         : {max_mae_pct:.4f}%")
    print(f"  Ort. Flux Koruma : {avg_flux:.2f}%")
    print(f"  Min Flux Koruma  : {min_flux:.2f}%")
    print(f"  Ort. Sure        : {avg_time:.1f} ms")
    print(f"  Tahmini FPS      : {1000.0 / avg_time:.0f}")
    print()

    # Degerlendirme
    print("  DEGERLENDIRME:")
    if avg_mae_pct < 0.5:
        print("  [BASARILI] Background tahmini ground truth'a cok yakin (MAE% < 0.5%)")
    elif avg_mae_pct < 2.0:
        print("  [IYI] Background tahmini makul seviyede (MAE% < 2%)")
    else:
        print("  [ZAYIF] Background tahmini iyilestirilmeli (MAE% > 2%)")

    if min_flux > 95:
        print("  [BASARILI] Yildiz fluxu korunuyor (>95%)")
    elif min_flux > 85:
        print("  [IYI] Yildiz fluxu buyuk oranda korunuyor (>85%)")
    else:
        print(f"  [UYARI] Bazi senaryolarda flux kaybi var (min={min_flux:.1f}%)")

    if avg_time < 100:
        print(f"  [BASARILI] Gercek zamanli uygun ({1000/avg_time:.0f} FPS)")
    else:
        print(f"  [UYARI] Gercek zamanli icin yavas ({avg_time:.0f} ms/frame)")
    print("=" * 60)
