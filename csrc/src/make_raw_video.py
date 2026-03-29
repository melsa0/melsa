"""
Hipparcos katalogundan 16 farkli gokyuzu yonunde ham goruntu uret,
ard arda dizip 30 FPS video olustur.
"""
import numpy as np
import struct
import os
import sys
import cv2

W, H = 2048, 2048
ZERO_POINT_FLUX = 2_100_000
READ_NOISE = 13.0
DARK_CURRENT = 125.0
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_hipparcos(mag_limit=6.5):
    import csv
    cache_path = os.path.join(SCRIPT_DIR, "hipparcos_cache.csv")
    stars = []
    with open(cache_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            vmag = float(row["Vmag"])
            if vmag <= mag_limit:
                stars.append({
                    "RA_deg": float(row["RA_deg"]),
                    "Dec_deg": float(row["Dec_deg"]),
                    "Vmag": vmag,
                })
    return stars

def project(stars, ra0, dec0, roll=0.0):
    ra0_r, dec0_r, roll_r = np.radians(ra0), np.radians(dec0), np.radians(roll)
    ra = np.radians([s["RA_deg"] for s in stars])
    dec = np.radians([s["Dec_deg"] for s in stars])
    vmag = np.array([s["Vmag"] for s in stars])

    cos_d, sin_d = np.cos(dec), np.sin(dec)
    cos_d0, sin_d0 = np.cos(dec0_r), np.sin(dec0_r)
    dra = ra - ra0_r
    denom = sin_d0 * sin_d + cos_d0 * cos_d * np.cos(dra)
    valid = denom > 0.01

    xi = np.where(valid, cos_d * np.sin(dra) / denom, 0)
    eta = np.where(valid, (cos_d0 * sin_d - sin_d0 * cos_d * np.cos(dra)) / denom, 0)

    fl, pitch = 42.8598, 5.5e-3
    dx = fl * xi; dy = fl * eta
    cr, sr = np.cos(roll_r), np.sin(roll_r)
    dxr = dx * cr - dy * sr; dyr = dx * sr + dy * cr
    cx, cy = W / 2.0, H / 2.0
    xp = cx + dxr / pitch; yp = cy + dyr / pitch

    m = 10
    mask = valid & (xp >= m) & (xp < W - m) & (yp >= m) & (yp < H - m)
    vis = []
    for i in range(len(stars)):
        if mask[i]:
            vis.append({"x": float(xp[i]), "y": float(yp[i]), "Vmag": float(vmag[i])})
    return vis

def render(visible, exposure=0.1, sigma=1.5, seed=42):
    rng = np.random.default_rng(seed)
    bg_level = DARK_CURRENT * exposure
    y, x = np.mgrid[0:H, 0:W]
    cx, cy = W / 2.0, H / 2.0
    r = np.sqrt((x - cx)**2 + (y - cy)**2) / np.sqrt(cx**2 + cy**2)
    background = bg_level * (1.0 - 0.10 * r**2)

    image = np.zeros((H, W), dtype=np.float64)
    radius = int(6 * sigma)
    norm = 1.0 / (2.0 * np.pi * sigma**2)
    for star in visible:
        flux = ZERO_POINT_FLUX * 10**(-0.4 * star["Vmag"]) * exposure
        if flux < 0.1: continue
        sx, sy = star["x"], star["y"]
        ix, iy = int(sx), int(sy)
        fx, fy = sx - ix, sy - iy
        for dy in range(-radius, radius + 1):
            py = iy + dy
            if py < 0 or py >= H: continue
            for dx in range(-radius, radius + 1):
                px = ix + dx
                if px < 0 or px >= W: continue
                r2 = (dx - fx)**2 + (dy - fy)**2
                image[py, px] += flux * norm * np.exp(-r2 / (2 * sigma**2))

    signal = image + background
    noisy = rng.poisson(np.clip(signal, 0, None).astype(np.float64))
    noisy = noisy.astype(np.float64) + rng.normal(0, READ_NOISE, (H, W))
    return noisy.astype(np.float32)

def to_display(data):
    d = np.log1p(np.maximum(data - np.percentile(data, 1), 0))
    p99 = np.percentile(d, 99.5)
    if p99 <= 0: p99 = 1
    d = np.clip(d / p99 * 255, 0, 255).astype(np.uint8)
    return d

# ---- 16 farkli gokyuzu yonu ----
POINTINGS = [
    (83.6, -5.4, "Orion"),
    (88.8, 7.4, "Betelgeuse"),
    (95.0, 10.0, "Monoceros"),
    (101.3, -16.7, "Sirius"),
    (114.8, 5.2, "Procyon"),
    (120.0, 20.0, "Gemini"),
    (132.0, 28.0, "Cancer"),
    (152.1, 11.9, "Regulus"),
    (177.3, 14.6, "Denebola"),
    (186.6, -63.1, "Crux"),
    (201.3, -11.2, "Spica"),
    (213.9, 19.2, "Arcturus"),
    (247.3, -26.4, "Antares"),
    (279.2, 38.8, "Vega"),
    (297.7, 8.9, "Altair"),
    (310.4, 45.3, "Deneb"),
]

print("Katalog yukleniyor...")
catalog = load_hipparcos(6.5)
print(f"  {len(catalog)} yildiz\n")

video_path = os.path.join(SCRIPT_DIR, "hipparcos_raw_16frames.mp4")
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
video = cv2.VideoWriter(video_path, fourcc, 30, (2048, 2048))

font = cv2.FONT_HERSHEY_SIMPLEX

print(f"{'#':>2}  {'Yon':<15}  {'RA':>8}  {'Dec':>8}  {'Yildiz':>7}")
print("-" * 50)

for i, (ra, dec, name) in enumerate(POINTINGS):
    visible = project(catalog, ra, dec, roll=0)
    frame = render(visible, exposure=0.1, sigma=1.5, seed=42 + i)

    disp = to_display(frame)
    bgr = cv2.cvtColor(disp, cv2.COLOR_GRAY2BGR)

    # Bilgi ekle
    cv2.putText(bgr, f"{name}", (20, 50), font, 1.2, (0, 255, 255), 2)
    cv2.putText(bgr, f"RA={ra:.1f}  Dec={dec:.1f}  Stars={len(visible)}",
                (20, 90), font, 0.7, (180, 180, 180), 1)
    cv2.putText(bgr, f"Frame {i+1}/16", (20, 2020), font, 0.8, (150, 150, 150), 1)

    video.write(bgr)
    print(f"{i+1:>2}  {name:<15}  {ra:>8.1f}  {dec:>8.1f}  {len(visible):>7}")

video.release()
print(f"\nVideo: {video_path}")
print(f"  16 frame, 30 FPS, {16/30:.2f} saniye, 2048x2048")
