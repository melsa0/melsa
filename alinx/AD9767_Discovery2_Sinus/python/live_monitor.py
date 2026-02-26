"""
AD9767 DAC Output - Live Monitor & Logger
0.5 saniye arayla anlik olcum yapar, ekrana yazar ve CSV dosyasina kaydeder.
Ctrl+C ile durdurulur.
"""

from ctypes import *
import sys
import time
import numpy as np
from datetime import datetime

# Load DWF
dwf = cdll.dwf
hdwfNone = c_int(0)
DwfStateDone = c_ubyte(2)

SAMPLE_RATE = 10_000_000.0
BUFFER_SIZE = 8192
VOLTAGE_RANGE = 5.0
LOG_INTERVAL = 0.5  # saniye

# Open device
print("Analog Discovery 2 aciliyor...")
hdwf = c_int()
dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

if hdwf.value == hdwfNone.value:
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(f"Hata: {szerr.value.decode()}")
    sys.exit(1)

dwf.FDwfDeviceAutoConfigureSet(hdwf, c_int(0))

# Configure
dwf.FDwfAnalogInFrequencySet(hdwf, c_double(SAMPLE_RATE))
dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(BUFFER_SIZE))
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_int(1))
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(1), c_int(1))
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(VOLTAGE_RANGE))
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(1), c_double(VOLTAGE_RANGE))
dwf.FDwfAnalogInChannelFilterSet(hdwf, c_int(-1), c_int(0))
dwf.FDwfAnalogInConfigure(hdwf, c_int(1), c_int(0))

print("Offset stabilizasyonu bekleniyor...")
time.sleep(2)

# CSV log file
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_path = f"C:/Users/melsa/OneDrive/Desktop/dac_output_project/log_{timestamp}.csv"
csv_file = open(csv_path, 'w')
csv_file.write("Zaman,Saniye,CH1_Vpp_mV,CH1_Vrms_mV,CH1_DC_mV,CH1_Freq_kHz,CH1_THD_pct,CH2_Vpp_mV,CH2_Vrms_mV,CH2_DC_mV,CH2_Freq_kHz,CH2_THD_pct\n")

dt = 1.0 / SAMPLE_RATE
rgd1 = (c_double * BUFFER_SIZE)()
rgd2 = (c_double * BUFFER_SIZE)()


def measure_channel(data):
    dc = np.mean(data)
    vmin = np.min(data)
    vmax = np.max(data)
    vpp = vmax - vmin
    vrms = np.sqrt(np.mean((data - dc) ** 2))

    # Frequency
    centered = data - dc
    crossings = []
    for i in range(1, len(centered)):
        if centered[i - 1] < 0 and centered[i] >= 0:
            frac = -centered[i - 1] / (centered[i] - centered[i - 1])
            crossings.append(i - 1 + frac)
    freq = 0
    if len(crossings) >= 2:
        periods = np.diff(crossings) * dt
        freq = 1.0 / np.mean(periods)

    # THD
    fft_mag = np.abs(np.fft.rfft(centered))
    fund_idx = np.argmax(fft_mag[1:]) + 1
    fund_mag = fft_mag[fund_idx]
    freqs = np.fft.rfftfreq(BUFFER_SIZE, dt)
    fund_freq = freqs[fund_idx]
    harm_pow = 0
    for h in range(2, 6):
        hf = fund_freq * h
        if hf > freqs[-1]:
            break
        hi = np.argmin(np.abs(freqs - hf))
        harm_pow += fft_mag[hi] ** 2
    thd = np.sqrt(harm_pow) / fund_mag * 100 if fund_mag > 0 else 0

    return vpp, vrms, dc, freq, thd


print(f"\nLog dosyasi: {csv_path}")
print(f"Olcum araligi: {LOG_INTERVAL} s")
print("Ctrl+C ile durdurun.\n")

header = f"{'#':>4} | {'Zaman':>10} | {'CH1 Vpp':>10} {'CH1 Vrms':>10} {'CH1 DC':>9} {'CH1 Freq':>10} {'THD':>6} | {'CH2 Vpp':>10} {'CH2 Vrms':>10} {'CH2 DC':>9} {'CH2 Freq':>10} {'THD':>6}"
sep = "-" * len(header)
print(header)
print(sep)

start_time = time.time()
count = 0

try:
    while True:
        # Capture
        dwf.FDwfAnalogInConfigure(hdwf, c_int(0), c_int(1))
        for _ in range(100):
            sts = c_byte()
            dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
            if sts.value == DwfStateDone.value:
                break
            time.sleep(0.005)

        dwf.FDwfAnalogInStatusData(hdwf, 0, rgd1, BUFFER_SIZE)
        dwf.FDwfAnalogInStatusData(hdwf, 1, rgd2, BUFFER_SIZE)

        d1 = np.array(rgd1[:])
        d2 = np.array(rgd2[:])

        vpp1, vrms1, dc1, f1, thd1 = measure_channel(d1)
        vpp2, vrms2, dc2, f2, thd2 = measure_channel(d2)

        elapsed = time.time() - start_time
        now = datetime.now().strftime("%H:%M:%S")
        count += 1

        # Print
        line = (
            f"{count:4d} | {now:>10} | "
            f"{vpp1*1000:8.1f} mV {vrms1*1000:8.1f} mV {dc1*1000:7.1f} mV {f1/1000:8.2f} kHz {thd1:5.1f}% | "
            f"{vpp2*1000:8.1f} mV {vrms2*1000:8.1f} mV {dc2*1000:7.1f} mV {f2/1000:8.2f} kHz {thd2:5.1f}%"
        )
        print(line)

        # Log to CSV
        csv_file.write(f"{now},{elapsed:.1f},{vpp1*1000:.1f},{vrms1*1000:.1f},{dc1*1000:.1f},{f1/1000:.2f},{thd1:.2f},{vpp2*1000:.1f},{vrms2*1000:.1f},{dc2*1000:.1f},{f2/1000:.2f},{thd2:.2f}\n")
        csv_file.flush()

        # Reprint header every 20 lines
        if count % 20 == 0:
            print(sep)
            print(header)
            print(sep)

        time.sleep(LOG_INTERVAL)

except KeyboardInterrupt:
    print(f"\n\nDurduruldu. Toplam {count} olcum kaydedildi.")
    print(f"Log: {csv_path}")
finally:
    csv_file.close()
    dwf.FDwfDeviceCloseAll()
    print("Cihaz kapatildi.")
