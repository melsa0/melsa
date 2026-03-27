"""
Pipeline .bin ciktisini FITS formatina cevir. AstroImageJ ile acmak icin.

Kullanim:
  python bin2fits.py tests/catalog_002/catalog_002
  -> catalog_002_input.fits, catalog_002_subtracted.fits, ...

  python bin2fits.py tests/catalog_002/catalog_002_subtracted
  -> sadece subtracted.fits
"""
import numpy as np
import struct
import sys
import os
from astropy.io import fits

def bin_to_fits(bin_path):
    with open(bin_path, "rb") as f:
        w, h = struct.unpack("<ii", f.read(8))
        data = np.frombuffer(f.read(), dtype=np.float32).reshape(h, w)

    fits_path = bin_path.replace(".bin", ".fits")
    hdu = fits.PrimaryHDU(data.astype(np.float32))
    hdu.header['NAXIS1'] = w
    hdu.header['NAXIS2'] = h
    hdu.writeto(fits_path, overwrite=True)
    print(f"  {fits_path}  ({w}x{h})")
    return fits_path

if len(sys.argv) < 2:
    print("Kullanim: python bin2fits.py <prefix>")
    print("Ornek:    python bin2fits.py tests/catalog_002/catalog_002")
    sys.exit(1)

prefix = sys.argv[1]

# Tek dosya mi prefix mi?
if prefix.endswith(".bin"):
    bin_to_fits(prefix)
else:
    suffixes = ["_input.bin", "_background.bin", "_subtracted.bin", "_errormap.bin"]
    found = False
    for s in suffixes:
        p = prefix + s
        if os.path.exists(p):
            bin_to_fits(p)
            found = True
    if not found:
        # Belki .bin uzantisiz tek dosya
        if os.path.exists(prefix + ".bin"):
            bin_to_fits(prefix + ".bin")
        else:
            print(f"Dosya bulunamadi: {prefix}*")
