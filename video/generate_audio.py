"""Synthesize a clean, understated instrument-grade audio bed for Pulse-0G.

All sounds are generated procedurally via NumPy (zero external samples,
zero copyright issues). Designed to sit subtly behind the 23.0s 30fps video:
- Low instrument pulse (65 Hz / 130 Hz)
- Crisp terminal key ticks during typewriter beats
- Subtle telemetry lock chimes on section cuts
- Low muffled thud + warning click on the red Claim Verifier strike-out
"""

from __future__ import annotations

import os
import wave
import numpy as np

SR = 48000
DURATION = 23.0
N_SAMPLES = int(SR * DURATION)


def add_sine_blip(
    buf: np.ndarray,
    t0: float,
    freq: float,
    dur: float,
    amp: float = 0.08,
    freq_end: float | None = None,
    pan: float = 0.0,
) -> None:
    """Add an exponentially decaying sine tone with optional pitch glide."""
    i0 = max(0, int(t0 * SR))
    n = min(int(dur * SR), N_SAMPLES - i0)
    if n <= 0:
        return
    t = np.arange(n, dtype=np.float64) / SR
    if freq_end is not None:
        freqs = np.linspace(freq, freq_end, n)
        phase = 2.0 * np.pi * np.cumsum(freqs) / SR
    else:
        phase = 2.0 * np.pi * freq * t
    env = np.minimum(t / 0.004, 1.0) * np.exp(-t / max(dur * 0.28, 0.01))
    sig = amp * env * np.sin(phase)
    lg = np.cos((pan + 1.0) * np.pi / 4.0)
    rg = np.sin((pan + 1.0) * np.pi / 4.0)
    buf[i0 : i0 + n, 0] += sig * lg
    buf[i0 : i0 + n, 1] += sig * rg


def add_click(buf: np.ndarray, t0: float, amp: float = 0.05, bright: float = 2800.0) -> None:
    """Add a short dry instrument/key click."""
    i0 = max(0, int(t0 * SR))
    dur = 0.018
    n = min(int(dur * SR), N_SAMPLES - i0)
    if n <= 0:
        return
    t = np.arange(n, dtype=np.float64) / SR
    env = np.exp(-t / 0.0035)
    sig = amp * env * (0.65 * np.sin(2.0 * np.pi * bright * t) + 0.35 * np.sin(2.0 * np.pi * bright * 1.47 * t))
    buf[i0 : i0 + n, 0] += sig
    buf[i0 : i0 + n, 1] += sig


def add_whoosh(buf: np.ndarray, t0: float, dur: float = 0.35, amp: float = 0.045) -> None:
    """Add a soft filtered air-sweep transition."""
    i0 = max(0, int(t0 * SR))
    n = min(int(dur * SR), N_SAMPLES - i0)
    if n <= 0:
        return
    rng = np.random.default_rng(int(t0 * 1000) + 7)
    noise = rng.standard_normal(n)
    # Simple moving-average low-pass for smooth air texture
    kernel = np.ones(45) / 45.0
    smooth = np.convolve(noise, kernel, mode="same")
    t = np.arange(n, dtype=np.float64) / SR
    env = np.sin(np.pi * t / dur) ** 1.6
    sig = amp * env * smooth * 3.0
    buf[i0 : i0 + n, 0] += sig
    buf[i0 : i0 + n, 1] += sig


def build_audio(out_path: str) -> None:
    buf = np.zeros((N_SAMPLES, 2), dtype=np.float64)

    # 1. Subtle low instrument drone / heartbeat pulse (0.0s -> 22.8s)
    t = np.arange(N_SAMPLES, dtype=np.float64) / SR
    fade_in = np.clip(t / 1.2, 0.0, 1.0)
    fade_out = np.clip((DURATION - t) / 1.5, 0.0, 1.0)
    pad = (
        0.030 * np.sin(2.0 * np.pi * 65.41 * t)
        + 0.015 * np.sin(2.0 * np.pi * 98.00 * t)
        + 0.008 * np.sin(2.0 * np.pi * 130.81 * t)
    ) * fade_in * fade_out
    buf[:, 0] += pad
    buf[:, 1] += pad

    # Subtle 1 Hz telemetry pulse ticks during active data blocks
    for sec in np.arange(1.0, 21.0, 0.5):
        if 18.7 <= sec <= 20.6:
            continue
        add_sine_blip(buf, float(sec), freq=110.0, dur=0.06, amp=0.022, freq_end=78.0)

    # 2. Boot typewriter clicks (0.05s - 0.72s)
    for k in range(12):
        add_click(buf, 0.06 + k * 0.055, amp=0.045, bright=2400.0 + k * 45)

    # 3. Parentheses lockup + portal zoom
    add_sine_blip(buf, 1.00, freq=520.0, dur=0.18, amp=0.055)
    add_sine_blip(buf, 2.00, freq=392.0, dur=0.22, amp=0.060)
    add_whoosh(buf, 2.85, dur=0.45, amp=0.065)

    # 4. Halftone baseline wipe + counter ticks
    add_sine_blip(buf, 3.30, freq=261.6, dur=0.25, amp=0.055)
    add_click(buf, 3.85, amp=0.055, bright=1900.0)
    for k in range(14):
        add_click(buf, 5.45 + k * 0.09, amp=0.032, bright=1600.0 + (k % 4) * 200)
    add_sine_blip(buf, 6.72, freq=440.0, dur=0.20, amp=0.055)

    # 5. Stat 1 -> Slide -> Stat 2
    add_sine_blip(buf, 7.30, freq=330.0, dur=0.24, amp=0.055)
    add_whoosh(buf, 9.30, dur=0.40, amp=0.055)
    add_sine_blip(buf, 9.70, freq=392.0, dur=0.24, amp=0.055)

    # 6. Stacked cards -> Verifier focus -> Strike-out
    add_whoosh(buf, 12.05, dur=0.32, amp=0.045)
    for k in range(10):
        add_click(buf, 13.75 + k * 0.06, amp=0.028, bright=2200.0)
    # Row 1 anchored ping
    add_sine_blip(buf, 14.15, freq=587.3, dur=0.18, amp=0.05)
    # Row 2 strike-out impact (15.05s): crisp warning drop + red strike sweep
    add_sine_blip(buf, 15.05, freq=180.0, dur=0.35, amp=0.11, freq_end=68.0)
    add_sine_blip(buf, 15.05, freq=311.1, dur=0.16, amp=0.055, freq_end=220.0)
    add_click(buf, 15.45, amp=0.055, bright=1400.0)

    # 7. Side 3-word reveal ticks (16.45, 16.72, 16.99)
    add_whoosh(buf, 16.25, dur=0.35, amp=0.045)
    add_sine_blip(buf, 16.55, freq=440.0, dur=0.14, amp=0.05)
    add_sine_blip(buf, 16.82, freq=523.25, dur=0.14, amp=0.05)
    add_sine_blip(buf, 17.09, freq=659.25, dur=0.18, amp=0.055)

    # 8. Wordmark + Endcard
    add_sine_blip(buf, 18.80, freq=261.6, dur=0.60, amp=0.065)
    add_sine_blip(buf, 20.60, freq=392.0, dur=0.55, amp=0.050)
    for k in range(12):
        add_click(buf, 21.00 + k * 0.065, amp=0.022, bright=2100.0)

    # Soft limiter & 16-bit PCM WAV export
    peak = np.max(np.abs(buf))
    if peak > 0.85:
        buf = buf * (0.85 / peak)
    pcm = np.clip(buf * 32767.0, -32767, 32767).astype(np.int16)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with wave.open(out_path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    print(f"Wrote {out_path} ({DURATION:.1f}s @ {SR} Hz)")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    build_audio(os.path.join(base_dir, "pulse_0g_audio.wav"))
