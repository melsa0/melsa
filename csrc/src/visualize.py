"""
C pipeline ciktisi .bin dosyalarini okunabilir PNG'ye donustur.
Kullanim:
  python visualize.py test_new
  -> test_new_input.png, test_new_background.png, test_new_subtracted.png, test_new_errormap.png
"""
import numpy as np
import struct
import sys
from PIL import Image

def read_bin(path):
    with open(path, "rb") as f:
        w, h = struct.unpack("<ii", f.read(8))
        data = np.frombuffer(f.read(), dtype=np.float32).reshape(h, w)
    return data

def save_png(data, path, log_scale=False):
    if log_scale:
        d = np.maximum(data, 0)
        d = np.log1p(d)  # log(1+x)
    else:
        d = data.copy()
    p1, p99 = np.percentile(d, [1, 99])
    d = np.clip(d, p1, p99)
    if p99 > p1:
        d = ((d - p1) / (p99 - p1) * 255).astype(np.uint8)
    else:
        d = np.zeros_like(d, dtype=np.uint8)
    Image.fromarray(d).save(path)
    print(f"  {path}")

if len(sys.argv) < 2:
    print("Kullanim: python visualize.py <prefix>")
    print("Ornek:    python visualize.py test_new")
    sys.exit(1)

prefix = sys.argv[1]

print(f"Gorselleştirme: {prefix}")

for suffix, log in [("_input", False), ("_background", False),
                     ("_subtracted", True), ("_errormap", True)]:
    bin_path = f"{prefix}{suffix}.bin"
    png_path = f"{prefix}{suffix}.png"
    try:
        data = read_bin(bin_path)
        save_png(data, png_path, log_scale=log)
    except FileNotFoundError:
        print(f"  {bin_path} bulunamadi, atlandi.")
