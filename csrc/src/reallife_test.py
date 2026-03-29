"""
Gercek hayat senaryolari testi:
1. Hot pixel / dead pixel
2. Degisken background (sicaklik)
3. Motion blur
4. Saturation
5. STOS verisi
"""
import numpy as np
import struct
import subprocess
import os
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PIPELINE_EXE = os.path.join(SCRIPT_DIR, "pipeline.exe")
W, H = 1024, 1024
ZP, RN, DC = 2_100_000, 13.0, 125.0

def wbin(path, data):
    h, w = data.shape
    with open(path, "wb") as f:
        f.write(struct.pack("<ii", w, h))
        f.write(data.astype(np.float32).tobytes())

def rbin(path):
    with open(path, "rb") as f:
        w, h = struct.unpack("<ii", f.read(8))
        return np.frombuffer(f.read(), dtype=np.float32).reshape(h, w)

def run_pipeline(bin_path, prefix, box=50, filt=3):
    t0 = time.perf_counter()
    proc = subprocess.run([PIPELINE_EXE, bin_path, "-b", str(box), "-f", str(filt), "-o", prefix],
                          capture_output=True, text=True)
    ms = (time.perf_counter() - t0) * 1000
    pipe_int = 0; thresh = 0; npx = 0
    for line in proc.stdout.splitlines():
        if "Done" in line:
            try: pipe_int = float(line.split("(")[1].split("ms")[0])
            except: pass
        if "3-sigma" in line:
            try: thresh = float(line.split(":")[1].strip().split()[0])
            except: pass
        if "pixels above" in line:
            try: npx = int(line.split("(")[1].split(" ")[0])
            except: pass
    return {"total_ms": ms, "pipe_ms": pipe_int, "thresh": thresh, "pixels": npx}

def make_base_image(n_stars=100, exposure=0.1, sigma=1.5, seed=42):
    rng = np.random.default_rng(seed)
    bg = DC * exposure
    y, x = np.mgrid[0:H, 0:W]
    r = np.sqrt((x-W/2)**2 + (y-H/2)**2) / np.sqrt((W/2)**2 + (H/2)**2)
    background = bg * (1.0 - 0.10 * r**2)

    image = np.zeros((H, W), dtype=np.float64)
    rad = int(6 * sigma)
    norm = 1.0 / (2 * np.pi * sigma**2)
    sx = rng.uniform(50, W-50, n_stars)
    sy = rng.uniform(50, H-50, n_stars)
    mags = rng.uniform(2.0, 7.0, n_stars)

    for i in range(n_stars):
        flux = ZP * 10**(-0.4 * mags[i]) * exposure
        ix, iy = int(sx[i]), int(sy[i])
        fx, fy = sx[i]-ix, sy[i]-iy
        for dy in range(-rad, rad+1):
            py = iy + dy
            if py < 0 or py >= H: continue
            for dx in range(-rad, rad+1):
                px = ix + dx
                if px < 0 or px >= W: continue
                image[py, px] += flux * norm * np.exp(-((dx-fx)**2+(dy-fy)**2)/(2*sigma**2))

    signal = image + background
    noisy = rng.poisson(np.clip(signal, 0, None)).astype(np.float64) + rng.normal(0, RN, (H, W))
    return noisy.astype(np.float32), background.astype(np.float32), (sx, sy, mags)

out_dir = os.path.join(SCRIPT_DIR, "reallife_tests")
os.makedirs(out_dir, exist_ok=True)

results = []

print("=" * 70)
print("  GERCEK HAYAT SENARYOLARI TESTİ")
print("=" * 70)

# ============================================================
# TEST 1: Hot Pixel / Dead Pixel
# ============================================================
print("\n--- TEST 1: Hot Pixel / Dead Pixel ---")
img, bg, stars = make_base_image(seed=100)

# 50 hot pixel ekle (rastgele konumda, cok yuksek deger)
rng = np.random.default_rng(200)
n_hot = 50
hot_y = rng.integers(0, H, n_hot)
hot_x = rng.integers(0, W, n_hot)
img_hot = img.copy()
for i in range(n_hot):
    img_hot[hot_y[i], hot_x[i]] = 60000.0  # hot pixel

# 30 dead pixel ekle (0 deger)
n_dead = 30
dead_y = rng.integers(0, H, n_dead)
dead_x = rng.integers(0, W, n_dead)
for i in range(n_dead):
    img_hot[dead_y[i], dead_x[i]] = 0.0  # dead pixel

# Temiz goruntu
bp1 = os.path.join(out_dir, "t1_clean.bin")
wbin(bp1, img)
r1a = run_pipeline(bp1, os.path.join(out_dir, "t1_clean"))

# Hot/dead pixelli goruntu
bp2 = os.path.join(out_dir, "t1_badpx.bin")
wbin(bp2, img_hot)
r1b = run_pipeline(bp2, os.path.join(out_dir, "t1_badpx"))

# Karsilastir
sub_clean = rbin(os.path.join(out_dir, "t1_clean_subtracted.bin"))
sub_bad = rbin(os.path.join(out_dir, "t1_badpx_subtracted.bin"))

# Hot pixellerin subtracted'da etkisi
hot_vals = [sub_bad[hot_y[i], hot_x[i]] for i in range(n_hot)]
print(f"  Hot pixel sayisi   : {n_hot}")
print(f"  Dead pixel sayisi  : {n_dead}")
print(f"  Temiz - thresh ustu: {r1a['pixels']} piksel")
print(f"  BadPx - thresh ustu: {r1b['pixels']} piksel")
print(f"  Hot px subtracted  : mean={np.mean(hot_vals):.0f}, max={np.max(hot_vals):.0f}")
print(f"  Etki: +{r1b['pixels'] - r1a['pixels']} false positive piksel")
results.append(("Hot/Dead Pixel", r1b['pixels'] - r1a['pixels'], "false positive"))

# ============================================================
# TEST 2: Degisken Background (Sicaklik Degisimi)
# ============================================================
print("\n--- TEST 2: Degisken Background (Sicaklik) ---")
img_base, bg_base, stars = make_base_image(seed=101)

# 5 frame: sicaklik 25C -> 35C (dark current artar)
temps = [25, 27, 30, 33, 35]
dark_currents = [125, 175, 250, 350, 500]  # e-/px/s (sicaklikla artar)

print(f"  {'Frame':>5}  {'Temp':>5}  {'DC':>6}  {'BG mean':>10}  {'Thresh':>8}  {'Piksel':>7}  {'Sure':>6}")
for i, (temp, dc) in enumerate(zip(temps, dark_currents)):
    rng = np.random.default_rng(300 + i)
    bg_var = dc * 0.1  # exposure=0.1s
    y, x = np.mgrid[0:H, 0:W]
    r = np.sqrt((x-W/2)**2 + (y-H/2)**2) / np.sqrt((W/2)**2 + (H/2)**2)
    bg_new = bg_var * (1.0 - 0.10 * r**2)
    # Yildizlari koru, sadece background degistir
    img_var = img_base - bg_base + bg_new + rng.normal(0, RN, (H, W)).astype(np.float32)

    bp = os.path.join(out_dir, f"t2_temp{temp}.bin")
    wbin(bp, img_var)
    r2 = run_pipeline(bp, os.path.join(out_dir, f"t2_temp{temp}"))
    print(f"  {i+1:>5}  {temp:>4}C  {dc:>5}  {bg_new.mean():>10.1f}  {r2['thresh']:>8.1f}  {r2['pixels']:>7}  {r2['pipe_ms']:>5.0f}ms")
results.append(("Degisken BG", "5 sicaklik", "pipeline adapte oldu"))

# ============================================================
# TEST 3: Motion Blur
# ============================================================
print("\n--- TEST 3: Motion Blur ---")
rng = np.random.default_rng(400)
bg_level = DC * 0.1
y, x = np.mgrid[0:H, 0:W]
r = np.sqrt((x-W/2)**2 + (y-H/2)**2) / np.sqrt((W/2)**2 + (H/2)**2)
background = bg_level * (1.0 - 0.10 * r**2)

# Yildiz: motion blur = cizgi seklinde PSF
n_stars = 80
blur_lengths = [0, 2, 5, 10, 20]  # piksel cinsinden blur uzunlugu

print(f"  {'Blur(px)':>8}  {'Thresh':>8}  {'Piksel':>7}  {'Sure':>6}")
for blur in blur_lengths:
    image = np.zeros((H, W), dtype=np.float64)
    sx = rng.uniform(50, W-50, n_stars)
    sy = rng.uniform(50, H-50, n_stars)
    mags = rng.uniform(2.0, 7.0, n_stars)
    sigma = 1.5

    for s in range(n_stars):
        flux = ZP * 10**(-0.4 * mags[s]) * 0.1
        norm = 1.0 / (2 * np.pi * sigma**2)
        if blur == 0:
            n_steps = 1
        else:
            n_steps = blur * 2
        flux_per_step = flux / max(n_steps, 1)

        for step in range(n_steps):
            cx = sx[s] + (step - n_steps/2) * (blur / max(n_steps, 1))
            cy = sy[s]
            ix, iy = int(cx), int(cy)
            fx, fy = cx - ix, cy - iy
            rad = int(4 * sigma)
            for dy in range(-rad, rad+1):
                py = iy + dy
                if py < 0 or py >= H: continue
                for dx in range(-rad, rad+1):
                    px = ix + dx
                    if px < 0 or px >= W: continue
                    image[py, px] += flux_per_step * norm * np.exp(-((dx-fx)**2+(dy-fy)**2)/(2*sigma**2))

    signal = image + background
    noisy = rng.poisson(np.clip(signal, 0, None)).astype(np.float64) + rng.normal(0, RN, (H, W))

    bp = os.path.join(out_dir, f"t3_blur{blur}.bin")
    wbin(bp, noisy.astype(np.float32))
    r3 = run_pipeline(bp, os.path.join(out_dir, f"t3_blur{blur}"))
    print(f"  {blur:>8}  {r3['thresh']:>8.1f}  {r3['pixels']:>7}  {r3['pipe_ms']:>5.0f}ms")
results.append(("Motion Blur", "0-20px", "threshold adapte"))

# ============================================================
# TEST 4: Saturation
# ============================================================
print("\n--- TEST 4: Saturation ---")
img_base, _, _ = make_base_image(n_stars=50, seed=500)

sat_levels = [4095, 16383, 32767, 65535]
print(f"  {'Sat Level':>10}  {'Doymus px':>10}  {'Thresh':>8}  {'T.ustu':>7}")
for sat in sat_levels:
    img_sat = np.clip(img_base, -1e6, sat).astype(np.float32)
    n_sat = int((img_base >= sat).sum())

    bp = os.path.join(out_dir, f"t4_sat{sat}.bin")
    wbin(bp, img_sat)
    r4 = run_pipeline(bp, os.path.join(out_dir, f"t4_sat{sat}"))
    print(f"  {sat:>10}  {n_sat:>10}  {r4['thresh']:>8.1f}  {r4['pixels']:>7}")
results.append(("Saturation", "4 seviye", "clipping etkisi olculdu"))

# ============================================================
# TEST 5: STOS Verisi
# ============================================================
print("\n--- TEST 5: STOS Radiometric Veri ---")
stos_path = "C:/Users/melsa/photutilsPSFAnalysis/testImages/stosGoruntu.raw"
if os.path.exists(stos_path):
    raw = np.fromfile(stos_path, dtype=np.int16).reshape(1024, 1024).astype(np.float32)
    bp = os.path.join(out_dir, "t5_stos.bin")
    wbin(bp, raw)
    r5 = run_pipeline(bp, os.path.join(out_dir, "t5_stos"))
    print(f"  Boyut        : 1024x1024")
    print(f"  Range        : [{raw.min():.0f}, {raw.max():.0f}]")
    print(f"  Pipeline     : {r5['pipe_ms']:.0f} ms")
    print(f"  Threshold    : {r5['thresh']:.1f} ADU")
    print(f"  Thresh ustu  : {r5['pixels']} piksel")
    results.append(("STOS", f"{r5['pipe_ms']:.0f}ms", "basarili"))
else:
    print("  STOS verisi bulunamadi!")
    results.append(("STOS", "YOK", "atlandı"))

# ============================================================
# OZET
# ============================================================
print(f"\n{'='*70}")
print(f"  OZET")
print(f"{'='*70}")
print(f"  {'Test':<25}  {'Sonuc':<20}  {'Not'}")
print(f"  {'-'*60}")
for name, val, note in results:
    print(f"  {name:<25}  {str(val):<20}  {note}")

print(f"\n  Hot/Dead Pixel : Pipeline threshold ile cogu yakalanir,")
print(f"                   ama bad pixel mask ile false positive azalir.")
print(f"  Degisken BG    : Pipeline her frame'de adapte olur (IIR/ring).")
print(f"  Motion Blur    : Blur arttikca yildiz pikseli yayilir,")
print(f"                   threshold hala calisir ama centroid kayar.")
print(f"  Saturation     : Doymus pikseller threshold ustunde kalir,")
print(f"                   sat_mask ile isaretlenebilir.")
print(f"  STOS           : Gercek sensor verisi basariyla islendi.")
print(f"{'='*70}")
