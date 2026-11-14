# Pulse-0G Video Pipeline (V2)

Pipeline reproducible de motion graphics 2D (PyCairo + Pillow + NumPy + FFmpeg) para **Pulse-0G** (NASA Space Apps Challenge 2026), en **español** y en dos formatos nativos (`1920×1080` y `1080×1920`, 30 fps, 28.0 s, H.264 MP4).

## Requisitos

- Python 3 con `pycairo`, `Pillow`, `numpy`
- `ffmpeg`
- Fuentes del sistema en `/usr/share/fonts/TTF/`: `OpenSans-*.ttf` y `MesloLGLNerdFontMono-*.ttf`

## Regenerar

```bash
python3 video/generate_video.py --all
```

O por formato individual (`--1080p` o `--vertical`). Los entregables se escriben en `docs/deliverables/`:

- `pulse_0g_1080p.mp4` — Master horizontal `1920×1080`
- `pulse_0g_vertical_1080x1920.mp4` — Master vertical `1080×1920`
- `pulse_0g_es.srt` — Subtítulos en español
- `still_01_mapa_corporal.png`, `still_02_base_propia.png`, `still_03_verificador_tachado.png` — Cuadros clave

## Decisiones de dirección (V2)

- **Problema → Solución → Cómo queda** en 6 bloques en español.
- **Zoom real** sobre la UI vectorial del producto (≥60 % del cuadro), con banda inferior dedicada para leyendas.
- **Todo número con su objeto** (`2.9 h de sueño`, `−60 % contra tu propia base`, `base previa 7.3 h`) y cero código en pantalla.
- **Honestidad estricta:** rótulo `SINTÉTICO` visible, sin diagnóstico, 4 huecos reales sin interpolar en la serie y frase sin respaldo tachada en rojo en el Verificador durante >3 s.
