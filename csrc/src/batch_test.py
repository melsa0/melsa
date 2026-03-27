"""
Batch test: Farkli parametrelerle goruntu uret, C pipeline ile isle, sonuclari karsilastir.
Kullanim:
  python batch_test.py
Cikti:  batch_results/ klasoru altinda her senaryo icin ayri klasor.
"""
import numpy as np
import struct
import subprocess
import os
import csv

# ============================================================
#  TEST SENARYOLARI — istedigin kadar ekle/cikar
# ============================================================
SCENARIOS = [
    # (isim,        n_stars, sky_bg, read_noise, exposure, sigma, seed)
    ("az_yildiz",       20,   20.0,      13.0,    100.0,   1.5,   1),
    ("cok_yildiz",     500,   20.0,      13.0,    100.0,   1.5,   2),
    ("dusuk_gurultu",  200,    5.0,       3.0,    100.0,   1.5,   3),
    ("yuksek_gurultu", 200,   80.0,      30.0,    100.0,   1.5,   4),
    ("genis_psf",      200,   20.0,      13.0,    100.0,   3.0,   5),
    ("dar_psf",        200,   20.0,      13.0,    100.0,   0.8,   6),
    ("kisa_pozlama",   200,   20.0,      13.0,     10.0,   1.5,   7),
    ("uzun_pozlama",   200,   20.0,      13.0,    500.0,   1.5,   8),
]

W, H = 2048, 2048
DARK_CURRENT = 0.1
PIPELINE_EXE = "./pipeline.exe"
BOX_SIZE = 50
FILTER_SIZE = 3
OUT_DIR = "batch_results"

os.makedirs(OUT_DIR, exist_ok=True)

results = []

for name, n_stars, sky_bg, read_noise, exposure, sigma, seed in SCENARIOS:
    print(f"\n{'='*60}")
    print(f"  SENARYO: {name}")
    print(f"  stars={n_stars}, sky={sky_bg}, rn={read_noise}, exp={exposure}, sigma={sigma}")
    print(f"{'='*60}")

    np.random.seed(seed)
    scenario_dir = os.path.join(OUT_DIR, name)
    os.makedirs(scenario_dir, exist_ok=True)

    # --- 1) Background ---
    y, x = np.mgrid[0:H, 0:W]
    cx, cy = W / 2, H / 2
    r = np.sqrt((x - cx)**2 + (y - cy)**2) / np.sqrt(cx**2 + cy**2)
    vignetting = 1.0 - 0.15 * r**2

    sky = sky_bg * exposure * vignetting
    dark = DARK_CURRENT * exposure
    background = sky + dark

    # --- 2) Yildizlar ---
    star_x = np.random.uniform(50, W - 50, n_stars)
    star_y = np.random.uniform(50, H - 50, n_stars)
    magnitudes = np.random.uniform(2.0, 8.0, n_stars)
    zero_point = 1e6 * exposure
    fluxes = zero_point * 10**(-0.4 * magnitudes)

    star_image = np.zeros((H, W), dtype=np.float64)
    radius = int(5 * sigma)
    for i in range(n_stars):
        ix, iy = int(star_x[i]), int(star_y[i])
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                px, py = ix + dx, iy + dy
                if 0 <= px < W and 0 <= py < H:
                    r2 = (dx - (star_x[i] - ix))**2 + (dy - (star_y[i] - iy))**2
                    star_image[py, px] += fluxes[i] * np.exp(-r2 / (2 * sigma**2))

    # --- 3) Noise ---
    signal = background + star_image
    noisy = np.random.poisson(np.maximum(signal, 0)).astype(np.float64)
    noisy += np.random.normal(0, read_noise, (H, W))

    # --- 4) Binary kaydet ---
    bin_path = os.path.join(scenario_dir, f"{name}.bin")
    gt_path = os.path.join(scenario_dir, f"{name}_truebkg.bin")

    with open(bin_path, "wb") as f:
        f.write(struct.pack("<ii", W, H))
        f.write(noisy.astype(np.float32).tobytes())

    with open(gt_path, "wb") as f:
        f.write(struct.pack("<ii", W, H))
        f.write(background.astype(np.float32).tobytes())

    print(f"  Goruntu: {bin_path}")

    # --- 5) C pipeline calistir ---
    prefix = os.path.join(scenario_dir, name)
    cmd = [PIPELINE_EXE, bin_path, "-b", str(BOX_SIZE), "-f", str(FILTER_SIZE), "-o", prefix]
    print(f"  CMD: {' '.join(cmd)}")

    proc = subprocess.run(cmd, capture_output=True, text=True)
    print(proc.stdout)
    if proc.returncode != 0:
        print(f"  HATA: {proc.stderr}")
        continue

    # --- 6) C background oku ve karsilastir ---
    c_bkg_path = prefix + "_background.bin"
    if os.path.exists(c_bkg_path):
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
        pct_err = mae / np.mean(gt_bkg) * 100

        row = {
            "senaryo": name,
            "n_stars": n_stars,
            "sky_bg": sky_bg,
            "read_noise": read_noise,
            "exposure": exposure,
            "sigma": sigma,
            "MAE": f"{mae:.4f}",
            "RMSE": f"{rmse:.4f}",
            "MaxErr": f"{max_err:.4f}",
            "MAE%": f"{pct_err:.4f}",
        }
        results.append(row)
        print(f"  MAE={mae:.4f}  RMSE={rmse:.4f}  MaxErr={max_err:.4f}  MAE%={pct_err:.4f}%")

# --- 7) Sonuc tablosu ---
csv_path = os.path.join(OUT_DIR, "results.csv")
if results:
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"\n{'='*60}")
    print(f"  SONUC TABLOSU")
    print(f"{'='*60}")
    header = f"{'Senaryo':<20} {'MAE':>10} {'RMSE':>10} {'MaxErr':>10} {'MAE%':>8}"
    print(header)
    print("-" * len(header))
    for r in results:
        print(f"{r['senaryo']:<20} {r['MAE']:>10} {r['RMSE']:>10} {r['MaxErr']:>10} {r['MAE%']:>8}%")
    print(f"\nCSV: {csv_path}")
    print(f"BMP dosyalari: {OUT_DIR}/<senaryo>/ altinda")
    print(f"\nAstroImageJ ile acmak icin:")
    print(f"  File > Open > batch_results/<senaryo>/<senaryo>_subtracted.bmp")
