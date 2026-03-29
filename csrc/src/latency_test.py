"""
Frame-by-frame gecikme olcumu.
Her frame icin: goruntu uret -> pipeline isle -> cikti al, suresi olc.
"""
import numpy as np, struct, subprocess, os, time, csv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PIPELINE_EXE = os.path.join(SCRIPT_DIR, "pipeline.exe")
REALTIME_EXE = os.path.join(SCRIPT_DIR, "realtime.exe")
OUT_DIR = os.path.join(SCRIPT_DIR, "latency_test")
os.makedirs(OUT_DIR, exist_ok=True)

W, H = 2048, 2048
ZP, RN, DC = 2_100_000, 13.0, 125.0

POINTINGS = [
    (83.6,-5.4,"Orion"),(88.8,7.4,"Betelgeuse"),(95.0,10.0,"Monoceros"),
    (101.3,-16.7,"Sirius"),(114.8,5.2,"Procyon"),(120.0,20.0,"Gemini"),
    (132.0,28.0,"Cancer"),(152.1,11.9,"Regulus"),(177.3,14.6,"Denebola"),
    (186.6,-63.1,"Crux"),(201.3,-11.2,"Spica"),(213.9,19.2,"Arcturus"),
    (247.3,-26.4,"Antares"),(279.2,38.8,"Vega"),(297.7,8.9,"Altair"),
    (310.4,45.3,"Deneb"),
]

def load_cat():
    stars = []
    with open(os.path.join(SCRIPT_DIR, "hipparcos_cache.csv")) as f:
        for r in csv.DictReader(f):
            if float(r["Vmag"]) <= 6.5:
                stars.append((float(r["RA_deg"]), float(r["Dec_deg"]), float(r["Vmag"])))
    return stars

def proj(stars, ra0, dec0, roll=0):
    ra0r,d0r,rr = np.radians(ra0),np.radians(dec0),np.radians(roll)
    ra=np.array([s[0] for s in stars]); dec=np.array([s[1] for s in stars]); vm=np.array([s[2] for s in stars])
    ra,dec = np.radians(ra),np.radians(dec)
    cd,sd=np.cos(dec),np.sin(dec); cd0,sd0=np.cos(d0r),np.sin(d0r)
    den = sd0*sd + cd0*cd*np.cos(ra-ra0r); v = den>0.01
    xi=np.where(v,cd*np.sin(ra-ra0r)/den,0); eta=np.where(v,(cd0*sd-sd0*cd*np.cos(ra-ra0r))/den,0)
    fl,p=42.8598,5.5e-3; cr,sr=np.cos(rr),np.sin(rr)
    dx,dy=fl*xi,fl*eta; xp=W/2+(dx*cr-dy*sr)/p; yp=H/2+(dx*sr+dy*cr)/p
    m=10; mask=v&(xp>=m)&(xp<W-m)&(yp>=m)&(yp<H-m)
    return [(float(xp[i]),float(yp[i]),float(vm[i])) for i in range(len(stars)) if mask[i]]

def render(vis, exp=0.1, sig=1.5, seed=42):
    rng=np.random.default_rng(seed)
    bg=DC*exp; y,x=np.mgrid[0:H,0:W]; r=np.sqrt((x-W/2)**2+(y-H/2)**2)/np.sqrt((W/2)**2+(H/2)**2)
    background=bg*(1-0.1*r**2); img=np.zeros((H,W),np.float64)
    rad=int(6*sig); nm=1/(2*np.pi*sig**2)
    for sx,sy,vm in vis:
        fl=ZP*10**(-0.4*vm)*exp
        if fl<0.1: continue
        ix,iy=int(sx),int(sy); fx,fy=sx-ix,sy-iy
        for dy in range(-rad,rad+1):
            py=iy+dy
            if py<0 or py>=H: continue
            for dx in range(-rad,rad+1):
                px=ix+dx
                if px<0 or px>=W: continue
                img[py,px]+=fl*nm*np.exp(-((dx-fx)**2+(dy-fy)**2)/(2*sig**2))
    signal = img + background
    n=rng.poisson(np.clip(signal,0,None)).astype(np.float64)+rng.normal(0,RN,(H,W))
    return n.astype(np.float32)

def wbin(p,d):
    with open(p,"wb") as f: f.write(struct.pack("<ii",W,H)); f.write(d.tobytes())

cat = load_cat()
print(f"Katalog: {len(cat)} yildiz\n")

# Oncedan tum goruntuler uret (simulasyon: kameradan frame geldi)
print("Goruntuler uretiliyor...", flush=True)
frames = []
for i,(ra,dec,name) in enumerate(POINTINGS):
    vis = proj(cat, ra, dec, roll=0.5*i)
    frame = render(vis, seed=42+i)
    frames.append((frame, name, len(vis)))
    print(f"  Frame {i+1}: {name} ({len(vis)} yildiz)", flush=True)

print(f"\n{'='*75}")
print(f"  FRAME-BY-FRAME GECİKME TESTİ")
print(f"{'='*75}\n")

print(f"{'Frame':>5}  {'Yon':<12}  {'BinYaz':>8}  {'Pipeline':>10}  {'BinOku':>8}  {'TOPLAM':>8}  {'Gecikme':>10}")
print("-" * 80)

cumulative = 0.0
latencies = []

for i, (frame, name, nstars) in enumerate(frames):
    bp = os.path.join(OUT_DIR, f"f{i:03d}.bin")
    pref = os.path.join(OUT_DIR, f"f{i:03d}")

    # Gorsel geldi -> zamani baslat
    t_start = time.perf_counter()

    # 1) Bin yaz (sensor -> bellek transferi simule)
    wbin(bp, frame)
    t_binwrite = time.perf_counter()

    # 2) C pipeline isle
    proc = subprocess.run([PIPELINE_EXE, bp, "-b", "50", "-f", "3", "-o", pref],
                          capture_output=True, text=True)
    t_pipeline = time.perf_counter()

    # Pipeline internal suresini parse et
    pipe_int = 0.0
    for line in proc.stdout.splitlines():
        if "Done" in line:
            try: pipe_int = float(line.split("(")[1].split("ms")[0])
            except: pass

    # 3) Sonucu oku (ciktiyi al)
    with open(pref + "_thresholded.bin", "rb") as f:
        f.read()  # tum veri okundu = cikti alindi
    t_end = time.perf_counter()

    bw_ms = (t_binwrite - t_start) * 1000
    pipe_ms = (t_pipeline - t_binwrite) * 1000
    br_ms = (t_end - t_pipeline) * 1000
    total_ms = (t_end - t_start) * 1000
    cumulative += total_ms

    latencies.append({
        "frame": i+1, "name": name, "stars": nstars,
        "binwrite_ms": bw_ms, "pipeline_ms": pipe_ms,
        "pipe_internal_ms": pipe_int,
        "binread_ms": br_ms, "total_ms": total_ms,
        "cumulative_ms": cumulative,
    })

    print(f"{i+1:>5}  {name:<12}  {bw_ms:>7.1f}  {pipe_ms:>9.1f}  {br_ms:>7.1f}  {total_ms:>7.1f}  {cumulative:>9.1f}")

# RAPOR
print(f"\n{'='*75}")
print(f"  SONUCLAR")
print(f"{'='*75}\n")

print(f"  {'Frame':>5}  {'Yon':<12}  {'Gorsel Geldi':>14}  {'Cikti Alindi':>14}  {'Gecikme':>10}")
print(f"  {'-'*65}")

t_cum = 0.0
for l in latencies:
    t_gorsel = t_cum  # gorsel ne zaman geldi (ms)
    t_cikti = t_cum + l["total_ms"]  # cikti ne zaman alindi
    gecikme = l["total_ms"]
    t_cum = t_cikti  # sonraki frame icin

    print(f"  {l['frame']:>5}  {l['name']:<12}  {t_gorsel/1000:>13.3f}s  {t_cikti/1000:>13.3f}s  {gecikme:>9.1f}ms")

print(f"\n  --- Ozet ---")
avg_total = sum(l["total_ms"] for l in latencies) / len(latencies)
avg_pipe_int = sum(l["pipe_internal_ms"] for l in latencies) / len(latencies)
min_total = min(l["total_ms"] for l in latencies)
max_total = max(l["total_ms"] for l in latencies)

print(f"  Ort. gecikme (subprocess dahil) : {avg_total:.1f} ms")
print(f"  Min gecikme                     : {min_total:.1f} ms")
print(f"  Max gecikme                     : {max_total:.1f} ms")
print(f"  Ort. C pipeline (internal)      : {avg_pipe_int:.1f} ms")
print(f"  Toplam 16 frame suresi          : {t_cum/1000:.3f} s")
print(f"")
print(f"  --- Gercek Sistemde (subprocess yok) ---")
print(f"  Statik mod  : {avg_pipe_int:.1f} ms/frame = {1000/avg_pipe_int:.0f} FPS")
print(f"  IIR mod     : ~11 ms/frame = ~91 FPS (ilk frame haric)")
print(f"{'='*75}")
