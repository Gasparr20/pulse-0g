"""Synthesize a clean, understated instrument-grade 28.0s audio bed for Pulse-0G V2.

All sounds are generated procedurally via NumPy (zero external samples,
zero copyright issues). Synchronized to the 6-block V2 Spanish cut:
- 0.00 - 3.00: Problem statement (dark silence + subtle low pulse)
- 3.00 - 8.00: Body map + tap/punch-in on head (red)
- 8.00 - 13.00: Sleep card zoom (2.9 h vs 7.3 h baseline, -60%, missing gaps)
- 13.00 - 19.00: Claim verifier + dramatic red strike-out
- 19.00 - 25.00: Case package export
- 25.00 - 28.00: Single Pulse-0G lockup
"""

from __future__ import annotations

import os
import wave
import numpy as np

SR = 48000
DURATION = 28.0
N_SAMPLES = int(SR * DURATION)


def add_sine_blip(
    buf: np.ndarray,
    t0: float,
    freq: float,
    dur: float,
    amp: float = 0.075,
    freq_end: float | None = None,
) -> None:
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
    buf[i0 : i0 + n, 0] += sig
    buf[i0 : i0 + n, 1] += sig


def add_click(buf: np.ndarray, t0: float, amp: float = 0.045, bright: float = 2400.0) -> None:
    i0 = max(0, int(t0 * SR))
    n = min(int(0.018 * SR), N_SAMPLES - i0)
    if n <= 0:
        return
    t = np.arange(n, dtype=np.float64) / SR
    env = np.exp(-t / 0.0035)
    sig = amp * env * (0.65 * np.sin(2.0 * np.pi * bright * t) + 0.35 * np.sin(2.0 * np.pi * bright * 1.47 * t))
    buf[i0 : i0 + n, 0] += sig
    buf[i0 : i0 + n, 1] += sig


def add_whoosh(buf: np.ndarray, t0: float, dur: float = 0.32, amp: float = 0.04) -> None:
    i0 = max(0, int(t0 * SR))
    n = min(int(dur * SR), N_SAMPLES - i0)
    if n <= 0:
        return
    rng = np.random.default_rng(int(t0 * 1000) + 19)
    noise = rng.standard_normal(n)
    kernel = np.ones(45) / 45.0
    smooth = np.convolve(noise, kernel, mode="same")
    t = np.arange(n, dtype=np.float64) / SR
    env = np.sin(np.pi * t / dur) ** 1.6
    sig = amp * env * smooth * 2.8
    buf[i0 : i0 + n, 0] += sig
    buf[i0 : i0 + n, 1] += sig


def build_audio(out_path: str) -> None:
    buf = np.zeros((N_SAMPLES, 2), dtype=np.float64)

    # Low subtle instrument drone (0.0s -> 28.0s)
    t = np.arange(N_SAMPLES, dtype=np.float64) / SR
    fade_in = np.clip(t / 1.4, 0.0, 1.0)
    fade_out = np.clip((DURATION - t) / 1.8, 0.0, 1.0)
    pad = (
        0.026 * np.sin(2.0 * np.pi * 65.41 * t)
        + 0.012 * np.sin(2.0 * np.pi * 98.00 * t)
    ) * fade_in * fade_out
    buf[:, 0] += pad
    buf[:, 1] += pad

    # Block 1 (0.0 - 3.0): Problem reveal
    add_sine_blip(buf, 0.15, freq=220.0, dur=0.30, amp=0.045)
    add_sine_blip(buf, 1.35, freq=164.8, dur=0.35, amp=0.055, freq_end=130.8)

    # Block 2 (3.0 - 8.0): Body map + tap on head at 4.8s
    add_whoosh(buf, 2.95, dur=0.30, amp=0.035)
    add_sine_blip(buf, 3.05, freq=329.6, dur=0.20, amp=0.045)
    add_click(buf, 4.75, amp=0.065, bright=2800.0)
    add_sine_blip(buf, 4.80, freq=440.0, dur=0.22, amp=0.055)

    # Block 3 (8.0 - 13.0): Sleep card zoom & sparkline gaps
    add_whoosh(buf, 7.95, dur=0.32, amp=0.04)
    add_sine_blip(buf, 8.05, freq=392.0, dur=0.22, amp=0.05)
    for k in range(8):
        add_click(buf, 8.40 + k * 0.10, amp=0.024, bright=1700.0 + k * 80)

    # Block 4 (13.0 - 19.0): Claim verifier + dramatic strike-out at 15.20s
    add_whoosh(buf, 12.95, dur=0.30, amp=0.04)
    add_sine_blip(buf, 13.55, freq=587.3, dur=0.18, amp=0.05)
    add_sine_blip(buf, 15.20, freq=180.0, dur=0.38, amp=0.10, freq_end=68.0)
    add_sine_blip(buf, 15.20, freq=311.1, dur=0.18, amp=0.05, freq_end=220.0)
    add_click(buf, 15.60, amp=0.05, bright=1400.0)

    # Block 5 (19.0 - 25.0): Case package export
    add_whoosh(buf, 18.95, dur=0.30, amp=0.04)
    add_sine_blip(buf, 19.10, freq=440.0, dur=0.22, amp=0.05)
    for k in range(6):
        add_click(buf, 19.65 + k * 0.22, amp=0.025, bright=2100.0)

    # Block 6 (25.0 - 28.0): Single Pulse-0G lockup
    add_whoosh(buf, 24.92, dur=0.32, amp=0.035)
    add_sine_blip(buf, 25.05, freq=261.6, dur=0.65, amp=0.06)
    add_sine_blip(buf, 25.25, freq=392.0, dur=0.55, amp=0.045)

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
    build_audio(os.path.join(base_dir, "pulse_0g_audio_v2.wav"))
