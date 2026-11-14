# Pulse-0G Video Pipeline

Reproducible 2D motion-graphics pipeline (PyCairo + Pillow + NumPy + FFmpeg) for the **Pulse-0G** NASA Space Apps Challenge 2026 pitch/launch video (`1920x1080`, `30 fps`, `23.0 s`, H.264 MP4).

## Requirements

- Python 3 with `pycairo`, `Pillow`, `numpy`
- `ffmpeg`
- System fonts in `/usr/share/fonts/TTF/`: `OpenSans-*.ttf` and `MesloLGLNerdFontMono-*.ttf`

## Regenerate

```bash
python3 video/generate_audio.py
python3 video/generate_video.py
```

Outputs are written to `docs/deliverables/`:

- `pulse_0g_1080p.mp4` — 1920x1080 H.264 master with procedural telemetry audio
- `pulse_0g_en.srt` — English subtitle track
- `still_01_baseline_metric.png`, `still_02_claim_struck.png`, `still_03_every_claim_traced.png` — keyframe stills

## Key Constraints Enforced

- Zero webpage screenshots, zero stock photos, zero 3D renders.
- Strict honesty rules: no diagnosis/disease prediction claims, explicit `SYNTHETIC` badges on demo scenario numbers, and only approved metrics (`2.9 h`, `-60%`, `4.3 / 10`, `76 / 600 mSv`, `2`, `4`, `7`, `19`).
