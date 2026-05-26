#!/usr/bin/env python3
"""
CubeSat IMU Server — Mahony Filter Fusion
==========================================
Supports two hardware modes:

  arduino  (HIL — actual project hardware)
    Arduino Uno on USB serial at 115200 baud
    CSV: "ax ay az gx gy gz ldr0 ldr1 ldr2 ldr3\\n"
    Install: pip install pyserial

  esp32    (exhibition display only)
    ESP32 WiFi AP + TCP on 192.168.4.1:4210
    CSV: "ax ay az gx gy gz\\n"

Usage:
  python imu_server.py                        # arduino mode, auto COM3
  python imu_server.py --mode arduino --port COM3
  python imu_server.py --mode arduino --port /dev/ttyUSB0
  python imu_server.py --mode esp32

HTTP API:
  GET  /data              JSON: q, accel, gyro, ldr, lux, source, t
  GET  /reset             Reset quaternion to identity
  GET  /config            Current axis remapping config
  POST /config            Update axis order/sign (JSON body)
  GET  /imu_view.html     Three.js 3D visualizer

Mahony filter: Kp=2.0, Ki=0.005, 50 Hz
"""

import argparse, http.server, json, threading, time, math, socket, os, sys

# ── defaults ───────────────────────────────────────────────────────────────────
DEFAULT_MODE   = "arduino"
DEFAULT_PORT   = "COM3"
ESP32_IP       = "192.168.4.1"
ESP32_TCP_PORT = 4210
HTTP_PORT      = 8765

# ── quaternion math ────────────────────────────────────────────────────────────
def qmul(q, r):
    w0,x0,y0,z0 = q;  w1,x1,y1,z1 = r
    return [
        w0*w1 - x0*x1 - y0*y1 - z0*z1,
        w0*x1 + x0*w1 + y0*z1 - z0*y1,
        w0*y1 - x0*z1 + y0*w1 + z0*x1,
        w0*z1 + x0*y1 - y0*x1 + z0*w1,
    ]

def qnorm(q):
    n = math.sqrt(sum(v*v for v in q))
    return [v/n for v in q] if n > 1e-9 else [1.0, 0.0, 0.0, 0.0]

def gyro_to_dq(gx, gy, gz, dt):
    """Convert angular velocity vector to delta quaternion for dt seconds."""
    mag = math.sqrt(gx*gx + gy*gy + gz*gz)
    if mag < 1e-9:
        return [1.0, 0.0, 0.0, 0.0]
    half = 0.5 * mag * dt
    s = math.sin(half) / mag
    return [math.cos(half), gx*s, gy*s, gz*s]

# ── Mahony complementary filter ────────────────────────────────────────────────
#   Reference: Mahony et al., "Nonlinear Complementary Filters on the
#              Special Orthogonal Group", IEEE T-AC 2008.
#
#   Error term: e = cross(accel_measured_normalised, accel_estimated_from_q)
#   accel_estimated = lower row of rotation matrix = [2(xz-wy), 2(yz+wx), w²-x²-y²+z²]
#   Correction applied to gyro: gyro_corr = gyro + Kp*e + Ki*∫e·dt
#
KP = 2.0
KI = 0.005
_eInt      = [0.0, 0.0, 0.0]
_eInt_lock = threading.Lock()

def mahony_update(q, gx, gy, gz, ax, ay, az, dt):
    """One Mahony filter step. Returns normalised quaternion."""
    global _eInt
    anorm = math.sqrt(ax*ax + ay*ay + az*az)
    if anorm > 1e-6:
        ax /= anorm;  ay /= anorm;  az /= anorm
        w, x, y, z = q
        # Gravity estimate from current quaternion (3rd column of R^T)
        gx_est = 2.0*(x*z - w*y)
        gy_est = 2.0*(y*z + w*x)
        gz_est = w*w - x*x - y*y + z*z
        # Cross-product error
        ex = ay*gz_est - az*gy_est
        ey = az*gx_est - ax*gz_est
        ez = ax*gy_est - ay*gx_est
        with _eInt_lock:
            _eInt[0] += KI * ex * dt
            _eInt[1] += KI * ey * dt
            _eInt[2] += KI * ez * dt
            gx += KP*ex + _eInt[0]
            gy += KP*ey + _eInt[1]
            gz += KP*ez + _eInt[2]
    return qnorm(qmul(q, gyro_to_dq(gx, gy, gz, dt)))

def reset_filter():
    global _eInt
    with _eInt_lock:
        _eInt[:] = [0.0, 0.0, 0.0]

# ── Axis remapping (configurable at runtime) ───────────────────────────────────
#   order: which sensor axis maps to filter X/Y/Z  (0=X, 1=Y, 2=Z)
#   sign:  ±1 per filter axis
axis_cfg  = {"order": [0, 1, 2], "sign": [1, 1, 1]}
axis_lock = threading.Lock()

def apply_axis(ax, ay, az, gx, gy, gz):
    with axis_lock:
        o, s = list(axis_cfg["order"]), list(axis_cfg["sign"])
    sa = [ax, ay, az];  sg = [gx, gy, gz]
    return (s[0]*sa[o[0]], s[1]*sa[o[1]], s[2]*sa[o[2]],
            s[0]*sg[o[0]], s[1]*sg[o[1]], s[2]*sg[o[2]])

# ── Shared state (read by HTTP /data endpoint) ─────────────────────────────────
state = {
    "q":      [1.0, 0.0, 0.0, 0.0],   # quaternion [w, x, y, z]
    "ax": 0.0, "ay": 0.0, "az": 0.0,  # accel [g]
    "gx": 0.0, "gy": 0.0, "gz": 0.0,  # gyro  [rad/s]
    "ldr":    [0, 0, 0, 0],            # lux per LDR face [+X, -X, +Y, -Y]
    "lux":    0,                        # max face lux (dominant sun direction)
    "source": "waiting",               # "arduino:COM3" | "esp32:192.168.4.1" | "DEMO"
    "t":      0.0,                     # elapsed time [s]
}
lock = threading.Lock()

def gravity_in_body(q):
    """Return estimated gravity direction from quaternion (lower row of R^T)."""
    w, x, y, z = q
    return 2.0*(x*z - w*y), 2.0*(y*z + w*x), w*w - x*x - y*y + z*z

# ── DEMO mode — activates when no hardware is connected ────────────────────────
_demo_active = False

def demo_loop():
    t = 0.0
    while _demo_active:
        dt = 0.02
        gx = 0.30 * math.sin(t * 0.7)
        gy = 0.50 * math.cos(t * 0.4)
        gz = 0.20 * math.sin(t * 1.1)
        with lock:
            q = list(state["q"])
        new_q = mahony_update(q, gx, gy, gz, *gravity_in_body(q), dt)
        with lock:
            state["q"]  = new_q
            state["gx"], state["gy"], state["gz"] = gx, gy, gz
            state["ax"], state["ay"], state["az"] = gravity_in_body(new_q)
            state["ldr"] = [0, 0, 0, 0]
            state["lux"] = 0
            state["source"] = "DEMO"
            state["t"] = t
        t += dt
        time.sleep(dt)

def _start_demo():
    global _demo_active
    _demo_active = True
    threading.Thread(target=demo_loop, daemon=True).start()

def _stop_demo():
    global _demo_active
    _demo_active = False
    reset_filter()
    with lock:
        state["q"] = [1.0, 0.0, 0.0, 0.0]

# ── Shared update helper ───────────────────────────────────────────────────────
def _update_state(ax, ay, az, gx, gy, gz, ldr, source, prev_ref):
    now = time.monotonic()
    dt  = min(now - prev_ref[0], 0.1)
    prev_ref[0] = now

    ax, ay, az, gx, gy, gz = apply_axis(ax, ay, az, gx, gy, gz)
    with lock:
        q = list(state["q"])
    new_q = mahony_update(q, gx, gy, gz, ax, ay, az, dt)
    with lock:
        state["q"]  = new_q
        state["ax"], state["ay"], state["az"] = ax, ay, az
        state["gx"], state["gy"], state["gz"] = gx, gy, gz
        state["ldr"] = ldr
        state["lux"] = max(ldr)
        state["source"] = source
        state["t"] += dt

# ── Arduino Uno serial reader ──────────────────────────────────────────────────
def arduino_loop(port):
    """Read "ax ay az gx gy gz ldr0 ldr1 ldr2 ldr3\n" from Arduino Uno via USB serial."""
    try:
        import serial
    except ImportError:
        sys.exit("[IMU] ERROR: pyserial not installed. Run: pip install pyserial")

    demo_started = False
    prev = [time.monotonic()]

    while True:
        ser = None
        while ser is None:
            try:
                ser = serial.Serial(port, 115200, timeout=1)
                time.sleep(2.0)    # Arduino resets on connect — wait for boot
                ser.reset_input_buffer()
                print(f"[IMU] Arduino baglandi ({port} @ 115200)")
                if demo_started:
                    _stop_demo();  demo_started = False
            except Exception as e:
                if not demo_started:
                    print(f"[IMU] Arduino bulunamadi ({port}) — DEMO baslatiliyor")
                    _start_demo();  demo_started = True
                time.sleep(2)

        try:
            while True:
                raw = ser.readline()
                if not raw:
                    continue
                line = raw.decode("ascii", errors="ignore").strip()
                if line.startswith("#") or not line:
                    continue   # skip comment/header lines from Arduino
                parts = line.split()
                if len(parts) < 6:
                    continue
                try:
                    ax, ay, az = float(parts[0]), float(parts[1]), float(parts[2])
                    gx, gy, gz = float(parts[3]), float(parts[4]), float(parts[5])
                    ldr = [int(parts[i]) if i < len(parts) else 0 for i in range(6, 10)]
                except ValueError:
                    continue
                _update_state(ax, ay, az, gx, gy, gz, ldr, f"arduino:{port}", prev)

        except Exception as e:
            print(f"[IMU] Seri baglanti koptu: {e}")
        finally:
            try:
                ser.close()
            except Exception:
                pass
        time.sleep(1)

# ── ESP32 TCP reader ───────────────────────────────────────────────────────────
def esp32_loop():
    """Read "ax ay az gx gy gz\n" from ESP32 WiFi AP via TCP."""
    demo_started = False
    prev = [time.monotonic()]

    while True:
        sock = None
        while sock is None:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((ESP32_IP, ESP32_TCP_PORT))
                sock.settimeout(1)
                print(f"[IMU] ESP32 baglandi ({ESP32_IP}:{ESP32_TCP_PORT})")
                if demo_started:
                    _stop_demo();  demo_started = False
            except Exception:
                sock = None
                if not demo_started:
                    print(f"[IMU] ESP32 bulunamadi — DEMO baslatiliyor")
                    _start_demo();  demo_started = True
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
                    _update_state(ax, ay, az, gx, gy, gz, [0,0,0,0],
                                  f"esp32:{ESP32_IP}", prev)
        except Exception as e:
            print(f"[IMU] TCP baglanti koptu: {e}")
        finally:
            try:
                sock.close()
            except Exception:
                pass
        time.sleep(1)

# ── HTTP handler ───────────────────────────────────────────────────────────────
class Handler(http.server.SimpleHTTPRequestHandler):

    def _send_json(self, payload, code=200):
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/data":
            with lock:
                self._send_json(dict(state))
        elif self.path == "/config":
            with axis_lock:
                self._send_json(dict(axis_cfg))
        elif self.path == "/reset":
            reset_filter()
            with lock:
                state["q"] = [1.0, 0.0, 0.0, 0.0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/config":
            n = int(self.headers.get("Content-Length", 0))
            try:
                data = json.loads(self.rfile.read(n))
                with axis_lock:
                    if "order" in data:
                        axis_cfg["order"] = [int(v) for v in data["order"]]
                    if "sign" in data:
                        axis_cfg["sign"]  = [int(v) for v in data["sign"]]
                reset_filter()
                with lock:
                    state["q"] = [1.0, 0.0, 0.0, 0.0]
                with axis_lock:
                    self._send_json(dict(axis_cfg))
                print(f"[CFG] order={axis_cfg['order']} sign={axis_cfg['sign']}")
            except Exception:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        msg = str(args[0]) if args else ""
        if "/data" not in msg and "favicon" not in msg:
            super().log_message(fmt, *args)

# ── entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CubeSat IMU HTTP Server")
    parser.add_argument("--mode", choices=["arduino", "esp32"], default=DEFAULT_MODE,
                        help="Hardware source (default: arduino)")
    parser.add_argument("--port", default=DEFAULT_PORT,
                        help="Serial port for arduino mode, e.g. COM3 or /dev/ttyUSB0")
    args = parser.parse_args()

    if args.mode == "arduino":
        reader = threading.Thread(target=arduino_loop, args=(args.port,), daemon=True)
        src_desc = f"Arduino Uno on {args.port} @ 115200 baud"
    else:
        reader = threading.Thread(target=esp32_loop, daemon=True)
        src_desc = f"ESP32 TCP {ESP32_IP}:{ESP32_TCP_PORT}"

    reader.start()

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    srv = http.server.HTTPServer(("0.0.0.0", HTTP_PORT), Handler)

    print(f"\n{'='*56}")
    print(f"  CubeSat IMU Server")
    print(f"  Mode    : {args.mode.upper()} ({src_desc})")
    print(f"  Filter  : Mahony Kp={KP} Ki={KI} @ 50 Hz")
    print(f"  HTTP    : http://localhost:{HTTP_PORT}/imu_view.html")
    print(f"  API     : http://localhost:{HTTP_PORT}/data")
    print(f"{'='*56}\n")

    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nDurduruldu.")
