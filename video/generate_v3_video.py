"""Pulse-0G V3 Motion Graphics Renderer (1920x1080 & 1080x1920).

Visual Direction (aligned with design/system.md & app/globals.css):
- Graphite console surfaces (#0B0B0C, #101012, #17171A) & sharp 0-2px geometry
- NASA Pantone 286 blue (#0B3D91) & high-vis companion (#3B7BD4) for identity/links
- Warm Bone (#EDE9E2) & muted stone (#8C877E) for nominal state, typography & rules
- Signal Amber (#FFB020) and Alarm Red (#FF5347) strictly for attention/action
- Lexend variable typeface across all display, UI, and English subtitle copy
- Uses ONLY the BodyMap character silhouette from the app; all other frames
  are custom conceptual motion graphics synced to v3_timings.json.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from typing import Dict, List, Tuple

import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FPS = 30

# Pulse-0G Console Palette (Graphite + NASA Blue + Bone + Signal Accents)
BG = (11 / 255, 11 / 255, 12 / 255)          # #0B0B0C Graphite base
BG_BAND = (8 / 255, 8 / 255, 9 / 255)        # #080809 Deep graphite footer
SURFACE = (16 / 255, 16 / 255, 18 / 255)     # #101012 Graphite panel
SURFACE2 = (23 / 255, 23 / 255, 26 / 255)    # #17171A Elevated graphite
HAIR = (38 / 255, 38 / 255, 42 / 255)        # #26262A Fine structural rule
HAIR2 = (58 / 255, 58 / 255, 63 / 255)       # #3A3A3F 2px card/chip border
BONE = (237 / 255, 233 / 255, 226 / 255)     # #EDE9E2 Warm bone (primary + nominal)
BONE2 = (156 / 255, 150 / 255, 140 / 255)    # #9C968C Warm stone secondary
DIM = (85 / 255, 81 / 255, 74 / 255)         # #55514A Muted dim / no data
NASA = (11 / 255, 61 / 255, 145 / 255)       # #0B3D91 Pantone 286 NASA blue
NASA_HI = (59 / 255, 123 / 255, 212 / 255)   # #3B7BD4 High-visibility NASA blue
AMBER = (255 / 255, 176 / 255, 32 / 255)     # #FFB020 Attention
RED = (255 / 255, 83 / 255, 71 / 255)        # #FF5347 Action / Strike-out

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEXEND_PATH = os.path.join(BASE_DIR, "fonts", "Lexend-Variable.ttf")

FONTS = {
    "sans_extrabold": (LEXEND_PATH, b"ExtraBold"),
    "sans_bold": (LEXEND_PATH, b"Bold"),
    "sans_semibold": (LEXEND_PATH, b"SemiBold"),
    "sans_medium": (LEXEND_PATH, b"Medium"),
    "sans_regular": (LEXEND_PATH, b"Regular"),
    "mono_bold": ("/usr/share/fonts/TTF/MesloLGLNerdFontMono-Bold.ttf", None),
    "mono_regular": ("/usr/share/fonts/TTF/MesloLGLNerdFontMono-Regular.ttf", None),
    "mono_italic": ("/usr/share/fonts/TTF/MesloLGLNerdFontMono-Italic.ttf", None),
}

_FONT_CACHE: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}
_TEXT_CACHE: Dict[Tuple, Tuple[cairo.ImageSurface, np.ndarray, int, int]] = {}


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if v < lo else hi if v > hi else v


def ease_out_cubic(t: float) -> float:
    t = clamp(t)
    return 1.0 - (1.0 - t) ** 3


def ease_in_out_cubic(t: float) -> float:
    t = clamp(t)
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - ((-2.0 * t + 2.0) ** 3) / 2.0


def progress(t: float, t0: float, t1: float) -> float:
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return clamp((t - t0) / (t1 - t0))


def get_font(font_key: str, size: int) -> ImageFont.FreeTypeFont:
    key = (font_key, size)
    if key not in _FONT_CACHE:
        path, var_name = FONTS[font_key]
        if not os.path.exists(path):
            path = (
                "/usr/share/fonts/TTF/DejaVuSansMono-Bold.ttf"
                if "mono" in font_key
                else "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
            )
            var_name = None
        f = ImageFont.truetype(path, size)
        if var_name is not None:
            try:
                f.set_variation_by_name(var_name)
            except Exception:
                pass
        _FONT_CACHE[key] = f
    return _FONT_CACHE[key]


def rgb_tuple_255(c: Tuple[float, float, float]) -> Tuple[int, int, int]:
    return (int(round(c[0] * 255)), int(round(c[1] * 255)), int(round(c[2] * 255)))


def render_text_surface(
    text: str,
    font_key: str,
    size: int,
    color: Tuple[float, float, float],
    tracking: float = 0.0,
) -> Tuple[cairo.ImageSurface, np.ndarray, int, int]:
    """Render anti-aliased text via Pillow into a cached Cairo ARGB32 surface."""
    if not text:
        text = " "
    c255 = rgb_tuple_255(color)
    cache_key = (text, font_key, size, c255, round(tracking, 2))
    if cache_key in _TEXT_CACHE:
        return _TEXT_CACHE[cache_key]

    font = get_font(font_key, size)
    pad = max(8, size // 4)
    if tracking == 0.0:
        bbox = font.getbbox(text)
        tw = max(1, bbox[2] - bbox[0])
        th = max(1, bbox[3] - bbox[1])
        ox = -bbox[0] + pad
        oy = -bbox[1] + pad
        img = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((ox, oy), text, font=font, fill=(c255[0], c255[1], c255[2], 255))
    else:
        advances = [font.getlength(ch) + tracking for ch in text]
        total_w = max(1, int(math.ceil(sum(advances))))
        ascent, descent = font.getmetrics()
        total_h = max(1, ascent + descent)
        img = Image.new("RGBA", (total_w + pad * 2, total_h + pad * 2), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx = float(pad)
        for ch, adv in zip(text, advances):
            draw.text((cx, pad), ch, font=font, fill=(c255[0], c255[1], c255[2], 255))
            cx += adv

    arr = np.array(img, dtype=np.uint8)
    alpha_mask = arr[..., 3] > 0
    if np.any(alpha_mask):
        ys, xs = np.where(alpha_mask)
        arr = arr[
            max(0, int(ys.min()) - 2) : min(arr.shape[0], int(ys.max()) + 3),
            max(0, int(xs.min()) - 2) : min(arr.shape[1], int(xs.max()) + 3),
        ]
    else:
        arr = arr[:4, :4]

    h_px, w_px = arr.shape[:2]
    a = arr[..., 3:4].astype(np.float32) / 255.0
    rgb = (arr[..., :3].astype(np.float32) * a + 0.5).astype(np.uint8)
    bgra = np.empty((h_px, w_px, 4), dtype=np.uint8)
    bgra[..., 0] = rgb[..., 2]
    bgra[..., 1] = rgb[..., 1]
    bgra[..., 2] = rgb[..., 0]
    bgra[..., 3] = arr[..., 3]
    buf = np.ascontiguousarray(bgra)
    surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, w_px, h_px, w_px * 4)
    val = (surf, buf, w_px, h_px)
    _TEXT_CACHE[cache_key] = val
    return val


def draw_text(
    ctx: cairo.Context,
    text: str,
    x: float,
    y: float,
    font_key: str,
    size: int,
    color: Tuple[float, float, float],
    alpha: float = 1.0,
    anchor: str = "tl",
    tracking: float = 0.0,
) -> Tuple[int, int]:
    if alpha <= 0.005 or not text:
        return (0, 0)
    surf, _buf, tw, th = render_text_surface(text, font_key, size, color, tracking=tracking)
    dx, dy = x, y
    if anchor[1] == "c":
        dx -= tw / 2.0
    elif anchor[1] == "r":
        dx -= tw
    if anchor[0] == "c":
        dy -= th / 2.0
    elif anchor[0] == "b":
        dy -= th

    ctx.save()
    ctx.set_source_surface(surf, dx, dy)
    if alpha >= 0.999:
        ctx.paint()
    else:
        ctx.paint_with_alpha(clamp(alpha))
    ctx.restore()
    return (tw, th)


def wrap_lines(text: str, font_key: str, size: int, max_width: float) -> List[str]:
    font = get_font(font_key, size)
    words = text.split()
    lines: List[str] = []
    cur: List[str] = []
    for w in words:
        cand = " ".join(cur + [w])
        if cur and font.getlength(cand) > max_width:
            lines.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    return lines


def draw_rounded_rect(ctx: cairo.Context, x: float, y: float, w: float, h: float, r: float) -> None:
    if r <= 0.5:
        ctx.rectangle(x, y, w, h)
        return
    r = min(r, w / 2.0, h / 2.0)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def draw_console_card(
    ctx: cairo.Context,
    x: float,
    y: float,
    w: float,
    h: float,
    border_color: Tuple[float, float, float] = HAIR2,
    border_alpha: float = 1.0,
    fill_color: Tuple[float, float, float] = SURFACE,
    fill_alpha: float = 1.0,
    lw: float = 2.0,
    shadow: bool = False,
    top_accent: Tuple[float, float, float] | None = None,
) -> None:
    """Sharp-edged mission console card (radius=0 per design/system.md)."""
    ctx.save()
    if shadow:
        ctx.set_source_rgba(0.0, 0.0, 0.0, 0.90 * fill_alpha)
        ctx.rectangle(x + 7, y + 7, w, h)
        ctx.fill()

    ctx.rectangle(x, y, w, h)
    ctx.set_source_rgba(fill_color[0], fill_color[1], fill_color[2], fill_alpha)
    ctx.fill_preserve()
    ctx.set_source_rgba(border_color[0], border_color[1], border_color[2], border_alpha)
    ctx.set_line_width(lw)
    ctx.stroke()

    if top_accent is not None:
        ctx.set_source_rgba(top_accent[0], top_accent[1], top_accent[2], border_alpha)
        ctx.rectangle(x, y, w, 3.5)
        ctx.fill()
    ctx.restore()


def draw_chip(
    ctx: cairo.Context,
    x: float,
    y: float,
    label: str,
    border_color: Tuple[float, float, float],
    text_color: Tuple[float, float, float] | None = None,
    fill_color: Tuple[float, float, float] = SURFACE2,
    alpha: float = 1.0,
    anchor: str = "tl",
    font_size: int = 16,
    px: int = 14,
    py: int = 7,
) -> Tuple[float, float]:
    """Square-cornered console chip matching .chip in app/globals.css."""
    t_col = text_color if text_color is not None else border_color
    surf, _buf, tw, th = render_text_surface(label, "mono_bold", font_size, t_col, tracking=1.4)
    bw = tw + px * 2
    bh = th + py * 2
    dx, dy = x, y
    if anchor[1] == "c":
        dx -= bw / 2.0
    elif anchor[1] == "r":
        dx -= bw
    if anchor[0] == "c":
        dy -= bh / 2.0
    elif anchor[0] == "b":
        dy -= bh

    ctx.save()
    ctx.rectangle(dx, dy, bw, bh)
    ctx.set_source_rgba(fill_color[0], fill_color[1], fill_color[2], 0.96 * alpha)
    ctx.fill_preserve()
    ctx.set_source_rgba(border_color[0], border_color[1], border_color[2], 0.90 * alpha)
    ctx.set_line_width(2.0)
    ctx.stroke()
    ctx.set_source_surface(surf, dx + px, dy + py)
    ctx.paint_with_alpha(alpha)
    ctx.restore()
    return (bw, bh)


def draw_crosshair_grid(ctx: cairo.Context, W: int, stage_h: int, alpha: float = 0.45) -> None:
    xs = [int(W * 0.18), int(W * 0.50), int(W * 0.82)]
    ys = [int(stage_h * 0.22), int(stage_h * 0.52), int(stage_h * 0.82)]
    ctx.save()
    ctx.set_source_rgba(HAIR[0], HAIR[1], HAIR[2], 0.80 * alpha)
    ctx.set_line_width(1.0)
    for x in xs:
        ctx.move_to(x, 0)
        ctx.line_to(x, stage_h)
    for y in ys:
        ctx.move_to(0, y)
        ctx.line_to(W, y)
    ctx.stroke()

    ctx.set_source_rgba(BONE2[0], BONE2[1], BONE2[2], 0.30 * alpha)
    ctx.set_line_width(1.2)
    for x in xs:
        for y in ys:
            ctx.move_to(x - 6, y)
            ctx.line_to(x + 6, y)
            ctx.move_to(x, y - 6)
            ctx.line_to(x, y + 6)
    ctx.stroke()
    ctx.restore()


def draw_header_bar(
    ctx: cairo.Context,
    W: int,
    pad_x: float,
    left_label: str,
    right_chip: str,
    right_col: Tuple[float, float, float] = NASA_HI,
    right_fill: Tuple[float, float, float] = NASA,
    alpha: float = 1.0,
) -> float:
    """Mission console header with 3px NASA-blue underline (from app/globals.css)."""
    bar_h = 68
    ctx.save()
    ctx.set_source_rgba(SURFACE[0], SURFACE[1], SURFACE[2], alpha)
    ctx.rectangle(0, 0, W, bar_h)
    ctx.fill()
    ctx.set_source_rgba(NASA_HI[0], NASA_HI[1], NASA_HI[2], alpha)
    ctx.rectangle(0, bar_h - 3.0, W, 3.0)
    ctx.fill()
    ctx.restore()

    draw_text(ctx, left_label, pad_x, bar_h / 2.0, "mono_bold", 19, BONE, alpha=alpha, anchor="cl", tracking=1.6)
    draw_chip(
        ctx,
        W - pad_x,
        bar_h / 2.0,
        right_chip,
        border_color=right_col,
        text_color=BONE,
        fill_color=right_fill,
        alpha=alpha,
        anchor="cr",
        font_size=14,
        px=12,
        py=6,
    )
    return float(bar_h)


def draw_pulse_mark(ctx: cairo.Context, cx: float, cy: float, radius: float, alpha: float = 1.0) -> None:
    """Hexagonal NASA-blue console mark with crisp Bone pulse trace."""
    if alpha <= 0.01:
        return
    ctx.save()
    for idx in range(6):
        ang = math.radians(idx * 60 - 90)
        px = cx + radius * math.cos(ang)
        py = cy + radius * math.sin(ang)
        ctx.move_to(px, py) if idx == 0 else ctx.line_to(px, py)
    ctx.close_path()
    ctx.set_source_rgba(NASA[0], NASA[1], NASA[2], 0.42 * alpha)
    ctx.fill_preserve()
    ctx.set_source_rgba(NASA_HI[0], NASA_HI[1], NASA_HI[2], 0.95 * alpha)
    ctx.set_line_width(2.8)
    ctx.stroke()

    pts = [
        (-0.56, 0.0),
        (-0.24, 0.0),
        (-0.12, -0.34),
        (0.05, 0.38),
        (0.20, -0.18),
        (0.32, 0.0),
        (0.56, 0.0),
    ]
    ctx.new_sub_path()
    for i, (dx, dy) in enumerate(pts):
        x, y = cx + dx * radius, cy + dy * radius
        ctx.move_to(x, y) if i == 0 else ctx.line_to(x, y)
    ctx.set_source_rgba(BONE[0], BONE[1], BONE[2], 0.98 * alpha)
    ctx.set_line_width(3.2)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()
    ctx.restore()


def draw_body_silhouette(
    ctx: cairo.Context,
    cx: float,
    cy: float,
    scale: float,
    alert_p: float,
    alpha: float = 1.0,
) -> Tuple[float, float]:
    """Program's BodyMap silhouette styled directly from app/globals.css:
    - Nominal (legs, arms, pre-alert head): Graphite Surface-2 fill + Warm Bone stroke
    - Attention (thorax): Amber tint + Amber stroke
    - Action (head alert): Red tint + Red stroke
    - Eyes (no_data): Transparent + Dim dashed stroke
    """
    ctx.save()
    ctx.translate(cx - 100 * scale, cy - 200 * scale)
    ctx.scale(scale, scale)

    def fill_stroke(fill_col, fill_a, stroke_col, lw=1.6, dash=False):
        if fill_a > 0.01:
            ctx.set_source_rgba(fill_col[0], fill_col[1], fill_col[2], fill_a * alpha)
            ctx.fill_preserve()
        ctx.set_source_rgba(stroke_col[0], stroke_col[1], stroke_col[2], alpha)
        ctx.set_line_width(lw)
        ctx.set_dash([4.0, 3.0] if dash else [])
        ctx.stroke()

    # Legs (nominal = graphite surface-2 + bone stroke)
    for rx, ry, rw, rh, rr in [
        (82, 165, 36, 30, 8),
        (82, 191, 16, 178, 8),
        (102, 191, 16, 178, 8),
        (72, 367, 24, 11, 5),
        (104, 367, 24, 11, 5),
    ]:
        draw_rounded_rect(ctx, rx, ry, rw, rh, rr)
        fill_stroke(SURFACE2, 1.0, BONE, 1.45)

    # Thorax (amber attention)
    amb_fill = (
        SURFACE2[0] * 0.84 + AMBER[0] * 0.16,
        SURFACE2[1] * 0.84 + AMBER[1] * 0.16,
        SURFACE2[2] * 0.84 + AMBER[2] * 0.16,
    )
    ctx.new_sub_path()
    ctx.move_to(70, 104)
    ctx.curve_to(70, 94, 79, 88, 90, 88)
    ctx.line_to(110, 88)
    ctx.curve_to(121, 88, 130, 94, 130, 104)
    ctx.line_to(128, 146)
    ctx.curve_to(128, 158, 122, 165, 114, 167)
    ctx.line_to(86, 167)
    ctx.curve_to(78, 165, 72, 158, 72, 146)
    ctx.close_path()
    fill_stroke(amb_fill, 1.0, AMBER, 1.55)

    # Arms (measurement site = graphite surface-2 + bone stroke)
    for ax, ay, ang in [(131, 96, 7), (56, 96, -7)]:
        ctx.save()
        ctx.translate(ax + 6.5, ay)
        ctx.rotate(math.radians(ang))
        draw_rounded_rect(ctx, -6.5, 0, 13, 112, 6.5)
        ctx.restore()
        fill_stroke(SURFACE2, 1.0, BONE, 1.45)

    # Head transitions from nominal Bone to Action Red
    head_stroke = (
        BONE[0] * (1.0 - alert_p) + RED[0] * alert_p,
        BONE[1] * (1.0 - alert_p) + RED[1] * alert_p,
        BONE[2] * (1.0 - alert_p) + RED[2] * alert_p,
    )
    head_fill = (
        SURFACE2[0] * (1.0 - 0.20 * alert_p) + RED[0] * (0.20 * alert_p),
        SURFACE2[1] * (1.0 - 0.20 * alert_p) + RED[1] * (0.20 * alert_p),
        SURFACE2[2] * (1.0 - 0.20 * alert_p) + RED[2] * (0.20 * alert_p),
    )
    draw_rounded_rect(ctx, 92, 76, 16, 14, 5)
    fill_stroke(head_fill, 1.0, head_stroke, 1.6 + alert_p * 1.2)

    ctx.new_sub_path()
    ctx.arc(100, 54, 24, 0, 2 * math.pi)
    fill_stroke(head_fill, 1.0, head_stroke, 1.7 + alert_p * 1.5)

    # Eyes (no_data dashed dim)
    for ex in (92, 108):
        ctx.save()
        ctx.translate(ex, 50)
        ctx.scale(4.2, 2.8)
        ctx.new_sub_path()
        ctx.arc(0, 0, 1.0, 0, 2 * math.pi)
        ctx.restore()
        fill_stroke(BG, 0.0, DIM, 1.2, dash=True)

    ctx.restore()
    return (cx, cy - 146 * scale)


def draw_subtitle_band(
    ctx: cairo.Context,
    W: int,
    H: int,
    band_h: int,
    en_sub: str,
    t: float,
    total_dur: float,
    alpha: float = 1.0,
) -> None:
    """Dedicated graphite English subtitle footer with NASA-blue progress rule."""
    y0 = H - band_h
    is_vert = H > W
    ctx.save()
    ctx.set_source_rgb(BG_BAND[0], BG_BAND[1], BG_BAND[2])
    ctx.rectangle(0, y0, W, band_h)
    ctx.fill()

    ctx.set_source_rgba(HAIR2[0], HAIR2[1], HAIR2[2], 1.0)
    ctx.rectangle(0, y0, W, 2.0)
    ctx.fill()

    prog = clamp(t / max(total_dur, 0.1))
    ctx.set_source_rgba(NASA_HI[0], NASA_HI[1], NASA_HI[2], 0.90)
    ctx.rectangle(0, H - 5, W * prog, 5)
    ctx.fill()
    ctx.restore()

    if not en_sub or alpha <= 0.01:
        return

    font_size = 32 if is_vert else 29
    max_w = W - (110 if is_vert else 240)
    lines = wrap_lines(en_sub, "sans_medium", font_size, max_w)
    line_gap = 10
    total_th = len(lines) * (font_size + 6) + max(0, len(lines) - 1) * line_gap
    cy0 = y0 + (band_h - total_th) / 2.0 + (font_size + 4) / 2.0
    for i, ln in enumerate(lines):
        draw_text(
            ctx,
            ln,
            W / 2.0,
            cy0 + i * (font_size + line_gap),
            "sans_medium",
            font_size,
            BONE,
            alpha=alpha,
            anchor="cc",
        )


# ---------------------------------------------------------------------------
# Block 1: Problem — Mars 22-minute delay & no doctor on board
# ---------------------------------------------------------------------------
def render_block_problem(ctx: cairo.Context, W: int, H: int, band_h: int, u: float) -> None:
    stage_h = H - band_h
    is_vert = H > W
    draw_crosshair_grid(ctx, W, stage_h, alpha=0.40)

    p_nodes = ease_out_cubic(progress(u, 0.04, 0.28))
    p_arc = ease_out_cubic(progress(u, 0.14, 0.68))
    p_tags = ease_out_cubic(progress(u, 0.34, 0.72))

    draw_header_bar(
        ctx,
        W,
        64 if is_vert else 96,
        "PULSE-0G · MISIONES DE LARGA DURACIÓN",
        "TELEMETRÍA PROFUNDA",
        right_col=NASA_HI,
        right_fill=NASA,
        alpha=p_nodes,
    )

    if not is_vert:
        ex, ey = W * 0.23, stage_h * 0.45
        mx, my = W * 0.77, stage_h * 0.45
    else:
        ex, ey = W * 0.25, stage_h * 0.36
        mx, my = W * 0.75, stage_h * 0.36

    # Orbital telemetry link
    ctx.save()
    ctx.set_source_rgba(HAIR2[0], HAIR2[1], HAIR2[2], 0.9 * p_nodes)
    ctx.set_line_width(2.0)
    ctx.set_dash([8.0, 8.0])
    ctx.move_to(ex + 54, ey)
    ctx.line_to(mx - 54, my)
    ctx.stroke()

    sig_x = (ex + 58) + ((mx - 58) - (ex + 58)) * p_arc
    ctx.set_dash([])
    ctx.set_source_rgba(NASA_HI[0], NASA_HI[1], NASA_HI[2], 0.95 * p_nodes)
    ctx.set_line_width(3.5)
    ctx.move_to(ex + 58, ey)
    ctx.line_to(sig_x, ey)
    ctx.stroke()

    ctx.arc(sig_x, ey, 7.0, 0, 2 * math.pi)
    ctx.set_source_rgba(BONE[0], BONE[1], BONE[2], p_nodes)
    ctx.fill()
    ctx.restore()

    # Earth (NASA blue) & Mars (Red) nodes
    ctx.save()
    ctx.set_source_rgba(NASA[0], NASA[1], NASA[2], 0.48 * p_nodes)
    ctx.arc(ex, ey, 44, 0, 2 * math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgba(NASA_HI[0], NASA_HI[1], NASA_HI[2], 0.95 * p_nodes)
    ctx.set_line_width(2.6)
    ctx.stroke()

    ctx.set_source_rgba(RED[0], RED[1], RED[2], 0.16 * p_nodes)
    ctx.arc(mx, my, 40, 0, 2 * math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgba(RED[0], RED[1], RED[2], 0.95 * p_nodes)
    ctx.set_line_width(2.6)
    ctx.stroke()
    ctx.restore()

    draw_text(ctx, "TIERRA", ex, ey + 66, "mono_bold", 20, NASA_HI, alpha=p_nodes, anchor="tc", tracking=1.8)
    draw_text(ctx, "MARTE", mx, my + 66, "mono_bold", 20, RED, alpha=p_nodes, anchor="tc", tracking=1.8)

    delay_val = int(round(22 * ease_out_cubic(progress(u, 0.12, 0.56))))
    draw_text(
        ctx,
        f"{delay_val} MIN",
        W / 2.0,
        ey - (112 if not is_vert else 125),
        "mono_bold",
        78 if not is_vert else 72,
        BONE,
        alpha=p_nodes,
        anchor="cc",
    )
    draw_text(
        ctx,
        "RETARDO DE RESPUESTA",
        W / 2.0,
        ey - (48 if not is_vert else 60),
        "mono_bold",
        18,
        BONE2,
        alpha=p_nodes * 0.95,
        anchor="cc",
        tracking=1.8,
    )

    cy_card = stage_h * (0.72 if not is_vert else 0.65)
    if not is_vert:
        cw, ch = 480, 92
        gap = 36
        x1 = W / 2.0 - cw - gap / 2.0
        x2 = W / 2.0 + gap / 2.0
        draw_console_card(ctx, x1, cy_card, cw, ch, border_color=RED, border_alpha=0.85 * p_tags, fill_alpha=p_tags, shadow=True)
        draw_text(ctx, "■ SIN MÉDICO A BORDO", x1 + cw / 2.0, cy_card + ch / 2.0, "sans_bold", 25, BONE, alpha=p_tags, anchor="cc")

        draw_console_card(ctx, x2, cy_card, cw, ch, border_color=HAIR2, border_alpha=p_tags, fill_alpha=p_tags)
        draw_text(ctx, "Un número suelto no alcanza", x2 + cw / 2.0, cy_card + ch / 2.0, "sans_semibold", 24, BONE2, alpha=p_tags, anchor="cc")
    else:
        cw, ch = W - 128, 96
        x1 = 64
        draw_console_card(ctx, x1, cy_card, cw, ch, border_color=RED, border_alpha=0.85 * p_tags, fill_alpha=p_tags, shadow=True)
        draw_text(ctx, "■ SIN MÉDICO A BORDO", W / 2.0, cy_card + ch / 2.0, "sans_bold", 27, BONE, alpha=p_tags, anchor="cc")
        draw_console_card(ctx, x1, cy_card + ch + 24, cw, ch, border_color=HAIR2, border_alpha=p_tags, fill_alpha=p_tags)
        draw_text(ctx, "Un número suelto no alcanza", W / 2.0, cy_card + ch + 24 + ch / 2.0, "sans_semibold", 25, BONE2, alpha=p_tags, anchor="cc")


# ---------------------------------------------------------------------------
# Block 2: Solution — Program Body Character + Own Baseline -> Action
# ---------------------------------------------------------------------------
def render_block_solution(ctx: cairo.Context, W: int, H: int, band_h: int, u: float) -> None:
    stage_h = H - band_h
    is_vert = H > W
    draw_crosshair_grid(ctx, W, stage_h, alpha=0.40)

    p_in = ease_out_cubic(progress(u, 0.0, 0.22))
    alert_p = ease_in_out_cubic(progress(u, 0.28, 0.54))
    p_action = ease_out_cubic(progress(u, 0.52, 0.76))

    top_h = draw_header_bar(
        ctx,
        W,
        64 if is_vert else 96,
        "PULSE-0G · GUÍA DE DECISIÓN",
        "ESCENARIO SINTÉTICO",
        right_col=HAIR2,
        right_fill=SURFACE2,
        alpha=p_in,
    )

    if not is_vert:
        body_cx = W * 0.25
        body_cy = top_h + (stage_h - top_h) * 0.52
        draw_body_silhouette(ctx, body_cx, body_cy, scale=1.68, alert_p=alert_p, alpha=p_in)
        if alert_p > 0.15:
            ctx.save()
            ctx.set_source_rgba(RED[0], RED[1], RED[2], 0.55 * alert_p)
            ctx.set_line_width(2.2)
            ctx.arc(body_cx, body_cy - 146 * 1.68, 52 + 10 * math.sin(u * math.pi * 2), 0, 2 * math.pi)
            ctx.stroke()
            ctx.restore()

        rx = W * 0.43
        rw = W - rx - 96
        y1 = top_h + 62
        h1 = 175

        draw_console_card(ctx, rx, y1, rw, h1, border_color=HAIR2, border_alpha=p_in, fill_alpha=p_in, top_accent=NASA_HI)
        draw_text(ctx, "No compara solo contra una tabla general", rx + 32, y1 + 30, "sans_regular", 23, BONE2, alpha=p_in)
        draw_text(ctx, "Compara contra TU PROPIA HISTORIA", rx + 32, y1 + 68, "sans_extrabold", 31, BONE, alpha=p_in)

        bx0, bx1 = rx + 32, rx + rw - 32
        by_line = y1 + 134
        ctx.save()
        ctx.set_source_rgba(NASA_HI[0], NASA_HI[1], NASA_HI[2], 0.85 * p_in)
        ctx.set_line_width(2.4)
        ctx.set_dash([7.0, 5.0])
        ctx.move_to(bx0, by_line)
        ctx.line_to(bx1, by_line)
        ctx.stroke()
        ctx.set_dash([])

        dev_x = bx0 + (bx1 - bx0) * (0.25 + 0.60 * alert_p)
        dev_y = by_line + 20 * alert_p
        ctx.set_source_rgba(RED[0], RED[1], RED[2], 0.95 * p_in)
        ctx.set_line_width(3.8)
        ctx.move_to(bx0, by_line - 2)
        ctx.curve_to(bx0 + (bx1 - bx0) * 0.35, by_line, dev_x - 60, by_line + 4, dev_x, dev_y)
        ctx.stroke()
        ctx.arc(dev_x, dev_y, 7.5, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()
        draw_text(ctx, "TU BASE PREVIA", bx1, by_line - 24, "mono_bold", 14, NASA_HI, alpha=p_in * 0.95, anchor="br")

        y2 = y1 + h1 + 32
        h2 = 225
        draw_console_card(
            ctx,
            rx,
            y2,
            rw,
            h2,
            border_color=RED if alert_p > 0.4 else HAIR2,
            border_alpha=p_in * 0.95,
            lw=2.4,
            shadow=(alert_p > 0.4),
        )
        draw_chip(ctx, rx + 32, y2 + 26, "SIN DIAGNÓSTICO", border_color=HAIR2, text_color=BONE2, alpha=p_in, font_size=14)
        draw_chip(ctx, rx + rw - 32, y2 + 26, "▲ DESVÍO PERSONAL", border_color=RED, text_color=RED, alpha=alert_p, anchor="tr", font_size=14)

        draw_text(ctx, "Acción concreta para el tripulante", rx + 32, y2 + 90, "sans_bold", 29, BONE, alpha=p_action)
        ctx.save()
        ctx.set_source_rgba(RED[0], RED[1], RED[2], p_action)
        ctx.rectangle(rx + 32, y2 + 142, 5, 48)
        ctx.fill()
        ctx.restore()
        draw_text(ctx, "Qué hacer ahora  ·  Cuándo avisar a Tierra", rx + 52, y2 + 152, "sans_regular", 23, BONE2, alpha=p_action)
    else:
        body_cx = W / 2.0
        body_cy = top_h + (stage_h - top_h) * 0.31
        draw_body_silhouette(ctx, body_cx, body_cy, scale=1.50, alert_p=alert_p, alpha=p_in)
        if alert_p > 0.15:
            ctx.save()
            ctx.set_source_rgba(RED[0], RED[1], RED[2], 0.55 * alert_p)
            ctx.set_line_width(2.2)
            ctx.arc(body_cx, body_cy - 146 * 1.50, 48 + 10 * math.sin(u * math.pi * 2), 0, 2 * math.pi)
            ctx.stroke()
            ctx.restore()

        rx, rw = 64, W - 128
        y1 = stage_h * 0.58
        draw_console_card(ctx, rx, y1, rw, 190, border_color=HAIR2, border_alpha=p_in, fill_alpha=p_in, top_accent=NASA_HI)
        draw_text(ctx, "No usa solo una tabla general", rx + 28, y1 + 26, "sans_regular", 23, BONE2, alpha=p_in)
        draw_text(ctx, "Compara contra TU PROPIA HISTORIA", rx + 28, y1 + 66, "sans_extrabold", 33, BONE, alpha=p_in)
        draw_text(ctx, "TU BASE PREVIA  →  DESVÍO DETECTADO", rx + 28, y1 + 128, "mono_bold", 20, RED, alpha=alert_p)

        y2 = y1 + 215
        draw_console_card(ctx, rx, y2, rw, 175, border_color=RED, border_alpha=0.85 * p_action, fill_alpha=p_action, shadow=True)
        draw_chip(ctx, rx + 28, y2 + 24, "SIN DIAGNÓSTICO", border_color=HAIR2, text_color=BONE2, alpha=p_action, font_size=14)
        draw_text(ctx, "Guía tu acción concreta", rx + 28, y2 + 80, "sans_bold", 33, BONE, alpha=p_action)
        draw_text(ctx, "Qué hacer ahora · Cuándo escalar a Tierra", rx + 28, y2 + 128, "sans_regular", 22, BONE2, alpha=p_action)


# ---------------------------------------------------------------------------
# Block 3: How it works — Offline + Honest Gaps + Red Strike-out Verifier
# ---------------------------------------------------------------------------
def render_block_how(ctx: cairo.Context, W: int, H: int, band_h: int, u: float) -> None:
    stage_h = H - band_h
    is_vert = H > W
    draw_crosshair_grid(ctx, W, stage_h, alpha=0.40)

    p_top = ease_out_cubic(progress(u, 0.0, 0.22))
    p_gap = ease_out_cubic(progress(u, 0.12, 0.45))
    p_verif = ease_out_cubic(progress(u, 0.40, 0.60))
    strike_p = ease_in_out_cubic(progress(u, 0.65, 0.83))

    pad_x = 64 if is_vert else 96
    top_h = draw_header_bar(
        ctx,
        W,
        pad_x,
        "SIN INTERNET · CERO INVENCIÓN",
        "100 % DETERMINÍSTICO",
        right_col=NASA_HI,
        right_fill=NASA,
        alpha=p_top,
    )

    cw = W - pad_x * 2
    y_gap = top_h + (36 if not is_vert else 44)
    h_gap = 235 if not is_vert else 305
    draw_console_card(ctx, pad_x, y_gap, cw, h_gap, border_color=HAIR2, border_alpha=p_top)
    draw_text(ctx, "Si falta un dato, muestra el hueco real", pad_x + 32, y_gap + 28, "sans_bold", 27 if not is_vert else 29, BONE, alpha=p_top)
    draw_chip(ctx, pad_x + cw - 32, y_gap + 24, "NUNCA SE RELLENA CON CERO", border_color=AMBER, text_color=AMBER, alpha=p_gap, anchor="tr", font_size=14)

    gx0, gx1 = pad_x + 48, pad_x + cw - 48
    gy = y_gap + (148 if not is_vert else 188)
    gap_l = gx0 + (gx1 - gx0) * 0.44
    gap_r = gx0 + (gx1 - gx0) * 0.64

    ctx.save()
    ctx.set_source_rgba(BONE[0], BONE[1], BONE[2], 0.92 * p_gap)
    ctx.set_line_width(3.6)
    pts_left = [
        (gx0, gy + 12),
        (gx0 + (gap_l - gx0) * 0.35, gy - 14),
        (gx0 + (gap_l - gx0) * 0.72, gy + 6),
        (gap_l, gy - 8),
    ]
    for i, (px, py) in enumerate(pts_left):
        ctx.move_to(px, py) if i == 0 else ctx.line_to(px, py)
    ctx.stroke()

    pts_right = [
        (gap_r, gy + 10),
        (gap_r + (gx1 - gap_r) * 0.45, gy - 10),
        (gx1, gy + 4),
    ]
    for i, (px, py) in enumerate(pts_right):
        ctx.move_to(px, py) if i == 0 else ctx.line_to(px, py)
    ctx.stroke()

    ctx.rectangle(gap_l + 6, gy - 38, (gap_r - gap_l) - 12, 76)
    ctx.set_source_rgba(DIM[0], DIM[1], DIM[2], 0.22 * p_gap)
    ctx.fill_preserve()
    ctx.set_source_rgba(AMBER[0], AMBER[1], AMBER[2], 0.85 * p_gap)
    ctx.set_line_width(2.0)
    ctx.set_dash([6.0, 5.0])
    ctx.stroke()
    ctx.restore()
    draw_text(ctx, "HUECO REAL", (gap_l + gap_r) / 2.0, gy, "mono_bold", 17, AMBER, alpha=p_gap, anchor="cc")

    # Bottom half: Deterministic Claim Verifier + Dramatic Red Strike-out
    y_ver = y_gap + h_gap + 28
    h_ver = stage_h - y_ver - 34
    b_col = (
        HAIR2[0] * (1.0 - strike_p) + RED[0] * strike_p,
        HAIR2[1] * (1.0 - strike_p) + RED[1] * strike_p,
        HAIR2[2] * (1.0 - strike_p) + RED[2] * strike_p,
    )
    draw_console_card(
        ctx,
        pad_x,
        y_ver,
        cw,
        h_ver,
        border_color=b_col,
        border_alpha=p_verif,
        lw=2.4,
        shadow=(strike_p > 0.3),
        top_accent=NASA_HI if strike_p < 0.2 else RED,
    )
    draw_text(ctx, "VERIFICADOR DE AFIRMACIONES", pad_x + 32, y_ver + 28, "sans_bold", 25 if not is_vert else 27, BONE, alpha=p_verif)
    draw_chip(ctx, pad_x + cw - 32, y_ver + 24, "CADA FRASE CITADA", border_color=NASA_HI, text_color=BONE, fill_color=NASA, alpha=p_verif, anchor="tr", font_size=14)

    r1y = y_ver + (116 if not is_vert else 142)
    ctx.save()
    ctx.set_source_rgba(BONE[0], BONE[1], BONE[2], p_verif)
    ctx.rectangle(pad_x + 32, r1y - 7, 14, 14)
    ctx.fill()
    ctx.restore()
    draw_text(
        ctx,
        '"Desvío detectado contra tu propia base"' if not is_vert else '"Desvío contra tu base previa"',
        pad_x + 62,
        r1y,
        "mono_regular",
        24 if not is_vert else 23,
        BONE,
        alpha=p_verif,
        anchor="cl",
    )
    draw_chip(
        ctx,
        pad_x + cw - 32,
        r1y if not is_vert else r1y + 44,
        "✓ ANCLADA",
        border_color=BONE,
        text_color=BONE,
        alpha=p_verif,
        anchor="cr" if not is_vert else "tr",
        font_size=14,
    )

    div_y = r1y + (46 if not is_vert else 96)
    ctx.save()
    ctx.set_source_rgba(HAIR[0], HAIR[1], HAIR[2], 1.0 * p_verif)
    ctx.rectangle(pad_x + 32, div_y, cw - 64, 2.0)
    ctx.fill()
    ctx.restore()

    r2y = div_y + (56 if not is_vert else 64)
    bad_text = '"La recuperación del tripulante mejora"'
    bad_col = (
        BONE[0] * (1.0 - strike_p * 0.35) + RED[0] * (strike_p * 0.35),
        BONE[1] * (1.0 - strike_p) + RED[1] * strike_p,
        BONE[2] * (1.0 - strike_p) + RED[2] * strike_p,
    )
    ctx.save()
    ctx.set_source_rgba(RED[0], RED[1], RED[2], p_verif)
    ctx.rectangle(pad_x + 32, r2y - 7, 14, 14)
    ctx.fill()
    ctx.restore()
    tw, _th = draw_text(
        ctx,
        bad_text,
        pad_x + 62,
        r2y,
        "mono_bold",
        26 if not is_vert else 24,
        bad_col,
        alpha=p_verif,
        anchor="cl",
    )
    if strike_p > 0.02:
        ctx.save()
        ctx.set_source_rgba(RED[0], RED[1], RED[2], 0.98)
        ctx.set_line_width(4.5)
        ctx.move_to(pad_x + 56, r2y)
        ctx.line_to(pad_x + 68 + tw * strike_p, r2y)
        ctx.stroke()
        ctx.restore()
    draw_chip(
        ctx,
        pad_x + cw - 32,
        r2y if not is_vert else r2y + 84,
        "× TACHADA EN PANTALLA",
        border_color=RED,
        text_color=RED,
        alpha=max(0.15, strike_p),
        anchor="cr" if not is_vert else "tr",
        font_size=15,
    )

    draw_text(
        ctx,
        "motivo: sin respaldo en datos ni tarjetas de evidencia",
        pad_x + 62,
        r2y + 42,
        "mono_italic",
        19 if not is_vert else 18,
        RED,
        alpha=strike_p,
        anchor="cl",
    )


def _cubic_bezier(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
    mt = 1.0 - t
    return (mt ** 3) * p0 + 3.0 * (mt ** 2) * t * p1 + 3.0 * mt * (t ** 2) * p2 + (t ** 3) * p3


# ---------------------------------------------------------------------------
# Block 4: Potential — Open NASA Data + ESA & CSA Wearables Ecosystem
# ---------------------------------------------------------------------------
def render_block_potential(ctx: cairo.Context, W: int, H: int, band_h: int, u: float) -> None:
    stage_h = H - band_h
    is_vert = H > W
    draw_crosshair_grid(ctx, W, stage_h, alpha=0.40)

    p1 = ease_out_cubic(progress(u, 0.0, 0.25))
    p_flow = ease_out_cubic(progress(u, 0.20, 0.65))
    p_out = ease_out_cubic(progress(u, 0.45, 0.78))

    pad_x = 64 if is_vert else 96
    top_h = draw_header_bar(
        ctx,
        W,
        pad_x,
        "ECOSISTEMA Y POTENCIAL",
        "SIN HARDWARE PROPIO",
        right_col=NASA_HI,
        right_fill=NASA,
        alpha=p1,
    )

    sources = [
        ("NASA · DATOS ABIERTOS", "Estudios reales de vuelo", NASA_HI, True),
        ("CANADÁ (CSA) · BIO-MONITOR", "Camiseta biométrica continua", BONE, False),
        ("EUROPA (ESA) · EVERYWEAR", "Hub de salud de tripulación", BONE, False),
    ]

    if not is_vert:
        lx, lw, lh = 96, 480, 118
        ys = [top_h + 68, top_h + 230, top_h + 392]
        hub_cx, hub_cy = W * 0.56, top_h + (stage_h - top_h) * 0.50
        out_x, out_w, out_h = W - 460 - 96, 460, 220
        out_y = hub_cy - out_h / 2.0

        ctx.save()
        end_x = hub_cx - 64
        for idx, (_title, _sub, col, _acc) in enumerate(sources):
            sy = ys[idx] + lh / 2.0
            x0, y0 = lx + lw, sy
            x1, y1 = lx + lw + 100, sy
            x2, y2 = hub_cx - 135, hub_cy
            x3, y3 = end_x, hub_cy
            ctx.set_source_rgba(NASA_HI[0] if idx == 0 else BONE2[0], NASA_HI[1] if idx == 0 else BONE2[1], NASA_HI[2] if idx == 0 else BONE2[2], 0.55 * p_flow)
            ctx.set_line_width(2.4)
            ctx.move_to(x0, y0)
            ctx.curve_to(x1, y1, x2, y2, x3, y3)
            ctx.stroke()

            dot_t = (u * 1.4 + idx * 0.22) % 1.0
            dx = _cubic_bezier(x0, x1, x2, x3, dot_t)
            dy = _cubic_bezier(y0, y1, y2, y3, dot_t)
            ctx.arc(dx, dy, 5.5, 0, 2 * math.pi)
            ctx.set_source_rgba(col[0], col[1], col[2], p_flow)
            ctx.fill()

        ctx.set_source_rgba(NASA_HI[0], NASA_HI[1], NASA_HI[2], 0.85 * p_out)
        ctx.set_line_width(3.0)
        ctx.move_to(hub_cx + 64, hub_cy)
        ctx.line_to(out_x, hub_cy)
        ctx.stroke()
        ctx.restore()

        for idx, (title, sub, col, is_nasa) in enumerate(sources):
            cy = ys[idx]
            draw_console_card(
                ctx,
                lx,
                cy,
                lw,
                lh,
                border_color=NASA_HI if is_nasa else HAIR2,
                border_alpha=p1,
                fill_alpha=p1,
                top_accent=NASA_HI if is_nasa else BONE,
            )
            draw_text(ctx, title, lx + 28, cy + 32, "mono_bold", 20, col, alpha=p1)
            draw_text(ctx, sub, lx + 28, cy + 70, "sans_regular", 21, BONE2, alpha=p1)

        draw_pulse_mark(ctx, hub_cx, hub_cy, radius=58, alpha=p1)
        draw_text(ctx, "PULSE-0G", hub_cx, hub_cy + 84, "mono_bold", 20, BONE, alpha=p1, anchor="tc", tracking=1.6)
        draw_text(ctx, "Capa de interpretación", hub_cx, hub_cy + 112, "sans_regular", 18, BONE2, alpha=p1, anchor="tc")

        draw_console_card(ctx, out_x, out_y, out_w, out_h, border_color=NASA_HI, border_alpha=p_out, fill_alpha=p_out, lw=2.4, shadow=True, top_accent=NASA_HI)
        draw_chip(ctx, out_x + 28, out_y + 26, "ESPACIO PROFUNDO", border_color=NASA_HI, text_color=BONE, fill_color=NASA, alpha=p_out, font_size=14)
        draw_text(ctx, "Decisión trazable", out_x + 28, out_y + 88, "sans_extrabold", 30, BONE, alpha=p_out)
        draw_text(ctx, "+ Informe listo para Tierra", out_x + 28, out_y + 138, "sans_regular", 23, BONE2, alpha=p_out)
    else:
        cw = W - 128
        cx = 64
        ys = [top_h + 44, top_h + 206, top_h + 368]
        for idx, (title, sub, col, is_nasa) in enumerate(sources):
            cy = ys[idx]
            draw_console_card(
                ctx,
                cx,
                cy,
                cw,
                130,
                border_color=NASA_HI if is_nasa else HAIR2,
                border_alpha=p1,
                fill_alpha=p1,
                top_accent=NASA_HI if is_nasa else BONE,
            )
            draw_text(ctx, title, cx + 28, cy + 30, "mono_bold", 22, col, alpha=p1)
            draw_text(ctx, sub, cx + 28, cy + 74, "sans_regular", 23, BONE2, alpha=p1)

        hub_cx, hub_cy = W / 2.0, stage_h * 0.56
        ctx.save()
        ctx.set_source_rgba(NASA_HI[0], NASA_HI[1], NASA_HI[2], 0.80 * p_flow)
        ctx.set_line_width(3.0)
        ctx.move_to(hub_cx, ys[-1] + 130)
        ctx.line_to(hub_cx, hub_cy - 68)
        ctx.move_to(hub_cx, hub_cy + 114)
        ctx.line_to(hub_cx, stage_h * 0.72)
        ctx.stroke()
        ctx.restore()

        draw_pulse_mark(ctx, hub_cx, hub_cy, radius=62, alpha=p1)
        draw_text(ctx, "CAPA DE INTERPRETACIÓN", hub_cx, hub_cy + 78, "mono_bold", 19, BONE, alpha=p1, anchor="tc", tracking=1.4)

        oy = stage_h * 0.72
        draw_console_card(ctx, cx, oy, cw, 220, border_color=NASA_HI, border_alpha=p_out, fill_alpha=p_out, lw=2.4, shadow=True, top_accent=NASA_HI)
        draw_chip(ctx, cx + 28, oy + 26, "ESPACIO PROFUNDO", border_color=NASA_HI, text_color=BONE, fill_color=NASA, alpha=p_out, font_size=15)
        draw_text(ctx, "Decisión trazable", cx + 28, oy + 92, "sans_extrabold", 35, BONE, alpha=p_out)
        draw_text(ctx, "Listo para toda la tripulación + Tierra", cx + 28, oy + 148, "sans_regular", 23, BONE2, alpha=p_out)


# ---------------------------------------------------------------------------
# Block 5: Endcard
# ---------------------------------------------------------------------------
def render_block_endcard(ctx: cairo.Context, W: int, H: int, band_h: int, u: float) -> None:
    stage_h = H - band_h
    is_vert = H > W
    p = ease_out_cubic(progress(u, 0.0, 0.30))
    p2 = ease_out_cubic(progress(u, 0.22, 0.55))

    draw_crosshair_grid(ctx, W, stage_h, alpha=0.25)
    cy = stage_h / 2.0
    draw_pulse_mark(ctx, W / 2.0, cy - (115 if not is_vert else 140), radius=54 if not is_vert else 64, alpha=p)
    draw_text(ctx, "PULSE-0G", W / 2.0, cy + 4, "sans_extrabold", 76 if not is_vert else 84, BONE, alpha=p, anchor="cc", tracking=3.0)
    draw_text(ctx, "Decisiones de salud trazables · Sin diagnóstico", W / 2.0, cy + 82, "sans_regular", 26 if not is_vert else 28, BONE2, alpha=p2, anchor="cc")
    draw_chip(
        ctx,
        W / 2.0,
        stage_h - 52,
        "NASA SPACE APPS CHALLENGE 2026 · CÓRDOBA",
        border_color=NASA_HI,
        text_color=BONE,
        fill_color=NASA,
        alpha=p2 * 0.92,
        anchor="cc",
        font_size=15,
    )


# ---------------------------------------------------------------------------
# Master Frame & SRT Builder
# ---------------------------------------------------------------------------
def active_cue(cues: List[dict], t: float) -> Tuple[dict, float]:
    for c in cues:
        if t < c["block_end"]:
            span = max(0.01, c["block_end"] - c["block_start"])
            return c, clamp((t - c["block_start"]) / span)
    last = cues[-1]
    return last, 1.0


def active_subtitle(cues: List[dict], t: float) -> Tuple[str, float]:
    for c in cues:
        s0 = max(0.0, c["speech_start"] - 0.12)
        s1 = c["block_end"] - 0.06
        if s0 <= t <= s1:
            fade_in = progress(t, s0, s0 + 0.14)
            fade_out = 1.0 - progress(t, s1 - 0.14, s1)
            return c["en_sub"], min(fade_in, fade_out)
    return "", 0.0


def render_frame(surface: cairo.ImageSurface, W: int, H: int, frame_idx: int, meta: dict) -> None:
    t = frame_idx / FPS
    ctx = cairo.Context(surface)
    ctx.set_source_rgb(BG[0], BG[1], BG[2])
    ctx.paint()

    band_h = 210 if H > W else 140
    cue, u = active_cue(meta["cues"], t)
    bid = cue["block_id"]

    if bid == "problem":
        render_block_problem(ctx, W, H, band_h, u)
    elif bid == "solution":
        render_block_solution(ctx, W, H, band_h, u)
    elif bid == "how":
        render_block_how(ctx, W, H, band_h, u)
    elif bid == "potential":
        render_block_potential(ctx, W, H, band_h, u)
    else:
        render_block_endcard(ctx, W, H, band_h, u)

    sub_text, sub_alpha = active_subtitle(meta["cues"], t)
    draw_subtitle_band(ctx, W, H, band_h, sub_text, t, meta["total_duration"], alpha=sub_alpha)


def fmt_srt_time(sec: float) -> str:
    ms = int(round(max(0.0, sec) * 1000))
    hh = ms // 3600000
    mm = (ms % 3600000) // 60000
    ss = (ms % 60000) // 1000
    rem = ms % 1000
    return f"{hh:02d}:{mm:02d}:{ss:02d},{rem:03d}"


def write_english_srt(meta: dict, out_srt: str) -> None:
    lines: List[str] = []
    for idx, c in enumerate(meta["cues"], start=1):
        t0 = max(0.0, c["speech_start"] - 0.10)
        t1 = max(t0 + 0.5, c["block_end"] - 0.05)
        lines.append(f"{idx}")
        lines.append(f"{fmt_srt_time(t0)} --> {fmt_srt_time(t1)}")
        lines.append(c["en_sub"])
        lines.append("")
    with open(out_srt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {out_srt}")


def surface_to_rgb24(surface: cairo.ImageSurface, W: int, H: int) -> bytes:
    buf = np.frombuffer(surface.get_data(), dtype=np.uint8).reshape((H, W, 4))
    return buf[:, :, 2::-1].tobytes()


def encode_video(
    W: int,
    H: int,
    out_mp4: str,
    meta: dict,
    save_stills_dir: str | None = None,
) -> None:
    total_dur = meta["total_duration"]
    total_frames = int(math.ceil(total_dur * FPS))
    audio_path = meta["audio_path"]

    ffmpeg_cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
        out_mp4,
    ]
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)

    still_map = {}
    if save_stills_dir:
        prefix = "v3_vert_still_" if H > W else "v3_still_"
        for c in meta["cues"]:
            mid_t = c["block_start"] + (c["block_end"] - c["block_start"]) * 0.72
            if c["block_id"] == "how":
                mid_t = c["block_start"] + (c["block_end"] - c["block_start"]) * 0.86
            still_map[min(total_frames - 1, int(round(mid_t * FPS)))] = os.path.join(
                save_stills_dir, f"{prefix}{c['block_id']}.png"
            )

    for fidx in range(total_frames):
        render_frame(surface, W, H, fidx, meta)
        if fidx in still_map:
            surface.write_to_png(still_map[fidx])
        proc.stdin.write(surface_to_rgb24(surface, W, H))
        if fidx % 150 == 0 or fidx == total_frames - 1:
            print(f"[{W}x{H}] {fidx + 1}/{total_frames} ({(fidx + 1) / total_frames * 100:.0f}%)", flush=True)

    proc.stdin.close()
    ret = proc.wait()
    if ret != 0:
        raise RuntimeError(f"ffmpeg failed with exit code {ret}")
    print(f"Done: {out_mp4}")


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(base_dir)
    deliverables_dir = os.path.join(repo_root, "docs", "deliverables")
    os.makedirs(deliverables_dir, exist_ok=True)

    timings_path = os.path.join(base_dir, "v3_timings.json")
    if not os.path.exists(timings_path):
        raise FileNotFoundError(f"Missing {timings_path}. Run generate_v3_audio.py first.")
    with open(timings_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    write_english_srt(meta, os.path.join(deliverables_dir, "pulse_0g_v3_en.srt"))

    mode = sys.argv[1] if len(sys.argv) > 1 else "--all"
    if mode in ("--1080p", "--all"):
        encode_video(
            1920,
            1080,
            os.path.join(deliverables_dir, "pulse_0g_v3_1080p.mp4"),
            meta,
            save_stills_dir=base_dir,
        )
    if mode in ("--vertical", "--all"):
        encode_video(
            1080,
            1920,
            os.path.join(deliverables_dir, "pulse_0g_v3_vertical_1080x1920.mp4"),
            meta,
            save_stills_dir=base_dir,
        )


if __name__ == "__main__":
    main()
