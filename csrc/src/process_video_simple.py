"""
16 frame uret, C pipeline isle, H264 video cikart.
"""
import numpy as np, struct, subprocess, os, time, csv, cv2, sys
import imageio.v3 as iio

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PIPELINE_EXE = os.path.join(SCRIPT_DIR, "pipeline.exe")
OUT_DIR = os.path.join(SCRIPT_DIR, "processed_frames")
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
    sig2=img+background
    n=rng.poisson(np.clip(sig2,0,None)).astype(np.float64)+rng.normal(0,RN,(H,W))
    return n.astype(np.float32)

def wbin(p,d):
    with open(p,"wb") as f: f.write(struct.pack("<ii",W,H)); f.write(d.tobytes())
def rbin(p):
    with open(p,"rb") as f: w,h=struct.unpack("<ii",f.read(8)); return np.frombuffer(f.read(),np.float32).reshape(h,w)
def disp(d,lo=1,hi=99.5,log=False):
    d2=np.log1p(np.maximum(d,0)) if log else d.copy()
    p1,p99=np.percentile(d2,lo),np.percentile(d2,hi)
    if p99<=p1: p99=p1+1
    return np.clip((d2-p1)/(p99-p1)*255,0,255).astype(np.uint8)

print("Katalog...", flush=True)
cat = load_cat()
print(f"  {len(cat)} yildiz", flush=True)

frames_rgb = []
results = []

print(f"\n{'#':>3} {'Yon':<12} {'Star':>5} {'Pipe':>6} {'Thresh':>7} {'Pix':>6}", flush=True)
print("-"*50, flush=True)

for i,(ra,dec,name) in enumerate(POINTINGS):
    sys.stdout.flush()
    vis = proj(cat, ra, dec, roll=0.5*i)
    frame = render(vis, seed=42+i)

    bp = os.path.join(OUT_DIR, f"f{i:03d}.bin")
    wbin(bp, frame)

    pref = os.path.join(OUT_DIR, f"f{i:03d}")
    t0 = time.perf_counter()
    pr = subprocess.run([PIPELINE_EXE,bp,"-b","50","-f","3","-o",pref], capture_output=True, text=True)
    pipe_ms = (time.perf_counter()-t0)*1000

    th=0; npx=0
    for l in pr.stdout.splitlines():
        if "3-sigma" in l:
            try: th=float(l.split(":")[1].strip().split()[0])
            except: pass
        if "pixels above" in l:
            try: npx=int(l.split("(")[1].split(" ")[0])
            except: pass

    sub=rbin(pref+"_subtracted.bin"); thr=rbin(pref+"_thresholded.bin")

    r_d=cv2.cvtColor(disp(frame,log=True),cv2.COLOR_GRAY2BGR)
    s_d=cv2.cvtColor(disp(sub,log=True),cv2.COLOR_GRAY2BGR)
    t_d=cv2.cvtColor(disp(thr,lo=0,hi=99.5),cv2.COLOR_GRAY2BGR)

    ft=cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(r_d,f"HAM - {name}",(20,60),ft,1.5,(0,255,255),3)
    cv2.putText(s_d,"SUBTRACTED",(20,60),ft,1.5,(0,255,0),3)
    cv2.putText(t_d,f"THRESHOLDED ({npx}px)",(20,60),ft,1.2,(0,100,255),3)
    cv2.putText(r_d,f"RA={ra} Dec={dec} Stars={len(vis)} Pipe={pipe_ms:.0f}ms",(20,H-30),ft,0.7,(200,200,200),1)

    comb = cv2.cvtColor(np.hstack([r_d,s_d,t_d]), cv2.COLOR_BGR2RGB)
    frames_rgb.append(comb)
    results.append({"name":name,"stars":len(vis),"pipe_ms":pipe_ms,"thresh":th,"pix":npx})
    print(f"{i+1:>3} {name:<12} {len(vis):>5} {pipe_ms:>5.0f} {th:>7.1f} {npx:>6}", flush=True)

# Video yaz (imageio + ffmpeg H264)
out_path = os.path.join(SCRIPT_DIR, "pipeline_processed.mp4")
print(f"\nVideo yaziliyor: {out_path}", flush=True)
import av
container = av.open(out_path, mode='w')
stream = container.add_stream('h264', rate=30)
stream.width = W * 3
stream.height = H
stream.pix_fmt = 'yuv420p'
# Her frame'i 15 kez tekrarla (30fps'te 0.5sn goruntulenir = toplam 8sn)
REPEAT = 15
for rgb_frame in frames_rgb:
    vf = av.VideoFrame.from_ndarray(rgb_frame, format='rgb24')
    for _ in range(REPEAT):
        for packet in stream.encode(vf):
            container.mux(packet)
for packet in stream.encode():
    container.mux(packet)
container.close()
total_frames = len(frames_rgb) * REPEAT
print(f"  {total_frames} frame ({len(frames_rgb)}x{REPEAT}), {total_frames/30:.1f} saniye")

avg_pipe = sum(r["pipe_ms"] for r in results)/len(results)
avg_pix = sum(r["pix"] for r in results)/len(results)
print(f"\n{'='*50}")
print(f"  Pipeline ort: {avg_pipe:.0f} ms ({1000/avg_pipe:.0f} FPS subprocess)")
print(f"  Threshold   : {results[0]['thresh']:.1f} ADU")
print(f"  Piksel ort  : {avg_pix:.0f}")
print(f"  Video       : {out_path}")
print(f"{'='*50}")
