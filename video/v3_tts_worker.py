#!/usr/bin/env python3
"""
Qwen3-TTS voice generation worker for Pulse-0G V3 pitch audio.

Runs inside the isolated CUDA venv (`/home/gaspar_22/dev/crewcheck/venv/bin/python`)
so PyTorch 2.11 + qwen-tts do not conflict with system torch packages.

Outputs raw cloned 24 kHz WAV stems in the target directory plus durations JSON.
"""

from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path
import sys

import numpy as np
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel


ANCHOR_TEXT = (
    "En Marte no hay médico a bordo, y la Tierra tarda veintidós minutos en responder."
)
ANCHOR_INSTRUCT = (
    "Narrador profesional masculino de documental aeroespacial en español latinoamericano neutro. "
    "Hombre de 32 años, voz cálida, cercana y segura, dicción nítida y brillante, ritmo ágil y natural, "
    "micrófono de condensador de estudio cercano sin eco ni reverberación."
)
ANCHOR_SEED = 42
CLONE_SEED = 123


def trim_silence(wav: np.ndarray, sr: int, thresh_db: float = -42.0, pad_s: float = 0.04) -> np.ndarray:
    """Trim leading and trailing low-energy silence with soft padding."""
    arr = np.asarray(wav, dtype=np.float32)
    peak = float(np.max(np.abs(arr))) if arr.size else 0.0
    if peak < 1e-6:
        return arr
    thresh = (10.0 ** (thresh_db / 20.0)) * peak
    idx = np.where(np.abs(arr) > thresh)[0]
    if len(idx) == 0:
        return arr
    pad = int(round(pad_s * sr))
    start = max(0, int(idx[0]) - pad)
    end = min(len(arr), int(idx[-1]) + pad)
    return arr[start:end]


def ensure_anchor(anchor_path: Path, anchor_text: str) -> tuple[np.ndarray, int]:
    """Load locked voice anchor WAV or generate it reproducibly with VoiceDesign."""
    if anchor_path.exists():
        wav, sr = sf.read(str(anchor_path), dtype="float32")
        return wav, sr

    print(f"Generating anchor voice via VoiceDesign (seed={ANCHOR_SEED})...", file=sys.stderr)
    vd = Qwen3TTSModel.from_pretrained(
        "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
        device_map="cuda:0",
        dtype=torch.bfloat16,
    )
    torch.manual_seed(ANCHOR_SEED)
    wavs, sr = vd.generate_voice_design(
        text=anchor_text,
        language="Spanish",
        instruct=ANCHOR_INSTRUCT,
    )
    anchor_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(anchor_path), wavs[0], sr)

    del vd
    gc.collect()
    torch.cuda.empty_cache()
    return wavs[0], sr


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, help="JSON list of {block_id, tts_text}")
    parser.add_argument("--anchor", required=True, help="Path to voice anchor WAV")
    parser.add_argument("--out-dir", required=True, help="Directory for raw stem WAVs")
    args = parser.parse_args()

    items = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    anchor_path = Path(args.anchor)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    anchor_wav, anchor_sr = ensure_anchor(anchor_path, ANCHOR_TEXT)
    trimmed_anchor = trim_silence(anchor_wav, anchor_sr, pad_s=0.06)

    print("Loading Qwen/Qwen3-TTS-12Hz-1.7B-Base...", file=sys.stderr)
    base = Qwen3TTSModel.from_pretrained(
        "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
        device_map="cuda:0",
        dtype=torch.bfloat16,
    )
    clone_prompt = base.create_voice_clone_prompt(
        ref_audio=(trimmed_anchor, anchor_sr),
        ref_text=ANCHOR_TEXT,
    )

    results = []
    for item in items:
        block_id = item["block_id"]
        tts_text = item["tts_text"]
        out_wav = out_dir / f"{block_id}.wav"

        if block_id == "problem" and tts_text.strip() == ANCHOR_TEXT:
            wav = trim_silence(anchor_wav, anchor_sr, pad_s=0.04)
            sr = anchor_sr
        else:
            torch.manual_seed(CLONE_SEED)
            wavs, sr = base.generate_voice_clone(
                text=tts_text,
                language="Spanish",
                voice_clone_prompt=clone_prompt,
            )
            wav = trim_silence(wavs[0], sr, pad_s=0.04)

        sf.write(str(out_wav), wav, sr)
        dur = len(wav) / sr
        print(f"Stem {block_id}: {dur:.3f}s -> {out_wav}", file=sys.stderr)
        results.append({"block_id": block_id, "wav": str(out_wav), "sr": sr, "duration": dur})

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
