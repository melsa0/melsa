#!/usr/bin/env python3
"""
IMU HTTP + UDP Server — Mahony Filter fusion (gyro + accel)
- Listens for UDP packets from ESP32 on port 4210
- Format: "ax ay az gx gy gz\n"  (accel in g, gyro in rad/s)
- Mahony filter fuses both → drift-free quaternion
- Serves JSON at http://0.0.0.0:8765/data
"""

import http.server, json, threading, time, math, socket, os

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
# Gains: Kp=2.0 (stiff correction), Ki=0.005 (slow integral wind-up)
Kp = 2.0
Ki = 0.005
_eInt = [0.0, 0.0, 0.0]   # integral error accumulator

def mahony_update(q, gx, gy, gz, ax, ay, az, dt):
    """
    Fuses gyro (rad/s) + accel (any unit, gets normalized) → new quaternion.
    If accel norm is near zero (free-fall or missing) → gyro-only fallback.
    """
    global _eInt

    # Normalize accelerometer
    anorm = math.sqrt(ax*ax + ay*ay + az*az)
    if anorm > 1e-6:
        ax /= anorm;  ay /= anorm;  az /= anorm

        # Estimated gravity direction in body frame from current quaternion
        # (rotate world +Z=[0,0,1] into body frame via q*)
        w, x, y, z = q
        gx_est = 2*(x*z - w*y)
        gy_est = 2*(y*z + w*x)
        gz_est = w*w - x*x - y*y + z*z

        # Error = cross(accel_meas, accel_estimated)
        ex = ay*gz_est - az*gy_est
        ey = az*gx_est - ax*gz_est
        ez = ax*gy_est - ay*gx_est

        # Integral anti-drift
        _eInt[0] += Ki * ex * dt
        _eInt[1] += Ki * ey * dt
        _eInt[2] += Ki * ez * dt

        # Correct gyro with PI feedback
        gx += Kp*ex + _eInt[0]
        gy += Kp*ey + _eInt[1]
        gz += Kp*ez + _eInt[2]

    return qnorm(qmul(q, gyro_to_dq(gx, gy, gz, dt)))

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

def demo_loop():
    """Simulates gyro motion + matching accel (gravity rotated into body frame)."""
    t = 0
    while _demo_active:
        dt = 0.02
        gx = 0.3 * math.sin(t * 0.7)
        gy = 0.5 * math.cos(t * 0.4)
        gz = 0.2 * math.sin(t * 1.1)

        with lock:
            q = list(state["q"])

        new_q = mahony_update(q, gx, gy, gz,
                              *gravity_in_body(q),   # simulated accel
                              dt)

        # Simulate accel = gravity in body frame (no linear accel in demo)
        ax_s, ay_s, az_s = gravity_in_body(new_q)

        with lock:
            state["q"] = new_q
            state["gx"], state["gy"], state["gz"] = gx, gy, gz
            state["ax"], state["ay"], state["az"] = ax_s, ay_s, az_s
            state["source"] = "DEMO"
            state["t"] = t
        t += dt
        time.sleep(dt)

def gravity_in_body(q):
    """Returns the gravity unit vector expressed in body frame for quaternion q."""
    w, x, y, z = q
    return (
        2*(x*z - w*y),
        2*(y*z + w*x),
        w*w - x*x - y*y + z*z,
    )

# ── UDP listener ──────────────────────────────────────────────────────────────
UDP_PORT = 4210

def udp_loop():
    global _demo_active
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", UDP_PORT))
    sock.settimeout(1.0)
    print(f"[IMU] UDP listening on port {UDP_PORT}")

    prev = time.monotonic()
    last_packet = 0.0
    demo_started = False

    while True:
        if time.monotonic() - last_packet > 3.0 and not demo_started:
            print("[IMU] No UDP data — running DEMO animation")
            _demo_active = True
            threading.Thread(target=demo_loop, daemon=True).start()
            demo_started = True

        try:
            data, addr = sock.recvfrom(256)
        except socket.timeout:
            continue

        if demo_started:
            _demo_active = False
            demo_started = False
            # Reset integral on reconnect
            global _eInt
            _eInt = [0.0, 0.0, 0.0]
            print(f"[IMU] ESP32 connected from {addr[0]}")

        last_packet = time.monotonic()

        try:
            parts = data.decode().strip().split()
            if len(parts) < 6:
                continue
            ax, ay, az = float(parts[0]), float(parts[1]), float(parts[2])
            gx, gy, gz = float(parts[3]), float(parts[4]), float(parts[5])
        except Exception:
            continue

        now = time.monotonic()
        dt  = min(now - prev, 0.1)
        prev = now

        with lock:
            q = list(state["q"])

        new_q = mahony_update(q, gx, gy, gz, ax, ay, az, dt)

        with lock:
            state["q"] = new_q
            state["gx"], state["gy"], state["gz"] = gx, gy, gz
            state["ax"], state["ay"], state["az"] = ax, ay, az
            state["source"] = f"esp32:{addr[0]}"
            state["t"] += dt

# ── HTTP server ───────────────────────────────────────────────────────────────
class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/data":
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
        if "/data" not in args[0]:
            super().log_message(fmt, *args)

if __name__ == "__main__":
    HTTP_PORT = 8765
    threading.Thread(target=udp_loop, daemon=True).start()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = http.server.HTTPServer(("0.0.0.0", HTTP_PORT), Handler)
    host_ip = socket.gethostbyname(socket.gethostname())

    print(f"\n{'='*52}")
    print(f"  IMU Visualizer — Mahony Filter (gyro + accel)")
    print(f"  UDP {UDP_PORT}   ← ESP32 sends 'ax ay az gx gy gz'")
    print(f"  HTTP {HTTP_PORT}  → http://localhost:{HTTP_PORT}/imu_view.html")
    print(f"  WSL IP: {host_ip}")
    print(f"{'='*52}\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
