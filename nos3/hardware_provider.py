#!/usr/bin/env python3
"""
NOS3 HIL Hardware Provider — CubeSat IMU/CSS Bridge
=====================================================
Bridges imu_server.py HTTP API to NOS3 (NASA Operational Simulator for
Small Satellites) hardware provider UDP interface.

Data flow:
  Arduino Uno → imu_server.py (HTTP :8765) → this script → NOS3 UDP → cFS apps

NOS3 apps receiving data:
  GENERIC_IMU   — accel + gyro (→ attitude determination)
  GENERIC_CSS   — coarse sun sensor / LDR irradiance (→ sun pointing)

UDP packet formats (big-endian doubles):
  GENERIC_IMU  : double[6] = ax, ay, az [m/s²],  gx, gy, gz [rad/s]  (48 bytes)
  GENERIC_CSS  : double[4] = face0, face1, face2, face3 [0.0–1.0]    (32 bytes)

CCSDS packet structure (assembled by cFS, not here):
  Primary header   :  6 bytes  (APID 0x0C80, seq flags 0xC0, seq count, data length)
  Secondary header : 10 bytes  (MET seconds 4B, MET subseconds 2B, pad 4B)
  Payload          : sensor data

Usage:
  python nos3/hardware_provider.py
  python nos3/hardware_provider.py --imu-server http://localhost:8765
  python nos3/hardware_provider.py --imu-port 5013 --css-port 5020

Requirements:
  pip install requests

Phases:
  SIL (Software-in-the-Loop): NOS3 generates synthetic IMU data internally.
                               This script NOT needed for SIL.
  HIL (Hardware-in-the-Loop): This script reads from real Arduino via
                               imu_server.py and forwards to NOS3.
"""

import argparse, struct, socket, time, sys

try:
    import requests
except ImportError:
    sys.exit("[NOS3] ERROR: requests not installed. Run: pip install requests")

# ── NOS3 defaults ──────────────────────────────────────────────────────────────
NOS3_HOST     = "127.0.0.1"
NOS3_IMU_PORT = 5013    # GENERIC_IMU hardware provider UDP port
NOS3_CSS_PORT = 5020    # GENERIC_CSS (coarse sun sensor) hardware provider UDP port

# ── Constants ──────────────────────────────────────────────────────────────────
G_TO_MS2 = 9.80665          # 1 g → m/s²
MAX_LUX  = 2000.0           # lux normalization ceiling (bright indoor/sim sun)
POLL_HZ  = 50               # target update rate — matches Arduino 50 Hz output

def pack_imu(ax_g, ay_g, az_g, gx, gy, gz):
    """
    Pack IMU data for NOS3 GENERIC_IMU hardware provider.
    Returns 48-byte big-endian struct of 6 doubles.
      [ax, ay, az] in m/s²  (converted from g)
      [gx, gy, gz] in rad/s
    """
    return struct.pack(">6d",
        ax_g * G_TO_MS2,
        ay_g * G_TO_MS2,
        az_g * G_TO_MS2,
        gx, gy, gz,
    )

def pack_css(ldr_lux_list):
    """
    Pack sun sensor data for NOS3 GENERIC_CSS hardware provider.
    Returns 32-byte big-endian struct of 4 doubles.
    Each value is normalised irradiance: 0.0 (dark) → 1.0 (full sun).
    LDR face mapping: [0]=+X, [1]=-X, [2]=+Y, [3]=-Y
    """
    faces = [min(1.0, max(0.0, lux / MAX_LUX)) for lux in ldr_lux_list]
    return struct.pack(">4d", *faces)

def run(imu_server_url: str, imu_port: int, css_port: int):
    imu_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    css_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    session  = requests.Session()

    dt         = 1.0 / POLL_HZ
    fail_count = 0
    pkt_count  = 0

    print(f"[NOS3 Bridge] Polling {imu_server_url}/data @ {POLL_HZ} Hz")
    print(f"[NOS3 Bridge] IMU  → UDP {NOS3_HOST}:{imu_port}  (GENERIC_IMU)")
    print(f"[NOS3 Bridge] CSS  → UDP {NOS3_HOST}:{css_port}  (GENERIC_CSS)")
    print(f"[NOS3 Bridge] Accel scale: 1 g = {G_TO_MS2} m/s²")
    print(f"[NOS3 Bridge] CSS  scale:  {MAX_LUX} lux = 1.0 (full sun)\n")

    while True:
        t0 = time.monotonic()
        try:
            r = session.get(f"{imu_server_url}/data", timeout=0.5)
            d = r.json()

            ax  = d.get("ax",  0.0)
            ay  = d.get("ay",  0.0)
            az  = d.get("az",  0.0)
            gx  = d.get("gx",  0.0)
            gy  = d.get("gy",  0.0)
            gz  = d.get("gz",  0.0)
            ldr = d.get("ldr", [0, 0, 0, 0])

            imu_pkt = pack_imu(ax, ay, az, gx, gy, gz)
            css_pkt = pack_css(ldr)

            imu_sock.sendto(imu_pkt, (NOS3_HOST, imu_port))
            css_sock.sendto(css_pkt, (NOS3_HOST, css_port))

            pkt_count += 1
            fail_count = 0

            if pkt_count % 500 == 0:   # status every 10 s
                src = d.get("source", "?")
                q   = d.get("q", [1,0,0,0])
                print(f"[NOS3 Bridge] #{pkt_count}  src={src}  "
                      f"q=[{q[0]:.3f},{q[1]:.3f},{q[2]:.3f},{q[3]:.3f}]  "
                      f"lux_max={max(ldr)}")

        except Exception as e:
            fail_count += 1
            if fail_count == 1:
                print(f"[NOS3 Bridge] WARN: {e}")
            if fail_count > 50:
                print(f"[NOS3 Bridge] ERROR: imu_server.py unreachable — is it running?")
                fail_count = 0

        elapsed = time.monotonic() - t0
        time.sleep(max(0.0, dt - elapsed))

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="NOS3 HIL hardware provider bridge")
    p.add_argument("--imu-server", default="http://localhost:8765",
                   help="imu_server.py base URL")
    p.add_argument("--imu-port",   type=int, default=NOS3_IMU_PORT,
                   help=f"UDP port for GENERIC_IMU (default {NOS3_IMU_PORT})")
    p.add_argument("--css-port",   type=int, default=NOS3_CSS_PORT,
                   help=f"UDP port for GENERIC_CSS (default {NOS3_CSS_PORT})")
    args = p.parse_args()
    run(args.imu_server, args.imu_port, args.css_port)
