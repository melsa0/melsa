"""
Realtime pipeline simulasyonu: 16 frame uret, C pipeline ile isle,
ham / subtracted / thresholded yan yana video olustur.

Kullanim:
  python make_video.py
  python make_video.py --frames 32 --fps 30
"""
import numpy as np
import struct
import subprocess
import os
import sys
import argparse
import cv2

# Sensor parametreleri
W, H = 2048, 2048
ZERO_POINT_FLUX = 2_100_000
READ_NOISE = 13.0
DARK_CURRENT = 125.0

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PIPELINE_EXE = os.path.join(SCRIPT_DIR, "pipeline.exe")

def load_hipparcos(mag_limit=6.5):
    cache_path = os.path.join(SCRIPT_DIR, "hipparcos_cache.csv")
    if os.path.exists(cache_path):
        import csv
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
    # Fallback
    np.random.seed(12345)
    n = 5000
    stars = []
    for i in range(n):
        stars.append({
            "RA_deg": np.random.uniform(0, 360),
            "Dec_deg": np.degrees(np.arcsin(np.random.uniform(-1, 1))),
            "Vmag": 6.5 - 6.0 * np.random.power(0.4),
        })
    return stars

def project_to_sensor(stars, ra0, dec0, roll=0.0):
    ra0_r = np.radians(ra0)
    dec0_r = np.radians(dec0)
    roll_r = np.radians(roll)

    ra = np.radians([s["RA_deg"] for s in stars])
    dec = np.radians([s["Dec_deg"] for s in stars])
    vmag = np.array([s["Vmag"] for s in stars])

    cos_dec = np.cos(dec)
    sin_dec = np.sin(dec)
    cos_dec0 = np.cos(dec0_r)
    sin_dec0 = np.sin(dec0_r)
    delta_ra = ra - ra0_r

    denom = sin_dec0 * sin_dec + cos_dec0 * cos_dec * np.cos(delta_ra)
    valid = denom > 0.01

    xi = np.where(valid, cos_dec * np.sin(delta_ra) / denom, 0)
    eta = np.where(valid, (cos_dec0 * sin_dec - sin_dec0 * cos_dec * np.cos(delta_ra)) / denom, 0)

    fl_mm = 42.8598
    pitch_mm = 5.5e-3
    dx_mm = fl_mm * xi
    dy_mm = fl_mm * eta

    cos_r = np.cos(roll_r)
    sin_r = np.sin(roll_r)
    dx_rot = dx_mm * cos_r - dy_mm * sin_r
    dy_rot = dx_mm * sin_r + dy_mm * cos_r

    cx, cy = W / 2.0, H / 2.0
    x_px = cx + dx_rot / pitch_mm
    y_px = cy + dy_rot / pitch_mm

    margin = 10
    in_fov = valid & (x_px >= margin) & (x_px < W - margin) & (y_px >= margin) & (y_px < H - margin)

    visible = []
    for i in range(len(stars)):
        if in_fov[i]:
            visible.append({"x": float(x_px[i]), "y": float(y_px[i]), "Vmag": float(vmag[i])})
    return visible

def render_frame(visible, exposure=0.1, sigma=1.5, seed=42):
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
        if flux < 0.1:
            continue
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
    return noisy.astype(np.float32), background.astype(np.float32)

def read_bin(path):
    with open(path, "rb") as f:
        w, h = struct.unpack("<ii", f.read(8))
        return np.frombuffer(f.read(), dtype=np.float32).reshape(h, w)

def write_bin(path, data):
    h, w = data.shape
    with open(path, "wb") as f:
        f.write(struct.pack("<ii", w, h))
        f.write(data.astype(np.float32).tobytes())

def to_display(data, percentile_lo=1, percentile_hi=99.5, log_scale=False):
    """Float veriden 8-bit goruntu olustur."""
    d = data.copy()
    if log_scale:
        d = np.log1p(np.maximum(d, 0))
    p1 = np.percentile(d, percentile_lo)
    p99 = np.percentile(d, percentile_hi)
    if p99 <= p1:
        p99 = p1 + 1
    d = np.clip(d, p1, p99)
    d = ((d - p1) / (p99 - p1) * 255).astype(np.uint8)
    return d

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", type=int, default=16)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--ra", type=float, default=83.6)
    parser.add_argument("--dec", type=float, default=-5.4)
    parser.add_argument("--drift", type=float, default=0.3, help="Derece/frame kayma")
    parser.add_argument("--exp", type=float, default=0.1)
    args = parser.parse_args()

    out_dir = os.path.join(SCRIPT_DIR, "video_frames")
    os.makedirs(out_dir, exist_ok=True)

    print(f"Katalog yukleniyor...")
    catalog = load_hipparcos(mag_limit=6.5)
    print(f"  {len(catalog)} yildiz yuklendi")

    # Video boyutu: 3 panel yan yana (kucultulmus)
    panel_w, panel_h = 512, 512
    video_w = panel_w * 3
    video_h = panel_h

    video_path = os.path.join(SCRIPT_DIR, "pipeline_demo.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(video_path, fourcc, args.fps, (video_w, video_h))

    print(f"\n{args.frames} frame uretiliyor (RA={args.ra}, Dec={args.dec}, drift={args.drift} deg/frame)...\n")
    print(f"{'Frame':>5}  {'RA':>8}  {'Dec':>8}  {'Yildiz':>7}  {'Threshold':>10}  {'Piksel':>7}")
    print("-" * 60)

    for f in range(args.frames):
        # Boresight her frame'de biraz kayar
        ra = args.ra + args.drift * f
        dec = args.dec + args.drift * 0.2 * f
        roll = 0.5 * f

        # Projeksiyon + render
        visible = project_to_sensor(catalog, ra, dec, roll)
        noisy, background = render_frame(visible, exposure=args.exp, seed=42 + f)

        # .bin kaydet
        frame_bin = os.path.join(out_dir, f"frame_{f:03d}.bin")
        write_bin(frame_bin, noisy)

        # C pipeline calistir
        prefix = os.path.join(out_dir, f"frame_{f:03d}")
        cmd = [PIPELINE_EXE, frame_bin, "-b", "50", "-f", "3", "-o", prefix]
        proc = subprocess.run(cmd, capture_output=True, text=True)

        # Threshold ustu piksel say
        thresh_line = [l for l in proc.stdout.splitlines() if "pixels above" in l]
        n_pix = 0
        if thresh_line:
            try:
                n_pix = int(thresh_line[0].split("(")[1].split(" ")[0])
            except:
                pass

        thresh_val = ""
        for l in proc.stdout.splitlines():
            if "Threshold (3-sigma)" in l:
                thresh_val = l.split(":")[1].strip()

        print(f"{f+1:>5}  {ra:>8.2f}  {dec:>8.2f}  {len(visible):>7}  {thresh_val:>10}  {n_pix:>7}")

        # Ciktilari oku
        sub_path = prefix + "_subtracted.bin"
        thr_path = prefix + "_thresholded.bin"

        sub_data = read_bin(sub_path) if os.path.exists(sub_path) else np.zeros((H, W), np.float32)
        thr_data = read_bin(thr_path) if os.path.exists(thr_path) else np.zeros((H, W), np.float32)

        # Goruntu panelleri olustur
        raw_disp = to_display(noisy, log_scale=True)
        sub_disp = to_display(sub_data, log_scale=True)
        thr_disp = to_display(thr_data, percentile_lo=0, percentile_hi=99.5)

        # Kucult
        raw_small = cv2.resize(raw_disp, (panel_w, panel_h))
        sub_small = cv2.resize(sub_disp, (panel_w, panel_h))
        thr_small = cv2.resize(thr_disp, (panel_w, panel_h))

        # BGR'ye cevir (OpenCV)
        raw_bgr = cv2.cvtColor(raw_small, cv2.COLOR_GRAY2BGR)
        sub_bgr = cv2.cvtColor(sub_small, cv2.COLOR_GRAY2BGR)
        thr_bgr = cv2.cvtColor(thr_small, cv2.COLOR_GRAY2BGR)

        # Etiketler
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(raw_bgr, "HAM", (10, 30), font, 0.8, (0, 255, 255), 2)
        cv2.putText(sub_bgr, "SUBTRACTED", (10, 30), font, 0.8, (0, 255, 0), 2)
        cv2.putText(thr_bgr, "THRESHOLDED", (10, 30), font, 0.8, (0, 100, 255), 2)

        # Frame bilgisi
        info = f"Frame {f+1}/{args.frames}  RA={ra:.1f} Dec={dec:.1f}  Stars={len(visible)}"
        cv2.putText(raw_bgr, info, (10, panel_h - 15), font, 0.45, (200, 200, 200), 1)

        # Birlestir
        combined = np.hstack([raw_bgr, sub_bgr, thr_bgr])
        video.write(combined)

    video.release()
    print(f"\nVideo: {video_path}")
    print(f"  {args.frames} frame, {args.fps} FPS, {args.frames / args.fps:.1f} saniye")
    print(f"  Boyut: {video_w}x{video_h}")

    # Temizlik (opsiyonel)
    # import shutil
    # shutil.rmtree(out_dir)

if __name__ == "__main__":
    main()
