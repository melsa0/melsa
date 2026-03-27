"""
Her calistirmada yeni numarali goruntu uret + C pipeline ile isle.
Kullanim:
  python run_test.py                  (varsayilan parametreler)
  python run_test.py --stars 500      (500 yildiz)
  python run_test.py --sky 80 --rn 30 (yuksek gurultu)

Ciktilar:  tests/test_001/, tests/test_002/, ...
"""
import numpy as np
import struct
import subprocess
import os
import sys
import glob
import argparse

# --- Arguman parse ---
parser = argparse.ArgumentParser()
parser.add_argument("--stars", type=int, default=200)
parser.add_argument("--sky", type=float, default=20.0)
parser.add_argument("--rn", type=float, default=13.0)
parser.add_argument("--exp", type=float, default=100.0)
parser.add_argument("--sigma", type=float, default=1.5)
parser.add_argument("--seed", type=int, default=None)
parser.add_argument("-b", "--box", type=int, default=50)
parser.add_argument("-f", "--filter", type=int, default=3)
args = parser.parse_args()

# --- Otomatik numaralama ---
base_dir = "tests"
os.makedirs(base_dir, exist_ok=True)

existing = glob.glob(os.path.join(base_dir, "test_*"))
nums = []
for d in existing:
    name = os.path.basename(d)
    try:
        nums.append(int(name.split("_")[1]))
    except (IndexError, ValueError):
        pass

next_num = max(nums) + 1 if nums else 1
test_name = f"test_{next_num:03d}"
test_dir = os.path.join(base_dir, test_name)
os.makedirs(test_dir, exist_ok=True)

# --- Seed ---
seed = args.seed if args.seed is not None else next_num
np.random.seed(seed)

W, H = 2048, 2048

print(f"\n{'='*60}")
print(f"  {test_name}")
print(f"  stars={args.stars}, sky={args.sky}, rn={args.rn}, exp={args.exp}, sigma={args.sigma}, seed={seed}")
print(f"  box={args.box}, filter={args.filter}")
print(f"{'='*60}\n")

# --- 1) Background ---
y, x = np.mgrid[0:H, 0:W]
cx, cy = W / 2, H / 2
r = np.sqrt((x - cx)**2 + (y - cy)**2) / np.sqrt(cx**2 + cy**2)
vignetting = 1.0 - 0.15 * r**2
sky = args.sky * args.exp * vignetting
dark = 0.1 * args.exp
background = sky + dark

# --- 2) Yildizlar ---
star_x = np.random.uniform(50, W - 50, args.stars)
star_y = np.random.uniform(50, H - 50, args.stars)
magnitudes = np.random.uniform(2.0, 8.0, args.stars)
zero_point = 1e6 * args.exp
fluxes = zero_point * 10**(-0.4 * magnitudes)

star_image = np.zeros((H, W), dtype=np.float64)
radius = int(5 * args.sigma)
for i in range(args.stars):
    ix, iy = int(star_x[i]), int(star_y[i])
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            px, py = ix + dx, iy + dy
            if 0 <= px < W and 0 <= py < H:
                r2 = (dx - (star_x[i] - ix))**2 + (dy - (star_y[i] - iy))**2
                star_image[py, px] += fluxes[i] * np.exp(-r2 / (2 * args.sigma**2))

# --- 3) Noise ---
signal = background + star_image
noisy = np.random.poisson(np.maximum(signal, 0)).astype(np.float64)
noisy += np.random.normal(0, args.rn, (H, W))

# --- 4) Kaydet ---
bin_path = os.path.join(test_dir, f"{test_name}.bin")
with open(bin_path, "wb") as f:
    f.write(struct.pack("<ii", W, H))
    f.write(noisy.astype(np.float32).tobytes())

gt_path = os.path.join(test_dir, f"{test_name}_truebkg.bin")
with open(gt_path, "wb") as f:
    f.write(struct.pack("<ii", W, H))
    f.write(background.astype(np.float32).tobytes())

# --- 5) Parametreleri kaydet ---
info_path = os.path.join(test_dir, "params.txt")
with open(info_path, "w") as f:
    f.write(f"stars={args.stars}\n")
    f.write(f"sky={args.sky}\n")
    f.write(f"read_noise={args.rn}\n")
    f.write(f"exposure={args.exp}\n")
    f.write(f"sigma={args.sigma}\n")
    f.write(f"seed={seed}\n")
    f.write(f"box={args.box}\n")
    f.write(f"filter={args.filter}\n")

print(f"[1] Goruntu: {bin_path}")

# --- 6) C pipeline ---
prefix = os.path.join(test_dir, test_name)
cmd = ["./pipeline.exe", bin_path, "-b", str(args.box), "-f", str(args.filter), "-o", prefix]
print(f"[2] C pipeline: {' '.join(cmd)}\n")
proc = subprocess.run(cmd, capture_output=False, text=True)

if proc.returncode != 0:
    print("HATA!")
    sys.exit(1)

print(f"\n[3] Ciktilar:")
print(f"    {test_dir}/")
for f in sorted(os.listdir(test_dir)):
    size = os.path.getsize(os.path.join(test_dir, f))
    print(f"      {f}  ({size // 1024} KB)")

print(f"\n[4] AstroImageJ ile ac:")
abs_dir = os.path.abspath(test_dir)
print(f"    File > Open > {abs_dir}\\{test_name}_subtracted.bmp")
print(f"    File > Open > {abs_dir}\\{test_name}_input.bmp")
print()
