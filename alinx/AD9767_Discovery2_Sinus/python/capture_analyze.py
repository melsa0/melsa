"""
AD9767 DAC Output - Capture and Analyze
Captures waveform data and saves analysis + screenshot
"""

from ctypes import *
import sys
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Load DWF library
dwf = cdll.dwf

# Constants
hdwfNone = c_int(0)
DwfStateDone = c_ubyte(2)
filterDecimate = c_int(0)

SAMPLE_RATE = 10_000_000.0
BUFFER_SIZE = 8192
VOLTAGE_RANGE = 5.0

# Open device
print("Opening Analog Discovery 2...")
hdwf = c_int()
dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

if hdwf.value == hdwfNone.value:
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(f"Error: {szerr.value.decode()}")
    sys.exit(1)

print("Device opened.")
dwf.FDwfDeviceAutoConfigureSet(hdwf, c_int(0))

# Configure oscilloscope
dwf.FDwfAnalogInFrequencySet(hdwf, c_double(SAMPLE_RATE))
dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(BUFFER_SIZE))
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_int(1))
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(1), c_int(1))
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(VOLTAGE_RANGE))
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(1), c_double(VOLTAGE_RANGE))
dwf.FDwfAnalogInChannelFilterSet(hdwf, c_int(-1), filterDecimate)

# Trigger on CH1 rising edge at 0V
dwf.FDwfAnalogInTriggerSourceSet(hdwf, c_ubyte(2))
dwf.FDwfAnalogInTriggerChannelSet(hdwf, c_int(0))
dwf.FDwfAnalogInTriggerTypeSet(hdwf, c_int(0))
dwf.FDwfAnalogInTriggerConditionSet(hdwf, c_int(0))
dwf.FDwfAnalogInTriggerLevelSet(hdwf, c_double(0.0))
dwf.FDwfAnalogInTriggerAutoTimeoutSet(hdwf, c_double(1.0))

dwf.FDwfAnalogInConfigure(hdwf, c_int(1), c_int(0))
time.sleep(2)

# Capture
print("Capturing...")
dwf.FDwfAnalogInConfigure(hdwf, c_int(0), c_int(1))

for i in range(100):
    sts = c_byte()
    dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
    if sts.value == DwfStateDone.value:
        break
    time.sleep(0.01)

rgdSamples1 = (c_double * BUFFER_SIZE)()
rgdSamples2 = (c_double * BUFFER_SIZE)()
dwf.FDwfAnalogInStatusData(hdwf, 0, rgdSamples1, BUFFER_SIZE)
dwf.FDwfAnalogInStatusData(hdwf, 1, rgdSamples2, BUFFER_SIZE)
dwf.FDwfDeviceCloseAll()

data1 = np.array(rgdSamples1[:])
data2 = np.array(rgdSamples2[:])

# =========================================================================
# Analysis
# =========================================================================
dt = 1.0 / SAMPLE_RATE
time_us = np.arange(BUFFER_SIZE) * dt * 1e6

print("\n" + "="*60)
print("  AD9767 DAC OUTPUT ANALYSIS")
print("="*60)

for ch_idx, (data, name) in enumerate([(data1, "CH1"), (data2, "CH2")]):
    dc = np.mean(data)
    vmin = np.min(data)
    vmax = np.max(data)
    vpp = vmax - vmin
    vrms = np.sqrt(np.mean((data - dc)**2))

    # Frequency estimation via zero crossings
    centered = data - dc
    crossings = []
    for i in range(1, len(centered)):
        if centered[i-1] < 0 and centered[i] >= 0:
            # Linear interpolation for better accuracy
            frac = -centered[i-1] / (centered[i] - centered[i-1])
            crossings.append(i - 1 + frac)

    freq = 0
    period = 0
    if len(crossings) >= 2:
        periods = np.diff(crossings) * dt
        period = np.mean(periods)
        freq = 1.0 / period

    # THD estimation via FFT
    fft_data = np.fft.rfft(data - dc)
    fft_mag = np.abs(fft_data)
    freqs = np.fft.rfftfreq(BUFFER_SIZE, dt)

    # Find fundamental
    fund_idx = np.argmax(fft_mag[1:]) + 1
    fund_freq = freqs[fund_idx]
    fund_mag = fft_mag[fund_idx]

    # Find harmonics (2nd to 5th)
    harmonic_power = 0
    harmonics_info = []
    for h in range(2, 6):
        h_freq = fund_freq * h
        if h_freq > freqs[-1]:
            break
        h_idx = np.argmin(np.abs(freqs - h_freq))
        h_mag = fft_mag[h_idx]
        harmonic_power += h_mag**2
        h_db = 20*np.log10(h_mag/fund_mag) if h_mag > 0 and fund_mag > 0 else -999
        harmonics_info.append((h, h_freq, h_db))

    thd = np.sqrt(harmonic_power) / fund_mag * 100 if fund_mag > 0 else 0
    snr_linear = fund_mag / np.sqrt(np.sum(fft_mag**2) - fund_mag**2) if fund_mag > 0 else 0
    snr_db = 20*np.log10(snr_linear) if snr_linear > 0 else -999

    print(f"\n--- {name} ---")
    print(f"  DC Offset:     {dc*1000:.1f} mV")
    print(f"  Vmin:          {vmin*1000:.1f} mV")
    print(f"  Vmax:          {vmax*1000:.1f} mV")
    print(f"  Vpp:           {vpp*1000:.1f} mV")
    print(f"  Vrms (AC):     {vrms*1000:.1f} mV")
    print(f"  Frequency:     {freq/1000:.2f} kHz")
    if period > 0:
        print(f"  Period:        {period*1e6:.2f} us")
    print(f"  THD:           {thd:.2f}%")
    print(f"  SNR:           {snr_db:.1f} dB")
    for h, hf, hdb in harmonics_info:
        print(f"  {h}. Harmonik:   {hf/1000:.1f} kHz ({hdb:.1f} dB)")

# Check if signal looks like a sine wave
print(f"\n--- GENEL DEGERLENDIRME ---")
if data1.std() < 0.001:
    print("  [!] CH1: Sinyal YOK veya cok zayif. Kablo baglantisini kontrol edin.")
elif vpp < 0.01:
    print("  [!] CH1: Sinyal cok kucuk (Vpp < 10mV). DAC cikisi kontrol edin.")
else:
    # Check sine wave quality
    centered1 = data1 - np.mean(data1)
    amplitude = (np.max(data1) - np.min(data1)) / 2
    if amplitude > 0:
        ideal_sine = amplitude * np.sin(2 * np.pi * freq * np.arange(BUFFER_SIZE) * dt)
        # Find best phase alignment
        best_corr = 0
        for phase_shift in range(int(SAMPLE_RATE/freq)):
            shifted = np.roll(ideal_sine, phase_shift)
            corr = np.corrcoef(centered1[:4000], shifted[:4000])[0,1]
            if abs(corr) > abs(best_corr):
                best_corr = corr
        print(f"  Sinus benzerligi: {abs(best_corr)*100:.1f}%")

    if thd < 1:
        print("  Sinyal kalitesi: MUKEMMEL (THD < 1%)")
    elif thd < 5:
        print("  Sinyal kalitesi: IYI (THD < 5%)")
    elif thd < 10:
        print("  Sinyal kalitesi: ORTA (THD < 10%)")
    else:
        print("  Sinyal kalitesi: DUSUK (THD > 10%) - Filtre gerekebilir")

print("="*60)

# =========================================================================
# Generate Plot
# =========================================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 9))
fig.suptitle('AD9767 DAC Output Analysis', fontsize=14, fontweight='bold')

# Time domain CH1
ax = axes[0, 0]
ax.plot(time_us[:2000], data1[:2000], color='#00CC00', linewidth=0.8)
ax.set_title('CH1 - Time Domain')
ax.set_xlabel('Time (us)')
ax.set_ylabel('Voltage (V)')
ax.grid(True, alpha=0.3)
ax.axhline(y=np.mean(data1), color='yellow', linestyle='--', linewidth=0.5, label=f'DC={np.mean(data1)*1000:.1f}mV')
ax.legend(fontsize=8)

# Time domain CH2
ax = axes[0, 1]
ax.plot(time_us[:2000], data2[:2000], color='#0088FF', linewidth=0.8)
ax.set_title('CH2 - Time Domain')
ax.set_xlabel('Time (us)')
ax.set_ylabel('Voltage (V)')
ax.grid(True, alpha=0.3)
ax.axhline(y=np.mean(data2), color='yellow', linestyle='--', linewidth=0.5, label=f'DC={np.mean(data2)*1000:.1f}mV')
ax.legend(fontsize=8)

# FFT CH1
ax = axes[1, 0]
fft1 = np.fft.rfft(data1 - np.mean(data1))
fft1_mag = np.abs(fft1) / (BUFFER_SIZE/2)
freqs = np.fft.rfftfreq(BUFFER_SIZE, dt) / 1000  # kHz
ax.plot(freqs[:500], 20*np.log10(fft1_mag[:500] + 1e-10), color='#00CC00', linewidth=0.8)
ax.set_title('CH1 - Frequency Spectrum')
ax.set_xlabel('Frequency (kHz)')
ax.set_ylabel('Magnitude (dB)')
ax.grid(True, alpha=0.3)
ax.set_xlim(0, freqs[500])

# FFT CH2
ax = axes[1, 1]
fft2 = np.fft.rfft(data2 - np.mean(data2))
fft2_mag = np.abs(fft2) / (BUFFER_SIZE/2)
ax.plot(freqs[:500], 20*np.log10(fft2_mag[:500] + 1e-10), color='#0088FF', linewidth=0.8)
ax.set_title('CH2 - Frequency Spectrum')
ax.set_xlabel('Frequency (kHz)')
ax.set_ylabel('Magnitude (dB)')
ax.grid(True, alpha=0.3)
ax.set_xlim(0, freqs[500])

plt.tight_layout()
out_path = r'C:\Users\melsa\OneDrive\Desktop\dac_output_project\waveform_analysis.png'
plt.savefig(out_path, dpi=150)
print(f"\nGrafik kaydedildi: {out_path}")

# Save raw data
np.savez(r'C:\Users\melsa\OneDrive\Desktop\dac_output_project\capture_data.npz',
         ch1=data1, ch2=data2, time_us=time_us, sample_rate=SAMPLE_RATE)
print("Ham veri kaydedildi: capture_data.npz")
