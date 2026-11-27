#!/usr/bin/env python3
"""Builds the hand-made, animated SVGs used by the profile README.

Art direction: editorial type + small isometric illustrations, calm palette,
one accent colour (sodium-lamp amber at night, burnt orange by day).

Plain SVG only (CSS @keyframes + SMIL), which GitHub renders inside <img>.
No external fonts, scripts or <foreignObject>.

Run:  python3 scripts/build_assets.py      ->  assets/*.svg
"""
from __future__ import annotations

import math
import random
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

SANS = "'Inter','Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono','SFMono-Regular',Consolas,'Liberation Mono','DejaVu Sans Mono',Menlo,monospace"
SERIF = "Georgia,'Iowan Old Style','Times New Roman','Liberation Serif',serif"

T = {
    "dark": dict(
        bg="#0f1218", card="#12161e", line="#232a36", line2="#2e3644",
        ink="#ece6da", ink2="#c9c3b6", muted="#8b93a3", faint="#566072",
        accent="#f5a524", accent2="#ffcc6a", green="#6ee7a8", red="#ff5d5d",
        sky_star="#e9e4d8",
        slab=("#1d2330", "#161b25", "#11151d"),
        road="#0d1016", road_line="#3a4252", plot=("#202736", "#1a202b", "#141922"),
        bld=[("#2b3242", "#222838", "#191e29"),   # slate
             ("#3a2f2c", "#2f2624", "#231c1b"),   # brick
             ("#243236", "#1c282b", "#152022"),   # teal
             ("#30303c", "#262632", "#1d1d26")],  # graphite
        win_off="#141822", win_on=["#ffcc6a", "#ffd98f", "#f5a524"],
        tree=("#2c4a3f", "#1f3a31"), trunk="#3a2f2a",
        car=["#f5a524", "#d9d4c7", "#c4734f", "#7fa7a0"],
        cloud="#1a2030", cloud_op=0.55,
        crow="#07090d", crow_edge="#3b4458",
        langs=["#f5a524", "#e8e2d6", "#9aa3b2", "#c4734f", "#7fa7a0", "#5f6b7e"],
    ),
    "light": dict(
        bg="#f7f4ee", card="#fffdf9", line="#e5dfd2", line2="#d9d1c1",
        ink="#1b1915", ink2="#3b3730", muted="#6f6a60", faint="#a59f93",
        accent="#e0791b", accent2="#f0a24f", green="#2f9e66", red="#d9433b",
        sky_star="#c9bfae",
        slab=("#efe8da", "#dfd4c0", "#cdbfa6"),
        road="#d3cab9", road_line="#f7f4ee", plot=("#f6f1e7", "#e8dfcf", "#d8ccb6"),
        bld=[("#fbf8f2", "#e9e1d2", "#d6cbb6"),   # sand
             ("#f3dccd", "#e4bfa6", "#cf9f80"),   # terracotta
             ("#e3ebe0", "#c9d8c4", "#aec3a8"),   # sage
             ("#e4e9f0", "#c9d3e0", "#aebccf")],  # slate blue
        win_off="#9fb7cc", win_on=["#e8f0f7", "#ffffff", "#f6e2c8"],
        tree=("#9cc3a1", "#7aa984"), trunk="#9a7b62",
        car=["#e0791b", "#3b3730", "#c4734f", "#4f8278"],
        cloud="#ffffff", cloud_op=0.95,
        crow="#1b1915", crow_edge="#1b1915",
        langs=["#e0791b", "#1b1915", "#6f6a60", "#b4532d", "#4f8278", "#a9a294"],
    ),
}


def write(name: str, svg: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(svg.strip() + "\n", encoding="utf-8")
    print(f"wrote assets/{name} ({len(svg):,} bytes)")


def style_block(extra: str = "") -> str:
    return f"""<style>
    .sans {{ font-family: {SANS}; }}
    .mono {{ font-family: {MONO}; }}
    .serif {{ font-family: {SERIF}; }}
    {extra}
  </style>"""


# --------------------------------------------------------------------------
# Isometric helpers
# --------------------------------------------------------------------------
C30, S30 = math.cos(math.radians(30)), 0.5


class Iso:
    def __init__(self, s: float, ox: float, oy: float):
        self.s, self.ox, self.oy = s, ox, oy

    def p(self, x, y, z=0.0):
        return (self.ox + (x - y) * C30 * self.s, self.oy + (x + y) * S30 * self.s - z * self.s)

    def poly(self, pts, fill, extra=""):
        d = " ".join(f"{a:.1f},{b:.1f}" for a, b in (self.p(*q) for q in pts))
        return f'<polygon points="{d}" fill="{fill}" {extra}/>'

    def box(self, x, y, z, w, d, h, cols, extra=""):
        top, left, right = cols
        return (
            self.poly([(x + w, y, z), (x + w, y + d, z), (x + w, y + d, z + h), (x + w, y, z + h)], right, extra)
            + self.poly([(x, y + d, z), (x + w, y + d, z), (x + w, y + d, z + h), (x, y + d, z + h)], left, extra)
            + self.poly([(x, y, z + h), (x + w, y, z + h), (x + w, y + d, z + h), (x, y + d, z + h)], top, extra)
        )

    def cyl(self, x, y, z, r, h, cols):
        top, side, _ = cols
        cx, cy_top = self.p(x, y, z + h)
        _, cy_bot = self.p(x, y, z)
        rx, ry = 1.2247 * r * self.s, 0.7071 * r * self.s
        body = (f'<path d="M{cx - rx:.1f},{cy_top:.1f} L{cx - rx:.1f},{cy_bot:.1f} '
                f'A{rx:.1f},{ry:.1f} 0 0 0 {cx + rx:.1f},{cy_bot:.1f} L{cx + rx:.1f},{cy_top:.1f} Z" fill="{side}"/>')
        return body + f'<ellipse cx="{cx:.1f}" cy="{cy_top:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{top}"/>'


# --------------------------------------------------------------------------
# Banner: editorial type on the left, a small isometric city on the right
# --------------------------------------------------------------------------
# (x, y, w, d, h, palette index)
BUILDINGS = [
    (0.3, 0.3, 1.6, 2.3, 3.8, 0), (2.2, 0.3, 1.8, 1.4, 6.0, 3), (4.3, 0.3, 1.4, 2.3, 3.0, 1),
    (2.2, 1.9, 1.8, 0.8, 1.8, 2),
    (7.3, 0.3, 2.4, 1.2, 3.4, 2), (7.3, 1.8, 1.1, 0.9, 2.0, 1), (8.7, 1.8, 1.0, 0.9, 4.8, 0),
    (0.4, 4.4, 1.4, 1.3, 1.8, 1), (2.1, 4.4, 2.0, 1.2, 2.8, 0), (4.4, 4.4, 1.3, 2.2, 4.2, 3),
    (7.3, 4.4, 1.6, 1.5, 2.5, 3), (9.2, 4.4, 0.6, 2.2, 1.3, 1),
]
TREES = [(0.9, 6.4), (1.9, 6.5), (2.9, 6.3), (3.8, 6.55), (7.6, 6.45), (8.5, 6.55), (5.1, 2.9), (0.6, 2.85)]
LAMPS = [(1.0, 3.05), (3.6, 3.05), (5.6, 3.05), (8.2, 3.05), (9.8, 3.05), (6.05, 5.2), (6.05, 6.7)]
GX, GY = 10.0, 7.2


def windows(iso, b, c, rnd, theme):
    x, y, w, d, h, _ = b
    out_off, out_on = [], []
    ww, wh, sx, sy = 0.2, 0.3, 0.42, 0.56
    rows = int((h - 0.45) / sy)
    for face in ("left", "right"):
        span = w if face == "left" else d
        cols = int((span - 0.25) / sx)
        if cols < 1 or rows < 1:
            continue
        pad = (span - (cols - 1) * sx - ww) / 2
        for r in range(rows):
            z0 = 0.35 + r * sy
            for k in range(cols):
                u = pad + k * sx
                if face == "left":
                    q = [(x + u, y + d, z0), (x + u + ww, y + d, z0), (x + u + ww, y + d, z0 + wh), (x + u, y + d, z0 + wh)]
                else:
                    q = [(x + w, y + u, z0), (x + w, y + u + ww, z0), (x + w, y + u + ww, z0 + wh), (x + w, y + u, z0 + wh)]
                pts = " ".join(f"{a:.1f},{bb:.1f}" for a, bb in (iso.p(*qq) for qq in q))
                lit = rnd.random() < (0.38 if theme == "dark" else 0.22)
                if lit:
                    col = rnd.choice(c["win_on"])
                    cls = ""
                    if rnd.random() < 0.28:
                        cls = (f' class="fl" style="animation-duration:{rnd.uniform(5, 14):.1f}s;'
                               f'animation-delay:-{rnd.uniform(0, 14):.1f}s"')
                    out_on.append(f'<polygon points="{pts}" fill="{col}"{cls}/>')
                else:
                    out_off.append(f"M{pts.replace(' ', ' L')}Z")
    off = f'<path d="{" ".join(out_off)}" fill="{c["win_off"]}"/>' if out_off else ""
    return off + "".join(out_on)


def car(iso, c, color, axis, lane, start, dist, dur, delay, theme, reverse=False):
    """A tiny car that drives along the x- or y-axis road."""
    if axis == "x":
        x0, y0 = start, lane
        body = iso.box(x0, y0 - 0.19, 0.02, 0.72, 0.38, 0.2, (color, shade(color, 0.82), shade(color, 0.66)))
        cab = iso.box(x0 + 0.2, y0 - 0.15, 0.22, 0.34, 0.3, 0.15, (shade(color, 1.08), "#0b0d12" if theme == "dark" else "#5d6b78", "#0b0d12" if theme == "dark" else "#4d5a66"))
        front = (x0 + 0.72, y0, 0.12) if not reverse else (x0, y0, 0.12)
        back = (x0, y0, 0.12) if not reverse else (x0 + 0.72, y0, 0.12)
        vec = (dist * C30 * iso.s, dist * S30 * iso.s)
    else:
        x0, y0 = lane, start
        body = iso.box(x0 - 0.19, y0, 0.02, 0.38, 0.72, 0.2, (color, shade(color, 0.82), shade(color, 0.66)))
        cab = iso.box(x0 - 0.15, y0 + 0.2, 0.22, 0.3, 0.34, 0.15, (shade(color, 1.08), "#0b0d12" if theme == "dark" else "#5d6b78", "#0b0d12" if theme == "dark" else "#4d5a66"))
        front = (x0, y0 + 0.72, 0.12)
        back = (x0, y0, 0.12)
        vec = (-dist * C30 * iso.s, dist * S30 * iso.s)
    if reverse:
        vec = (-vec[0], -vec[1])
    fx, fy = iso.p(*front)
    bx, by = iso.p(*back)
    lights = f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="1.6" fill="{c["accent2"]}"/><circle cx="{bx:.1f}" cy="{by:.1f}" r="1.3" fill="{c["red"]}"/>'
    beam = ""
    if theme == "dark":
        if axis == "x":
            dx = 1.3 if not reverse else -1.3
            b1, b2 = iso.p(front[0] + dx, front[1] - 0.35, 0), iso.p(front[0] + dx, front[1] + 0.35, 0)
        else:
            b1, b2 = iso.p(front[0] - 0.35, front[1] + 1.3, 0), iso.p(front[0] + 0.35, front[1] + 1.3, 0)
        beam = f'<polygon points="{fx:.1f},{fy:.1f} {b1[0]:.1f},{b1[1]:.1f} {b2[0]:.1f},{b2[1]:.1f}" fill="{c["accent2"]}" opacity="0.16"/>'
    name = f"drive{abs(hash((axis, lane, reverse, dist))) % 10000}"
    kf = (f"@keyframes {name} {{ 0% {{ transform: translate(0,0); opacity: 0; }} 7% {{ opacity: 1; }} 90% {{ opacity: 1; }} "
          f"100% {{ transform: translate({vec[0]:.1f}px,{vec[1]:.1f}px); opacity: 0; }} }}")
    g = (f'<g style="animation:{name} {dur}s linear infinite;animation-delay:-{delay:.1f}s">'
         f"{beam}{body}{cab}{lights}</g>")
    return g, kf


def shade(hex_col: str, f: float) -> str:
    h = hex_col.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = (max(0, min(255, int(v * f))) for v in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


CROW_UP = "M-2,0 C2,-10 9,-17 16,-19 C11,-11 8,-5 6,0 Z"
CROW_DOWN = "M-2,0 C2,6 6,12 9,17 C9,10 8,4 6,0 Z"


def crow(color, edge, scale=1.0):
    return f"""<g transform="scale({scale})">
      <path d="M-14,3 L-6,1 L-6,5 Z" fill="{color}" stroke="{edge}" stroke-width="0.6"/>
      <ellipse cx="0" cy="2" rx="8" ry="4" fill="{color}" stroke="{edge}" stroke-width="0.6"/>
      <circle cx="8" cy="-0.5" r="3.6" fill="{color}" stroke="{edge}" stroke-width="0.6"/>
      <path d="M11,-1.4 L16,0 L11,1.2 Z" fill="{color}" stroke="{edge}" stroke-width="0.6"/>
      <path d="{CROW_UP}" fill="{color}" stroke="{edge}" stroke-width="0.6">
        <animate attributeName="d" values="{CROW_UP};{CROW_DOWN};{CROW_UP}" dur="0.9s" repeatCount="indefinite"/>
      </path>
    </g>"""


def banner(theme: str) -> str:
    c = T[theme]
    W, H = 1200, 440
    rnd = random.Random(42)
    iso = Iso(23, 0, 0)
    # fit the scene: right half, vertically centred
    xs = [iso.p(x, y)[0] for x in (0, GX) for y in (0, GY)]
    iso.ox = 905 - (min(xs) + max(xs)) / 2
    iso.oy = 172

    keyframes = []
    parts = []

    # slab (floating diorama)
    sl = c["slab"]
    parts.append(iso.box(-0.4, -0.4, -0.9, GX + 0.8, GY + 0.8, 0.9, sl))
    # roads
    parts.append(iso.poly([(-0.4, 2.9, 0), (GX + 0.4, 2.9, 0), (GX + 0.4, 4.1, 0), (-0.4, 4.1, 0)], c["road"]))
    parts.append(iso.poly([(5.9, -0.4, 0), (7.1, -0.4, 0), (7.1, GY + 0.4, 0), (5.9, GY + 0.4, 0)], c["road"]))
    a, b = iso.p(-0.3, 3.5), iso.p(GX + 0.3, 3.5)
    parts.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{c["road_line"]}" stroke-width="1.2" stroke-dasharray="6 7"/>')
    a, b = iso.p(6.5, -0.3), iso.p(6.5, GY + 0.3)
    parts.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{c["road_line"]}" stroke-width="1.2" stroke-dasharray="6 7"/>')
    # crossing stripes
    for i in range(5):
        u = 5.95 + i * 0.24
        parts.append(iso.poly([(u, 4.15, 0.005), (u + 0.12, 4.15, 0.005), (u + 0.12, 4.6, 0.005), (u, 4.6, 0.005)], c["road_line"], 'opacity="0.7"'))
    # plots (raised sidewalks)
    for (x0, y0, x1, y1) in [(-0.2, -0.2, 5.8, 2.8), (7.2, -0.2, GX + 0.2, 2.8), (-0.2, 4.2, 5.8, GY + 0.2), (7.2, 4.2, GX + 0.2, GY + 0.2)]:
        parts.append(iso.box(x0, y0, 0, x1 - x0, y1 - y0, 0.12, c["plot"]))

    def building(bd):
        x, y, w, d, h, pi = bd
        cols = c["bld"][pi]
        s = iso.box(x, y, 0.12, w, d, h, cols)
        s += windows(iso, (x, y, w, d, h + 0.12, pi), c, rnd, theme)
        # roof edge
        s += iso.box(x - 0.04, y - 0.04, h + 0.12, w + 0.08, d + 0.08, 0.08, (shade(cols[0], 0.94), shade(cols[1], 0.9), shade(cols[2], 0.9)))
        if h > 2.5 and rnd.random() < 0.8:  # rooftop units
            ux, uy = x + rnd.uniform(0.15, max(0.16, w - 0.55)), y + rnd.uniform(0.15, max(0.16, d - 0.5))
            s += iso.box(ux, uy, h + 0.2, 0.4, 0.32, 0.22, (shade(cols[0], 0.92), shade(cols[1], 0.85), shade(cols[2], 0.85)))
        return s

    def tree(tx, ty):
        bx, by = iso.p(tx, ty, 0.12)
        return (f'<rect x="{bx - 1.2:.1f}" y="{by - 9:.1f}" width="2.4" height="9" fill="{c["trunk"]}"/>'
                f'<circle cx="{bx:.1f}" cy="{by - 14:.1f}" r="8.5" fill="{c["tree"][1]}"/>'
                f'<circle cx="{bx - 2:.1f}" cy="{by - 16:.1f}" r="6" fill="{c["tree"][0]}"/>')

    def lamp(lx, ly):
        bx, by = iso.p(lx, ly, 0.12)
        glow = ""
        if theme == "dark":
            glow = f'<circle class="lamp" cx="{bx:.1f}" cy="{by - 17:.1f}" r="7" fill="{c["accent2"]}" opacity="0.18"/>'
        return (f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{bx:.1f}" y2="{by - 16:.1f}" stroke="{c["faint"]}" stroke-width="1.2"/>'
                f'{glow}<circle cx="{bx:.1f}" cy="{by - 17:.1f}" r="1.8" fill="{c["accent2"] if theme == "dark" else c["faint"]}"/>')

    back = [b for b in BUILDINGS if b[1] + b[3] <= 3.0]
    front_left = [b for b in BUILDINGS if b[1] >= 4.0 and b[0] < 6]
    front_right = [b for b in BUILDINGS if b[1] >= 4.0 and b[0] >= 7]
    order = lambda b: (b[0] + b[2] / 2) + (b[1] + b[3] / 2)

    for t in [t for t in TREES if t[1] < 3]:
        parts.append(tree(*t))
    for bd in sorted(back, key=order):
        parts.append(building(bd))
    # antenna + beacon on the tallest tower
    tall = max(BUILDINGS, key=lambda b: b[4])
    ax, ay = iso.p(tall[0] + tall[2] / 2, tall[1] + tall[3] / 2, tall[4] + 0.2)
    parts.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{ax:.1f}" y2="{ay - 34:.1f}" stroke="{c["faint"]}" stroke-width="1.5"/>'
                 f'<circle class="beacon" cx="{ax:.1f}" cy="{ay - 35:.1f}" r="2.6" fill="{c["red"]}"/>')
    # water tank on a back roof
    wt = BUILDINGS[4]
    parts.append(iso.cyl(wt[0] + 1.8, wt[1] + 0.6, wt[4] + 0.2, 0.32, 0.55, (shade(c["bld"][1][0], 0.95), c["bld"][1][2], None)))

    for l in [l for l in LAMPS if l[1] < 3.5]:
        parts.append(lamp(*l))

    # cars on the x-road
    for i, (col, lane, rev, dur, dly) in enumerate([
        (c["car"][0], 3.27, False, 9, 0), (c["car"][1], 3.27, False, 9, 4.6),
        (c["car"][2], 3.73, True, 11, 2.0), (c["car"][3], 3.73, True, 11, 7.5)]):
        start = -0.9 if not rev else GX + 0.2
        g, kf = car(iso, c, col, "x", lane, start, GX + 1.1, dur, dly, theme, reverse=rev)
        parts.append(g)
        keyframes.append(kf)

    for bd in sorted(front_left, key=order):
        parts.append(building(bd))
    # cars on the y-road (front half only, so occlusion stays correct)
    for col, dur, dly in [(c["car"][1], 7, 1.0), (c["car"][0], 7, 4.5)]:
        g, kf = car(iso, c, col, "y", 6.27, 3.0, GY - 2.4, dur, dly, theme)
        parts.append(g)
        keyframes.append(kf)
    for l in [l for l in LAMPS if l[1] >= 3.5]:
        parts.append(lamp(*l))
    for bd in sorted(front_right, key=order):
        parts.append(building(bd))
    for t in sorted([t for t in TREES if t[1] >= 3], key=lambda t: t[0] + t[1]):
        parts.append(tree(*t))

    # shadow under the diorama
    sx, _ = iso.p(GX / 2, GY / 2, -0.9)
    _, sy = iso.p(GX + 0.4, GY + 0.4, -0.9)
    shadow = f'<ellipse class="shadow" cx="{sx:.1f}" cy="{sy + 14:.1f}" rx="210" ry="9" fill="{"#000000" if theme == "dark" else c["ink"]}" opacity="{0.10 if theme == "light" else 0.5}"/>'

    # sky
    sky = []
    if theme == "dark":
        for i in range(46):
            x, y = rnd.uniform(560, W - 30), rnd.uniform(24, 200)
            sky.append(f'<circle class="tw" cx="{x:.0f}" cy="{y:.0f}" r="{rnd.choice([0.6, 0.8, 1.1])}" fill="{c["sky_star"]}" '
                       f'style="animation-duration:{rnd.uniform(2.5, 6):.1f}s;animation-delay:-{rnd.uniform(0, 6):.1f}s"/>')
        sky.append(f'<circle cx="1108" cy="74" r="54" fill="{c["sky_star"]}" opacity="0.05"/>'
                   f'<circle cx="1108" cy="74" r="30" fill="#efe6cf"/>'
                   f'<circle cx="1098" cy="68" r="6" fill="#e2d6b8"/><circle cx="1117" cy="83" r="4" fill="#e2d6b8"/>'
                   f'<circle cx="1114" cy="63" r="2.6" fill="#e2d6b8"/>')
    else:
        sky.append(f'<circle class="sunhalo" cx="1108" cy="74" r="50" fill="{c["accent2"]}" opacity="0.18"/>'
                   f'<circle cx="1108" cy="74" r="28" fill="{c["accent2"]}"/>')
    clouds = []
    for i, (cx, cy, sc, dur, dly) in enumerate([(640, 70, 1.0, 70, 0), (900, 120, 0.7, 90, 30), (760, 40, 0.55, 110, 60)]):
        clouds.append(
            f'<g class="cloud" style="animation-duration:{dur}s;animation-delay:-{dly}s" opacity="{c["cloud_op"]}">'
            f'<g transform="translate({cx} {cy}) scale({sc})">'
            f'<rect x="-46" y="-6" width="92" height="16" rx="8" fill="{c["cloud"]}"/>'
            f'<circle cx="-14" cy="-6" r="14" fill="{c["cloud"]}"/><circle cx="10" cy="-10" r="17" fill="{c["cloud"]}"/></g></g>')

    # left: editorial typography
    L = 64
    text = f"""
    <g class="rise">
      <rect x="{L}" y="54" width="22" height="22" fill="none" stroke="{c['ink']}" stroke-width="1.5"/>
      <rect x="{L + 5}" y="59" width="12" height="12" fill="{c['accent']}"><animate attributeName="opacity" values="1;0.25;1" dur="3s" repeatCount="indefinite"/></rect>
      <text x="{L + 36}" y="70" class="mono" font-size="13" font-weight="600" letter-spacing="2.4" fill="{c['muted']}">FULL-STACK ENGINEER  /  DIGITAL ARCHITECT</text>
    </g>
    <g class="rise d1">
      <text x="{L - 6}" y="176" class="sans" font-size="104" font-weight="800" letter-spacing="-4.5" fill="{c['ink']}">Sanjay</text>
      <text x="{L - 6}" y="270" class="sans" font-size="104" font-weight="800" letter-spacing="-4.5" fill="{c['ink']}">Kumar<tspan fill="{c['accent']}">.</tspan></text>
    </g>
    <g class="rise d2">
      <text x="{L}" y="316" class="serif" font-size="21" font-style="italic" fill="{c['ink2']}">Creative full-stack builds for the web, 3D and mobile.</text>
    </g>
    <g class="rise d3">
      <line x1="{L}" x2="{L + 460}" y1="346" y2="346" stroke="{c['line2']}"/>
      <circle class="ping" cx="{L + 5}" cy="372" r="4" fill="{c['green']}"/>
      <circle cx="{L + 5}" cy="372" r="4" fill="{c['green']}"/>
      <text x="{L + 20}" y="376.5" class="mono" font-size="12.5" font-weight="600" letter-spacing="1.6" fill="{c['ink2']}">OPEN TO HIGH-IMPACT ROLES &amp; CONTRACTS</text>
      <text x="{L}" y="404" class="mono" font-size="12.5" letter-spacing="1.6" fill="{c['muted']}">@CLEVERCROWORG  ·  INDIA</text>
    </g>"""

    # corner marks
    marks = []
    for (x, y, dx, dy) in [(16, 16, 1, 1), (W - 16, 16, -1, 1), (16, H - 16, 1, -1), (W - 16, H - 16, -1, -1)]:
        marks.append(f'<path d="M{x},{y + dy * 14} L{x},{y} L{x + dx * 14},{y}" fill="none" stroke="{c["faint"]}" stroke-width="1.2"/>')
    caption = f'<text transform="translate({W - 30} {H - 34}) rotate(-90)" class="mono" font-size="11" letter-spacing="1.5" fill="{c["faint"]}">FIG. 01 — A SMALL CITY OF THINGS I BUILD</text>'

    css = f"""
    .rise {{ animation: rise 1s cubic-bezier(.2,.8,.2,1) both; }}
    .d1 {{ animation-delay: .12s; }} .d2 {{ animation-delay: .28s; }} .d3 {{ animation-delay: .42s; }}
    @keyframes rise {{ from {{ transform: translateY(10px); opacity: 0; }} to {{ transform: none; opacity: 1; }} }}
    .float {{ animation: float 7s ease-in-out infinite; }}
    @keyframes float {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-6px); }} }}
    .shadow {{ transform-box: fill-box; transform-origin: center; animation: shadow 7s ease-in-out infinite; }}
    @keyframes shadow {{ 0%,100% {{ transform: scale(1); }} 50% {{ transform: scale(.94); }} }}
    .fl {{ animation: fl 9s steps(1) infinite; }}
    @keyframes fl {{ 0%,62% {{ opacity: 1; }} 63%,78% {{ opacity: .08; }} 79%,100% {{ opacity: 1; }} }}
    .beacon {{ animation: beacon 1.6s steps(1) infinite; }}
    @keyframes beacon {{ 0%,55% {{ opacity: 1; }} 56%,100% {{ opacity: .15; }} }}
    .lamp {{ transform-box: fill-box; transform-origin: center; animation: lamp 4s ease-in-out infinite; }}
    @keyframes lamp {{ 0%,100% {{ opacity: .12; }} 50% {{ opacity: .26; }} }}
    .tw {{ animation: tw 4s ease-in-out infinite; }}
    @keyframes tw {{ 0%,100% {{ opacity: .15; }} 50% {{ opacity: .9; }} }}
    .cloud {{ animation: cloud 80s linear infinite; }}
    @keyframes cloud {{ from {{ transform: translateX(-160px); }} to {{ transform: translateX(560px); }} }}
    .sunhalo {{ transform-box: fill-box; transform-origin: center; animation: halo 6s ease-in-out infinite; }}
    @keyframes halo {{ 0%,100% {{ transform: scale(1); }} 50% {{ transform: scale(1.12); }} }}
    .ping {{ transform-box: fill-box; transform-origin: center; animation: ping 2.2s ease-out infinite; }}
    @keyframes ping {{ from {{ transform: scale(1); opacity: .6; }} to {{ transform: scale(3); opacity: 0; }} }}
    .crow {{ animation: crow 19s linear infinite; animation-delay: -6s; }}
    @keyframes crow {{ 0% {{ transform: translate(520px, 120px); }} 50% {{ transform: translate(880px, 52px); }} 100% {{ transform: translate(1290px, 92px); }} }}
    .bob {{ animation: bob 2.4s ease-in-out infinite; }}
    @keyframes bob {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-5px); }} }}
    {' '.join(keyframes)}
    """

    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">Sanjay Kumar</title>
  <desc id="d">Full-stack engineer and digital architect at Clever Crow, India. An animated isometric city with cars, lit windows and a flying crow.</desc>
  <defs><clipPath id="frame"><rect width="{W}" height="{H}" rx="20"/></clipPath></defs>
  {style_block(css)}
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="{c['bg']}"/>
    {''.join(sky)}
    {''.join(clouds)}
    {shadow}
    <g class="float">{''.join(parts)}</g>
    <g class="crow"><g class="bob">{crow(c['crow'], c['crow_edge'], 1.15)}</g></g>
    {text}
    {''.join(marks)}
    {caption}
  </g>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="20" fill="none" stroke="{c['line']}"/>
</svg>
"""


# --------------------------------------------------------------------------
# Section header
# --------------------------------------------------------------------------
SECTIONS = [
    ("01", "About", "WHOAMI", "about"),
    ("02", "Stack", "TOOLS OF THE TRADE", "stack"),
    ("03", "Selected work", "SHIPPED & IN PRODUCTION", "work"),
    ("04", "GitHub pulse", "LIVE · REFRESHED DAILY", "pulse"),
    ("05", "Kind words", "FROM A CLIENT", "words"),
    ("06", "Say hello", "LET'S BUILD SOMETHING", "contact"),
]


def section_header(num, title, caption, theme):
    c = T[theme]
    W, H = 1200, 84
    iso = Iso(9, 18, 26)
    cube = iso.box(0, 0, 0, 1.6, 1.6, 1.6, (c["accent"], shade(c["accent"], 0.78), shade(c["accent"], 0.6)))
    css = """
    .draw { animation: draw 1.4s cubic-bezier(.2,.8,.2,1) .2s both; }
    @keyframes draw { from { transform: scaleX(0); } to { transform: scaleX(1); } }
    .cube { transform-box: fill-box; transform-origin: center; animation: hop 3.2s ease-in-out infinite; }
    @keyframes hop { 0%,70%,100% { transform: translateY(0); } 80% { transform: translateY(-4px); } 90% { transform: translateY(0); } }
    """
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(title)}">
  {style_block(css)}
  <g class="cube">{cube}</g>
  <text x="54" y="44" class="mono" font-size="15" font-weight="700" fill="{c['accent']}">{num}</text>
  <text x="84" y="46" class="sans" font-size="32" font-weight="800" letter-spacing="-1" fill="{c['ink']}">{escape(title)}</text>
  <text x="{W - 4}" y="44" text-anchor="end" class="mono" font-size="12" letter-spacing="2" fill="{c['muted']}">{escape(caption)}</text>
  <rect x="0" y="66" width="{W}" height="1" fill="{c['line2']}"/>
  <rect x="0" y="65" width="96" height="3" fill="{c['accent']}">
    <animate attributeName="width" values="0;96" dur="1.2s" fill="freeze" calcMode="spline" keySplines=".2 .8 .2 1" keyTimes="0;1"/>
  </rect>
</svg>
"""


# --------------------------------------------------------------------------
# Small isometric illustrations for the project cards
# --------------------------------------------------------------------------
def mini(kind: str, c: dict, theme: str) -> tuple[str, str]:
    """Returns (svg, css) of an illustration centred around (0,0), ~150px wide."""
    iso = Iso(28, 0, 0)
    A = c["accent"]
    pal = c["bld"]
    css = ""
    if kind == "phone":
        ph = c["ink2"]
        body = iso.box(-0.6, -0.1, 0, 1.3, 0.22, 2.3, (shade(ph, 0.95), shade(ph, 0.8), shade(ph, 0.62)))
        # screen on the left (y+d) face
        scr = iso.poly([(-0.5, 0.125, 0.2), (0.6, 0.125, 0.2), (0.6, 0.125, 2.1), (-0.5, 0.125, 2.1)], c["bg"])
        pts = []
        for i, (u, v) in enumerate([(-0.45, 1.1), (-0.15, 1.1), (-0.05, 1.5), (0.05, 0.75), (0.15, 1.25), (0.22, 1.1), (0.55, 1.1)]):
            pts.append("%.1f,%.1f" % iso.p(u, 0.12, v))
        line = f'<polyline class="ecg" points="{" ".join(pts)}" fill="none" stroke="{A}" stroke-width="2" stroke-linejoin="round" pathLength="100"/>'
        cx, cy = iso.p(1.2, 0.4, 2.0)
        badge = (f'<g class="bob"><rect x="{cx - 13:.1f}" y="{cy - 13:.1f}" width="26" height="26" rx="6" fill="{c["red"]}"/>'
                 f'<rect x="{cx - 2.5:.1f}" y="{cy - 8:.1f}" width="5" height="16" fill="#fff"/><rect x="{cx - 8:.1f}" y="{cy - 2.5:.1f}" width="16" height="5" fill="#fff"/></g>')
        css = (".ecg { stroke-dasharray: 100; animation: ecg 2.4s linear infinite; }"
               "@keyframes ecg { from { stroke-dashoffset: 100; } 70%,to { stroke-dashoffset: 0; } }")
        return body + scr + line + badge, css
    if kind == "keyboard":
        s = iso.box(-1.5, -0.7, 0, 3.0, 1.4, 0.22, (pal[0][0], pal[0][1], pal[0][2]))
        keys = []
        k = 0
        for r in range(3):
            for q in range(6):
                x, y = -1.38 + q * 0.47, -0.58 + r * 0.42
                col = A if (r, q) in [(1, 2), (2, 4)] else shade(pal[0][0], 0.9 if theme == "light" else 1.25)
                cls = f' class="key" style="animation-delay:{(k * 0.37) % 3:.2f}s"' if (r * 6 + q) % 4 == 1 else ""
                keys.append(f"<g{cls}>" + iso.box(x, y, 0.22, 0.36, 0.32, 0.12, (col, shade(col, 0.8), shade(col, 0.65))) + "</g>")
                k += 1
        bx, by = iso.p(0.6, -0.8, 1.6)
        bubble = (f'<g class="bob"><rect x="{bx - 30:.1f}" y="{by - 20:.1f}" width="60" height="32" rx="12" fill="{c["card"]}" stroke="{c["line2"]}"/>'
                  + "".join(f'<circle class="dot" style="animation-delay:{i * 0.2:.1f}s" cx="{bx - 14 + i * 14:.1f}" cy="{by - 4:.1f}" r="3.2" fill="{A}"/>' for i in range(3))
                  + "</g>")
        css = (".key { animation: key 3s ease-in-out infinite; } @keyframes key { 0%,80%,100% { transform: translateY(0); } 88% { transform: translateY(2.5px); } }"
               ".dot { animation: dot 1.2s ease-in-out infinite; } @keyframes dot { 0%,100% { opacity: .25; } 50% { opacity: 1; } }")
        return s + "".join(keys) + bubble, css
    if kind == "car":
        col = A
        body = iso.box(-1.4, -0.55, 0.18, 2.8, 1.1, 0.42, (col, shade(col, 0.8), shade(col, 0.62)))
        cab = iso.box(-0.55, -0.45, 0.6, 1.2, 0.9, 0.36, (shade(col, 1.06), "#1a1d24", "#13151a"))
        wheels = ""
        for (x, y) in [(-0.85, 0.56), (0.85, 0.56)]:
            wx, wy = iso.p(x, y, 0.2)
            wheels += f'<ellipse cx="{wx:.1f}" cy="{wy:.1f}" rx="9" ry="11" fill="#14161b"/><ellipse cx="{wx:.1f}" cy="{wy:.1f}" rx="3.5" ry="4.5" fill="{c["faint"]}"/>'
        hx, hy = iso.p(1.4, 0.3, 0.42)
        light = f'<circle class="blink" cx="{hx:.1f}" cy="{hy:.1f}" r="3" fill="{c["accent2"]}"/>'
        speed = "".join(
            f'<line class="spd" style="animation-delay:{i * 0.25:.2f}s" x1="{-120 + i * 6}" y1="{-14 + i * 14}" x2="{-80 + i * 6}" y2="{-14 + i * 14 + 23}" stroke="{c["faint"]}" stroke-width="2" stroke-linecap="round"/>'
            for i in range(3))
        css = (".spd { animation: spd 1s linear infinite; } @keyframes spd { 0% { transform: translate(14px,8px); opacity: 0; } 30% { opacity: 1; } 100% { transform: translate(-20px,-12px); opacity: 0; } }"
               ".blink { animation: blink 2s steps(1) infinite; } @keyframes blink { 50% { opacity: .3; } }")
        return speed + f'<g class="bob">{body}{cab}{wheels}{light}</g>', css
    if kind == "can":
        s = iso.cyl(0, 0, 0, 0.75, 2.2, (shade(pal[2][0], 1.0), pal[2][1], None))
        cx, top = iso.p(0, 0, 1.45)
        _, bot = iso.p(0, 0, 0.75)
        rx, ry = 1.2247 * 0.75 * 28, 0.7071 * 0.75 * 28
        band = (f'<path d="M{cx - rx:.1f},{top:.1f} L{cx - rx:.1f},{bot:.1f} A{rx:.1f},{ry:.1f} 0 0 0 {cx + rx:.1f},{bot:.1f} '
                f'L{cx + rx:.1f},{top:.1f} A{rx:.1f},{ry:.1f} 0 0 1 {cx - rx:.1f},{top:.1f} Z" fill="{A}"/>')
        tx, ty = iso.p(0, 0, 2.2)
        tab = f'<ellipse cx="{tx:.1f}" cy="{ty:.1f}" rx="{rx * 0.7:.1f}" ry="{ry * 0.7:.1f}" fill="none" stroke="{c["faint"]}"/>'
        bubbles = "".join(
            f'<circle class="bub" style="animation-delay:{i * 0.7:.1f}s" cx="{tx - 14 + i * 12:.1f}" cy="{ty - 6:.1f}" r="{2.5 + (i % 2)}" fill="none" stroke="{A}" stroke-width="1.5"/>'
            for i in range(4))
        css = ".bub { animation: bub 2.8s ease-in infinite; } @keyframes bub { 0% { transform: translateY(0); opacity: 0; } 20% { opacity: 1; } 100% { transform: translateY(-44px); opacity: 0; } }"
        return s + band + tab + bubbles, css
    if kind == "radar":
        base = iso.box(-1.3, -1.3, 0, 2.6, 2.6, 0.25, pal[3])
        cx, cy = iso.p(0, 0, 0.25)
        rings = "".join(f'<circle r="{r}" fill="none" stroke="{A}" stroke-opacity="{0.5 - r / 200:.2f}" stroke-width="1.5"/>' for r in (20, 38, 54))
        sweep = f'<g class="sweep"><path d="M0,0 L54,0 A54,54 0 0 0 38.2,-38.2 Z" fill="{A}" opacity="0.35"/><line x1="0" y1="0" x2="54" y2="0" stroke="{A}" stroke-width="2"/></g>'
        blips = "".join(f'<circle class="blip" style="animation-delay:{d}s" cx="{x}" cy="{y}" r="3.5" fill="{c["red"]}"/>' for x, y, d in [(24, -30, 0.3), (-34, 14, 1.6), (12, 40, 2.6)])
        disc = f'<g transform="translate({cx:.1f} {cy:.1f}) scale(1 0.577) rotate(45)">{rings}{sweep}{blips}</g>'
        css = (".sweep { transform-origin: 0 0; animation: sw 3.6s linear infinite; } @keyframes sw { to { transform: rotate(360deg); } }"
               ".blip { animation: blip 3.6s ease-out infinite; } @keyframes blip { 0%,100% { opacity: 0; } 10% { opacity: 1; } 60% { opacity: 0; } }")
        return base + disc, css
    if kind == "boat":
        hull = '<path d="M-62,6 L62,6 L46,30 L-50,30 Z" fill="%s"/>' % shade(pal[0][2], 1.0)
        deck = '<path d="M-62,6 L62,6 L56,0 L-56,0 Z" fill="%s"/>' % pal[0][0]
        cabin = f'<rect x="-30" y="-16" width="50" height="16" fill="{pal[3][1]}"/><rect x="-24" y="-12" width="10" height="7" fill="{c["bg"]}"/><rect x="-8" y="-12" width="10" height="7" fill="{c["bg"]}"/>'
        mast = f'<line x1="6" y1="-16" x2="6" y2="-78" stroke="{c["ink2"]}" stroke-width="2.5"/>'
        sail = f'<path class="sail" d="M10,-74 L10,-22 L52,-22 Z" fill="{A}"/>'
        flag = f'<path d="M6,-78 L-10,-73 L6,-68 Z" fill="{c["red"]}"/>'
        waves = "".join(
            f'<path class="wave" style="animation-delay:-{i * 0.8:.1f}s" d="M-120,{38 + i * 10} q12,-6 24,0 t24,0 t24,0 t24,0 t24,0 t24,0 t24,0 t24,0 t24,0 t24,0" fill="none" stroke="{A if i == 0 else c["faint"]}" stroke-width="2" stroke-linecap="round" opacity="{0.9 - i * 0.3:.1f}"/>'
            for i in range(3))
        css = (".wave { animation: wave 2.4s linear infinite; } @keyframes wave { to { transform: translateX(-48px); } }"
               ".rock { transform-box: fill-box; transform-origin: center bottom; animation: rock 4s ease-in-out infinite; } @keyframes rock { 0%,100% { transform: rotate(-3deg) translateY(0); } 50% { transform: rotate(3deg) translateY(-3px); } }")
        return f'<g transform="translate(0 12) scale(0.85)"><g class="rock">{mast}{sail}{flag}{cabin}{deck}{hull}</g></g><g clip-path="url(#wclip)">{waves}</g>', css
    if kind == "calendar":
        base = iso.box(-1.5, -1.5, 0, 3.0, 3.0, 0.2, pal[0])
        cells = []
        n = 0
        for r in range(4):
            for q in range(4):
                x, y = -1.35 + q * 0.7, -1.35 + r * 0.7
                lit = (r * 4 + q) in (2, 5, 11, 12)
                col = A if lit else shade(pal[0][0], 0.94 if theme == "light" else 1.2)
                cls = f' class="slot" style="animation-delay:{n * 0.6:.1f}s"' if lit else ""
                n += lit
                cells.append(f"<g{cls}>" + iso.box(x, y, 0.2, 0.56, 0.56, 0.1, (col, shade(col, 0.8), shade(col, 0.65))) + "</g>")
        rings = "".join(iso.box(-1.1 + i * 0.9, -1.62, 0.2, 0.14, 0.14, 0.5, (c["ink2"], c["ink2"], c["ink2"])) for i in range(3))
        css = ".slot { animation: slot 3.2s ease-in-out infinite; } @keyframes slot { 0%,100% { transform: translateY(0); } 15% { transform: translateY(-4px); } 30% { transform: translateY(0); } }"
        return base + "".join(cells) + rings, css
    if kind == "crow":
        block = iso.box(-1.0, -1.0, 0, 2.0, 2.0, 1.5, pal[0])
        px, py = iso.p(0, 0, 1.5)
        bird = f'<g transform="translate({px:.1f} {py - 20:.1f}) scale(2.4)">'
        bird += (f'<path d="M-14,4 L-6,1 L-6,6 Z" fill="{c["crow"]}"/>'
                 f'<ellipse cx="-1" cy="2" rx="8" ry="5" fill="{c["crow"]}"/>'
                 f'<g class="head"><circle cx="7" cy="-3" r="4.2" fill="{c["crow"]}"/>'
                 f'<path d="M10.5,-4.4 L16,-2.6 L10.5,-1 Z" fill="{c["crow"]}"/>'
                 f'<circle class="eye" cx="8.4" cy="-3.8" r="1.1" fill="{c["accent"]}"/></g>'
                 f'<line x1="-2" y1="7" x2="-3" y2="9.5" stroke="{c["crow"]}" stroke-width="1"/><line x1="2" y1="7" x2="2" y2="9.5" stroke="{c["crow"]}" stroke-width="1"/>'
                 "</g>")
        css = (".head { transform-box: fill-box; transform-origin: left bottom; animation: tilt 5s ease-in-out infinite; } @keyframes tilt { 0%,60%,100% { transform: rotate(0); } 70%,85% { transform: rotate(-14deg); } }"
               ".eye { animation: eye 4s steps(1) infinite; } @keyframes eye { 0%,92% { opacity: 1; } 93%,97% { opacity: 0; } }")
        return block + bird, css
    return "", ""


PROJECTS = [
    dict(slug="healthtracker", name="HealthTracker", kind="HEALTHCARE · MOBILE", tag="NEW", art="phone",
         lines=["An app for doctors, with patient records,", "PDF reports and an AI assistant."],
         stack="REACT NATIVE · EXPO · TYPESCRIPT", cta="REPO"),
    dict(slug="persona-keyboard", name="Persona Keyboard", kind="ANDROID · AI", tag="NEW", art="keyboard",
         lines=["An Android keyboard with AI personas,", "emoji, GIFs, stickers and autocorrect."],
         stack="KOTLIN · ANDROID", cta="REPO"),
    dict(slug="turbo-ride", name="Turbo Ride Supercars", kind="LUXURY MOBILITY", tag="LIVE", art="car",
         lines=["+185% bookings lift, sub-second", "checkout, 0.000 CLS."],
         stack="NEXT.JS 15 · STRIPE · DJANGO", cta="VISIT"),
    dict(slug="cocofuse", name="COCO FUSE", kind="D2C 3D COMMERCE", tag="LIVE", art="can",
         lines=["3-flavor liquid visualizer, 2.4x cart", "uplift, 60 FPS."],
         stack="REACT 19 · SHOPIFY · GLSL", cta="VISIT"),
    dict(slug="ssquad", name="SSquad Global", kind="ENTERPRISE DEFENSE", tag="LIVE", art="radar",
         lines=["Real-time threat HUD, sub-12ms", "telemetry, zero-trust SOC2."],
         stack="REACT 19 · TYPESCRIPT · CLOUD", cta="VISIT"),
    dict(slug="yacht-club", name="Yacht Club India", kind="LUXURY MARITIME", tag="LIVE", art="boat",
         lines=["500+ luxury charters, a Goa route", "planner, 4.9★ CSAT."],
         stack="DJANGO · FASTAPI · FRAMER MOTION", cta="VISIT"),
    dict(slug="tanubhi", name="Tanubhi Couture", kind="HAUTE COUTURE & SPA", tag="LIVE", art="calendar",
         lines=["Multi-stylist slot calendar with an", "under-20-second reservation flow."],
         stack="NEXT.JS 15 · REDIS · TYPESCRIPT", cta="VISIT"),
    dict(slug="clever-crow", name="Clever Crow", kind="STUDIO WEBSITE", tag="LIVE", art="crow",
         lines=["The studio's own site, with landing", "pages and a leads dashboard."],
         stack="NEXT.JS · TYPESCRIPT · VERCEL", cta="VISIT"),
]


def project_card(p: dict, theme: str, idx: int) -> str:
    c = T[theme]
    W, H = 600, 250
    art, art_css = mini(p["art"], c, theme)
    tag_col = c["green"] if p["tag"] == "LIVE" else c["accent"]
    css = f"""
    .bob {{ animation: bob 3.6s ease-in-out infinite; }}
    @keyframes bob {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-5px); }} }}
    .ping {{ transform-box: fill-box; transform-origin: center; animation: ping 2s ease-out infinite; }}
    @keyframes ping {{ from {{ transform: scale(1); opacity: .6; }} to {{ transform: scale(2.8); opacity: 0; }} }}
    .arrow {{ animation: arrow 2.6s ease-in-out infinite; }}
    @keyframes arrow {{ 0%,100% {{ transform: translate(0,0); }} 50% {{ transform: translate(3px,-3px); }} }}
    {art_css}
    """
    lines = "".join(
        f'<text x="32" y="{132 + i * 24}" class="sans" font-size="16" fill="{c["ink2"]}">{escape(l)}</text>' for i, l in enumerate(p["lines"]))
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(p['name'])}">
  <defs><clipPath id="wclip"><rect x="-80" y="0" width="160" height="80"/></clipPath></defs>
  {style_block(css)}
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" fill="{c['card']}" stroke="{c['line']}"/>
  <text x="32" y="44" class="mono" font-size="12" font-weight="700" letter-spacing="1.8" fill="{c['accent']}">{idx + 1:02d}</text>
  <text x="58" y="44" class="mono" font-size="12" letter-spacing="1.8" fill="{c['muted']}">{escape(p['kind'])}</text>
  <text x="30" y="88" class="sans" font-size="29" font-weight="800" letter-spacing="-0.8" fill="{c['ink']}">{escape(p['name'])}</text>
  {lines}
  <line x1="32" x2="{W - 32}" y1="196" y2="196" stroke="{c['line']}"/>
  <text x="32" y="225" class="mono" font-size="11.5" letter-spacing="1.4" fill="{c['muted']}">{escape(p['stack'])}</text>
  <g class="arrow"><text x="{W - 32}" y="225" text-anchor="end" class="mono" font-size="12" font-weight="700" letter-spacing="1.6" fill="{c['ink']}">{p['cta']} ↗</text></g>
  <g transform="translate({W - 100} 34)">
    <circle class="ping" cx="0" cy="0" r="3.5" fill="{tag_col}"/><circle cx="0" cy="0" r="3.5" fill="{tag_col}"/>
    <text x="10" y="4.5" class="mono" font-size="11.5" font-weight="700" letter-spacing="1.6" fill="{tag_col}">{p['tag']}</text>
  </g>
  <g transform="translate(482 122)">{art}</g>
</svg>
"""


# --------------------------------------------------------------------------
# Stack sheet (replaces the icon rows)
# --------------------------------------------------------------------------
STACK = [
    ("Frontend & 3D", ["Next.js 15", "React 19", "TypeScript", "Tailwind CSS", "Three.js / WebGL", "GLSL shaders", "Framer Motion"]),
    ("Backend & data", ["Python", "Django REST", "FastAPI", "Node.js", "PostgreSQL", "Redis", "GraphQL · MongoDB"]),
    ("Mobile", ["React Native", "Expo", "Kotlin", "Android"]),
    ("Cloud & tools", ["Vercel", "AWS", "Cloudflare", "Docker", "Git & GitHub", "Figma", "Postman"]),
]


def stack_sheet(theme: str) -> str:
    c = T[theme]
    W, H = 1200, 330
    colw = W / 4
    cols = []
    k = 0
    for i, (title, items) in enumerate(STACK):
        x = i * colw + (10 if i == 0 else 26)
        cols.append(f'<text x="{x}" y="34" class="mono" font-size="12" font-weight="700" letter-spacing="2" fill="{c["accent"]}">{i + 1:02d}</text>'
                    f'<text x="{x + 30}" y="34" class="mono" font-size="12" letter-spacing="2" fill="{c["muted"]}">{escape(title.upper())}</text>')
        if i:
            cols.append(f'<line x1="{i * colw}" x2="{i * colw}" y1="14" y2="{H - 14}" stroke="{c["line"]}"/>')
        for j, it in enumerate(items):
            y = 82 + j * 34
            cols.append(f'<g class="in" style="animation-delay:{k * 0.05:.2f}s">'
                        f'<rect x="{x}" y="{y - 9}" width="7" height="7" fill="{c["accent"] if j == 0 else "none"}" stroke="{c["accent"]}" stroke-width="1.3" transform="rotate(45 {x + 3.5} {y - 5.5})"/>'
                        f'<text x="{x + 20}" y="{y}" class="sans" font-size="19" font-weight="{700 if j == 0 else 500}" fill="{c["ink"] if j == 0 else c["ink2"]}">{escape(it)}</text></g>')
            k += 1
    css = ".in { animation: in .7s cubic-bezier(.2,.8,.2,1) both; } @keyframes in { from { transform: translateX(-8px); opacity: 0; } to { transform: none; opacity: 1; } }"
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Tech stack: {escape('; '.join(t + ': ' + ', '.join(i) for t, i in STACK))}">
  {style_block(css)}
  {''.join(cols)}
</svg>
"""


# --------------------------------------------------------------------------
# Quote card
# --------------------------------------------------------------------------
QUOTE = ["Huge thanks for crushing the recent release! Your clean code,",
         "fast problem-solving, and calm focus under pressure made all",
         "the difference. We are lucky to have your skill on the team."]


def quote(theme: str) -> str:
    c = T[theme]
    W, H = 1200, 270
    lines = "".join(f'<text x="120" y="{88 + i * 40}" class="serif" font-size="27" font-style="italic" fill="{c["ink"]}">{escape(l)}</text>' for i, l in enumerate(QUOTE))
    css = ".q { animation: q 6s ease-in-out infinite; } @keyframes q { 0%,100% { opacity: 1; } 50% { opacity: .55; } }"
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="“{escape(' '.join(QUOTE))}” — Loka Shankaraha, Credit Consultant &amp; Financial Advisory">
  {style_block(css)}
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" fill="{c['card']}" stroke="{c['line']}"/>
  <text class="serif q" x="34" y="126" font-size="150" fill="{c['accent']}">“</text>
  {lines}
  <line x1="120" x2="160" y1="222" y2="222" stroke="{c['accent']}" stroke-width="2"/>
  <text x="174" y="227" class="sans" font-size="16" font-weight="700" fill="{c['ink']}">Loka Shankaraha</text>
  <text x="318" y="227" class="mono" font-size="12" letter-spacing="1.6" fill="{c['muted']}">CREDIT CONSULTANT &amp; FINANCIAL ADVISORY</text>
</svg>
"""


# --------------------------------------------------------------------------
# Link buttons
# --------------------------------------------------------------------------
BUTTONS = [("linkedin", "LinkedIn"), ("email", "Email"), ("instagram", "Instagram"), ("portfolio", "Portfolio"), ("clevercrow", "Clever Crow")]


def button(label: str, theme: str, primary=False) -> str:
    c = T[theme]
    w = int(len(label) * 9.2 + 64)
    H = 44
    fill = c["ink"] if primary else c["card"]
    fg = c["bg"] if primary else c["ink"]
    css = ".a { animation: a 2.8s ease-in-out infinite; } @keyframes a { 0%,100% { transform: translate(0,0); } 50% { transform: translate(2px,-2px); } }"
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {H}" width="{w}" height="{H}" role="img" aria-label="{escape(label)}">
  {style_block(css)}
  <rect x="0.5" y="0.5" width="{w - 1}" height="{H - 1}" rx="10" fill="{fill}" stroke="{c['line2'] if not primary else fill}"/>
  <text x="20" y="27.5" class="mono" font-size="13.5" font-weight="700" letter-spacing="1.2" fill="{fg}">{escape(label.upper())}</text>
  <g class="a"><text x="{w - 20}" y="27.5" text-anchor="end" class="mono" font-size="14" font-weight="700" fill="{c['accent']}">↗</text></g>
</svg>
"""


# --------------------------------------------------------------------------
# Footer: front-on skyline with a crow on the roof
# --------------------------------------------------------------------------
def footer(theme: str) -> str:
    c = T[theme]
    W, H = 1200, 220
    rnd = random.Random(5)
    blds, x = [], 0
    win = []
    while x < W:
        w = rnd.choice([44, 56, 70, 84, 100])
        h = rnd.choice([40, 56, 72, 90, 110, 64])
        y = H - h
        blds.append(f'<rect x="{x}" y="{y}" width="{w - 3}" height="{h}" fill="{c["line"]}"/>')
        if h >= 72 and rnd.random() < 0.6:
            ax = x + rnd.randint(8, max(9, w - 14))
            blds.append(f'<line x1="{ax}" x2="{ax}" y1="{y}" y2="{y - 18}" stroke="{c["line"]}" stroke-width="2"/>'
                        f'<circle class="bk" cx="{ax}" cy="{y - 19}" r="2" fill="{c["red"]}" style="animation-delay:-{rnd.uniform(0, 2):.1f}s"/>')
        elif h >= 56 and rnd.random() < 0.4:
            blds.append(f'<rect x="{x + 8}" y="{y - 10}" width="14" height="10" fill="{c["line"]}"/>')
        for wy in range(y + 12, H - 10, 16):
            for wx in range(x + 9, x + w - 14, 14):
                if rnd.random() < 0.3:
                    cls = f' class="fl" style="animation-duration:{rnd.uniform(5, 12):.1f}s;animation-delay:-{rnd.uniform(0, 12):.1f}s"' if rnd.random() < 0.35 else ""
                    win.append(f'<rect x="{wx}" y="{wy}" width="5" height="7" fill="{c["accent2"] if theme == "dark" else c["card"]}"{cls}/>')
        x += w
    perch_x = 1010
    css = """
    .bk { animation: bk 1.8s steps(1) infinite; } @keyframes bk { 50% { opacity: .15; } }
    .fl { animation: fl 8s steps(1) infinite; } @keyframes fl { 0%,60% { opacity: 1; } 61%,80% { opacity: .1; } 81%,100% { opacity: 1; } }
    .head { transform-box: fill-box; transform-origin: left bottom; animation: tilt 5s ease-in-out infinite; } @keyframes tilt { 0%,60%,100% { transform: rotate(0); } 70%,85% { transform: rotate(-14deg); } }
    """
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Thanks for stopping by">
  {style_block(css)}
  <defs><clipPath id="cl"><rect width="{W}" height="{H}" rx="16"/></clipPath></defs>
  <g clip-path="url(#cl)">
    {''.join(blds)}{''.join(win)}
    <rect x="{perch_x - 40}" y="{H - 130}" width="120" height="130" fill="{c['line2']}"/>
    <g transform="translate({perch_x + 18} {H - 152}) scale(2)">
      <path d="M-14,4 L-6,1 L-6,6 Z" fill="{c['crow']}" stroke="{c['crow_edge']}" stroke-width="0.6"/>
      <ellipse cx="-1" cy="2" rx="8" ry="5" fill="{c['crow']}" stroke="{c['crow_edge']}" stroke-width="0.6"/>
      <g class="head"><circle cx="7" cy="-3" r="4.2" fill="{c['crow']}" stroke="{c['crow_edge']}" stroke-width="0.6"/>
      <path d="M10.5,-4.4 L16,-2.6 L10.5,-1 Z" fill="{c['crow']}" stroke="{c['crow_edge']}" stroke-width="0.6"/>
      <circle cx="8.4" cy="-3.8" r="1.1" fill="{c['accent']}"/></g>
      <line x1="-2" y1="7" x2="-3" y2="10" stroke="{c['crow_edge']}"/><line x1="2" y1="7" x2="2" y2="10" stroke="{c['crow_edge']}"/>
    </g>
  </g>
  <text x="{W / 2}" y="46" text-anchor="middle" class="serif" font-size="30" font-style="italic" fill="{c['ink']}">Thanks for stopping by.</text>
  <text x="{W / 2}" y="76" text-anchor="middle" class="mono" font-size="12" letter-spacing="2.4" fill="{c['muted']}">SANJAY KUMAR  ·  CLEVER CROW  ·  INDIA</text>
</svg>
"""


def main() -> None:
    for old in OUT.glob("*.svg"):
        old.unlink()
    for t in T:
        write(f"banner-{t}.svg", banner(t))
        write(f"footer-{t}.svg", footer(t))
        write(f"stack-{t}.svg", stack_sheet(t))
        write(f"quote-{t}.svg", quote(t))
        for i, p in enumerate(PROJECTS):
            write(f"project-{p['slug']}-{t}.svg", project_card(p, t, i))
        for num, title, cap, slug in SECTIONS:
            write(f"header-{slug}-{t}.svg", section_header(num, title, cap, t))
        for slug, label in BUTTONS:
            write(f"btn-{slug}-{t}.svg", button(label, t, primary=(slug == "email")))


if __name__ == "__main__":
    main()
