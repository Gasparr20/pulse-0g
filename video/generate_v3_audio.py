#!/usr/bin/env python3
"""
Audio pipeline for Pulse-0G V3 30-second pitch video:
1. Natural Spanish narration using Qwen3-TTS-12Hz-1.7B (VoiceDesign anchor + Base clone lock)
2. Custom SFX timeline built with `earshot sfx render` presets
3. Warm, subtle low-volume ambient underscore (Cm9 -> Abmaj7 -> Ebmaj7 -> Cm9)
   using pitched `earshot` kalimba plucks + low-pass velvet pad + sidechain ducking
4. Final mastered 48 kHz stereo WAV + exact `v3_timings.json` sync map (<= 30.0s)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
import soundfile as sf


SR = 48000
MAX_TOTAL_SEC = 29.85
LEAD_PAD_SEC = 0.28
GAP_BEFORE_SPEECH = 0.28
GAP_AFTER_SPEECH = 0.24
OUTRO_RING_SEC = 1.55

REPO_ROOT = Path("/home/gaspar_22/dev/crewcheck")
VIDEO_DIR = Path(__file__).resolve().parent
VENV_CUDA_PY = REPO_ROOT / "venv" / "bin" / "python"
EARSHOT_BIN = REPO_ROOT / ".venv" / "bin" / "earshot"
TTS_WORKER = VIDEO_DIR / "v3_tts_worker.py"
ANCHOR_WAV = VIDEO_DIR / "v3_voice_anchor.wav"
OUT_WAV = VIDEO_DIR / "pulse_0g_audio_v3.wav"
OUT_TIMINGS = VIDEO_DIR / "v3_timings.json"
BUILD_DIR = Path("/tmp/v3_audio_build")


SCRIPT_LINES = [
    {
        "block_id": "problem",
        "es_text": "En Marte no hay médico a bordo, y la Tierra tarda veintidós minutos en responder.",
        "tts_text": "En Marte no hay médico a bordo, y la Tierra tarda veintidós minutos en responder.",
        "en_sub": "On Mars, there is no doctor on board — and Earth takes 22 minutes to reply.",
    },
    {
        "block_id": "solution",
        "es_text": "Pulse-0G no diagnostica ni suelta cifras: te compara con tu historia y guía tu acción.",
        "tts_text": "Pulse cero G no diagnostica ni suelta cifras: te compara con tu historia y guía tu acción.",
        "en_sub": "Pulse-0G doesn't diagnose or dump numbers: it compares you to your baseline and guides action.",
    },
    {
        "block_id": "how",
        "es_text": "Funciona sin conexión y nunca inventa. Sin datos, deja el hueco; sin respaldo, tacha el texto.",
        "tts_text": "Funciona sin conexión y nunca inventa. Sin datos, deja el hueco; sin respaldo, tacha el texto.",
        "en_sub": "Offline-first and never guesses. Missing data stays blank; unverified claims are struck out.",
    },
    {
        "block_id": "potential",
        "es_text": "Usa datos abiertos de NASA, listo para conectarse con sensores europeos y canadienses.",
        "tts_text": "Usa datos abiertos de NASA, listo para conectarse con sensores europeos y canadienses.",
        "en_sub": "Built on open NASA data, ready for European and Canadian orbital sensors.",
    },
    {
        "block_id": "endcard",
        "es_text": "Pulse-0G: decisiones de salud trazables.",
        "tts_text": "Pulse cero G: decisiones de salud trazables.",
        "en_sub": "Pulse-0G: traceable health decisions.",
    },
]


def run_cmd(cmd: list[str]) -> None:
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(
            f"Command failed ({res.returncode}): {' '.join(cmd)}\n"
            f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
        )


def read_mono(path: Path) -> np.ndarray:
    wav, sr = sf.read(str(path), dtype="float32")
    if wav.ndim > 1:
        wav = np.mean(wav, axis=1)
    if sr != SR:
        raise ValueError(f"Expected {SR} Hz in {path}, got {sr}")
    return wav


def read_stereo(path: Path) -> np.ndarray:
    wav, sr = sf.read(str(path), dtype="float32")
    if sr != SR:
        raise ValueError(f"Expected {SR} Hz in {path}, got {sr}")
    if wav.ndim == 1:
        wav = np.stack([wav, wav], axis=1)
    return wav


def trim_mono(wav: np.ndarray, thresh_db: float = -42.0, pad_s: float = 0.025) -> np.ndarray:
    peak = float(np.max(np.abs(wav))) if wav.size else 0.0
    if peak < 1e-6:
        return wav
    thresh = (10.0 ** (thresh_db / 20.0)) * peak
    idx = np.where(np.abs(wav) > thresh)[0]
    if len(idx) == 0:
        return wav
    pad = int(round(pad_s * SR))
    s = max(0, int(idx[0]) - pad)
    e = min(len(wav), int(idx[-1]) + pad)
    out = wav[s:e].copy()
    fade = min(int(0.015 * SR), len(out) // 4)
    if fade > 0:
        out[:fade] *= np.linspace(0.0, 1.0, fade, dtype=np.float32)
        out[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)
    return out


def generate_tts_stems(stems_dir: Path, reuse_stems: bool) -> list[dict[str, Any]]:
    stems_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = stems_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = stems_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps([{"block_id": x["block_id"], "tts_text": x["tts_text"]} for x in SCRIPT_LINES], indent=2),
        encoding="utf-8",
    )

    expected = [raw_dir / f"{x['block_id']}.wav" for x in SCRIPT_LINES]
    if not (reuse_stems and all(p.exists() for p in expected)):
        print("Running Qwen3-TTS CUDA worker...")
        run_cmd([
            str(VENV_CUDA_PY),
            str(TTS_WORKER),
            "--manifest",
            str(manifest_path),
            "--anchor",
            str(ANCHOR_WAV),
            "--out-dir",
            str(raw_dir),
        ])
    else:
        print("Reusing cached raw Qwen3-TTS stems...")

    out = []
    for item in SCRIPT_LINES:
        raw_p = raw_dir / f"{item['block_id']}.wav"
        wav, sr = sf.read(str(raw_p), dtype="float32")
        if wav.ndim > 1:
            wav = np.mean(wav, axis=1)
        out.append({**item, "raw_wav": str(raw_p), "raw_dur": len(wav) / sr})
    return out


def process_voice_stem(in_wav: Path, out_wav: Path, tempo: float) -> float:
    """Apply subtle brisk tempo adjustment + studio vocal clarity EQ & leveling at 48 kHz."""
    af_parts = []
    if abs(tempo - 1.0) > 1e-3:
        af_parts.append(f"atempo={tempo:.4f}")
    af_parts.extend([
        "highpass=f=85",
        "equalizer=f=240:t=q:w=1.2:g=-1.5",
        "equalizer=f=3200:t=q:w=1.4:g=2.0",
        "acompressor=threshold=-20dB:ratio=2.4:attack=15:release=160:makeup=1.5",
        f"aresample={SR}",
    ])
    run_cmd([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(in_wav),
        "-af", ",".join(af_parts),
        "-c:a", "pcm_f32le", "-ar", str(SR), "-ac", "1",
        str(out_wav),
    ])
    trimmed = trim_mono(read_mono(out_wav), thresh_db=-40.0, pad_s=0.02)
    sf.write(str(out_wav), trimmed, SR, subtype="FLOAT")
    return len(trimmed) / SR


def detect_pauses(wav: np.ndarray, min_pause_s: float = 0.085, rel_thresh: float = 0.045) -> list[tuple[float, float]]:
    """Return list of (start_s, end_s) internal quiet pauses in a mono speech clip."""
    win = int(0.020 * SR)
    hop = int(0.010 * SR)
    if len(wav) < win * 2:
        return []
    n_frames = 1 + (len(wav) - win) // hop
    rms = np.empty(n_frames, dtype=np.float32)
    for i in range(n_frames):
        seg = wav[i * hop : i * hop + win]
        rms[i] = float(np.sqrt(np.mean(seg * seg) + 1e-12))
    ref = float(np.percentile(rms, 92))
    quiet = rms < (ref * rel_thresh)
    pauses = []
    in_q = False
    s_idx = 0
    for i, q in enumerate(quiet):
        if q and not in_q:
            in_q = True
            s_idx = i
        elif not q and in_q:
            in_q = False
            dur = (i - s_idx) * hop / SR
            t0 = (s_idx * hop) / SR
            t1 = (i * hop) / SR
            if dur >= min_pause_s and t0 > 0.25 and t1 < (len(wav) / SR - 0.15):
                pauses.append((t0, t1))
    return pauses


def render_earshot_bank(sfx_dir: Path) -> dict[str, Path]:
    """Render all required SFX presets and C-minor musical kalimba notes via `earshot sfx`."""
    sfx_dir.mkdir(parents=True, exist_ok=True)
    specs = [
        ("whoosh_short", "fit/whoosh.short/bamboo_swish", ["--dur", "0.36", "--peak", "-3"]),
        ("swipe_glide", "swipe/glide", ["--dur", "0.44", "--apex", "0.14", "--peak", "-3"]),
        ("whoosh_swell", "whoosh_big/swell", ["--dur", "0.62", "--apex", "0.22", "--peak", "-3"]),
        ("click_floss", "fit/click/floss_lid", ["--peak", "-3"]),
        ("land_phone", "fit/land.light/finger_phone", ["--peak", "-3"]),
        ("pop_round", "pro_pop_in/round", ["--peak", "-3"]),
        ("snap_flip", "fit/snap/switch_flip", ["--peak", "-3"]),
        ("key_lubed", "fit/key/lubed", ["--peak", "-3"]),
        ("thock_space", "fit/key.space/thock_space", ["--peak", "-3"]),
        ("glitch_sparse", "pro_glitch/sparse", ["--dur", "0.24", "--peak", "-3"]),
        ("hit_tok", "fit/hit/bamboo_tok", ["--peak", "-3"]),
        ("sub_drop", "pro_sub_drop/soft", ["--dur", "0.75", "--peak", "-3"]),
        ("impact_deep", "pro_impact/deep", ["--dur", "1.30", "--peak", "-3"]),
    ]
    paths: dict[str, Path] = {}
    for key, sound_id, extra in specs:
        out = sfx_dir / f"{key}.wav"
        if not out.exists():
            run_cmd([str(EARSHOT_BIN), "sfx", "render", sound_id, "-o", str(out), "--sr", str(SR), *extra])
        paths[key] = out

    # Musical C minor / Dorian notes using organic kalimba_soft & kalimba_ring (long natural decay)
    notes = ["C3", "D3", "Eb3", "F3", "G3", "Ab3", "Bb3", "C4", "D4", "Eb4", "F4", "G4", "Ab4", "Bb4"]
    for note in notes:
        key = f"kal_{note}"
        out = sfx_dir / f"{key}.wav"
        if not out.exists():
            run_cmd([
                str(EARSHOT_BIN), "sfx", "render", "pluck/kalimba_soft",
                "-o", str(out), "--sr", str(SR), "--pitch", note, "--dur", "2.6", "--peak", "-3",
            ])
        paths[key] = out

    for note in ["C3", "Ab3", "Eb3", "Bb3", "G3", "C4", "G4"]:
        key = f"kalr_{note}"
        out = sfx_dir / f"{key}.wav"
        if not out.exists():
            run_cmd([
                str(EARSHOT_BIN), "sfx", "render", "pluck/kalimba_ring",
                "-o", str(out), "--sr", str(SR), "--pitch", note, "--dur", "2.8", "--peak", "-3",
            ])
        paths[key] = out
    return paths


def place_stereo(
    canvas: np.ndarray,
    clip: np.ndarray,
    t_sec: float,
    gain_db: float,
    pan: float = 0.0,
) -> None:
    """Place mono or stereo clip into stereo canvas at t_sec with peak gain_db and pan [-1..+1]."""
    if clip.ndim == 2:
        mono = np.mean(clip, axis=1)
    else:
        mono = clip
    peak = float(np.max(np.abs(mono)))
    if peak < 1e-8:
        return
    scale = (10.0 ** (gain_db / 20.0)) / peak
    sig = mono * scale

    theta = (np.clip(pan, -1.0, 1.0) + 1.0) * (np.pi / 4.0)
    gl = float(np.cos(theta))
    gr = float(np.sin(theta))

    idx0 = int(round(t_sec * SR))
    if idx0 >= len(canvas):
        return
    src_start = max(0, -idx0)
    dst_start = max(0, idx0)
    n = min(len(sig) - src_start, len(canvas) - dst_start)
    if n <= 0:
        return
    chunk = sig[src_start : src_start + n]
    canvas[dst_start : dst_start + n, 0] += chunk * gl
    canvas[dst_start : dst_start + n, 1] += chunk * gr


def build_music_bed(
    cues: list[dict[str, Any]],
    total_sec: float,
    sfx_bank: dict[str, Path],
    out_wav: Path,
) -> Path:
    """Compose organic C-minor ambient underscore using earshot kalimba plucks, sub pulses & stereo bloom."""
    n_samples = int(round(total_sec * SR))
    kal_bus = np.zeros((n_samples, 2), dtype=np.float32)
    sub_bus = np.zeros((n_samples, 2), dtype=np.float32)

    sub_clip = read_mono(sfx_bank["impact_deep"])
    fade_atk = int(0.18 * SR)
    sub_pad = sub_clip.copy()
    sub_pad[:fade_atk] *= np.linspace(0.0, 1.0, fade_atk, dtype=np.float32)

    progression = [
        # (cue_idx, ring_bass_note, arpeggio_notes)
        (0, "C3", ["C4", "G3", "Eb4", "Bb3", "G4", "D4", "Eb4"]),
        (1, "Ab3", ["Ab3", "Eb4", "C4", "G4", "Eb4", "C4", "Ab3", "Bb3"]),
        (2, "Eb3", ["Eb4", "Bb3", "G4", "D4", "F4", "C4", "Ab4", "Eb4"]),
        (3, "Bb3", ["Bb3", "F4", "D4", "G4", "Eb4", "Bb3", "G4"]),
        (4, "C3", ["C4", "G3", "Eb4", "Bb4"]),
    ]

    beat = 0.68  # ~88 BPM calm forward pulse
    for idx, bass_note, arp in progression:
        c = cues[idx]
        s = c["block_start"]
        e = c["block_end"]

        place_stereo(kal_bus, read_mono(sfx_bank[f"kalr_{bass_note}"]), s + 0.05, gain_db=-10.0, pan=-0.18 if idx % 2 == 0 else 0.18)
        place_stereo(sub_bus, sub_pad, s + 0.04, gain_db=-12.5, pan=0.0)

        if idx == 4:
            # Resolve warm chord blooming gently right after "trazables."
            t_res = c["speech_end"] + 0.02
            place_stereo(sub_bus, sub_pad, t_res, gain_db=-13.0, pan=0.0)
            for k_i, (kind, note) in enumerate([("kalr", "C3"), ("kalr", "G3"), ("kalr", "C4"), ("kal", "Eb4"), ("kalr", "G4")]):
                clip = read_mono(sfx_bank[f"{kind}_{note}"])
                pan = -0.34 + 0.17 * k_i
                place_stereo(kal_bus, clip, t_res + k_i * 0.06, gain_db=-10.0 - k_i * 0.4, pan=pan)
            continue

        # Soft melodic stereo kalimba pattern across block (wide stereo L/R)
        t_cur = s + 0.22
        step_idx = 0
        while t_cur < e - 0.20:
            note = arp[step_idx % len(arp)]
            clip = read_mono(sfx_bank[f"kal_{note}"])
            pan = 0.68 if (step_idx % 2 == 0) else -0.66
            vel_db = -12.5 if (step_idx % 4 == 0) else -15.5
            place_stereo(kal_bus, clip, t_cur, gain_db=vel_db, pan=pan)
            t_cur += beat * (0.75 if step_idx % 3 == 1 else 1.0)
            step_idx += 1

    kal_raw = BUILD_DIR / "kal_raw.wav"
    kal_warm = BUILD_DIR / "kal_warm.wav"
    sub_raw = BUILD_DIR / "sub_raw.wav"
    sf.write(str(kal_raw), kal_bus, SR, subtype="FLOAT")
    sf.write(str(sub_raw), sub_bus, SR, subtype="FLOAT")

    # Warm stereo room reflections + gentle HF tame on kalimba so speech crispness leads
    run_cmd([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(kal_raw),
        "-af", "lowpass=f=2800,aecho=0.80:0.60:27|53|89:0.28|0.20|0.12",
        "-c:a", "pcm_f32le", "-ar", str(SR), "-ac", "2",
        str(kal_warm),
    ])
    kal_track = read_stereo(kal_warm)[:n_samples]

    # Soft low-pass on sub_bus for warm 30-160 Hz cinematic bed foundation
    sub_lp = BUILD_DIR / "sub_lp.wav"
    run_cmd([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(sub_raw),
        "-af", "lowpass=f=180",
        "-c:a", "pcm_f32le", "-ar", str(SR), "-ac", "2",
        str(sub_lp),
    ])
    sub_track = read_stereo(sub_lp)[:n_samples]

    # Haas stereo spread + M/S width polish on kalimba for warm wrap-around background bed
    haas_shift = int(0.019 * SR)
    kal_wide = kal_track.copy()
    kal_wide[haas_shift:, 1] = 0.72 * kal_track[haas_shift:, 1] + 0.35 * kal_track[:-haas_shift, 0]
    mid_k = 0.5 * (kal_wide[:, 0] + kal_wide[:, 1])
    side_k = 0.5 * (kal_wide[:, 0] - kal_wide[:, 1]) * 1.45
    kal_wide[:, 0] = mid_k + side_k
    kal_wide[:, 1] = mid_k - side_k

    bed = (kal_wide * 0.78) + (sub_track * 0.65)

    # Smooth fade-in (0.30s) and graceful outro fade-out (0.85s)
    fin = int(0.30 * SR)
    fout = int(0.85 * SR)
    bed[:fin] *= np.linspace(0.0, 1.0, fin, dtype=np.float32)[:, None]
    bed[-fout:] *= np.linspace(1.0, 0.0, fout, dtype=np.float32)[:, None]

    sf.write(str(out_wav), bed, SR, subtype="FLOAT")
    return out_wav


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reuse-stems", action="store_true", help="Reuse existing raw Qwen stems in /tmp/v3_audio_build")
    args = parser.parse_args()

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    sfx_dir = BUILD_DIR / "sfx"

    # 1. Generate raw voice stems via Qwen3-TTS GPU worker
    raw_items = generate_tts_stems(BUILD_DIR / "stems", reuse_stems=args.reuse_stems)

    # Measure trimmed speech sum accurately before computing subtle tempo so full outro ring is preserved
    trimmed_sum = 0.0
    for item in raw_items:
        w_raw, sr_raw = sf.read(item["raw_wav"], dtype="float32")
        if w_raw.ndim > 1:
            w_raw = np.mean(w_raw, axis=1)
        idx_act = np.where(np.abs(w_raw) > 0.012 * max(1e-6, float(np.max(np.abs(w_raw)))))[0]
        dur_act = (idx_act[-1] - idx_act[0]) / sr_raw if len(idx_act) else len(w_raw) / sr_raw
        trimmed_sum += dur_act + 0.04

    overhead = LEAD_PAD_SEC + (len(raw_items) - 1) * (GAP_AFTER_SPEECH + GAP_BEFORE_SPEECH) + OUTRO_RING_SEC
    target_speech_budget = 29.65 - overhead
    tempo = max(1.04, min(1.12, trimmed_sum / target_speech_budget))
    print(f"Trimmed stems sum={trimmed_sum:.2f}s -> using gentle studio tempo={tempo:.3f}x")

    proc_dir = BUILD_DIR / "proc"
    proc_dir.mkdir(parents=True, exist_ok=True)

    cues: list[dict[str, Any]] = []
    processed_clips: dict[str, np.ndarray] = {}
    t_cursor = 0.0

    for i, item in enumerate(raw_items):
        out_p = proc_dir / f"{item['block_id']}.wav"
        dur = process_voice_stem(Path(item["raw_wav"]), out_p, tempo=tempo)
        wav = read_mono(out_p)
        processed_clips[item["block_id"]] = wav

        block_start = round(t_cursor, 3)
        speech_start = round(t_cursor + (LEAD_PAD_SEC if i == 0 else GAP_BEFORE_SPEECH), 3)
        speech_end = round(speech_start + dur, 3)
        if i < len(raw_items) - 1:
            block_end = round(speech_end + GAP_AFTER_SPEECH, 3)
        else:
            block_end = round(min(MAX_TOTAL_SEC, speech_end + OUTRO_RING_SEC), 3)

        cues.append({
            "block_id": item["block_id"],
            "speech_start": speech_start,
            "speech_end": speech_end,
            "speech_dur": round(dur, 3),
            "block_start": block_start,
            "block_end": block_end,
            "es_text": item["es_text"],
            "en_sub": item["en_sub"],
        })
        t_cursor = block_end

    total_duration = cues[-1]["block_end"]
    print(f"Final timeline total duration: {total_duration:.3f}s")
    if total_duration > 30.0:
        raise RuntimeError(f"Duration {total_duration:.3f}s exceeds 30.0s cap!")

    # 2. Assemble voice track
    n_total = int(round(total_duration * SR))
    voice_bus = np.zeros((n_total, 2), dtype=np.float32)
    for c in cues:
        clip = processed_clips[c["block_id"]]
        place_stereo(voice_bus, clip, c["speech_start"], gain_db=-1.5, pan=0.0)

    voice_raw_p = BUILD_DIR / "voice_bus_raw.wav"
    voice_norm_p = BUILD_DIR / "voice_bus_norm.wav"
    sf.write(str(voice_raw_p), voice_bus, SR, subtype="FLOAT")
    # Clean broadcast dialogue target around -15.0 LUFS
    run_cmd([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(voice_raw_p),
        "-af", "loudnorm=I=-15.0:TP=-1.5:LRA=5.0",
        "-c:a", "pcm_f32le", "-ar", str(SR), "-ac", "2",
        str(voice_norm_p),
    ])

    # 3. Render all `earshot` SFX & place cleanly on exact clause gaps/transitions
    sfx_bank = render_earshot_bank(sfx_dir)
    sfx_bus = np.zeros((n_total, 2), dtype=np.float32)

    pauses_by_block = {bid: detect_pauses(wav) for bid, wav in processed_clips.items()}
    print("Detected internal pauses:", pauses_by_block)

    def clause_time(bid: str, fallback_frac: float, prefer_idx: int = 0) -> float:
        c = next(x for x in cues if x["block_id"] == bid)
        ps = pauses_by_block.get(bid, [])
        if ps and prefer_idx < len(ps):
            return c["speech_start"] + 0.5 * (ps[prefer_idx][0] + ps[prefer_idx][1])
        return c["speech_start"] + fallback_frac * c["speech_dur"]

    # Block 1 (problem): opening air whoosh + telemetry clicks
    place_stereo(sfx_bus, read_mono(sfx_bank["whoosh_short"]), 0.02, gain_db=-14.0, pan=-0.28)
    place_stereo(sfx_bus, read_mono(sfx_bank["click_floss"]), clause_time("problem", 0.52), gain_db=-16.5, pan=0.28)
    place_stereo(sfx_bus, read_mono(sfx_bank["land_phone"]), cues[0]["speech_end"] + 0.02, gain_db=-16.0, pan=-0.22)

    # Block 2 (solution): glide into BodyMap + baseline ring pop + action switch
    c_sol = cues[1]
    place_stereo(sfx_bus, read_mono(sfx_bank["swipe_glide"]), c_sol["block_start"] + 0.02, gain_db=-14.0, pan=-0.32)
    place_stereo(sfx_bus, read_mono(sfx_bank["pop_round"]), clause_time("solution", 0.52), gain_db=-15.5, pan=-0.25)
    place_stereo(sfx_bus, read_mono(sfx_bank["snap_flip"]), c_sol["speech_start"] + 0.72 * c_sol["speech_dur"], gain_db=-15.5, pan=0.30)

    # Block 3 (how): swell into dual-card + missing blank key + unverified red strikeout!
    c_how = cues[2]
    place_stereo(sfx_bus, read_mono(sfx_bank["whoosh_swell"]), c_how["block_start"] + 0.02, gain_db=-14.5, pan=0.30)
    t_hueco = clause_time("how", 0.62, prefer_idx=1 if len(pauses_by_block["how"]) > 1 else 0)
    place_stereo(sfx_bus, read_mono(sfx_bank["key_lubed"]), t_hueco, gain_db=-15.0, pan=-0.30)

    # Strikeout hits cleanly right in pause before/as "tacha el texto" finishes
    t_strike = clause_time("how", 0.78, prefer_idx=3 if len(pauses_by_block["how"]) > 3 else 0) + 0.14
    place_stereo(sfx_bus, read_mono(sfx_bank["glitch_sparse"]), t_strike, gain_db=-16.0, pan=0.34)
    place_stereo(sfx_bus, read_mono(sfx_bank["hit_tok"]), t_strike + 0.03, gain_db=-13.0, pan=0.22)
    place_stereo(sfx_bus, read_mono(sfx_bank["sub_drop"]), t_strike - 0.06, gain_db=-13.5, pan=0.0)

    # Block 4 (potential): orbital glide + ESA & CSA sensor connect pings
    c_pot = cues[3]
    place_stereo(sfx_bus, read_mono(sfx_bank["swipe_glide"]), c_pot["block_start"] + 0.02, gain_db=-14.0, pan=0.32)
    place_stereo(sfx_bus, read_mono(sfx_bank["pop_round"]), clause_time("potential", 0.50), gain_db=-15.0, pan=-0.30)
    place_stereo(sfx_bus, read_mono(sfx_bank["click_floss"]), clause_time("potential", 0.78, prefer_idx=1 if len(pauses_by_block["potential"]) > 1 else 0), gain_db=-16.0, pan=0.32)

    # Block 5 (endcard): tactile settle lock + subtle bamboo breath (musical resolve sits on kalimba bed)
    c_end = cues[4]
    place_stereo(sfx_bus, read_mono(sfx_bank["whoosh_short"]), c_end["block_start"] + 0.02, gain_db=-14.5, pan=-0.20)
    place_stereo(sfx_bus, read_mono(sfx_bank["thock_space"]), c_end["block_start"] + 0.16, gain_db=-17.5, pan=0.20)

    sfx_bus_p = BUILD_DIR / "sfx_bus.wav"
    sf.write(str(sfx_bus_p), sfx_bus, SR, subtype="FLOAT")

    # 4. Build ambient low-volume music bed
    music_raw_p = BUILD_DIR / "music_raw.wav"
    build_music_bed(cues, total_duration, sfx_bank, music_raw_p)

    # Normalize music bed around -24 LUFS, then sidechain-duck by voice to stay whisper-quiet behind dialogue
    music_norm_p = BUILD_DIR / "music_norm.wav"
    run_cmd([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(music_raw_p),
        "-af", "loudnorm=I=-23.5:TP=-4.0:LRA=5.0",
        "-c:a", "pcm_f32le", "-ar", str(SR), "-ac", "2",
        str(music_norm_p),
    ])

    # 5. Final mix via ffmpeg filter_complex: sidechain-duck music under voice + blend SFX + final limiter
    final_filter = (
        "[1:a]asplit=2[v_mix][v_key];"
        "[0:a][v_key]sidechaincompress=threshold=0.022:ratio=3.8:attack=55:release=420:makeup=1.0[m_ducked];"
        "[m_ducked]volume=0.82[m_bed];"
        "[v_mix][m_bed][2:a]amix=inputs=3:weights='1 1 1':normalize=0:duration=first,"
        f"atrim=0:{total_duration:.4f},"
        "alimiter=limit=0.89:attack=5:release=60"
    )
    run_cmd([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(music_norm_p),
        "-i", str(voice_norm_p),
        "-i", str(sfx_bus_p),
        "-filter_complex", final_filter,
        "-c:a", "pcm_s16le", "-ar", str(SR), "-ac", "2",
        str(OUT_WAV),
    ])

    timings_payload = {
        "voice": "Qwen3-TTS-12Hz-1.7B (VoiceDesign anchor + Base clone)",
        "rate": f"{tempo:.3f}x",
        "total_duration": total_duration,
        "audio_path": str(OUT_WAV),
        "cues": cues,
    }
    OUT_TIMINGS.write_text(json.dumps(timings_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT_WAV} and {OUT_TIMINGS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
