"""
AD9767 DAC Output - Analog Discovery 2 Oscilloscope Viewer
Captures and displays the sine wave from DAC on CH1 and CH2.
Uses Digilent WaveForms SDK (DWF).

Usage: python view_waveform.py
"""

from ctypes import *
import sys
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Load DWF library
if sys.platform.startswith("win"):
    dwf = cdll.dwf
else:
    dwf = cdll.LoadLibrary("libdwf.so")

# Constants
hdwfNone = c_int(0)
DwfStateDone = c_ubyte(2)
filterDecimate = c_int(0)

# =========================================================================
# Configuration
# =========================================================================
SAMPLE_RATE = 10_000_000.0    # 10 MHz sampling rate
BUFFER_SIZE = 8192             # samples per acquisition
VOLTAGE_RANGE = 5.0            # +/- 2.5V range
CHANNEL = 0                    # CH1 = 0, CH2 = 1

# =========================================================================
# Open Device
# =========================================================================
version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print(f"DWF Version: {version.value.decode()}")

print("Opening Analog Discovery 2...")
hdwf = c_int()
dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

if hdwf.value == hdwfNone.value:
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(f"Error: {szerr.value.decode()}")
    print("Analog Discovery 2 bulunamadi! USB baglantisini kontrol edin.")
    sys.exit(1)

print("Cihaz acildi.")
dwf.FDwfDeviceAutoConfigureSet(hdwf, c_int(0))

# =========================================================================
# Configure Oscilloscope
# =========================================================================
print(f"Oscilloscope ayarlari:")
print(f"  Sampling rate: {SAMPLE_RATE/1e6:.1f} MHz")
print(f"  Buffer size: {BUFFER_SIZE}")
print(f"  Voltage range: +/- {VOLTAGE_RANGE/2:.1f} V")

# Set up acquisition for both channels
dwf.FDwfAnalogInFrequencySet(hdwf, c_double(SAMPLE_RATE))
dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(BUFFER_SIZE))

# Enable both channels
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_int(1))  # CH1
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(1), c_int(1))  # CH2
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(VOLTAGE_RANGE))
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(1), c_double(VOLTAGE_RANGE))
dwf.FDwfAnalogInChannelFilterSet(hdwf, c_int(-1), filterDecimate)

# Configure trigger: rising edge on CH1, auto-trigger
trigsrcDetectorAnalogIn = c_ubyte(2)
DwfTriggerSlopeRise = c_int(0)
dwf.FDwfAnalogInTriggerSourceSet(hdwf, trigsrcDetectorAnalogIn)
dwf.FDwfAnalogInTriggerChannelSet(hdwf, c_int(0))  # trigger on CH1
dwf.FDwfAnalogInTriggerTypeSet(hdwf, c_int(0))     # edge trigger
dwf.FDwfAnalogInTriggerConditionSet(hdwf, DwfTriggerSlopeRise)
dwf.FDwfAnalogInTriggerLevelSet(hdwf, c_double(0.0))  # trigger at 0V (mid-point)
dwf.FDwfAnalogInTriggerAutoTimeoutSet(hdwf, c_double(1.0))  # 1s auto-trigger

dwf.FDwfAnalogInConfigure(hdwf, c_int(1), c_int(0))

# Wait for offset to stabilize
print("Bekleniyor (offset stabilizasyonu)...")
time.sleep(2)

# =========================================================================
# Live Oscilloscope Display
# =========================================================================
print("Canli osiloskop baslatiliyor... (Kapatmak icin pencereyi kapatin)")

rgdSamples1 = (c_double * BUFFER_SIZE)()
rgdSamples2 = (c_double * BUFFER_SIZE)()

# Time axis
dt = 1.0 / SAMPLE_RATE
time_axis = np.arange(BUFFER_SIZE) * dt * 1e6  # microseconds

# Set up matplotlib for live display
plt.style.use('dark_background')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7))
fig.suptitle('AD9767 DAC Output - Analog Discovery 2', fontsize=14, color='white')

line1, = ax1.plot([], [], color='#00FF00', linewidth=1.2, label='CH1')
ax1.set_xlim(0, time_axis[-1])
ax1.set_ylim(-VOLTAGE_RANGE/2, VOLTAGE_RANGE/2)
ax1.set_ylabel('Voltage (V)')
ax1.set_title('Channel 1 (DA1 Output)', color='#00FF00')
ax1.grid(True, alpha=0.3)
ax1.legend(loc='upper right')

line2, = ax2.plot([], [], color='#00AAFF', linewidth=1.2, label='CH2')
ax2.set_xlim(0, time_axis[-1])
ax2.set_ylim(-VOLTAGE_RANGE/2, VOLTAGE_RANGE/2)
ax2.set_xlabel('Time (us)')
ax2.set_ylabel('Voltage (V)')
ax2.set_title('Channel 2 (DA2 Output)', color='#00AAFF')
ax2.grid(True, alpha=0.3)
ax2.legend(loc='upper right')

freq_text = ax1.text(0.02, 0.92, '', transform=ax1.transAxes, color='yellow', fontsize=11)
vpp_text1 = ax1.text(0.02, 0.80, '', transform=ax1.transAxes, color='#00FF00', fontsize=10)
vpp_text2 = ax2.text(0.02, 0.92, '', transform=ax2.transAxes, color='#00AAFF', fontsize=10)

plt.tight_layout()


def estimate_frequency(data, sample_rate):
    """Estimate frequency using zero-crossings."""
    # Remove DC offset
    data = data - np.mean(data)
    # Find zero crossings (positive slope)
    crossings = []
    for i in range(1, len(data)):
        if data[i-1] < 0 and data[i] >= 0:
            crossings.append(i)
    if len(crossings) >= 2:
        avg_period = (crossings[-1] - crossings[0]) / (len(crossings) - 1)
        freq = sample_rate / avg_period
        return freq
    return 0


def update(frame):
    """Update oscilloscope display."""
    sts = c_byte()

    # Start acquisition
    dwf.FDwfAnalogInConfigure(hdwf, c_int(0), c_int(1))

    # Wait for acquisition to complete
    timeout = 50
    while timeout > 0:
        dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
        if sts.value == DwfStateDone.value:
            break
        time.sleep(0.01)
        timeout -= 1

    if sts.value == DwfStateDone.value:
        # Get data from both channels
        dwf.FDwfAnalogInStatusData(hdwf, 0, rgdSamples1, BUFFER_SIZE)
        dwf.FDwfAnalogInStatusData(hdwf, 1, rgdSamples2, BUFFER_SIZE)

        data1 = np.array(rgdSamples1[:])
        data2 = np.array(rgdSamples2[:])

        line1.set_data(time_axis, data1)
        line2.set_data(time_axis, data2)

        # Measure and display
        vpp1 = np.max(data1) - np.min(data1)
        vpp2 = np.max(data2) - np.min(data2)
        freq = estimate_frequency(data1, SAMPLE_RATE)

        if freq > 1000:
            freq_text.set_text(f'Freq: {freq/1000:.1f} kHz')
        else:
            freq_text.set_text(f'Freq: {freq:.0f} Hz')

        vpp_text1.set_text(f'Vpp: {vpp1:.3f} V')
        vpp_text2.set_text(f'Vpp: {vpp2:.3f} V')

    return line1, line2, freq_text, vpp_text1, vpp_text2


try:
    ani = animation.FuncAnimation(fig, update, interval=100, blit=True, cache_frame_data=False)
    plt.show()
except KeyboardInterrupt:
    pass
finally:
    print("Cihaz kapatiliyor...")
    dwf.FDwfDeviceCloseAll()
    print("Tamam.")
