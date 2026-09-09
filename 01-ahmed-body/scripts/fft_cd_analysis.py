#!/usr/bin/env python3
"""
FFT/power-spectrum analysis of the Cd (drag coefficient) iteration
history from a steady SIMPLEC run, to distinguish structured
(periodic/quasi-periodic) oscillation from unstructured numerical
scatter.

IMPORTANT: this is a steady-state pseudo-time SIMPLEC calculation.
deltaT=1 in controlDict is a pseudo-time relaxation increment, NOT a
physically meaningful timestep. Any frequency identified here is
reported in cycles/iteration and period in iterations -- NOT Hz or
seconds -- unless/until a genuine transient calculation with a
physically meaningful timestep is run.
"""

import numpy as np

data = np.load('cd_history.npz')
iterations = data['iterations']
cd = data['cd']

n = len(cd)
dt_iter = np.median(np.diff(iterations))  # sampling interval, in iterations

print(f"Number of samples: {n}")
print(f"Sampling interval: {dt_iter:.1f} iteration(s) (uniform: {np.allclose(np.diff(iterations), dt_iter)})")

mean_cd = cd.mean()
std_cd = cd.std()
print(f"Mean Cd used for de-meaning: {mean_cd:.6f}")
print(f"Std Cd: {std_cd:.6f}")

# Remove mean
cd_demeaned = cd - mean_cd

# FFT
fft_vals = np.fft.rfft(cd_demeaned)
freqs = np.fft.rfftfreq(n, d=dt_iter)  # cycles per iteration
power = np.abs(fft_vals) ** 2

# Exclude the zero-frequency bin (DC, already removed by demeaning, but
# guard against numerical residual there)
power[0] = 0

# Find dominant peak
peak_idx = np.argmax(power)
peak_freq = freqs[peak_idx]
peak_power = power[peak_idx]
period_iterations = 1.0 / peak_freq if peak_freq > 0 else np.inf

print(f"\n--- Dominant spectral peak ---")
print(f"Frequency: {peak_freq:.6f} cycles/iteration")
print(f"Period:    {period_iterations:.2f} iterations")

# Compare peak to background (median power excluding the peak and its
# immediate neighbors, and excluding DC)
background = np.median(np.delete(power, [0, peak_idx]))
ratio = peak_power / background if background > 0 else np.inf
print(f"\nPeak power / median background power: {ratio:.2f}x")

# Report top 5 peaks for context
sorted_idx = np.argsort(power)[::-1][:5]
print(f"\n--- Top 5 spectral peaks ---")
for idx in sorted_idx:
    f = freqs[idx]
    p = 1.0/f if f > 0 else np.inf
    print(f"  freq={f:.6f} cycles/iter, period={p:.2f} iters, power={power[idx]:.6e}")

# Simple time-domain peak/trough check
from scipy.signal import find_peaks
peaks, _ = find_peaks(cd_demeaned)
troughs, _ = find_peaks(-cd_demeaned)
if len(peaks) > 1:
    peak_intervals = np.diff(iterations[peaks])
    print(f"\n--- Time-domain peak-to-peak intervals ---")
    print(f"Number of peaks found: {len(peaks)}")
    print(f"Mean interval: {peak_intervals.mean():.2f} iterations, std: {peak_intervals.std():.2f}")
if len(troughs) > 1:
    trough_intervals = np.diff(iterations[troughs])
    print(f"Number of troughs found: {len(troughs)}")
    print(f"Mean trough interval: {trough_intervals.mean():.2f} iterations, std: {trough_intervals.std():.2f}")
