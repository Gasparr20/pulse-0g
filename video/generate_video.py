"""Pulse-0G V2 Motion Graphics Renderer (1920x1080 Landscape & 1080x1920 Vertical).

Combines the crisp typography, crosshair grid, and dry easing of the first
reference with the product-first zoom/follow grammar of V2:
- 100% Spanish copy explaining the problem, solution, and final state
- Zero code snippets on screen, zero dot clouds, zero repeated logos
- Dedicated bottom caption band (140px landscape / 220px vertical)
- Prominent zoomed product cards (>=60% frame), real gaps in sparkline,
  enlarged Claim Verifier with >=3s visible red strike-out, and explicit
  SINTÉTICO / NASA OSD-575 labeling.
"""

from __future__ import annotations

import math
import os
import subprocess
import sys
from typing import Dict, List, Tuple

import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FPS = 30
DURATION = 28.0
TOTAL_FRAMES = int(round(DURATION * FPS))  # 840 frames

# Exact Pulse-0G Palette
BG = (10 / 255, 14 / 255, 19 / 255)          # #0A0E13
BG_DEEP = (13 / 255, 19 / 255, 27 / 255)     # #0D131B
SURFACE = (18 / 255, 24 / 255, 33 / 255)     # #121821
SURFACE2 = (24 / 255, 33 / 255, 48 / 255)    # #182130
HAIR = (31 / 255, 41 / 255, 55 / 255)        # #1F2937
TEXT = (229 / 255, 231 / 255, 235 / 255)     # #E5E7EB
TEXT2 = (148 / 255, 163 / 255, 184 / 255)    # #94A3B8
GREEN = (52 / 255, 211 / 255, 153 / 255)     # #34D399
AMBER = (251 / 255, 191 / 255, 36 / 255)     # #FBBF24
RED = (248 / 255, 113 / 255, 113 / 255)      # #F87171
NODATA = (75 / 255, 85 / 255, 99 / 255)      # #4B5563
TEAL = (45 / 255, 212 / 255, 191 / 255)      # #2DD4BF
VIOLET = (167 / 255, 139 / 255, 250 / 255)   # #A78BFA
SLATE = (203 / 255, 213 / 255, 225 / 255)    # #CBD5E1 (measurement site)

FONTS = {
    "sans_extrabold": "/usr/share/fonts/TTF/OpenSans-ExtraBold.ttf",
    "sans_bold": "/usr/share/fonts/TTF/OpenSans-Bold.ttf",
    "sans_semibold": "/usr/share/fonts/TTF/OpenSans-SemiBold.ttf",
    "sans_regular": "/usr/share/fonts/TTF/OpenSans-Regular.ttf",
    "mono_bold": "/usr/share/fonts/TTF/MesloLGLNerdFontMono-Bold.ttf",
    "mono_regular": "/usr/share/fonts/TTF/MesloLGLNerdFontMono-Regular.ttf",
    "mono_italic": "/usr/share/fonts/TTF/MesloLGLNerdFontMono-Italic.ttf",
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
        _FONT_CACHE[key] = ImageFont.truetype(FONTS[font_key], size)
    return _FONT_CACHE[key]


def rgb_tuple_255(c: Tuple[float, float, float]) -> Tuple[int, int, int]:
    return (int(round(c[0] * 255)), int(round(c[1] * 255)), int(round(c[2] * 255)))


def render_text_surface(
    text: str,
    font_key: str,
    size: int,
    color: Tuple[float, float, float],
    tracking: float = 0.0,
    tight_y: bool = True,
) -> Tuple[cairo.ImageSurface, np.ndarray, int, int]:
    if not text:
        text = " "
    c255 = rgb_tuple_255(color)
    cache_key = (text, font_key, size, c255, round(tracking, 2), tight_y)
    if cache_key in _TEXT_CACHE:
        return _TEXT_CACHE[cache_key]

    font = get_font(font_key, size)
    pad = max(8, size // 5)

    if tracking == 0.0 and tight_y:
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
        y0 = max(0, int(ys.min()) - 2) if tight_y else 0
        y1 = min(arr.shape[0], int(ys.max()) + 3) if tight_y else arr.shape[0]
        x0 = max(0, int(xs.min()) - 2) if tight_y else pad
        x1 = min(arr.shape[1], int(xs.max()) + 3)
        if x1 <= x0:
            x1 = min(arr.shape[1], x0 + 4)
        arr = arr[y0:y1, x0:x1]
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
    tight_y: bool = True,
) -> Tuple[int, int]:
    if alpha <= 0.005 or not text:
        return (0, 0)
    surf, _buf, tw, th = render_text_surface(text, font_key, size, color, tracking=tracking, tight_y=tight_y)
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


def draw_rounded_rect(ctx: cairo.Context, x: float, y: float, w: float, h: float, r: float) -> None:
    r = min(r, w / 2.0, h / 2.0)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def draw_pill(
    ctx: cairo.Context,
    x: float,
    y: float,
    label: str,
    color: Tuple[float, float, float],
    alpha: float = 1.0,
    anchor: str = "tl",
    font_size: int = 18,
    px: int = 14,
    py: int = 7,
    fill_alpha: float = 0.14,
) -> Tuple[float, float]:
    surf, _buf, tw, th = render_text_surface(label, "mono_bold", font_size, color, tracking=1.2)
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
    draw_rounded_rect(ctx, dx, dy, bw, bh, 5.0)
    ctx.set_source_rgba(BG[0], BG[1], BG[2], 0.88 * alpha)
    ctx.fill_preserve()
    ctx.set_source_rgba(color[0], color[1], color[2], fill_alpha * alpha)
    ctx.fill_preserve()
    ctx.set_source_rgba(color[0], color[1], color[2], 0.62 * alpha)
    ctx.set_line_width(1.5)
    ctx.stroke()
    ctx.set_source_surface(surf, dx + px, dy + py)
    ctx.paint_with_alpha(alpha)
    ctx.restore()
    return (bw, bh)


def draw_crosshair_grid(ctx: cairo.Context, W: int, H: int, stage_h: int, alpha: float = 0.55) -> None:
    xs = [int(W * 0.18), int(W * 0.50), int(W * 0.82)]
    ys = [int(stage_h * 0.20), int(stage_h * 0.52), int(stage_h * 0.84)]
    ctx.save()
    ctx.set_source_rgba(HAIR[0] * 1.4, HAIR[1] * 1.4, HAIR[2] * 1.4, 0.48 * alpha)
    ctx.set_line_width(1.0)
    for x in xs:
        ctx.move_to(x, 0)
        ctx.line_to(x, stage_h)
    for y in ys:
        ctx.move_to(0, y)
        ctx.line_to(W, y)
    ctx.stroke()

    ctx.set_source_rgba(TEXT2[0], TEXT2[1], TEXT2[2], 0.42 * alpha)
    ctx.set_line_width(1.4)
    for x in xs:
        for y in ys:
            ctx.move_to(x - 6, y)
            ctx.line_to(x + 6, y)
            ctx.move_to(x, y - 6)
            ctx.line_to(x, y + 6)
    ctx.stroke()
    ctx.restore()


def draw_pulse_mark(
    ctx: cairo.Context,
    cx: float,
    cy: float,
    radius: float,
    alpha: float = 1.0,
) -> None:
    ctx.save()
    ctx.translate(cx, cy)
    pts = [(math.cos(math.radians(-90 + k * 60)) * radius, math.sin(math.radians(-90 + k * 60)) * radius) for k in range(6)]
    ctx.set_line_width(max(3.0, radius * 0.24))
    ctx.set_line_cap(cairo.LINE_CAP_BUTT)
    ctx.set_line_join(cairo.LINE_JOIN_MITER)
    ctx.set_source_rgba(TEXT[0], TEXT[1], TEXT[2], alpha)
    for start_idx in (0, 2, 4):
        p0, p1, p2 = pts[start_idx], pts[(start_idx + 1) % 6], pts[(start_idx + 2) % 6]
        a0 = (p0[0] * 0.86 + p1[0] * 0.14, p0[1] * 0.86 + p1[1] * 0.14)
        a2 = (p2[0] * 0.86 + p1[0] * 0.14, p2[1] * 0.86 + p1[1] * 0.14)
        ctx.move_to(*a0)
        ctx.line_to(*p1)
        ctx.line_to(*a2)
    ctx.stroke()

    ir = radius * 0.44
    ctx.set_line_width(max(2.0, radius * 0.085))
    ctx.set_source_rgba(TEAL[0], TEAL[1], TEAL[2], alpha)
    ctx.move_to(-ir * 0.95, 0)
    ctx.line_to(-ir * 0.42, 0)
    ctx.line_to(-ir * 0.18, -ir * 0.62)
    ctx.line_to(ir * 0.14, ir * 0.56)
    ctx.line_to(ir * 0.38, 0)
    ctx.line_to(ir * 0.95, 0)
    ctx.stroke()
    ctx.restore()


def draw_led_bar(
    ctx: cairo.Context,
    x: float,
    y: float,
    w: float,
    h: float,
    fill_ratio: float,
    color: Tuple[float, float, float],
    alpha: float = 1.0,
    cols: int = 36,
    rows: int = 3,
) -> None:
    ctx.save()
    cell_w = w / cols
    cell_h = h / rows
    dw = max(2.0, cell_w - max(2.0, cell_w * 0.28))
    dh = max(2.0, cell_h - max(1.5, cell_h * 0.28))
    lit = int(round(clamp(fill_ratio) * cols))
    for c in range(cols):
        a = (0.95 if c < lit else 0.14) * alpha
        ctx.set_source_rgba(color[0], color[1], color[2], a)
        for r in range(rows):
            ctx.rectangle(x + c * cell_w, y + r * cell_h, dw, dh)
    ctx.fill()
    ctx.restore()


def draw_caption_band(
    ctx: cairo.Context,
    W: int,
    H: int,
    band_h: int,
    headline: str,
    subline: str,
    alpha: float = 1.0,
    accent: Tuple[float, float, float] = TEAL,
) -> None:
    """Dedicated clean bottom band (Rule 2: never on top of the UI)."""
    y_top = H - band_h
    ctx.save()
    ctx.set_source_rgb(BG[0], BG[1], BG[2])
    ctx.rectangle(0, y_top, W, band_h)
    ctx.fill()

    ctx.set_source_rgba(HAIR[0] * 1.4, HAIR[1] * 1.4, HAIR[2] * 1.4, 0.95)
    ctx.set_line_width(1.5)
    ctx.move_to(0, y_top)
    ctx.line_to(W, y_top)
    ctx.stroke()
    ctx.restore()

    is_vert = H > W
    pad_x = 64 if is_vert else 88
    h_size = 44 if is_vert else 42
    s_size = 24 if is_vert else 22

    # Accent vertical tick on left of caption
    ctx.save()
    ctx.set_source_rgba(accent[0], accent[1], accent[2], alpha)
    ctx.rectangle(pad_x - 20, y_top + (34 if not is_vert else 44), 5, band_h - (68 if not is_vert else 88))
    ctx.fill()
    ctx.restore()

    if subline:
        draw_text(ctx, headline, pad_x, y_top + (28 if not is_vert else 44), "sans_bold", h_size, TEXT, alpha=alpha, anchor="tl")
        draw_text(ctx, subline, pad_x, y_top + (82 if not is_vert else 108), "sans_regular", s_size, TEXT2, alpha=alpha * 0.92, anchor="tl")
    else:
        draw_text(ctx, headline, pad_x, y_top + band_h / 2.0, "sans_bold", h_size, TEXT, alpha=alpha, anchor="cl")


def draw_app_topbar(ctx: cairo.Context, W: int, pad_x: float, y: float, alpha: float = 1.0) -> float:
    """Replicate Pulse-0G top header bar cleanly in vector (no screenshots)."""
    is_vert = W < 1200
    bar_h = 64 if not is_vert else 74
    ctx.save()
    ctx.set_source_rgba(SURFACE[0], SURFACE[1], SURFACE[2], alpha)
    ctx.rectangle(0, y, W, bar_h)
    ctx.fill()
    ctx.set_source_rgba(HAIR[0] * 1.3, HAIR[1] * 1.3, HAIR[2] * 1.3, alpha)
    ctx.set_line_width(1.2)
    ctx.move_to(0, y + bar_h)
    ctx.line_to(W, y + bar_h)
    ctx.stroke()
    ctx.restore()

    cy = y + bar_h / 2.0
    draw_text(ctx, "PULSE-0G", pad_x, cy, "sans_extrabold", 24 if not is_vert else 26, TEXT, alpha=alpha, anchor="cl", tracking=1.0)
    draw_pill(ctx, pad_x + 150, cy, "SINTÉTICO", VIOLET, alpha=alpha, anchor="cl", font_size=15, px=11, py=5)
    draw_pill(ctx, pad_x + 286, cy, "DÍA 180", TEAL, alpha=alpha, anchor="cl", font_size=15, px=11, py=5)

    if not is_vert:
        draw_text(ctx, "Dosis acumulada: 76 / 600 mSv", W - pad_x, cy, "mono_regular", 17, TEXT2, alpha=alpha, anchor="cr")
    else:
        draw_text(ctx, "76 / 600 mSv", W - pad_x, cy, "mono_regular", 17, TEXT2, alpha=alpha, anchor="cr")
    return bar_h


def draw_body_silhouette(
    ctx: cairo.Context,
    cx: float,
    cy: float,
    scale: float,
    head_selected: float,
    alpha: float = 1.0,
) -> Tuple[float, float]:
    """Vector BodyMap matching components/BodyMap.tsx (viewBox 0 0 200 400). Returns head screen center."""
    ctx.save()
    ctx.translate(cx - 100 * scale, cy - 200 * scale)
    ctx.scale(scale, scale)

    def fill_stroke(fill_col, stroke_col, lw=1.8, dash=False):
        ctx.set_source_rgba(fill_col[0], fill_col[1], fill_col[2], alpha)
        ctx.fill_preserve()
        ctx.set_source_rgba(stroke_col[0], stroke_col[1], stroke_col[2], alpha)
        ctx.set_line_width(lw)
        if dash:
            ctx.set_dash([4.0, 3.0])
        else:
            ctx.set_dash([])
        ctx.stroke()

    # Legs (green - en rango)
    leg_fill = (SURFACE2[0] * 0.84 + GREEN[0] * 0.16, SURFACE2[1] * 0.84 + GREEN[1] * 0.16, SURFACE2[2] * 0.84 + GREEN[2] * 0.16)
    for rx, ry, rw, rh, rr in [
        (82, 165, 36, 30, 8),
        (82, 191, 16, 178, 8),
        (102, 191, 16, 178, 8),
        (72, 367, 24, 11, 5),
        (104, 367, 24, 11, 5),
    ]:
        draw_rounded_rect(ctx, rx, ry, rw, rh, rr)
        fill_stroke(leg_fill, GREEN, 1.4)

    # Thorax (amber - atención)
    amb_fill = (SURFACE2[0] * 0.82 + AMBER[0] * 0.18, SURFACE2[1] * 0.82 + AMBER[1] * 0.18, SURFACE2[2] * 0.82 + AMBER[2] * 0.18)
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
    fill_stroke(amb_fill, AMBER, 1.5)

    # Arms (measurement site - neutral slate)
    site_fill = (21 / 255, 30 / 255, 43 / 255)
    for ax, ay, ang in [(131, 96, 7), (56, 96, -7)]:
        ctx.save()
        ctx.translate(ax + 6.5, ay)
        ctx.rotate(math.radians(ang))
        draw_rounded_rect(ctx, -6.5, 0, 13, 112, 6.5)
        ctx.restore()
        fill_stroke(site_fill, SLATE, 1.5)

    # Head (red - requiere acción!)
    red_fill = (SURFACE2[0] * 0.78 + RED[0] * 0.22, SURFACE2[1] * 0.78 + RED[1] * 0.22, SURFACE2[2] * 0.78 + RED[2] * 0.22)
    draw_rounded_rect(ctx, 92, 76, 16, 14, 5)
    fill_stroke(red_fill, RED, 1.6 + head_selected * 1.4)

    ctx.new_sub_path()
    ctx.arc(100, 54, 24, 0, 2 * math.pi)
    fill_stroke(red_fill, RED, 1.8 + head_selected * 1.6)

    # Eyes (no_data dashed)
    for ex in (92, 108):
        ctx.save()
        ctx.translate(ex, 50)
        ctx.scale(4.2, 2.8)
        ctx.new_sub_path()
        ctx.arc(0, 0, 1.0, 0, 2 * math.pi)
        ctx.restore()
        fill_stroke((18 / 255, 26 / 255, 37 / 255), NODATA, 1.1, dash=True)

    ctx.restore()
    return (cx, cy - 146 * scale)


def draw_cursor(ctx: cairo.Context, x: float, y: float, click_p: float, alpha: float = 1.0) -> None:
    """Crisp pointer arrow + tap ripple ring."""
    if click_p > 0.01:
        r = 12.0 + click_p * 34.0
        a = (1.0 - click_p) * 0.85 * alpha
        ctx.save()
        ctx.set_source_rgba(RED[0], RED[1], RED[2], a)
        ctx.set_line_width(2.5)
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.stroke()
        ctx.restore()

    ctx.save()
    ctx.translate(x, y)
    ctx.move_to(0, 0)
    ctx.line_to(0, 24)
    ctx.line_to(6, 18)
    ctx.line_to(13, 27)
    ctx.line_to(17, 24)
    ctx.line_to(10, 15)
    ctx.line_to(18, 14)
    ctx.close_path()
    ctx.set_source_rgba(TEXT[0], TEXT[1], TEXT[2], alpha)
    ctx.fill_preserve()
    ctx.set_source_rgba(BG[0], BG[1], BG[2], alpha)
    ctx.set_line_width(1.6)
    ctx.stroke()
    ctx.restore()


# ---------------------------------------------------------------------------
# Block 1 (0.00 - 3.00): Problem Statement
# ---------------------------------------------------------------------------
def render_block_1_problem(ctx: cairo.Context, W: int, H: int, t: float) -> None:
    is_vert = H > W
    draw_crosshair_grid(ctx, W, H, H, alpha=0.40)

    p1 = ease_out_cubic(progress(t, 0.12, 0.60))
    p2 = ease_out_cubic(progress(t, 0.85, 1.35))
    p3 = ease_out_cubic(progress(t, 1.65, 2.20))

    s_big = 68 if not is_vert else 62
    s_sub = 24 if not is_vert else 26

    draw_text(ctx, "250 millones de millas.", W / 2.0, H / 2.0 - (68 if not is_vert else 86) + (1 - p1) * 16, "sans_extrabold", s_big, TEXT, alpha=p1, anchor="cc")
    draw_text(ctx, "Sin médico a bordo.", W / 2.0, H / 2.0 + (12 if not is_vert else 4) + (1 - p2) * 16, "sans_extrabold", s_big, RED, alpha=p2, anchor="cc")
    draw_text(
        ctx,
        "Un dato normal para cualquiera puede ser alerta para vos.",
        W / 2.0,
        H / 2.0 + (96 if not is_vert else 108),
        "sans_regular",
        s_sub,
        TEXT2,
        alpha=p3 * 0.92,
        anchor="cc",
    )


# ---------------------------------------------------------------------------
# Block 2 (3.00 - 8.00): BodyMap + Tap Head -> Neuroconductual
# ---------------------------------------------------------------------------
def render_block_2_bodymap(ctx: cairo.Context, W: int, H: int, t: float, band_h: int) -> None:
    is_vert = H > W
    stage_h = H - band_h
    draw_crosshair_grid(ctx, W, H, stage_h, alpha=0.45)

    pad_x = 64 if is_vert else 88
    top_h = draw_app_topbar(ctx, W, pad_x, 0, alpha=1.0)
    work_y0 = top_h
    work_h = stage_h - top_h

    # Punch-in zoom after tapping the head at t = 4.75s
    tap_p = progress(t, 4.70, 5.20)
    zoom_p = ease_in_out_cubic(progress(t, 5.05, 6.40))
    head_sel = ease_out_cubic(progress(t, 4.75, 5.10))

    ctx.save()
    if not is_vert:
        # Subtle punch-in focusing toward the Neuroconductual card + red head
        sc = 1.0 + zoom_p * 0.14
        ctx.translate(W * 0.62, work_y0 + work_h * 0.48)
        ctx.scale(sc, sc)
        ctx.translate(-W * 0.62, -(work_y0 + work_h * 0.48))

        # Left column: BodyMap
        map_cx = 310
        map_cy = work_y0 + work_h * 0.49
        head_x, head_y = draw_body_silhouette(ctx, map_cx, map_cy, scale=1.55, head_selected=head_sel)
        draw_text(ctx, "Tocar zona", map_cx, map_cy + 325, "mono_regular", 17, TEXT2, alpha=0.85, anchor="cc")

        # Right column: Neuroconductual panel (>=60% width)
        px = 550
        pw = W - px - pad_x
        py = work_y0 + 58
        draw_text(ctx, "Neuroconductual", px, py, "sans_bold", 38, TEXT, anchor="tl")
        draw_pill(ctx, px + 345, py + 6, "■ REQUIERE ACCIÓN", RED, anchor="tl", font_size=16)
        draw_text(ctx, "Sueño y estado de ánimo · Día 180", px, py + 50, "sans_regular", 21, TEXT2, anchor="tl")

        # Card 1: Sleep (highlighted in red after tap)
        c1y = py + 102
        c1h = 250
        draw_rounded_rect(ctx, px, c1y, pw, c1h, 10)
        ctx.set_source_rgba(SURFACE[0], SURFACE[1], SURFACE[2], 1.0)
        ctx.fill_preserve()
        ctx.set_source_rgba(RED[0] if head_sel > 0.3 else HAIR[0], RED[1] if head_sel > 0.3 else HAIR[1], RED[2] if head_sel > 0.3 else HAIR[2], 0.85)
        ctx.set_line_width(2.0 if head_sel > 0.3 else 1.4)
        ctx.stroke()

        draw_text(ctx, "Horas de sueño", px + 28, c1y + 24, "sans_semibold", 24, TEXT2)
        draw_pill(ctx, px + 245, c1y + 20, "SINTÉTICO", VIOLET, font_size=14, px=10, py=4)
        draw_pill(ctx, px + pw - 26, c1y + 20, "▲ FUERA DE BANDA", RED, anchor="tr", font_size=14, px=10, py=4)
        draw_text(ctx, "2.9 h de sueño", px + 28, c1y + 72, "mono_bold", 54, TEXT)
        draw_text(ctx, "base 7.3 h  ·  −60 % contra tu propia base  ·  4 muestras faltantes", px + 28, c1y + 146, "mono_regular", 20, RED)
        ctx.set_source_rgba(RED[0], RED[1], RED[2], 1.0)
        ctx.rectangle(px + 28, c1y + 190, 4, 34)
        ctx.fill()
        draw_text(ctx, "Revisar ciclo de sueño con el flight surgeon.", px + 44, c1y + 195, "sans_regular", 21, TEXT)

        # Card 2: Mood (amber)
        c2y = c1y + c1h + 24
        c2h = 195
        draw_rounded_rect(ctx, px, c2y, pw, c2h, 10)
        ctx.set_source_rgba(SURFACE[0], SURFACE[1], SURFACE[2], 1.0)
        ctx.fill_preserve()
        ctx.set_source_rgba(HAIR[0] * 1.4, HAIR[1] * 1.4, HAIR[2] * 1.4, 1.0)
        ctx.set_line_width(1.4)
        ctx.stroke()

        draw_text(ctx, "Estado de ánimo", px + 28, c2y + 22, "sans_semibold", 24, TEXT2)
        draw_pill(ctx, px + 245, c2y + 18, "SINTÉTICO", VIOLET, font_size=14, px=10, py=4)
        draw_pill(ctx, px + pw - 26, c2y + 18, "◆ ATENCIÓN", AMBER, anchor="tr", font_size=14, px=10, py=4)
        draw_text(ctx, "4.3 / 10 ánimo", px + 28, c2y + 68, "mono_bold", 48, TEXT)
        draw_text(ctx, "banda ámbar · requiere seguimiento de tripulación", px + 28, c2y + 136, "mono_regular", 20, AMBER)
    else:
        # Vertical 1080x1920 native layout: BodyMap top + big Neuroconductual card below
        sc = 1.0 + zoom_p * 0.12
        ctx.translate(W * 0.5, work_y0 + work_h * 0.58)
        ctx.scale(sc, sc)
        ctx.translate(-W * 0.5, -(work_y0 + work_h * 0.58))

        map_cx = W * 0.5
        map_cy = work_y0 + 365
        head_x, head_y = draw_body_silhouette(ctx, map_cx, map_cy, scale=1.58, head_selected=head_sel)

        px = pad_x
        pw = W - pad_x * 2
        py = work_y0 + 735
        draw_text(ctx, "Neuroconductual", px, py, "sans_bold", 42, TEXT)
        draw_pill(ctx, px + pw, py + 8, "■ REQUIERE ACCIÓN", RED, anchor="tr", font_size=17)

        c1y = py + 72
        c1h = 330
        draw_rounded_rect(ctx, px, c1y, pw, c1h, 12)
        ctx.set_source_rgba(SURFACE[0], SURFACE[1], SURFACE[2], 1.0)
        ctx.fill_preserve()
        ctx.set_source_rgba(RED[0] if head_sel > 0.3 else HAIR[0], RED[1] if head_sel > 0.3 else HAIR[1], RED[2] if head_sel > 0.3 else HAIR[2], 0.9)
        ctx.set_line_width(2.2)
        ctx.stroke()

        draw_text(ctx, "Horas de sueño", px + 30, c1y + 28, "sans_semibold", 28, TEXT2)
        draw_pill(ctx, px + pw - 28, c1y + 24, "SINTÉTICO", VIOLET, anchor="tr", font_size=16)
        draw_text(ctx, "2.9 h de sueño", px + 30, c1y + 92, "mono_bold", 66, TEXT)
        draw_text(ctx, "base 7.3 h · −60 % contra tu base", px + 30, c1y + 186, "mono_regular", 24, RED)
        draw_text(ctx, "4 muestras faltantes · no inventadas", px + 30, c1y + 230, "mono_regular", 22, TEXT2)

        c2y = c1y + c1h + 26
        c2h = 210
        draw_rounded_rect(ctx, px, c2y, pw, c2h, 12)
        ctx.set_source_rgba(SURFACE[0], SURFACE[1], SURFACE[2], 1.0)
        ctx.fill_preserve()
        ctx.set_source_rgba(HAIR[0] * 1.4, HAIR[1] * 1.4, HAIR[2] * 1.4, 1.0)
        ctx.set_line_width(1.5)
        ctx.stroke()
        draw_text(ctx, "Estado de ánimo", px + 30, c2y + 26, "sans_semibold", 28, TEXT2)
        draw_pill(ctx, px + pw - 28, c2y + 22, "◆ BANDA ÁMBAR", AMBER, anchor="tr", font_size=16)
        draw_text(ctx, "4.3 / 10 ánimo", px + 30, c2y + 92, "mono_bold", 56, TEXT)

    # Animated cursor moving to head and tapping
    move_p = ease_in_out_cubic(progress(t, 3.25, 4.60))
    cur_x = (head_x + 150) * (1 - move_p) + head_x * move_p
    cur_y = (head_y + 180) * (1 - move_p) + head_y * move_p
    if t < 6.40:
        draw_cursor(ctx, cur_x, cur_y, tap_p, alpha=1.0 - progress(t, 5.90, 6.40))
    ctx.restore()

    draw_caption_band(
        ctx, W, H, band_h,
        "Tocá una zona del cuerpo.",
        "Cada región muestra tu valor, su banda y qué hacer — sin diagnosticar.",
        alpha=ease_out_cubic(progress(t, 3.05, 3.45)),
        accent=RED,
    )


# ---------------------------------------------------------------------------
# Block 3 (8.00 - 13.00): Zoom on Sleep Card + Two-Layer Baseline + Real Gaps
# ---------------------------------------------------------------------------
def render_block_3_baseline_zoom(ctx: cairo.Context, W: int, H: int, t: float, band_h: int) -> None:
    is_vert = H > W
    stage_h = H - band_h
    draw_crosshair_grid(ctx, W, H, stage_h, alpha=0.50)

    pad_x = 64 if is_vert else 88
    top_h = draw_app_topbar(ctx, W, pad_x, 0, alpha=1.0)

    # Huge zoomed Sleep card (>=70% of the frame!)
    enter_p = ease_out_cubic(progress(t, 8.00, 8.45))
    scale_card = 0.94 + 0.06 * enter_p

    cw = (W - pad_x * 2) if is_vert else 1480
    ch = 1140 if is_vert else 670
    cx = W / 2.0
    cy = top_h + (stage_h - top_h) / 2.0

    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(scale_card, scale_card)
    x0, y0 = -cw / 2.0, -ch / 2.0

    draw_rounded_rect(ctx, x0, y0, cw, ch, 14)
    ctx.set_source_rgba(SURFACE[0], SURFACE[1], SURFACE[2], 1.0)
    ctx.fill_preserve()
    ctx.set_source_rgba(RED[0], RED[1], RED[2], 0.85)
    ctx.set_line_width(2.2)
    ctx.stroke()

    # Left red accent bar
    ctx.set_source_rgba(RED[0], RED[1], RED[2], 1.0)
    ctx.rectangle(x0 + 2, y0 + 2, 10, ch - 4)
    ctx.fill()

    pad = 44 if not is_vert else 38
    draw_text(ctx, "HORAS DE SUEÑO · DÍA 180", x0 + pad, y0 + 34, "mono_bold", 22 if not is_vert else 21, TEXT2)
    draw_pill(ctx, x0 + cw - pad, y0 + 28, "SINTÉTICO", VIOLET, anchor="tr", font_size=17)
    if not is_vert:
        draw_pill(ctx, x0 + cw - pad - 145, y0 + 28, "▲ FUERA DE BANDA", RED, anchor="tr", font_size=17)

    # Big metric WITH object (Rule 3)
    stat_y = y0 + (98 if not is_vert else 112)
    draw_text(ctx, "2.9 h de sueño", x0 + pad, stat_y, "mono_bold", 104 if not is_vert else 86, TEXT)

    # Explicit comparison against own baseline (Rule 3)
    meta_y = stat_y + (132 if not is_vert else 128)
    draw_pill(ctx, x0 + pad, meta_y, "▼ −60 % CONTRA TU PROPIA BASE", RED, font_size=22 if not is_vert else 21, px=16, py=8)
    if not is_vert:
        draw_pill(ctx, x0 + pad + 470, meta_y, "BASE PREVIA: 7.3 h", TEAL, font_size=22, px=16, py=8)
        draw_pill(ctx, x0 + pad + 780, meta_y, "4 FALTANTES", NODATA, font_size=22, px=16, py=8)
    else:
        draw_pill(ctx, x0 + pad, meta_y + 62, "BASE PREVIA: 7.3 h", TEAL, font_size=21, px=16, py=8)
        draw_pill(ctx, x0 + pad + 315, meta_y + 62, "4 MUESTRAS FALTANTES", NODATA, font_size=21, px=16, py=8)

    # Animated Sparkline with REAL GAPS (4 missing samples never interpolated!)
    sp_x = x0 + pad
    sp_y = y0 + (320 if not is_vert else 435)
    sp_w = cw - pad * 2
    sp_h = 200 if not is_vert else 320

    draw_rounded_rect(ctx, sp_x, sp_y, sp_w, sp_h, 8)
    ctx.set_source_rgba(BG_DEEP[0], BG_DEEP[1], BG_DEEP[2], 1.0)
    ctx.fill_preserve()
    ctx.set_source_rgba(HAIR[0] * 1.4, HAIR[1] * 1.4, HAIR[2] * 1.4, 1.0)
    ctx.set_line_width(1.2)
    ctx.stroke()

    # Baseline dashed horizontal line (7.3 h)
    base_y = sp_y + sp_h * 0.24
    ctx.save()
    ctx.set_source_rgba(TEAL[0], TEAL[1], TEAL[2], 0.70)
    ctx.set_line_width(1.8)
    ctx.set_dash([8.0, 6.0])
    ctx.move_to(sp_x + 20, base_y)
    ctx.line_to(sp_x + sp_w - 20, base_y)
    ctx.stroke()
    ctx.restore()
    draw_text(ctx, "tu propia base (7.3 h)", sp_x + sp_w - 26, base_y - 28, "mono_regular", 16, TEAL, anchor="tr")

    # Series points: None = real missing gap (4 gaps total!)
    series: List[float | None] = [7.4, 7.2, None, 7.1, 6.8, None, 5.9, 5.4, None, 4.5, 3.8, None, 3.1, 2.9]
    n_pts = len(series)
    px_at = lambda i: sp_x + 36 + (i / (n_pts - 1)) * (sp_w - 72)
    py_at = lambda v: sp_y + sp_h - 32 - ((v - 2.0) / 6.2) * (sp_h - 68)

    # Vertical dashed gap lines for the 4 missing samples
    gap_p = ease_out_cubic(progress(t, 8.70, 9.60))
    ctx.save()
    ctx.set_source_rgba(NODATA[0], NODATA[1], NODATA[2], 0.85 * gap_p)
    ctx.set_line_width(2.0)
    ctx.set_dash([5.0, 5.0])
    for idx, val in enumerate(series):
        if val is None:
            gx = px_at(idx)
            ctx.move_to(gx, sp_y + 22)
            ctx.line_to(gx, sp_y + sp_h - 22)
    ctx.stroke()
    ctx.restore()

    # Draw connected non-null segments sequentially left-to-right (stroke-dashoffset feel)
    draw_p = ease_out_cubic(progress(t, 8.35, 10.60))
    max_idx = draw_p * (n_pts - 1)
    ctx.save()
    ctx.set_source_rgba(RED[0], RED[1], RED[2], 1.0)
    ctx.set_line_width(4.0)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    seg: List[Tuple[float, float]] = []
    for idx, val in enumerate(series):
        if idx > max_idx:
            break
        if val is None:
            if len(seg) >= 2:
                ctx.move_to(*seg[0])
                for pt in seg[1:]:
                    ctx.line_to(*pt)
                ctx.stroke()
            seg = []
        else:
            seg.append((px_at(idx), py_at(val)))
    if len(seg) >= 2:
        ctx.move_to(*seg[0])
        for pt in seg[1:]:
            ctx.line_to(*pt)
        ctx.stroke()

    # Dots on samples + endpoint highlight on 2.9 h
    for idx, val in enumerate(series):
        if idx <= max_idx and val is not None:
            is_last = idx == n_pts - 1
            ctx.set_source_rgba(RED[0], RED[1], RED[2], 1.0)
            ctx.arc(px_at(idx), py_at(val), 7.5 if is_last else 4.2, 0, 2 * math.pi)
            ctx.fill()
    ctx.restore()

    draw_text(ctx, "4 huecos sin dato (no se interpolan)", sp_x + 24, sp_y + sp_h - 28, "mono_regular", 17, TEXT2, alpha=gap_p)

    # Action bar at bottom of card
    act_y = y0 + ch - (108 if not is_vert else 230)
    ctx.save()
    ctx.set_source_rgba(RED[0], RED[1], RED[2], 1.0)
    ctx.rectangle(x0 + pad, act_y, 5, 58 if not is_vert else 96)
    ctx.fill()
    ctx.restore()
    if not is_vert:
        draw_text(ctx, "Acción: revisar ciclo de sueño con el flight surgeon y control de iluminación.", x0 + pad + 20, act_y + 14, "sans_semibold", 26, TEXT)
    else:
        draw_text(ctx, "Acción: revisar ciclo de sueño con", x0 + pad + 20, act_y + 8, "sans_semibold", 28, TEXT)
        draw_text(ctx, "el flight surgeon e iluminación.", x0 + pad + 20, act_y + 48, "sans_semibold", 28, TEXT)

    ctx.restore()

    draw_caption_band(
        ctx, W, H, band_h,
        "Tu medición. Contra tu propia base.",
        "Compara contra tu línea previa al vuelo y expone los 4 huecos sin inventar.",
        alpha=ease_out_cubic(progress(t, 8.05, 8.45)),
        accent=TEAL,
    )


# ---------------------------------------------------------------------------
# Block 4 (13.00 - 19.00): Enlarged Claim Verifier + Visible Red Strike-Out
# ---------------------------------------------------------------------------
def render_block_4_verifier(ctx: cairo.Context, W: int, H: int, t: float, band_h: int) -> None:
    is_vert = H > W
    stage_h = H - band_h
    draw_crosshair_grid(ctx, W, H, stage_h, alpha=0.45)

    pad_x = 64 if is_vert else 88
    slide_p = ease_in_out_cubic(progress(t, 16.70, 17.30))
    strike_p = ease_out_cubic(progress(t, 14.90, 15.45))  # Struck phrase stays visible 15.45 -> 19.00 (>3.5s!)
    post_strike = t >= 14.90

    if not is_vert:
        card_w = 1480.0 - slide_p * 520.0  # 1480 -> 960
        card_h = 500.0
        card_cx = W / 2.0 - slide_p * 390.0
        card_cy = stage_h / 2.0 + 35.0
    else:
        card_w = W - pad_x * 2
        card_h = 690.0
        card_cx = W / 2.0
        card_cy = stage_h / 2.0 + 130.0 - slide_p * 220.0

    # Double hairline frame
    ctx.save()
    for pad_f, a_mul in ((20, 0.35), (40, 0.16)):
        draw_rounded_rect(ctx, card_cx - card_w / 2.0 - pad_f, card_cy - card_h / 2.0 - pad_f, card_w + pad_f * 2, card_h + pad_f * 2, 12)
        ctx.set_source_rgba(TEXT2[0], TEXT2[1], TEXT2[2], (1.0 - slide_p * 0.7) * a_mul)
        ctx.set_line_width(1.4)
        ctx.stroke()
    ctx.restore()

    # Typed header above card before side split
    if t < 17.20:
        hdr_a = 1.0 - progress(t, 16.65, 17.15)
        hx = card_cx - card_w / 2.0
        hy = card_cy - card_h / 2.0
        draw_text(ctx, "VERIFICADOR EN TIEMPO REAL", hx, hy - 118, "sans_extrabold", 34 if not is_vert else 36, TEXT, alpha=hdr_a)
        draw_text(ctx, "Cada frase debe estar anclada a datos reales", hx, hy - 70, "mono_regular", 23 if not is_vert else 22, TEXT2, alpha=hdr_a)

    # Card Body (Opaque, Huge & Legible)
    x0, y0 = card_cx - card_w / 2.0, card_cy - card_h / 2.0
    accent_col = RED if strike_p > 0.35 else TEAL
    ctx.save()
    draw_rounded_rect(ctx, x0, y0, card_w, card_h, 12)
    ctx.set_source_rgba(SURFACE[0], SURFACE[1], SURFACE[2], 1.0)
    ctx.fill_preserve()
    ctx.set_source_rgba(accent_col[0] if strike_p > 0.35 else HAIR[0] * 1.5, accent_col[1] if strike_p > 0.35 else HAIR[1] * 1.5, accent_col[2] if strike_p > 0.35 else HAIR[2] * 1.5, 1.0)
    ctx.set_line_width(2.4 if strike_p > 0.35 else 1.8)
    ctx.stroke()

    ctx.set_source_rgba(accent_col[0], accent_col[1], accent_col[2], 1.0)
    ctx.rectangle(x0 + 2, y0 + 2, 12, card_h - 4)
    ctx.fill()
    ctx.restore()

    draw_text(ctx, "VERIFICADOR DE AFIRMACIONES", x0 + 40, y0 + 30, "sans_bold", 28 if not is_vert else 26, TEXT)
    draw_pill(ctx, x0 + card_w - 32, y0 + 26, "DETERMINÍSTICO", TEAL, anchor="tr", font_size=16)

    # Row 1: Verified Claim
    r1_a = ease_out_cubic(progress(t, 13.20, 13.65))
    r1_y = y0 + (120 if not is_vert else 128)
    ctx.save()
    ctx.set_source_rgba(GREEN[0], GREEN[1], GREEN[2], r1_a)
    ctx.rectangle(x0 + 40, r1_y + 10, 16, 16)
    ctx.fill()
    ctx.restore()
    r1_sz = 26 if not is_vert else 25
    if slide_p > 0.5 and not is_vert:
        r1_sz = 22
    draw_text(ctx, '"2.9 h de sueño (−60 % vs base)"', x0 + 72, r1_y, "mono_regular", r1_sz, TEXT, alpha=r1_a)
    draw_pill(ctx, x0 + card_w - 32, r1_y - 2, "✓ ANCLADA", GREEN, alpha=r1_a, anchor="tr", font_size=16)

    # Divider
    div_y = y0 + (192 if not is_vert else 225)
    ctx.save()
    ctx.set_source_rgba(HAIR[0] * 1.6, HAIR[1] * 1.6, HAIR[2] * 1.6, 1.0)
    ctx.set_line_width(1.4)
    ctx.move_to(x0 + 40, div_y)
    ctx.line_to(x0 + card_w - 32, div_y)
    ctx.stroke()
    ctx.restore()

    # Row 2: Unanchored Claim -> Dramatic Red Strike-Out
    r2_a = ease_out_cubic(progress(t, 13.90, 14.35))
    r2_y = y0 + (235 if not is_vert else 280)
    ctx.save()
    ind_col = RED if post_strike else TEXT2
    ctx.set_source_rgba(ind_col[0], ind_col[1], ind_col[2], r2_a)
    ctx.rectangle(x0 + 40, r2_y + 10, 16, 16)
    ctx.fill()
    ctx.restore()

    claim2 = '"La recuperación del tripulante mejora"' if not is_vert else '"La recuperación mejora"'
    c2_sz = 26 if not is_vert else 26
    if slide_p > 0.5 and not is_vert:
        c2_sz = 22
    c2_col = RED if strike_p > 0.5 else TEXT
    cw, ch = draw_text(ctx, claim2, x0 + 72, r2_y, "mono_regular", c2_sz, c2_col, alpha=r2_a)

    if strike_p > 0.01:
        ctx.save()
        ctx.set_source_rgba(RED[0], RED[1], RED[2], 1.0)
        ctx.set_line_width(4.5)
        ctx.set_line_cap(cairo.LINE_CAP_SQUARE)
        sx0 = x0 + 68
        sy = r2_y + ch * 0.56
        ctx.move_to(sx0, sy)
        ctx.line_to(sx0 + (cw + 12) * strike_p, sy)
        ctx.stroke()
        ctx.restore()

    if strike_p > 0.40:
        ba = ease_out_cubic((strike_p - 0.40) / 0.60)
        if not is_vert:
            draw_pill(ctx, x0 + card_w - 32, r2_y - 2, "✕ TACHADA", RED, alpha=ba, anchor="tr", font_size=16)
            draw_text(ctx, "motivo: sin dato ni tarjeta de respaldo en OSD-575 o base", x0 + 72, r2_y + 54, "mono_italic", 20 if slide_p < 0.5 else 17, RED, alpha=ba)
        else:
            draw_pill(ctx, x0 + 72, r2_y + 52, "✕ TACHADA EN PANTALLA", RED, alpha=ba, font_size=16)
            draw_text(ctx, "motivo: sin dato de respaldo", x0 + 72, r2_y + 108, "mono_italic", 22, RED, alpha=ba)

    # Bottom LED bar inside Verifier card
    draw_led_bar(ctx, x0 + 40, y0 + card_h - 68, card_w - 340, 28, 1.0 if post_strike else 0.82, accent_col, cols=34, rows=3)
    draw_text(ctx, "TACHADA EN PANTALLA" if strike_p > 0.5 else "VERIFICANDO...", x0 + card_w - 32, y0 + card_h - 54, "mono_bold", 19, accent_col, anchor="cr")

    # Right / Bottom 3-line bold takeaway
    if t >= 16.90:
        p_w1 = ease_out_cubic(progress(t, 16.95, 17.25))
        p_w2 = ease_out_cubic(progress(t, 17.25, 17.55))
        p_w3 = ease_out_cubic(progress(t, 17.55, 17.85))
        if not is_vert:
            rx = 1095.0
            draw_text(ctx, "CERO", rx + (1 - p_w1) * 30, 310, "sans_extrabold", 76, TEXT, alpha=p_w1)
            draw_text(ctx, "AFIRMACIONES", rx + (1 - p_w2) * 30, 402, "sans_extrabold", 76, TEAL, alpha=p_w2)
            draw_text(ctx, "SIN RESPALDO", rx + (1 - p_w3) * 30, 494, "sans_extrabold", 76, RED, alpha=p_w3)
        else:
            bx = pad_x
            by = card_cy + card_h / 2.0 + 70
            draw_text(ctx, "CERO AFIRMACIONES", bx, by, "sans_extrabold", 64, TEXT, alpha=p_w1)
            draw_text(ctx, "SIN RESPALDO", bx, by + 84, "sans_extrabold", 64, RED, alpha=p_w3)

    draw_caption_band(
        ctx, W, H, band_h,
        "Cada afirmación se rastrea. O se tacha.",
        "El sistema desconfía incluso de su propio texto si falta evidencia.",
        alpha=ease_out_cubic(progress(t, 13.05, 13.45)),
        accent=RED,
    )


# ---------------------------------------------------------------------------
# Block 5 (19.00 - 25.00): Final State — Case Package Export for Flight Surgeon
# ---------------------------------------------------------------------------
def render_block_5_casefile(ctx: cairo.Context, W: int, H: int, t: float, band_h: int) -> None:
    is_vert = H > W
    stage_h = H - band_h
    draw_crosshair_grid(ctx, W, H, stage_h, alpha=0.45)

    pad_x = 64 if is_vert else 88
    top_h = draw_app_topbar(ctx, W, pad_x, 0, alpha=1.0)

    enter_p = ease_out_cubic(progress(t, 19.00, 19.45))
    cw = (W - pad_x * 2) if is_vert else 1480
    ch = 1180 if is_vert else 670
    cx = W / 2.0
    cy = top_h + (stage_h - top_h) / 2.0 + (1 - enter_p) * 24

    x0, y0 = cx - cw / 2.0, cy - ch / 2.0
    draw_rounded_rect(ctx, x0, y0, cw, ch, 14)
    ctx.set_source_rgba(SURFACE[0], SURFACE[1], SURFACE[2], 1.0)
    ctx.fill_preserve()
    ctx.set_source_rgba(TEAL[0], TEAL[1], TEAL[2], 0.72)
    ctx.set_line_width(2.0)
    ctx.stroke()

    pad = 42 if not is_vert else 36
    draw_text(ctx, "Paquete de caso", x0 + pad, y0 + 30, "sans_bold", 34 if not is_vert else 36, TEXT)
    draw_pill(ctx, x0 + cw - pad, y0 + 28, "ESCALAMIENTO", TEAL, anchor="tr", font_size=16)

    # Metadata chips
    chip_y = y0 + 88
    draw_pill(ctx, x0 + pad, chip_y, "ID 415DA199", TEAL, font_size=16, px=12, py=5)
    draw_pill(ctx, x0 + pad + 150, chip_y, "2 FUERA DE BANDA", RED, font_size=16, px=12, py=5)
    if not is_vert:
        draw_pill(ctx, x0 + pad + 380, chip_y, "OSD-575: 4 TRIPULANTES · 7 MUESTRAS · 19 ANALITOS", TEXT2, font_size=16, px=12, py=5)
    else:
        draw_pill(ctx, x0 + pad, chip_y + 46, "OSD-575: 4 TRIP. · 7 MUESTRAS · 19 ANALITOS", TEXT2, font_size=15, px=12, py=5)

    # Clean Spanish Report Box
    rep_y = chip_y + (56 if not is_vert else 102)
    rep_h = ch - (rep_y - y0) - 105
    draw_rounded_rect(ctx, x0 + pad, rep_y, cw - pad * 2, rep_h, 8)
    ctx.set_source_rgba(BG_DEEP[0], BG_DEEP[1], BG_DEEP[2], 1.0)
    ctx.fill_preserve()
    ctx.set_source_rgba(HAIR[0] * 1.4, HAIR[1] * 1.4, HAIR[2] * 1.4, 1.0)
    ctx.set_line_width(1.2)
    ctx.stroke()

    lines = [
        ("PULSE-0G — PAQUETE PARA FLIGHT SURGEON (TIERRA)", TEAL),
        ("Origen escenario: SINTÉTICO (FD180)  ·  Base real: NASA OSDR OSD-575", TEXT2),
        ("─────────────────────────────────────────────────────────────────────", HAIR),
        ("■ Sueño: 2.9 h de sueño  (banda roja · −60 % contra base 7.3 h)", RED),
        ("◆ Ánimo: 4.3 / 10 ánimo  (banda ámbar · requiere atención)", AMBER),
        ("● Radiación acumulada: 76 mSv de un límite de 600 mSv", TEXT),
        ("● Calidad de datos: 4 muestras de sueño faltantes declaradas", TEXT2),
        ('● Nota de tripulación: "Fatiga marcada tras turno nocturno"', TEXT),
    ]
    if is_vert:
        lines = [
            ("PULSE-0G — PAQUETE PARA TIERRA", TEAL),
            ("Escenario SINTÉTICO (FD180) · OSD-575", TEXT2),
            ("──────────────────────────────────────", HAIR),
            ("■ Sueño: 2.9 h (−60 % vs base 7.3 h)", RED),
            ("◆ Ánimo: 4.3 / 10 (banda ámbar)", AMBER),
            ("● Dosis: 76 mSv (límite 600 mSv)", TEXT),
            ("● Datos: 4 huecos declarados", TEXT2),
            ("● Real OSD-575: 4 trip · 7 m · 19 anal.", TEXT2),
            ('● Bitácora: "Fatiga tras turno"', TEXT),
        ]

    rev_p = progress(t, 19.35, 22.10)
    shown_lines = int(math.ceil(rev_p * len(lines)))
    ly = rep_y + 26
    lh = 44 if not is_vert else 56
    lsz = 21 if not is_vert else 23
    for idx in range(min(len(lines), shown_lines)):
        ltxt, lcol = lines[idx]
        la = ease_out_cubic(progress(t, 19.35 + idx * 0.30, 19.65 + idx * 0.30))
        draw_text(ctx, ltxt, x0 + pad + 24, ly + idx * lh, "mono_regular", lsz, lcol, alpha=la)

    # Bottom export confirmation pill
    ready_p = ease_out_cubic(progress(t, 22.25, 22.75))
    if ready_p > 0.01:
        draw_pill(
            ctx,
            x0 + pad,
            y0 + ch - 70,
            "✓ PAQUETE LISTO PARA LECTURA EN TIERRA · NADA SE TRANSMITE NI DIAGNOSTICA" if not is_vert else "✓ LISTO PARA TIERRA · NO DIAGNOSTICA",
            GREEN,
            alpha=ready_p,
            font_size=17 if not is_vert else 18,
            px=16,
            py=8,
        )

    draw_caption_band(
        ctx, W, H, band_h,
        "¿Fuera de banda? Exportá un paquete de caso.",
        "Así queda: medido, verificado y listo para lectura médica en Tierra.",
        alpha=ease_out_cubic(progress(t, 19.05, 19.45)),
        accent=TEAL,
    )


# ---------------------------------------------------------------------------
# Block 6 (25.00 - 28.00): Single Endcard (One logo, once)
# ---------------------------------------------------------------------------
def render_block_6_endcard(ctx: cairo.Context, W: int, H: int, t: float) -> None:
    is_vert = H > W
    p = ease_out_cubic(progress(t, 25.05, 25.55))
    p2 = ease_out_cubic(progress(t, 25.45, 25.95))

    draw_pulse_mark(ctx, W / 2.0, H / 2.0 - (115 if not is_vert else 145), radius=52.0 if not is_vert else 60.0, alpha=p)
    draw_text(ctx, "PULSE-0G", W / 2.0, H / 2.0 + 4, "sans_extrabold", 76 if not is_vert else 84, TEAL, alpha=p, anchor="cc", tracking=3.0)
    draw_text(ctx, "Sin diagnóstico. Cada afirmación respaldada.", W / 2.0, H / 2.0 + 78, "sans_regular", 26 if not is_vert else 28, TEXT, alpha=p2, anchor="cc")
    draw_text(ctx, "NASA SPACE APPS CHALLENGE 2026 · CÓRDOBA", W / 2.0, H - 86, "mono_regular", 18, TEXT2, alpha=p2 * 0.85, anchor="cc", tracking=1.0)


def render_frame(surface: cairo.ImageSurface, W: int, H: int, frame_idx: int) -> None:
    t = frame_idx / FPS
    ctx = cairo.Context(surface)
    ctx.set_source_rgb(BG[0], BG[1], BG[2])
    ctx.paint()

    band_h = 220 if H > W else 140

    if t < 3.00:
        render_block_1_problem(ctx, W, H, t)
    elif t < 8.00:
        render_block_2_bodymap(ctx, W, H, t, band_h)
    elif t < 13.00:
        render_block_3_baseline_zoom(ctx, W, H, t, band_h)
    elif t < 19.00:
        render_block_4_verifier(ctx, W, H, t, band_h)
    elif t < 25.00:
        render_block_5_casefile(ctx, W, H, t, band_h)
    else:
        render_block_6_endcard(ctx, W, H, t)


def surface_to_rgb24(surface: cairo.ImageSurface, W: int, H: int) -> bytes:
    buf = np.frombuffer(surface.get_data(), dtype=np.uint8).reshape((H, W, 4))
    return buf[:, :, 2::-1].tobytes()


def encode_video(W: int, H: int, out_mp4: str, audio_path: str, save_stills_dir: str | None = None) -> None:
    ffmpeg_cmd = [
        "ffmpeg", "-y",
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
        still_map = {
            int(5.60 * FPS): os.path.join(save_stills_dir, "still_01_mapa_corporal.png"),
            int(11.40 * FPS): os.path.join(save_stills_dir, "still_02_base_propia.png"),
            int(16.00 * FPS): os.path.join(save_stills_dir, "still_03_verificador_tachado.png"),
        }

    for fidx in range(TOTAL_FRAMES):
        render_frame(surface, W, H, fidx)
        if fidx in still_map:
            surface.write_to_png(still_map[fidx])
        proc.stdin.write(surface_to_rgb24(surface, W, H))
        if fidx % 140 == 0 or fidx == TOTAL_FRAMES - 1:
            print(f"[{W}x{H}] {fidx + 1}/{TOTAL_FRAMES} ({(fidx + 1) / TOTAL_FRAMES * 100:.0f}%)", flush=True)

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
    audio_path = os.path.join(base_dir, "pulse_0g_audio_v2.wav")

    if "--stills-only" in sys.argv:
        # Render validation stills for both 1080p and vertical
        for label, W, H in [("1080p", 1920, 1080), ("vert", 1080, 1920)]:
            surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
            for name, sec in [
                ("b1_problem", 2.30),
                ("b2_bodymap", 5.80),
                ("b3_sleep", 11.40),
                ("b4_verifier", 16.00),
                ("b4_split", 18.20),
                ("b5_casefile", 23.00),
                ("b6_endcard", 26.80),
            ]:
                render_frame(surf, W, H, int(sec * FPS))
                out_p = os.path.join(base_dir, f"v2_{label}_{name}.png")
                surf.write_to_png(out_p)
                print(f"Saved {out_p}")
        return

    from generate_audio import build_audio
    build_audio(audio_path)

    mode = sys.argv[1] if len(sys.argv) > 1 else "--all"
    if mode in ("--1080p", "--all"):
        encode_video(
            1920, 1080,
            os.path.join(deliverables_dir, "pulse_0g_1080p.mp4"),
            audio_path,
            save_stills_dir=deliverables_dir,
        )
    if mode in ("--vertical", "--all"):
        encode_video(
            1080, 1920,
            os.path.join(deliverables_dir, "pulse_0g_vertical_1080x1920.mp4"),
            audio_path,
        )


if __name__ == "__main__":
    main()
