#!/usr/bin/env python3
"""
IMU HTTP + Serial Server — Mahony Filter fusion (gyro + accel)
- Reads from ESP32 on COM5 at 115200 baud
- Format: "ax ay az gx gy gz\n"  (accel in g, gyro in rad/s)
- Mahony filter fuses both → drift-free quaternion
- Serves JSON at http://localhost:8765/data
- View at  http://localhost:8765/imu_view.html
"""

import http.server, json, threading, time, math, socket, os, sys

ESP32_IP   = "192.168.4.1"
ESP32_PORT = 4210

# ── quaternion math ──────────────────────────────────────────────────────────
def qmul(q, r):
    w0,x0,y0,z0 = q;  w1,x1,y1,z1 = r
    return [
        w0*w1 - x0*x1 - y0*y1 - z0*z1,
        w0*x1 + x0*w1 + y0*z1 - z0*y1,
        w0*y1 - x0*z1 + y0*w1 + z0*x1,
        w0*z1 + x0*y1 - y0*x1 + z0*w1,
    ]

def qnorm(q):
    n = math.sqrt(sum(x*x for x in q))
    return [x/n for x in q] if n > 1e-9 else [1,0,0,0]

def gyro_to_dq(gx, gy, gz, dt):
    mag = math.sqrt(gx*gx + gy*gy + gz*gz)
    if mag < 1e-9:
        return [1, 0, 0, 0]
    half = 0.5 * mag * dt
    s = math.sin(half) / mag
    return [math.cos(half), gx*s, gy*s, gz*s]

# ── Mahony filter ────────────────────────────────────────────────────────────
Kp = 2.0
Ki = 0.005
_eInt = [0.0, 0.0, 0.0]

def mahony_update(q, gx, gy, gz, ax, ay, az, dt):
    global _eInt
    anorm = math.sqrt(ax*ax + ay*ay + az*az)
    if anorm > 1e-6:
        ax /= anorm;  ay /= anorm;  az /= anorm
        w, x, y, z = q
        gx_est = 2*(x*z - w*y)
        gy_est = 2*(y*z + w*x)
        gz_est = w*w - x*x - y*y + z*z
        ex = ay*gz_est - az*gy_est
        ey = az*gx_est - ax*gz_est
        ez = ax*gy_est - ay*gx_est
        _eInt[0] += Ki * ex * dt
        _eInt[1] += Ki * ey * dt
        _eInt[2] += Ki * ez * dt
        gx += Kp*ex + _eInt[0]
        gy += Kp*ey + _eInt[1]
        gz += Kp*ez + _eInt[2]
    return qnorm(qmul(q, gyro_to_dq(gx, gy, gz, dt)))

# ── Axis config (canlı ayarlanabilir) ────────────────────────────────────────
# order: hangi sensör ekseni filtre X/Y/Z'sine gidiyor  [0=X,1=Y,2=Z]
# sign:  her filtre ekseninin işareti  +1 veya -1
axis_cfg = {
    "order": [0, 1, 2],
    "sign":  [1, 1, 1],
}
axis_lock = threading.Lock()

def apply_axis_cfg(ax, ay, az, gx, gy, gz):
    with axis_lock:
        o = list(axis_cfg["order"])
        s = list(axis_cfg["sign"])
    src_a = [ax, ay, az];  src_g = [gx, gy, gz]
    return (
        s[0]*src_a[o[0]], s[1]*src_a[o[1]], s[2]*src_a[o[2]],
        s[0]*src_g[o[0]], s[1]*src_g[o[1]], s[2]*src_g[o[2]],
    )

# ── shared state ─────────────────────────────────────────────────────────────
state = {
    "q": [1, 0, 0, 0],
    "gx": 0.0, "gy": 0.0, "gz": 0.0,
    "ax": 0.0, "ay": 0.0, "az": 0.0,
    "source": "waiting",
    "t": 0.0,
}
lock = threading.Lock()

# ── demo fallback ─────────────────────────────────────────────────────────────
_demo_active = False

def gravity_in_body(q):
    w, x, y, z = q
    return (2*(x*z - w*y), 2*(y*z + w*x), w*w - x*x - y*y + z*z)

def demo_loop():
    t = 0
    while _demo_active:
        dt = 0.02
        gx = 0.3 * math.sin(t * 0.7)
        gy = 0.5 * math.cos(t * 0.4)
        gz = 0.2 * math.sin(t * 1.1)
        with lock:
            q = list(state["q"])
        new_q = mahony_update(q, gx, gy, gz, *gravity_in_body(q), dt)
        ax_s, ay_s, az_s = gravity_in_body(new_q)
        with lock:
            state["q"] = new_q
            state["gx"], state["gy"], state["gz"] = gx, gy, gz
            state["ax"], state["ay"], state["az"] = ax_s, ay_s, az_s
            state["source"] = "DEMO"
            state["t"] = t
        t += dt
        time.sleep(dt)

# ── TCP client (ESP32 AP modda sunucu) ───────────────────────────────────────
def serial_loop():
    global _demo_active, _eInt
    demo_started = False
    last_packet  = 0.0
    prev         = time.monotonic()

    while True:
        sock = None
        while sock is None:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((ESP32_IP, ESP32_PORT))
                sock.settimeout(1)
                print(f"[IMU] ESP32'ye bağlandı ({ESP32_IP}:{ESP32_PORT})")
                if demo_started:
                    _demo_active = False
                    demo_started = False
                    _eInt = [0.0, 0.0, 0.0]
            except Exception as e:
                sock = None
                if not demo_started:
                    print(f"[IMU] ESP32 bulunamadı — DEMO başlatılıyor")
                    _demo_active = True
                    threading.Thread(target=demo_loop, daemon=True).start()
                    demo_started = True
                time.sleep(2)

        buf = b""
        try:
            while True:
                try:
                    chunk = sock.recv(256)
                    if not chunk:
                        break
                    buf += chunk
                except socket.timeout:
                    continue

                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    parts = line.decode("ascii", errors="ignore").strip().split()
                    if len(parts) != 6:
                        continue
                    try:
                        ax, ay, az = float(parts[0]), float(parts[1]), float(parts[2])
                        gx, gy, gz = float(parts[3]), float(parts[4]), float(parts[5])
                    except ValueError:
                        continue

                    last_packet = time.monotonic()
                    now = time.monotonic()
                    dt  = min(now - prev, 0.1)
                    prev = now

                    ax, ay, az, gx, gy, gz = apply_axis_cfg(ax, ay, az, gx, gy, gz)

                    with lock:
                        q = list(state["q"])
                    new_q = mahony_update(q, gx, gy, gz, ax, ay, az, dt)
                    with lock:
                        state["q"] = new_q
                        state["gx"], state["gy"], state["gz"] = gx, gy, gz
                        state["ax"], state["ay"], state["az"] = ax, ay, az
                        state["source"] = f"esp32:{ESP32_IP}"
                        state["t"] += dt

        except Exception as e:
            print(f"[IMU] Bağlantı kesildi: {e}")
        finally:
            try: sock.close()
            except: pass
        time.sleep(1)

# ── HTTP server ───────────────────────────────────────────────────────────────
class Handler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path == "/config":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                with axis_lock:
                    if "order" in data:
                        axis_cfg["order"] = [int(x) for x in data["order"]]
                    if "sign" in data:
                        axis_cfg["sign"]  = [int(x) for x in data["sign"]]
                global _eInt
                _eInt = [0.0, 0.0, 0.0]
                with lock:
                    state["q"] = [1, 0, 0, 0]
                payload = json.dumps(axis_cfg).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(payload)
                print(f"[CFG] order={axis_cfg['order']} sign={axis_cfg['sign']}")
            except Exception as e:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == "/config":
            with axis_lock:
                payload = json.dumps(axis_cfg).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(payload)
        elif self.path == "/data":
            with lock:
                payload = json.dumps(state).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", len(payload))
            self.end_headers()
            self.wfile.write(payload)
        elif self.path == "/reset":
            global _eInt
            _eInt = [0.0, 0.0, 0.0]
            with lock:
                state["q"] = [1, 0, 0, 0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            super().do_GET()

    def log_message(self, fmt, *args):
        msg = str(args[0]) if args else ""
        if "/data" not in msg and "favicon" not in msg:
            super().log_message(fmt, *args)

if __name__ == "__main__":
    HTTP_PORT = 8765
    threading.Thread(target=serial_loop, daemon=True).start()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = http.server.HTTPServer(("0.0.0.0", HTTP_PORT), Handler)

    print(f"\n{'='*52}")
    print(f"  IMU Visualizer — Mahony Filter (gyro + accel)")
    print(f"  TCP     {ESP32_IP}:{ESP32_PORT}  ← ESP32 AP")
    print(f"  HTTP    {HTTP_PORT}  → http://localhost:{HTTP_PORT}/imu_view.html")
    print(f"{'='*52}\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
