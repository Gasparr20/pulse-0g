"""Generate Spanish TTS voiceover + instrument-grade audio bed for Pulse-0G V3.

Uses `edge-tts` (GitHub: rany2/edge-tts) to synthesize individual Spanish phrases,
measures exact segment timings, pads/places them along a <=30.0s timeline, mixes in
a subtle procedural control-room drone and cues, and exports:
  - video/pulse_0g_audio_v3.wav
  - video/v3_timings.json (exact phrase start/end timestamps for video & English SRT)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import wave
from dataclasses import dataclass
from typing import List

import edge_tts
import numpy as np

SR = 48000
DEFAULT_VOICE = "es-AR-TomasNeural"
DEFAULT_RATE = "+0%"


@dataclass(frozen=True)
class CueLine:
    """One narrated beat with its Spanish TTS line and English subtitle."""

    block_id: str
    es_text: str
    en_sub: str
    min_gap_after: float = 0.45


SCRIPT_LINES: List[CueLine] = [
    CueLine(
        block_id="problem",
        es_text="En Marte no hay médico a bordo, y la Tierra tarda veintidós minutos en responder.",
        en_sub="On Mars, there is no doctor on board — and Earth takes 22 minutes to reply.",
        min_gap_after=0.50,
    ),
    CueLine(
        block_id="solution",
        es_text="Pulse-0G no diagnostica ni tira cifras sueltas: compara tu estado contra tu propia historia y guía tu acción.",
        en_sub="Pulse-0G doesn't diagnose or dump raw numbers: it compares you to your own baseline and guides action.",
        min_gap_after=0.55,
    ),
    CueLine(
        block_id="how",
        es_text="Funciona sin internet y nunca inventa. Si falta un dato, deja el hueco; sin respaldo, tacha la frase.",
        en_sub="It runs offline and never guesses. Missing data stays blank; any unverified claim is struck out.",
        min_gap_after=0.55,
    ),
    CueLine(
        block_id="potential",
        es_text="Usa datos abiertos de NASA y está listo para conectarse a sensores europeos y canadienses en órbita.",
        en_sub="Built on open NASA data, ready to plug into European and Canadian space wearables.",
        min_gap_after=0.55,
    ),
    CueLine(
        block_id="endcard",
        es_text="Pulse cero ge: decisiones de salud trazables.",
        en_sub="Pulse-0G: traceable health decisions.",
        min_gap_after=1.10,
    ),
]


async def synth_clips(
    lines: List[CueLine],
    voice: str,
    rate: str,
    tmp_dir: str,
) -> List[str]:
    """Synthesize each cue line to an MP3 file via edge-tts."""
    os.makedirs(tmp_dir, exist_ok=True)
    paths: List[str] = []
    for idx, line in enumerate(lines):
        out_mp3 = os.path.join(tmp_dir, f"cue_{idx}_{line.block_id}.mp3")
        comm = edge_tts.Communicate(line.es_text, voice=voice, rate=rate)
        await comm.save(out_mp3)
        paths.append(out_mp3)
    return paths


def decode_to_mono_f64(audio_path: str) -> np.ndarray:
    """Decode an audio file to 48 kHz mono float64 samples using ffmpeg."""
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", audio_path,
        "-ac", "1", "-ar", str(SR),
        "-f", "f32le", "-",
    ]
    res = subprocess.run(cmd, check=True, capture_output=True)
    samples = np.frombuffer(res.stdout, dtype=np.float32).astype(np.float64)
    return trim_silence(samples)


def trim_silence(samples: np.ndarray, thresh: float = 0.008) -> np.ndarray:
    """Trim leading and trailing silence from a synthesized speech clip."""
    above = np.where(np.abs(samples) > thresh)[0]
    if len(above) == 0:
        return samples
    pad_lead = int(0.03 * SR)
    pad_tail = int(0.06 * SR)
    i0 = max(0, int(above[0]) - pad_lead)
    i1 = min(len(samples), int(above[-1]) + pad_tail)
    return samples[i0:i1]


def add_sine_blip(
    buf: np.ndarray,
    t0: float,
    freq: float,
    dur: float,
    amp: float = 0.04,
    freq_end: float | None = None,
) -> None:
    """Add a subtle control-room tone cue to stereo buffer."""
    n_total = buf.shape[0]
    i0 = max(0, int(t0 * SR))
    n = min(int(dur * SR), n_total - i0)
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


def add_whoosh(buf: np.ndarray, t0: float, dur: float = 0.28, amp: float = 0.025) -> None:
    """Add a soft transition breath."""
    n_total = buf.shape[0]
    i0 = max(0, int(t0 * SR))
    n = min(int(dur * SR), n_total - i0)
    if n <= 0:
        return
    rng = np.random.default_rng(int(t0 * 1000) + 37)
    noise = rng.standard_normal(n)
    kernel = np.ones(45) / 45.0
    smooth = np.convolve(noise, kernel, mode="same")
    t = np.arange(n, dtype=np.float64) / SR
    env = np.sin(np.pi * t / dur) ** 1.6
    sig = amp * env * smooth * 2.5
    buf[i0 : i0 + n, 0] += sig
    buf[i0 : i0 + n, 1] += sig


def build_v3_audio(voice: str = DEFAULT_VOICE, rate: str = DEFAULT_RATE) -> dict:
    """Generate TTS clips, assemble the <=30s master audio track, and save timings JSON."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    tmp_dir = os.path.join(base_dir, ".tmp_v3_tts")
    mp3_paths = asyncio.run(synth_clips(SCRIPT_LINES, voice=voice, rate=rate, tmp_dir=tmp_dir))

    clips = [decode_to_mono_f64(p) for p in mp3_paths]
    # Normalize each clip gently to consistent speech level
    norm_clips: List[np.ndarray] = []
    for c in clips:
        rms = float(np.sqrt(np.mean(c ** 2))) if len(c) > 0 else 1.0
        target_rms = 0.17
        gain = min(target_rms / max(rms, 1e-6), 4.0)
        norm_clips.append(np.clip(c * gain, -0.88, 0.88))

    lead_in = 0.35
    cursor = lead_in
    placements = []
    for line, clip in zip(SCRIPT_LINES, norm_clips):
        dur = len(clip) / SR
        start_t = round(cursor, 3)
        end_t = round(cursor + dur, 3)
        placements.append(
            {
                "block_id": line.block_id,
                "speech_start": start_t,
                "speech_end": end_t,
                "speech_dur": round(dur, 3),
                "block_start": 0.0 if line.block_id == "problem" else round(start_t - 0.18, 3),
                "es_text": line.es_text,
                "en_sub": line.en_sub,
            }
        )
        cursor += dur + line.min_gap_after

    total_dur = round(max(cursor, 28.0), 3)
    for idx in range(len(placements)):
        if idx + 1 < len(placements):
            placements[idx]["block_end"] = placements[idx + 1]["block_start"]
        else:
            placements[idx]["block_end"] = total_dur

    n_samples = int(round(total_dur * SR))
    buf = np.zeros((n_samples, 2), dtype=np.float64)

    # Subtle ambient control-room drone underneath speech
    t = np.arange(n_samples, dtype=np.float64) / SR
    fade_in = np.clip(t / 1.0, 0.0, 1.0)
    fade_out = np.clip((total_dur - t) / 1.2, 0.0, 1.0)
    pad = (
        0.015 * np.sin(2.0 * np.pi * 65.41 * t)
        + 0.007 * np.sin(2.0 * np.pi * 98.00 * t)
    ) * fade_in * fade_out
    buf[:, 0] += pad
    buf[:, 1] += pad

    # Subtle transition cues aligned to block starts
    add_sine_blip(buf, 0.12, freq=220.0, dur=0.25, amp=0.030)
    for idx, pl in enumerate(placements[1:], start=1):
        bt = pl["block_start"]
        add_whoosh(buf, max(0.0, bt - 0.05), dur=0.26, amp=0.022)
        if pl["block_id"] == "how":
            # Strike-out cue near mid-block
            mid = pl["speech_start"] + pl["speech_dur"] * 0.72
            add_sine_blip(buf, mid, freq=185.0, dur=0.32, amp=0.055, freq_end=72.0)
        elif pl["block_id"] == "endcard":
            add_sine_blip(buf, bt + 0.08, freq=261.6, dur=0.55, amp=0.038)
            add_sine_blip(buf, bt + 0.20, freq=392.0, dur=0.45, amp=0.028)
        else:
            add_sine_blip(buf, bt + 0.05, freq=329.6 + idx * 45.0, dur=0.18, amp=0.028)

    # Mix voiceover clips cleanly
    for pl, clip in zip(placements, norm_clips):
        i0 = int(round(pl["speech_start"] * SR))
        i1 = min(n_samples, i0 + len(clip))
        seg = clip[: i1 - i0]
        buf[i0:i1, 0] += seg
        buf[i0:i1, 1] += seg

    peak = float(np.max(np.abs(buf)))
    if peak > 0.90:
        buf = buf * (0.90 / peak)
    pcm = np.clip(buf * 32767.0, -32767, 32767).astype(np.int16)

    out_wav = os.path.join(base_dir, "pulse_0g_audio_v3.wav")
    with wave.open(out_wav, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())

    meta = {
        "voice": voice,
        "rate": rate,
        "total_duration": total_dur,
        "audio_path": out_wav,
        "cues": placements,
    }
    meta_path = os.path.join(base_dir, "v3_timings.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"Voice: {voice} (rate={rate}) -> {out_wav} ({total_dur:.2f}s)")
    for pl in placements:
        print(
            f"  [{pl['block_start']:5.2f}s - {pl['block_end']:5.2f}s] "
            f"speech {pl['speech_start']:5.2f}s..{pl['speech_end']:5.2f}s ({pl['speech_dur']:.2f}s): {pl['block_id']}"
        )
    return meta


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Pulse-0G V3 Spanish TTS audio.")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="edge-tts voice name (e.g. es-AR-TomasNeural, es-AR-ElenaNeural)")
    parser.add_argument("--rate", default=DEFAULT_RATE, help="edge-tts speaking rate (e.g. +0%%, +12%%)")
    args = parser.parse_args()
    build_v3_audio(voice=args.voice, rate=args.rate)
