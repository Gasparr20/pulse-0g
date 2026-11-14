"""Pulse-0G 1080p motion-graphics video generator (2D PyCairo + Pillow + NumPy -> FFmpeg).

Follows the shot structure, pacing, and typography-first visual template of the
reference launch promo while strictly adhering to Pulse-0G's data, colors,
and honesty constraints (no diagnosis claims, explicit SYNTHETIC labeling,
only allowed metrics, zero webpage screenshots, zero 3D renders).
"""

from __future__ import annotations

import math
import os
import subprocess
import sys
from typing import Dict, Tuple

import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FPS = 30
DURATION = 23.0
TOTAL_FRAMES = int(round(DURATION * FPS))  # 690 frames

# Exact Pulse-0G Palette
BG = (10 / 255, 14 / 255, 19 / 255)          # #0A0E13
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

# Font paths
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


def ease_in_expo(t: float) -> float:
    t = clamp(t)
    return 0.0 if t <= 0.0 else 2.0 ** (10.0 * t - 10.0)


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
    """Render crisp anti-aliased text via Pillow into a cached premultiplied Cairo surface."""
    if not text:
        text = " "
    c255 = rgb_tuple_255(color)
    cache_key = (text, font_key, size, c255, round(tracking, 2), tight_y)
    if cache_key in _TEXT_CACHE:
        return _TEXT_CACHE[cache_key]

    font = get_font(font_key, size)
    pad = max(8, size // 5)

    # Measure total width with tracking
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
        x1 = min(arr.shape[1], int(xs.max()) + 3) if tight_y else min(arr.shape[1], int(xs.max()) + 3)
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
    """Draw cached text surface at (x, y) with anchor: tl, tc, tr, cl, cc, cr, bl, bc, br."""
    if alpha <= 0.005 or not text:
        return (0, 0)
    surf, _buf, tw, th = render_text_surface(text, font_key, size, color, tracking=tracking, tight_y=tight_y)
    dx = x
    dy = y
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
) -> Tuple[float, float]:
    surf, _buf, tw, th = render_text_surface(label, "mono_bold", font_size, color, tracking=1.4)
    bw = tw + px * 2
    bh = th + py * 2
    dx = x
    dy = y
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
    ctx.set_source_rgba(BG[0], BG[1], BG[2], 0.85 * alpha)
    ctx.fill_preserve()
    ctx.set_source_rgba(color[0], color[1], color[2], 0.14 * alpha)
    ctx.fill_preserve()
    ctx.set_source_rgba(color[0], color[1], color[2], 0.60 * alpha)
    ctx.set_line_width(1.4)
    ctx.stroke()
    ctx.set_source_surface(surf, dx + px, dy + py)
    ctx.paint_with_alpha(alpha)
    ctx.restore()
    return (bw, bh)


def draw_dot_grid(ctx: cairo.Context, spacing: int = 64, alpha: float = 0.28) -> None:
    ctx.save()
    ctx.set_source_rgba(HAIR[0] * 1.8, HAIR[1] * 1.8, HAIR[2] * 1.8, alpha)
    for gx in range(spacing // 2, W, spacing):
        for gy in range(spacing // 2, H, spacing):
            ctx.rectangle(gx - 1, gy - 1, 2, 2)
    ctx.fill()
    ctx.restore()


def draw_crosshair_grid(ctx: cairo.Context, alpha: float = 0.85, draw_labels: bool = True) -> None:
    """Technical HUD crosshair grid matching the reference video."""
    xs = [320, 960, 1600]
    ys = [210, 540, 870]
    ctx.save()
    ctx.set_source_rgba(HAIR[0] * 1.45, HAIR[1] * 1.45, HAIR[2] * 1.45, 0.55 * alpha)
    ctx.set_line_width(1.0)
    for x in xs:
        ctx.move_to(x, 0)
        ctx.line_to(x, H)
    for y in ys:
        ctx.move_to(0, y)
        ctx.line_to(W, y)
    ctx.stroke()

    # Crisp '+' ticks at intersections
    ctx.set_source_rgba(TEXT2[0], TEXT2[1], TEXT2[2], 0.60 * alpha)
    ctx.set_line_width(1.5)
    for x in xs:
        for y in ys:
            ctx.move_to(x - 7, y)
            ctx.line_to(x + 7, y)
            ctx.move_to(x, y - 7)
            ctx.line_to(x, y + 7)
    ctx.stroke()
    ctx.restore()

    if draw_labels:
        draw_text(ctx, "[OSD-575]", 1370, 175, "mono_regular", 15, TEXT2, alpha=0.55 * alpha, tracking=0.8)
        draw_text(ctx, "[CC0-1.0]", 342, 886, "mono_regular", 15, TEXT2, alpha=0.50 * alpha, tracking=0.8)
        draw_text(ctx, "[L-92 / R+194]", 1430, 886, "mono_regular", 15, TEXT2, alpha=0.50 * alpha, tracking=0.8)


def draw_pulse_mark(
    ctx: cairo.Context,
    cx: float,
    cy: float,
    radius: float,
    rotation: float = 0.0,
    alpha: float = 1.0,
    teal_inner: bool = True,
) -> None:
    """Geometric hexagonal Pulse-0G emblem: clean white broken hexagon + inner telemetry ring."""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rotation)

    # Outer crisp hexagon segmented into 3 technical arcs (mirrors reference mark silhouette)
    pts = []
    for k in range(6):
        ang = math.radians(-90 + k * 60)
        pts.append((math.cos(ang) * radius, math.sin(ang) * radius))

    ctx.set_line_width(max(3.0, radius * 0.24))
    ctx.set_line_cap(cairo.LINE_CAP_BUTT)
    ctx.set_line_join(cairo.LINE_JOIN_MITER)
    ctx.set_source_rgba(TEXT[0], TEXT[1], TEXT[2], alpha)

    # Draw 3 double-edge chevrons around the hexagon so it has technical open slots
    for start_idx in (0, 2, 4):
        p0 = pts[start_idx]
        p1 = pts[(start_idx + 1) % 6]
        p2 = pts[(start_idx + 2) % 6]
        # Inset slightly from p0 and p2 to create clean diagonal slots
        a0 = (p0[0] * 0.86 + p1[0] * 0.14, p0[1] * 0.86 + p1[1] * 0.14)
        a2 = (p2[0] * 0.86 + p1[0] * 0.14, p2[1] * 0.86 + p1[1] * 0.14)
        ctx.move_to(a0[0], a0[1])
        ctx.line_to(p1[0], p1[1])
        ctx.line_to(a2[0], a2[1])
    ctx.stroke()

    if teal_inner:
        ctx.rotate(-rotation)
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


# Precomputed halftone dot grid coordinates for Scene 3 & 4 (pure 2D procedural motion field)
_HT_COLS = 96
_HT_ROWS = 54
_HT_XS = np.linspace(10, W - 10, _HT_COLS)
_HT_YS = np.linspace(10, H - 10, _HT_ROWS)
_HT_GX, _HT_GY = np.meshgrid(_HT_XS, _HT_YS)


def draw_halftone_horizon(ctx: cairo.Context, t: float, intensity: float = 1.0) -> None:
    """Procedural 2D halftone dot-matrix orbital horizon & telemetry plume (zero photos, zero 3D)."""
    ctx.save()
    # Normalized coords
    nx = (_HT_GX - W * 0.5) / (W * 0.5)
    ny = (_HT_GY - H * 0.62) / (H * 0.5)

    # Analytical telemetry ridge + radial thruster/beacon plume
    ridge = -0.18 * np.cos(nx * 2.3 + t * 0.35) - 0.10 * np.sin(nx * 5.2 - t * 0.6)
    plume = np.exp(-((nx * 2.1) ** 2) * 1.8) * np.exp(-((ny + 0.15) ** 2) * 2.4)
    horizon = np.exp(-((ny - ridge) ** 2) * 7.5)
    field = np.clip((horizon * 0.65 + plume * 0.95) * intensity, 0.0, 1.0)

    # Subtle scanline glitch columns
    col_jitter = 0.08 * np.sin(_HT_GX * 0.05 + t * 9.0)
    field = np.clip(field + col_jitter * (field > 0.25), 0.0, 1.0)

    step_x = (W - 20) / _HT_COLS
    step_y = (H - 20) / _HT_ROWS

    for r_idx in range(_HT_ROWS):
        for c_idx in range(_HT_COLS):
            val = float(field[r_idx, c_idx])
            if val < 0.09:
                continue
            # Color ramp: deep slate -> teal -> amber -> coral red at hot core
            if val < 0.38:
                u = val / 0.38
                col = (
                    SURFACE2[0] * (1 - u) + TEAL[0] * u * 0.55,
                    SURFACE2[1] * (1 - u) + TEAL[1] * u * 0.55,
                    SURFACE2[2] * (1 - u) + TEAL[2] * u * 0.55,
                )
            elif val < 0.72:
                u = (val - 0.38) / 0.34
                col = (
                    TEAL[0] * (1 - u) * 0.65 + AMBER[0] * u * 0.85,
                    TEAL[1] * (1 - u) * 0.65 + AMBER[1] * u * 0.85,
                    TEAL[2] * (1 - u) * 0.65 + AMBER[2] * u * 0.85,
                )
            else:
                u = (val - 0.72) / 0.28
                col = (
                    AMBER[0] * (1 - u) * 0.9 + RED[0] * u,
                    AMBER[1] * (1 - u) * 0.9 + RED[1] * u,
                    AMBER[2] * (1 - u) * 0.9 + RED[2] * u,
                )

            dot_w = max(2.0, step_x * 0.78 * val)
            dot_h = max(2.0, step_y * 0.78 * val)
            px = float(_HT_GX[r_idx, c_idx]) - dot_w * 0.5
            py = float(_HT_GY[r_idx, c_idx]) - dot_h * 0.5
            ctx.set_source_rgba(col[0], col[1], col[2], 0.85 * intensity)
            ctx.rectangle(px, py, dot_w, dot_h)
            ctx.fill()
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
    cols: int = 38,
    rows: int = 4,
) -> None:
    """Crisp dotted LED matrix meter matching the benchmark bar aesthetic in the reference video."""
    ctx.save()
    cell_w = w / cols
    cell_h = h / rows
    gap_x = max(1.5, cell_w * 0.28)
    gap_y = max(1.5, cell_h * 0.28)
    dw = max(1.5, cell_w - gap_x)
    dh = max(1.5, cell_h - gap_y)
    lit_cols = int(round(clamp(fill_ratio) * cols))
    for c in range(cols):
        is_lit = c < lit_cols
        col_alpha = (0.95 if is_lit else 0.14) * alpha
        ctx.set_source_rgba(color[0], color[1], color[2], col_alpha)
        for r in range(rows):
            ctx.rectangle(x + c * cell_w, y + r * cell_h, dw, dh)
    ctx.fill()
    ctx.restore()


def draw_metric_card(
    ctx: cairo.Context,
    cx: float,
    cy: float,
    w: float,
    h: float,
    title: str,
    badge: str,
    badge_color: Tuple[float, float, float],
    value_str: str,
    accent_color: Tuple[float, float, float],
    fill_ratio: float,
    scale: float = 1.0,
    alpha: float = 1.0,
    darken: float = 0.0,
) -> None:
    """Draw a sleek dark Pulse-0G instrument card with left accent bar and LED dot meter."""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(scale, scale)

    x0, y0 = -w / 2.0, -h / 2.0
    bg_mix = 1.0 - darken * 0.45
    draw_rounded_rect(ctx, x0, y0, w, h, 8.0)
    ctx.set_source_rgba(SURFACE[0] * bg_mix, SURFACE[1] * bg_mix, SURFACE[2] * bg_mix, alpha)
    ctx.fill_preserve()
    ctx.set_source_rgba(HAIR[0] * 1.6, HAIR[1] * 1.6, HAIR[2] * 1.6, 0.95 * alpha)
    ctx.set_line_width(1.6)
    ctx.stroke()

    # Left vertical status accent stripe
    ctx.set_source_rgba(accent_color[0], accent_color[1], accent_color[2], alpha)
    ctx.rectangle(x0 + 1.5, y0 + 1.5, 10.0, h - 3.0)
    ctx.fill()

    # Title + Badge + Value + LED Bar
    draw_text(ctx, title, x0 + 38, y0 + 28, "sans_bold", 26, TEXT, alpha=alpha * (1.0 - darken * 0.4))
    draw_pill(ctx, x0 + w - 32, y0 + 26, badge, badge_color, alpha=alpha * (1.0 - darken * 0.35), anchor="tr", font_size=14, px=11, py=5)
    draw_led_bar(ctx, x0 + 38, y0 + h - 54, w - 260, 28, fill_ratio, accent_color, alpha=alpha * (1.0 - darken * 0.35), cols=36, rows=4)
    draw_text(ctx, value_str, x0 + w - 32, y0 + h - 40, "mono_bold", 24, TEXT, alpha=alpha * (1.0 - darken * 0.35), anchor="cr")

    ctx.restore()


# ---------------------------------------------------------------------------
# Scene Renderers
# ---------------------------------------------------------------------------

def render_scene_1_boot(ctx: cairo.Context, t: float) -> None:
    """0.00s - 1.00s: Giant typewriter INITIALIZING| on dark dot-matrix grid."""
    draw_dot_grid(ctx, spacing=72, alpha=0.35)
    full = "INITIALIZING"
    p = progress(t, 0.05, 0.70)
    n_chars = int(math.floor(p * len(full)))
    shown = full[:n_chars]
    blink = 1.0 if (t < 0.72 or int(t * 6) % 2 == 0) else 0.0

    # Left-aligned massive clean sans-serif matching 00:00
    x_start = 160.0
    tw, th = draw_text(ctx, shown, x_start, H / 2.0, "sans_semibold", 168, TEXT, alpha=1.0, anchor="cl", tracking=4.0)
    cursor_x = x_start + (tw + 14 if shown else 0)
    if blink > 0.5:
        ctx.save()
        ctx.set_source_rgba(TEXT[0], TEXT[1], TEXT[2], 0.95)
        ctx.rectangle(cursor_x, H / 2.0 - 92, 8, 184)
        ctx.fill()
        ctx.restore()


def render_scene_2_parentheses(ctx: cairo.Context, t: float) -> None:
    """1.00s - 3.30s: ( pulse [MARK] 0g ) -> ( 250M miles [MARK] no doctor ) -> portal zoom."""
    lt = t - 1.00
    draw_crosshair_grid(ctx, alpha=1.0, draw_labels=True)

    # Portal zoom at end (2.85s - 3.30s)
    zoom_p = ease_in_expo(progress(t, 2.82, 3.30))
    mark_scale = 1.0 + zoom_p * 24.0
    text_alpha = 1.0 - clamp(zoom_p * 4.5)

    # Rotation snap at 2.00s
    rot_p = ease_out_cubic(progress(t, 1.95, 2.35))
    rot = rot_p * math.pi / 3.0

    if t < 2.00:
        in_p = ease_out_cubic(progress(lt, 0.0, 0.35))
        draw_text(ctx, "( pulse", W / 2.0 - 150, H / 2.0, "mono_regular", 38, TEXT, alpha=in_p * text_alpha, anchor="cr", tracking=1.0)
        draw_text(ctx, "0g )", W / 2.0 + 150, H / 2.0, "mono_regular", 38, TEXT, alpha=in_p * text_alpha, anchor="cl", tracking=1.0)
    else:
        swap_p = ease_out_cubic(progress(t, 2.00, 2.25))
        draw_text(ctx, "( 250M miles", W / 2.0 - 155, H / 2.0, "mono_regular", 36, TEXT, alpha=swap_p * text_alpha, anchor="cr", tracking=0.8)
        draw_text(ctx, "no doctor )", W / 2.0 + 155, H / 2.0, "mono_italic", 36, RED, alpha=swap_p * text_alpha, anchor="cl", tracking=0.8)

    draw_pulse_mark(ctx, W / 2.0, H / 2.0, radius=74.0 * mark_scale, rotation=rot, alpha=1.0, teal_inner=(zoom_p < 0.35))


def render_scene_3_halftone_wipe(ctx: cairo.Context, t: float) -> None:
    """3.30s - 5.30s: Procedural halftone orbital wave + BASELINE// [TEAL BLOCK]."""
    draw_halftone_horizon(ctx, t, intensity=0.95)

    # Subtle top-right badge for context
    draw_pill(ctx, W - 70, 54, "TWO-LAYER BASELINE", TEAL, alpha=0.85, anchor="tr", font_size=15)

    p_line = ease_out_cubic(progress(t, 3.45, 3.85))
    p_text = ease_out_cubic(progress(t, 3.55, 3.95))
    p_block = ease_out_cubic(progress(t, 3.78, 4.15))
    p_reveal = ease_out_cubic(progress(t, 4.30, 4.65))

    y_mid = H / 2.0
    # Thin horizontal white hairline from left
    ctx.save()
    ctx.set_source_rgba(TEXT[0], TEXT[1], TEXT[2], 0.9)
    ctx.set_line_width(2.5)
    ctx.move_to(260, y_mid)
    ctx.line_to(260 + 270 * p_line, y_mid)
    ctx.stroke()
    ctx.restore()

    draw_text(ctx, "BASELINE//", 560 + (1.0 - p_text) * 40, y_mid, "sans_extrabold", 76, TEXT, alpha=p_text, anchor="cl", tracking=2.0)

    # Solid teal block wiping across / revealing SELF-CHECK
    bx = 1040
    bw = 430 * p_block
    bh = 98
    if bw > 2:
        ctx.save()
        ctx.rectangle(bx, y_mid - bh / 2.0, bw, bh)
        ctx.set_source_rgba(TEAL[0], TEAL[1], TEAL[2], 1.0)
        ctx.fill()
        ctx.restore()
        if p_reveal > 0.05:
            draw_text(ctx, "OWN BASELINE", bx + 24, y_mid, "mono_bold", 38, BG, alpha=p_reveal, anchor="cl", tracking=1.5)


def render_scene_4_counter(ctx: cairo.Context, t: float) -> None:
    """5.30s - 7.30s: Giant telemetry counter locking onto 2.9 h over halftone field."""
    draw_halftone_horizon(ctx, t, intensity=0.88)

    # Vertical center crosshair line + top badge
    ctx.save()
    ctx.set_source_rgba(TEXT2[0], TEXT2[1], TEXT2[2], 0.38)
    ctx.set_line_width(1.5)
    ctx.move_to(W / 2.0, 0)
    ctx.line_to(W / 2.0, H)
    ctx.stroke()
    ctx.restore()

    draw_pill(ctx, W / 2.0, 290, "SYNTHETIC · DAY 180", VIOLET, alpha=0.95, anchor="cc", font_size=18)

    # Stepped telemetry count-up landing cleanly on 2.9 h
    p = ease_out_cubic(progress(t, 5.42, 6.72))
    val = round(2.9 * p, 1)
    # Snap final hold cleanly to 2.9
    if t >= 6.72:
        val = 2.9
    num_str = f"{val:.1f} h"

    # Subtle glitch accent rects during active counting (mirrors 00:05-00:06)
    if 5.45 <= t < 6.70 and int(t * 24) % 3 == 0:
        ctx.save()
        rng = np.random.default_rng(int(t * 60))
        for _ in range(4):
            gx = W / 2.0 + float(rng.integers(-280, 240))
            gy = H / 2.0 + float(rng.integers(-90, 80))
            gw = float(rng.integers(24, 95))
            gh = float(rng.integers(10, 24))
            col = TEAL if rng.random() > 0.4 else RED
            ctx.set_source_rgba(col[0], col[1], col[2], 0.35)
            ctx.rectangle(gx, gy, gw, gh)
            ctx.fill()
        ctx.restore()

    draw_text(ctx, num_str, W / 2.0, H / 2.0 + 14, "mono_bold", 190, TEXT, alpha=1.0, anchor="cc", tracking=-2.0)
    draw_pill(ctx, W / 2.0, H / 2.0 + 158, "SLEEP DURATION · DAY 180", TEXT2, alpha=0.95, anchor="cc", font_size=17, px=16, py=6)


def _draw_stat_code_panel(
    ctx: cairo.Context,
    offset_x: float,
    badge_text: str,
    badge_color: Tuple[float, float, float],
    big_stat: str,
    delta_label: str | None,
    delta_color: Tuple[float, float, float],
    code_lines: list[list[Tuple[str, Tuple[float, float, float]]]],
    reveal_p: float,
) -> None:
    """Shared layout for Scenes 5 & 6 (mirrors 00:07 and 00:09)."""
    ctx.save()
    ctx.translate(offset_x, 0)

    draw_pill(ctx, W - 110, 72, badge_text, badge_color, alpha=0.95, anchor="tr", font_size=17)

    # Huge upper-left number
    draw_text(ctx, big_stat, 160, 175, "sans_bold", 250, TEXT, alpha=1.0, anchor="tl", tracking=-4.0)

    if delta_label:
        # Color + Shape (warning triangle) + Text redundancy
        draw_pill(ctx, 168, 495, f"▼ {delta_label}", delta_color, alpha=clamp(reveal_p * 2.0), anchor="tl", font_size=22, px=18, py=9)

    # Syntax-highlighted monospace code block underneath
    y_code = 585 if delta_label else 535
    line_h = 56
    total_chars = sum(sum(len(seg[0]) for seg in line) for line in code_lines)
    chars_budget = int(round(clamp(reveal_p) * total_chars))

    for li, line in enumerate(code_lines):
        cx = 165.0
        cy = y_code + li * line_h
        for seg_text, seg_col in line:
            if chars_budget <= 0:
                break
            take = min(len(seg_text), chars_budget)
            part = seg_text[:take]
            chars_budget -= take
            draw_text(ctx, part, cx, cy, "mono_regular", 36, seg_col, alpha=1.0, anchor="tl", tracking=0.3, tight_y=False)
            # Advance accurately using font length
            font = get_font("mono_regular", 36)
            cx += font.getlength(part) + len(part) * 0.3

    ctx.restore()


def render_scene_5_and_6_stats(ctx: cairo.Context, t: float) -> None:
    """7.30s - 12.10s: Giant stat 2.9 h + code -> smooth pan -> 19 ANALYTES (OSD-575) + code."""
    draw_crosshair_grid(ctx, alpha=0.85, draw_labels=False)

    # Pan transition between 9.25s and 9.75s (mirrors 00:08)
    pan_p = ease_in_out_cubic(progress(t, 9.25, 9.75))
    x1 = -pan_p * W
    x2 = (1.0 - pan_p) * W

    if pan_p < 0.999:
        rev1 = progress(t, 7.35, 8.65)
        code1 = [
            [("baseline", TEXT2), (".", TEXT), ("compare", TEAL), ("(", TEXT), ("SYNTHETIC", VIOLET), (");", TEXT)],
            [("sleep_day180", TEXT), (" = ", TEXT2), ("2.9 h", AMBER), (";", TEXT)],
            [("vs_own_baseline", TEXT), (" = ", TEXT2), ("-60%", RED), ("; // out of band", TEXT2)],
        ]
        _draw_stat_code_panel(
            ctx,
            x1,
            "SYNTHETIC · DEMO SCENARIO",
            VIOLET,
            "2.9 h",
            "-60% VS OWN BASELINE",
            RED,
            code1,
            rev1,
        )

    if pan_p > 0.001:
        rev2 = progress(t, 9.75, 11.20)
        code2 = [
            [("osdr", TEXT2), (".", TEXT), ("ingest", TEAL), ("(", TEXT), ('"OSD-575"', GREEN), (");", TEXT)],
            [("crew", TEXT), (" = ", TEXT2), ("4", TEAL), ("; ", TEXT2), ("samples", TEXT), (" = ", TEXT2), ("7", TEAL), (";", TEXT)],
            [("missing_sleep", TEXT), (" = ", TEXT2), ("4", AMBER), ("; // defects kept", TEXT2)],
        ]
        _draw_stat_code_panel(
            ctx,
            x2,
            "NASA OSDR OSD-575 · CC0",
            TEAL,
            "19 ANALYTES",
            "4 CREW · 7 TIMEPOINTS",
            TEAL,
            code2,
            rev2,
        )


def render_scene_7_cards_and_verifier(ctx: cairo.Context, t: float) -> None:
    """12.10s - 18.80s: Stacked telemetry cards -> Claim Verifier strike-out -> Side statement."""
    # Subtle dark atmospheric horizon wash (pure 2D gradient, no photos)
    ctx.save()
    grad = cairo.LinearGradient(0, 0, 0, H)
    grad.add_color_stop_rgba(0.0, BG[0], BG[1], BG[2], 1.0)
    grad.add_color_stop_rgba(0.55, SURFACE2[0], SURFACE2[1], SURFACE2[2], 0.85)
    grad.add_color_stop_rgba(1.0, BG[0], BG[1], BG[2], 1.0)
    ctx.set_source(grad)
    ctx.paint()
    ctx.restore()

    draw_dot_grid(ctx, spacing=80, alpha=0.20)

    # Phase 7a: 12.10s - 13.70s -> 4 stacked metric cards cascade & flatten
    # Phase 7b: 13.70s - 16.30s -> Focused Verifier Card + typed header + dramatic red strike-out
    # Phase 7c: 16.30s - 18.80s -> Card slides left, right side snaps in 3 bold stacked lines

    stack_flatten = ease_in_out_cubic(progress(t, 12.90, 13.65))
    slide_left_p = ease_in_out_cubic(progress(t, 16.25, 16.85))

    if t < 13.70:
        enter_p = ease_out_cubic(progress(t, 12.10, 12.75))
        cards = [
            ("MOOD · DAY 180", "SYNTHETIC", VIOLET, "4.3 / 10", AMBER, 0.43),
            ("RADIATION DOSE", "SYNTHETIC", VIOLET, "76 / 600 mSv", TEAL, 0.25),
            ("OUT OF BAND", "SYNTHETIC", VIOLET, "2 INDICATORS", RED, 0.65),
        ]
        # Back 3 cards fade/recede as stack flattens onto hero card
        back_alpha = (1.0 - stack_flatten) * enter_p
        if back_alpha > 0.01:
            for idx, (title, badge, bcol, val, acol, fill_r) in enumerate(cards):
                depth = 3 - idx  # 3, 2, 1
                cy = H / 2.0 + 80 - depth * 78 * (1.0 - stack_flatten * 0.55) + (1.0 - enter_p) * 90
                sc = 1.0 - depth * 0.055
                draw_metric_card(
                    ctx,
                    W / 2.0,
                    cy,
                    1040,
                    195,
                    title,
                    badge,
                    bcol,
                    val,
                    acol,
                    fill_r,
                    scale=sc,
                    alpha=back_alpha,
                    darken=depth * 0.16,
                )

    # Front Hero Card geometry (interpolates from stack front -> center flat -> left side)
    card_w = 1040.0 - slide_left_p * 170.0  # 1040 -> 870
    card_h = 260.0 + stack_flatten * 80.0   # transitions cleanly to 340px tall verifier card
    if t >= 13.70:
        card_h = 340.0
    card_cx = W / 2.0 - slide_left_p * 425.0  # 960 -> 535
    card_cy = H / 2.0 + 96.0 - stack_flatten * 56.0 + slide_left_p * 10.0

    # Double hairline outer frame (mirrors 00:11-00:12!)
    if t >= 12.90:
        frame_alpha = (1.0 - slide_left_p * 0.85) * ease_out_cubic(progress(t, 12.90, 13.55))
        if frame_alpha > 0.01:
            ctx.save()
            for pad_f, a_mul in ((22, 0.35), (44, 0.16)):
                draw_rounded_rect(
                    ctx,
                    card_cx - card_w / 2.0 - pad_f,
                    card_cy - card_h / 2.0 - pad_f,
                    card_w + pad_f * 2,
                    card_h + pad_f * 2,
                    10.0,
                )
                ctx.set_source_rgba(TEXT2[0], TEXT2[1], TEXT2[2], frame_alpha * a_mul)
                ctx.set_line_width(1.2)
                ctx.stroke()
            ctx.restore()

    # Typed header above card (13.65s -> 16.35s, fades cleanly as card slides left)
    if 13.55 <= t <= 16.55:
        hdr_alpha = 1.0 - ease_out_cubic(progress(t, 16.15, 16.50))
        line1 = "EVERY CLAIM IS TRACED"
        line2 = "or struck out on screen"
        p_type = progress(t, 13.65, 14.55)
        total_c = len(line1) + len(line2)
        c_now = int(round(p_type * total_c))
        s1 = line1[: min(len(line1), c_now)]
        s2 = line2[: max(0, c_now - len(line1))]
        cursor = "|" if (int(t * 5) % 2 == 0 or p_type < 1.0) else ""
        hx = card_cx - card_w / 2.0
        draw_text(ctx, s1, hx, card_cy - card_h / 2.0 - 148, "sans_bold", 38, TEXT, alpha=hdr_alpha, anchor="tl", tracking=1.0)
        draw_text(ctx, s2 + cursor, hx, card_cy - card_h / 2.0 - 94, "mono_regular", 30, TEXT2, alpha=hdr_alpha, anchor="tl", tracking=0.5)

    # Draw the Hero Verifier Card itself
    strike_p = ease_out_cubic(progress(t, 15.05, 15.55))
    post_strike = t >= 15.05
    card_accent = RED if strike_p > 0.35 else TEAL

    ctx.save()
    x0, y0 = card_cx - card_w / 2.0, card_cy - card_h / 2.0
    draw_rounded_rect(ctx, x0, y0, card_w, card_h, 10.0)
    ctx.set_source_rgba(SURFACE[0], SURFACE[1], SURFACE[2], 1.0)
    ctx.fill_preserve()
    border_col = RED if strike_p > 0.35 else HAIR
    ctx.set_source_rgba(border_col[0], border_col[1], border_col[2], 0.85 if strike_p > 0.35 else 1.0)
    ctx.set_line_width(2.0 if strike_p > 0.35 else 1.6)
    ctx.stroke()

    # Left status bar
    ctx.set_source_rgba(card_accent[0], card_accent[1], card_accent[2], 1.0)
    ctx.rectangle(x0 + 1.5, y0 + 1.5, 11.0, card_h - 3.0)
    ctx.fill()
    ctx.restore()

    # Card Top Header
    draw_text(ctx, "CLAIM VERIFIER", x0 + 38, y0 + 26, "sans_bold", 26, TEXT, alpha=1.0, tracking=0.8)
    draw_pill(ctx, x0 + card_w - 30, y0 + 24, "DETERMINISTIC", TEAL, alpha=0.95, anchor="tr", font_size=14, px=11, py=5)

    if t < 13.70:
        # Early compact preview inside stacked view before card expands
        draw_text(ctx, "2 CLAIMS · VERIFYING DATA ANCHORS", x0 + 38, y0 + 102, "mono_regular", 20, TEXT2, alpha=0.85)
        draw_led_bar(ctx, x0 + 38, y0 + card_h - 62, card_w - 260, 28, 0.82, TEAL, alpha=1.0, cols=36, rows=4)
        draw_text(ctx, "ANCHOR CHECK", x0 + card_w - 30, y0 + card_h - 48, "mono_bold", 20, TEAL, alpha=1.0, anchor="cr")
    else:
        # Row 1: Verified claim (Color + Shape + Text)
        r1_a = ease_out_cubic(progress(t, 13.85, 14.20))
        r1_y = y0 + 104
        ctx.save()
        ctx.set_source_rgba(GREEN[0], GREEN[1], GREEN[2], r1_a)
        ctx.rectangle(x0 + 38, r1_y + 6, 14, 14)
        ctx.fill()
        ctx.restore()
        draw_text(ctx, '"Sleep: 2.9 h (-60% vs baseline)"', x0 + 66, r1_y, "mono_regular", 21, TEXT, alpha=r1_a)
        draw_pill(ctx, x0 + card_w - 30, r1_y - 3, "✓ ANCHORED", GREEN, alpha=r1_a, anchor="tr", font_size=14, px=10, py=4)

        # Divider
        ctx.save()
        ctx.set_source_rgba(HAIR[0] * 1.6, HAIR[1] * 1.6, HAIR[2] * 1.6, 0.9)
        ctx.set_line_width(1.0)
        ctx.move_to(x0 + 38, y0 + 156)
        ctx.line_to(x0 + card_w - 30, y0 + 156)
        ctx.stroke()
        ctx.restore()

        # Row 2: Unanchored claim -> DRAMATIC RED STRIKE-THROUGH HERO MOMENT
        r2_a = ease_out_cubic(progress(t, 14.40, 14.75))
        r2_y = y0 + 184
        claim2 = '"Crew recovery trending normal"'
        claim_col = RED if strike_p > 0.5 else TEXT

        # Indicator square changes from neutral to red X badge
        ctx.save()
        ind_col = RED if post_strike else TEXT2
        ctx.set_source_rgba(ind_col[0], ind_col[1], ind_col[2], r2_a)
        ctx.rectangle(x0 + 38, r2_y + 6, 14, 14)
        ctx.fill()
        ctx.restore()

        cw, ch = draw_text(ctx, claim2, x0 + 66, r2_y, "mono_regular", 22, claim_col, alpha=r2_a * (0.85 if strike_p > 0.7 else 1.0))

        # Animated thick red strike-through line (stroke-dashoffset style!)
        if strike_p > 0.01:
            ctx.save()
            ctx.set_source_rgba(RED[0], RED[1], RED[2], 1.0)
            ctx.set_line_width(3.5)
            ctx.set_line_cap(cairo.LINE_CAP_SQUARE)
            sx0 = x0 + 62
            sy = r2_y + ch * 0.56
            ctx.move_to(sx0, sy)
            ctx.line_to(sx0 + (cw + 12) * strike_p, sy)
            ctx.stroke()
            ctx.restore()

        if strike_p > 0.45:
            badge_a = ease_out_cubic((strike_p - 0.45) / 0.55)
            draw_pill(ctx, x0 + card_w - 30, r2_y - 3, "✕ STRUCK OUT", RED, alpha=badge_a, anchor="tr", font_size=14, px=10, py=4)
            draw_text(ctx, "reason: no data anchor in OSD-575 or baseline", x0 + 66, r2_y + 38, "mono_italic", 16, RED, alpha=badge_a * 0.92)

        # Bottom LED meter shifts from teal to red alert on strike-out
        meter_fill = 0.86 if not post_strike else 1.0
        draw_led_bar(ctx, x0 + 38, y0 + card_h - 52, card_w - 280, 24, meter_fill, card_accent, alpha=0.95, cols=34, rows=3)
        status_label = "STRUCK ON SCREEN" if strike_p > 0.5 else "VERIFYING..."
        draw_text(ctx, status_label, x0 + card_w - 30, y0 + card_h - 40, "mono_bold", 17, card_accent, alpha=1.0, anchor="cr")

    # Phase 7c: Right-side 3 stacked punchy lines (mirrors 00:13-00:15!)
    if t >= 16.45:
        rx = 1045.0
        p1 = ease_out_cubic(progress(t, 16.45, 16.72))
        p2 = ease_out_cubic(progress(t, 16.72, 16.99))
        p3 = ease_out_cubic(progress(t, 16.99, 17.28))
        p4 = ease_out_cubic(progress(t, 17.35, 17.75))

        draw_text(ctx, "EVERY CLAIM", rx + (1.0 - p1) * 35, 395, "sans_extrabold", 76, TEXT, alpha=p1, anchor="tl", tracking=1.5)
        draw_text(ctx, "ANCHORED", rx + (1.0 - p2) * 35, 488, "sans_extrabold", 76, TEAL, alpha=p2, anchor="tl", tracking=1.5)
        draw_text(ctx, "OR STRUCK OUT", rx + (1.0 - p3) * 35, 581, "sans_extrabold", 76, RED, alpha=p3, anchor="tl", tracking=1.5)

        draw_text(ctx, "Out of range? Export a case file.", rx, 695, "mono_regular", 24, TEXT2, alpha=p4, anchor="tl", tracking=0.4)


def render_scene_8_wordmark(ctx: cairo.Context, t: float) -> None:
    """18.80s - 20.60s: Stark dark canvas + centered PULSE-0G wordmark (mirrors 00:16)."""
    p = ease_out_cubic(progress(t, 18.80, 19.15))
    draw_text(ctx, "PULSE-0G", W / 2.0, H / 2.0, "mono_bold", 92, TEAL, alpha=p, anchor="cc", tracking=6.0)


def render_scene_9_endcard(ctx: cairo.Context, t: float) -> None:
    """20.60s - 23.00s: Lockup mark + NASA Space Apps 2026 + bottom typewriter (mirrors 00:18-00:20)."""
    p_logo = ease_out_cubic(progress(t, 20.60, 21.00))
    # Centered mark + divider + competition lockup
    draw_pulse_mark(ctx, W / 2.0 - 255, H / 2.0 - 20, radius=56.0, rotation=0.0, alpha=p_logo, teal_inner=True)

    ctx.save()
    ctx.set_source_rgba(TEXT2[0], TEXT2[1], TEXT2[2], 0.55 * p_logo)
    ctx.set_line_width(2.0)
    ctx.move_to(W / 2.0 - 155, H / 2.0 - 60)
    ctx.line_to(W / 2.0 - 155, H / 2.0 + 20)
    ctx.stroke()
    ctx.restore()

    draw_text(ctx, "PULSE-0G", W / 2.0 - 115, H / 2.0 - 46, "sans_extrabold", 48, TEXT, alpha=p_logo, anchor="tl", tracking=2.0)
    draw_text(ctx, "NASA SPACE APPS 2026 · CÓRDOBA", W / 2.0 - 115, H / 2.0 + 12, "mono_regular", 20, TEAL, alpha=p_logo * 0.9, anchor="tl", tracking=1.0)

    # Bottom small monospace typing
    sub = "No diagnosis · Every claim traced"
    p_sub = progress(t, 20.95, 22.05)
    shown = sub[: int(round(p_sub * len(sub)))]
    cursor = "|" if (int(t * 5) % 2 == 0 or p_sub < 1.0) else ""
    draw_text(ctx, shown + cursor, W / 2.0, H - 96, "mono_regular", 24, TEXT2, alpha=0.95, anchor="cc", tracking=0.8)


def render_frame(surface: cairo.ImageSurface, frame_idx: int) -> None:
    t = frame_idx / FPS
    ctx = cairo.Context(surface)

    # Clear background to #0A0E13
    ctx.set_source_rgb(BG[0], BG[1], BG[2])
    ctx.paint()

    if t < 1.00:
        render_scene_1_boot(ctx, t)
    elif t < 3.30:
        render_scene_2_parentheses(ctx, t)
    elif t < 5.30:
        render_scene_3_halftone_wipe(ctx, t)
    elif t < 7.30:
        render_scene_4_counter(ctx, t)
    elif t < 12.10:
        render_scene_5_and_6_stats(ctx, t)
    elif t < 18.80:
        render_scene_7_cards_and_verifier(ctx, t)
    elif t < 20.60:
        render_scene_8_wordmark(ctx, t)
    else:
        render_scene_9_endcard(ctx, t)


def surface_to_rgb24(surface: cairo.ImageSurface) -> bytes:
    """Convert Cairo ARGB32 (BGRA little-endian) surface directly to RGB24 bytes."""
    buf = np.frombuffer(surface.get_data(), dtype=np.uint8).reshape((H, W, 4))
    # BGRA -> RGB
    return buf[:, :, 2::-1].tobytes()


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(base_dir)
    deliverables_dir = os.path.join(repo_root, "docs", "deliverables")
    os.makedirs(deliverables_dir, exist_ok=True)

    audio_path = os.path.join(base_dir, "pulse_0g_audio.wav")
    out_mp4 = os.path.join(deliverables_dir, "pulse_0g_1080p.mp4")

    if "--stills-only" in sys.argv:
        # Render key validation stills for quick visual inspection
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        checks = {
            "still_01_lockup.png": int(2.25 * FPS),
            "still_01b_halftone.png": int(4.75 * FPS),
            "still_01c_counter.png": int(6.85 * FPS),
            "still_02_stat_code.png": int(8.80 * FPS),
            "still_02b_stacked.png": int(12.75 * FPS),
            "still_03_verifier_strike.png": int(15.75 * FPS),
            "still_04_verifier_side.png": int(17.80 * FPS),
            "still_05_endcard.png": int(22.30 * FPS),
        }
        for fname, fidx in checks.items():
            render_frame(surface, fidx)
            out_png = os.path.join(base_dir, fname)
            surface.write_to_png(out_png)
            print(f"Saved {out_png}")
        return

    # Ensure procedural audio exists
    if not os.path.exists(audio_path):
        from generate_audio import build_audio
        build_audio(audio_path)

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}",
        "-r", str(FPS),
        "-i", "-",
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "16",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        out_mp4,
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    # Save 3 deliverables stills directly while encoding
    still_frames = {
        int(8.90 * FPS): os.path.join(deliverables_dir, "still_01_baseline_metric.png"),
        int(15.80 * FPS): os.path.join(deliverables_dir, "still_02_claim_struck.png"),
        int(17.90 * FPS): os.path.join(deliverables_dir, "still_03_every_claim_traced.png"),
    }

    for fidx in range(TOTAL_FRAMES):
        render_frame(surface, fidx)
        if fidx in still_frames:
            surface.write_to_png(still_frames[fidx])
        proc.stdin.write(surface_to_rgb24(surface))
        if fidx % 90 == 0 or fidx == TOTAL_FRAMES - 1:
            print(f"Rendered {fidx + 1}/{TOTAL_FRAMES} frames ({(fidx + 1) / TOTAL_FRAMES * 100:.0f}%)", flush=True)

    proc.stdin.close()
    ret = proc.wait()
    if ret != 0:
        raise RuntimeError(f"ffmpeg failed with exit code {ret}")
    print(f"Done! Master video: {out_mp4}")


if __name__ == "__main__":
    main()
