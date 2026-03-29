#!/usr/bin/env python3
"""
Hipparcos Katalogu ile Gercekci Sentetik Star Tracker Goruntusu Uretici

Photutils/rayoptics KULLANMAZ. Sadece numpy + astropy.
Hipparcos katalogundaki gercek yildiz konumlarini gnomonic (TAN) projeksiyonla
2048x2048 sensore yansitir, Gaussian PSF ile render eder.

Kullanim:
  python generate_catalog_image.py
  python generate_catalog_image.py --ra 180 --dec 45 --roll 30
  python generate_catalog_image.py --ra 90 --dec -20 --exp 0.05 --mag 7.0
  python generate_catalog_image.py --ra 0 --dec 90 --sigma 2.0 --seed 99

Ciktilar:
  tests/catalog_NNN/  klasorunde:
    - catalog_NNN.bin           (C pipeline girdisi)
    - catalog_NNN_truebkg.bin   (ground truth background)
    - catalog_NNN_stars.csv     (yildiz ground truth: x, y, mag, flux)
    - params.txt                (uretim parametreleri)
"""
import numpy as np
import struct
import os
import sys
import glob
import argparse
import csv

# ============================================================================
# SENSOR & OPTIK PARAMETRELER (CMV4000)
# ============================================================================
SENSOR_W, SENSOR_H = 2048, 2048
PIXEL_PITCH_UM = 5.5
FOCAL_LENGTH_MM = 42.8598
ZERO_POINT_FLUX = 2_100_000  # e-/s for mag=0 (optik kayiplar dahil)
READ_NOISE = 13.0            # e- RMS
DARK_CURRENT = 125.0         # e-/px/s @ 25C

# ============================================================================
# HIPPARCOS KATALOGU YUKLEME
# ============================================================================

def load_hipparcos(mag_limit=6.0, cache_dir=None):
    """
    Hipparcos katalogunu yukle. Ilk calistirmada VizieR'den indirir,
    sonrasinda lokal CSV cache kullanir.
    """
    if cache_dir is None:
        cache_dir = os.path.dirname(os.path.abspath(__file__))
    cache_path = os.path.join(cache_dir, "hipparcos_cache.csv")

    if os.path.exists(cache_path):
        # Cache'den yukle
        stars = []
        with open(cache_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                vmag = float(row["Vmag"])
                if vmag <= mag_limit:
                    stars.append({
                        "HIP": int(row["HIP"]),
                        "RA_deg": float(row["RA_deg"]),
                        "Dec_deg": float(row["Dec_deg"]),
                        "Vmag": vmag,
                    })
        print(f"  Katalog cache'den yuklendi: {len(stars)} yildiz (Vmag <= {mag_limit})")
        return stars

    # VizieR'den indir
    print(f"  Hipparcos katalogu VizieR'den indiriliyor (Vmag <= {mag_limit + 0.5})...")
    try:
        from astroquery.vizier import Vizier
        from astropy.coordinates import SkyCoord
        import astropy.units as u

        vizier = Vizier(columns=['HIP', 'RAhms', 'DEdms', 'Vmag'],
                        column_filters={"Vmag": f"<={mag_limit + 0.5}"},
                        row_limit=-1)
        result = vizier.get_catalogs('I/239/hip_main')
        if not result:
            raise RuntimeError("Katalog indirilemedi!")

        hip_table = result[0]
        coords = SkyCoord(hip_table['RAhms'], hip_table['DEdms'],
                          unit=(u.hourangle, u.deg), frame='icrs')

        stars = []
        with open(cache_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["HIP", "RA_deg", "Dec_deg", "Vmag"])
            writer.writeheader()
            for i in range(len(hip_table)):
                vmag = float(hip_table['Vmag'][i])
                ra_d = float(coords.ra.deg[i])
                dec_d = float(coords.dec.deg[i])
                if not (np.isfinite(vmag) and np.isfinite(ra_d)):
                    continue
                row = {
                    "HIP": int(hip_table['HIP'][i]),
                    "RA_deg": ra_d,
                    "Dec_deg": dec_d,
                    "Vmag": vmag,
                }
                writer.writerow(row)
                if vmag <= mag_limit:
                    stars.append(row)

        print(f"  {len(stars)} yildiz indirildi ve cache'lendi: {cache_path}")
        return stars

    except ImportError:
        print("  UYARI: astroquery yuklu degil. pip install astroquery")
        print("  Alternatif: Hipparcos bright star katalogu olusturuluyor...")
        return _generate_fallback_catalog(mag_limit)


def _generate_fallback_catalog(mag_limit=6.0):
    """
    astroquery yoksa, istatistiksel olarak gercekci rastgele katalog uret.
    Gercek Hipparcos dagilimindan esinlenilmis.
    """
    np.random.seed(12345)
    n_total = int(5000 * (mag_limit / 6.0) ** 2.5)

    # Gokyuzunde uniform dagilim (kure uzerinde)
    ra_deg = np.random.uniform(0, 360, n_total)
    cos_dec = np.random.uniform(-1, 1, n_total)
    dec_deg = np.degrees(np.arcsin(cos_dec))

    # Magnitude dagilimi (logaritmik artis)
    vmag = np.random.uniform(0.5, mag_limit, n_total)
    # Gercekci: sonuk yildiz cok, parlak az
    vmag = mag_limit - (mag_limit - 0.5) * np.random.power(0.4, n_total)

    stars = []
    for i in range(n_total):
        stars.append({
            "HIP": 100000 + i,
            "RA_deg": float(ra_deg[i]),
            "Dec_deg": float(dec_deg[i]),
            "Vmag": float(vmag[i]),
        })
    print(f"  Fallback katalog: {len(stars)} sentetik yildiz (Vmag <= {mag_limit})")
    return stars


# ============================================================================
# GNOMONIC (TAN) PROJEKSIYON
# ============================================================================

def project_to_sensor(stars, boresight_ra, boresight_dec, roll_deg=0.0):
    """
    RA/Dec -> sensor (x, y) donusumu: gnomonic projeksiyon + roll.
    """
    ra0 = np.radians(boresight_ra)
    dec0 = np.radians(boresight_dec)
    roll_rad = np.radians(roll_deg)

    ra = np.radians([s["RA_deg"] for s in stars])
    dec = np.radians([s["Dec_deg"] for s in stars])
    vmag = np.array([s["Vmag"] for s in stars])
    hip = np.array([s["HIP"] for s in stars])

    cos_dec = np.cos(dec)
    sin_dec = np.sin(dec)
    cos_dec0 = np.cos(dec0)
    sin_dec0 = np.sin(dec0)
    delta_ra = ra - ra0

    denom = sin_dec0 * sin_dec + cos_dec0 * cos_dec * np.cos(delta_ra)

    # Arka yarikure kontrolu
    valid = denom > 0.01
    xi = np.where(valid, cos_dec * np.sin(delta_ra) / denom, 0)
    eta = np.where(valid, (cos_dec0 * sin_dec - sin_dec0 * cos_dec * np.cos(delta_ra)) / denom, 0)

    # Radian -> mm -> piksel
    pitch_mm = PIXEL_PITCH_UM * 1e-3
    dx_mm = FOCAL_LENGTH_MM * xi
    dy_mm = FOCAL_LENGTH_MM * eta

    # Roll rotasyonu
    cos_r = np.cos(roll_rad)
    sin_r = np.sin(roll_rad)
    dx_rot = dx_mm * cos_r - dy_mm * sin_r
    dy_rot = dx_mm * sin_r + dy_mm * cos_r

    # Piksel koordinatlari (merkez = W/2, H/2)
    cx, cy = SENSOR_W / 2.0, SENSOR_H / 2.0
    x_px = cx + dx_rot / pitch_mm
    y_px = cy + dy_rot / pitch_mm

    # FOV icinde mi?
    margin = 10
    in_fov = (valid &
              (x_px >= margin) & (x_px < SENSOR_W - margin) &
              (y_px >= margin) & (y_px < SENSOR_H - margin))

    visible = []
    for i in range(len(stars)):
        if in_fov[i]:
            visible.append({
                "HIP": int(hip[i]),
                "RA_deg": stars[i]["RA_deg"],
                "Dec_deg": stars[i]["Dec_deg"],
                "Vmag": float(vmag[i]),
                "x": float(x_px[i]),
                "y": float(y_px[i]),
            })
    return visible


# ============================================================================
# GORUNTU RENDER (saf numpy, Gaussian PSF)
# ============================================================================

def render_image(visible_stars, exposure_s=0.01, psf_sigma=1.5,
                 read_noise=READ_NOISE, dark_current=DARK_CURRENT,
                 seed=42, noiseless=False):
    """
    Goruntu render: Gaussian PSF + Poisson + read noise.
    """
    rng = np.random.default_rng(seed)

    # Background
    bg_level = dark_current * exposure_s  # e-/px

    # Temiz goruntu (yildizlar)
    image_clean = np.zeros((SENSOR_H, SENSOR_W), dtype=np.float64)
    radius = int(6 * psf_sigma)

    for star in visible_stars:
        # Flux: Pogson formulu
        flux = ZERO_POINT_FLUX * 10**(-0.4 * star["Vmag"]) * exposure_s
        if flux < 0.1:
            continue

        sx, sy = star["x"], star["y"]
        ix, iy = int(sx), int(sy)
        frac_x, frac_y = sx - ix, sy - iy

        for dy in range(-radius, radius + 1):
            py = iy + dy
            if py < 0 or py >= SENSOR_H:
                continue
            for dx in range(-radius, radius + 1):
                px = ix + dx
                if px < 0 or px >= SENSOR_W:
                    continue
                r2 = (dx - frac_x)**2 + (dy - frac_y)**2
                image_clean[py, px] += flux * np.exp(-r2 / (2 * psf_sigma**2))

    # Normalize PSF (toplam flux korunmali)
    # 2D Gaussian normalizasyonu: 1/(2*pi*sigma^2)
    norm = 1.0 / (2.0 * np.pi * psf_sigma**2)
    image_clean *= norm

    # Flux bilgisini guncelle
    for star in visible_stars:
        star["flux"] = ZERO_POINT_FLUX * 10**(-0.4 * star["Vmag"]) * exposure_s

    # Background haritasi (vignetting dahil)
    y, x = np.mgrid[0:SENSOR_H, 0:SENSOR_W]
    cx, cy = SENSOR_W / 2.0, SENSOR_H / 2.0
    r = np.sqrt((x - cx)**2 + (y - cy)**2) / np.sqrt(cx**2 + cy**2)
    vignetting = 1.0 - 0.10 * r**2
    background = bg_level * vignetting

    if noiseless:
        return image_clean + background, image_clean, background

    # Noisy goruntu
    signal = image_clean + background
    noisy = rng.poisson(np.clip(signal, 0, None).astype(np.float64))
    noisy = noisy.astype(np.float64) + rng.normal(0, read_noise, (SENSOR_H, SENSOR_W))

    return noisy, image_clean, background


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Hipparcos katalog goruntu uretici")
    parser.add_argument("--ra", type=float, default=180.0, help="Boresight RA (derece)")
    parser.add_argument("--dec", type=float, default=45.0, help="Boresight Dec (derece)")
    parser.add_argument("--roll", type=float, default=0.0, help="Roll acisi (derece)")
    parser.add_argument("--mag", type=float, default=6.5, help="Magnitude limiti")
    parser.add_argument("--exp", type=float, default=0.1, help="Pozlama suresi (saniye)")
    parser.add_argument("--sigma", type=float, default=1.5, help="PSF sigma (piksel)")
    parser.add_argument("--rn", type=float, default=READ_NOISE, help="Read noise (e-)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--noiseless", action="store_true", help="Gurultusuz goruntu")
    parser.add_argument("-b", "--box", type=int, default=50, help="C pipeline box size")
    parser.add_argument("-f", "--filter", type=int, default=3, help="C pipeline filter size")
    args = parser.parse_args()

    # Otomatik numaralama
    base_dir = "tests"
    os.makedirs(base_dir, exist_ok=True)
    existing = glob.glob(os.path.join(base_dir, "catalog_*"))
    nums = []
    for d in existing:
        name = os.path.basename(d)
        try:
            nums.append(int(name.split("_")[1]))
        except (IndexError, ValueError):
            pass
    next_num = max(nums) + 1 if nums else 1
    test_name = f"catalog_{next_num:03d}"
    test_dir = os.path.join(base_dir, test_name)
    os.makedirs(test_dir, exist_ok=True)

    print(f"\n{'='*65}")
    print(f"  {test_name} — Hipparcos Katalog Goruntusu")
    print(f"  RA={args.ra:.1f}, Dec={args.dec:.1f}, Roll={args.roll:.1f}")
    print(f"  mag<={args.mag}, exp={args.exp}s, sigma={args.sigma}, rn={args.rn}")
    print(f"{'='*65}\n")

    # 1) Katalog yukle
    print("[1] Katalog yukleniyor...")
    catalog = load_hipparcos(mag_limit=args.mag)

    # 2) Sensor'e projeksiyon
    print("[2] Gnomonic projeksiyon...")
    visible = project_to_sensor(catalog, args.ra, args.dec, args.roll)
    print(f"    FOV icinde: {len(visible)} yildiz")

    if len(visible) == 0:
        print("  UYARI: Bu yonde hic yildiz yok! Farkli RA/Dec dene.")
        sys.exit(1)

    # 3) Render
    print("[3] Goruntu render ediliyor...")
    noisy, clean, background = render_image(
        visible, exposure_s=args.exp, psf_sigma=args.sigma,
        read_noise=args.rn, seed=args.seed, noiseless=args.noiseless
    )
    print(f"    Noisy range: [{noisy.min():.1f}, {noisy.max():.1f}]")
    print(f"    Background avg: {background.mean():.2f} e-")

    # 4) Binary kaydet (C pipeline icin)
    bin_path = os.path.join(test_dir, f"{test_name}.bin")
    with open(bin_path, "wb") as f:
        f.write(struct.pack("<ii", SENSOR_W, SENSOR_H))
        f.write(noisy.astype(np.float32).tobytes())
    print(f"[4] Binary: {bin_path}")

    gt_bkg_path = os.path.join(test_dir, f"{test_name}_truebkg.bin")
    with open(gt_bkg_path, "wb") as f:
        f.write(struct.pack("<ii", SENSOR_W, SENSOR_H))
        f.write(background.astype(np.float32).tobytes())

    # 5) Ground truth CSV
    csv_path = os.path.join(test_dir, f"{test_name}_stars.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["HIP", "RA_deg", "Dec_deg", "Vmag", "x", "y", "flux"])
        writer.writeheader()
        for s in sorted(visible, key=lambda s: s["Vmag"]):
            writer.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in s.items()})
    print(f"    Stars CSV: {csv_path} ({len(visible)} yildiz)")

    # 6) Parametreler
    info_path = os.path.join(test_dir, "params.txt")
    with open(info_path, "w") as f:
        f.write(f"ra={args.ra}\ndec={args.dec}\nroll={args.roll}\n")
        f.write(f"mag_limit={args.mag}\nexposure={args.exp}\n")
        f.write(f"sigma={args.sigma}\nread_noise={args.rn}\nseed={args.seed}\n")
        f.write(f"n_stars={len(visible)}\nnoiseless={args.noiseless}\n")
        f.write(f"box={args.box}\nfilter={args.filter}\n")

    # 7) C pipeline calistir
    print(f"\n[5] C pipeline calisiyor...")
    import subprocess
    prefix = os.path.join(test_dir, test_name)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    exe_path = os.path.join(script_dir, "pipeline.exe")
    cmd = [exe_path, bin_path, "-b", str(args.box), "-f", str(args.filter), "-o", prefix]
    proc = subprocess.run(cmd, capture_output=False, text=True)

    if proc.returncode != 0:
        print("  C pipeline HATA!")
    else:
        print(f"\n[6] Ciktilar:")
        abs_dir = os.path.abspath(test_dir)
        for fn in sorted(os.listdir(test_dir)):
            size = os.path.getsize(os.path.join(test_dir, fn))
            print(f"    {fn}  ({size // 1024} KB)")
        print(f"\n    AstroImageJ ile ac:")
        print(f"    File > Open > {abs_dir}\\{test_name}_subtracted.bmp")
        print(f"    File > Open > {abs_dir}\\{test_name}_input.bmp")

    print()


if __name__ == "__main__":
    main()
