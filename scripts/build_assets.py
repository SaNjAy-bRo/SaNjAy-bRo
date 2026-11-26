#!/usr/bin/env python3
"""Builds the static, hand-animated SVGs used by the profile README.

Everything here is plain SVG with CSS @keyframes and SMIL, which GitHub
renders inside <img>. No external fonts, scripts or <foreignObject>.

Run:  python3 scripts/build_assets.py
Out:  assets/*.svg
"""
from __future__ import annotations

import math
import random
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

SANS = "'Inter','Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono','Fira Code','SFMono-Regular',Consolas,'DejaVu Sans Mono',Menlo,monospace"

THEMES = {
    "dark": dict(
        bg0="#05050f", bg1="#0d0b24", bg2="#070712",
        text="#f5f7ff", muted="#9aa4c7", faint="#5b6488",
        cyan="#22d3ee", violet="#a78bfa", pink="#f472b6", green="#34d399", amber="#fbbf24",
        blob=0.55, star="#ffffff", grid="#a78bfa", grid_op=0.55,
        chip_bg="#ffffff", chip_bg_op=0.06, chip_stroke="#a78bfa", chip_stroke_op=0.35,
        card0="#0c0b1d", card1="#090816", panel_op=0.75,
    ),
    "light": dict(
        bg0="#fbfbff", bg1="#eef0ff", bg2="#f7f5ff",
        text="#0f172a", muted="#475569", faint="#94a3b8",
        cyan="#0891b2", violet="#7c3aed", pink="#db2777", green="#059669", amber="#d97706",
        blob=0.28, star="#7c3aed", grid="#7c3aed", grid_op=0.28,
        chip_bg="#7c3aed", chip_bg_op=0.07, chip_stroke="#7c3aed", chip_stroke_op=0.28,
        card0="#ffffff", card1="#f6f5ff", panel_op=0.9,
    ),
}


def write(name: str, svg: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(svg.strip() + "\n", encoding="utf-8")
    print(f"wrote assets/{name} ({len(svg):,} bytes)")


# --------------------------------------------------------------------------
# Banner
# --------------------------------------------------------------------------
PHRASES = [
    "Creative Full-Stack Engineer",
    "Digital Architect",
    "Next.js · React · Django · WebGL",
    "Mobile apps with React Native",
    "Shipping at Clever Crow",
]
CHIPS = ["Next.js", "React", "TypeScript", "Django", "Three.js", "React Native", "Kotlin", "Cloud"]


def typing_schedule(phrases, cw, type_s=0.075, del_s=0.035, hold=1.9, gap=0.35):
    """Per-character discrete schedule -> (dur, keyTimes, widths per phrase, cursor x offsets)."""
    events = []  # (t, phrase_index, chars)
    t = 0.0
    for i, p in enumerate(phrases):
        n = len(p)
        for c in range(n + 1):
            events.append((t, i, c))
            t += type_s
        t += hold
        for c in range(n - 1, -1, -1):
            events.append((t, i, c))
            t += del_s
        t += gap
    dur = round(t, 3)
    key_times = [e[0] / dur for e in events]
    widths = []
    for i in range(len(phrases)):
        widths.append([round(e[2] * cw, 2) if e[1] == i else 0 for e in events])
    cursor = [round(e[2] * cw, 2) for e in events]
    kt = ";".join(f"{k:.5f}" for k in key_times)
    return dur, kt, widths, cursor


def banner(theme: str) -> str:
    c = THEMES[theme]
    W, H = 1200, 420
    rnd = random.Random(7)

    # Stars / particles
    stars = []
    for i in range(70):
        x, y = rnd.uniform(20, W - 20), rnd.uniform(14, 300)
        r = rnd.choice([0.6, 0.8, 1.0, 1.2, 1.6])
        d = rnd.uniform(2.5, 6.5)
        delay = rnd.uniform(0, 6)
        op = rnd.uniform(0.35, 0.9) if theme == "dark" else rnd.uniform(0.15, 0.4)
        stars.append(
            f'<circle class="tw" cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{c["star"]}" '
            f'opacity="{op:.2f}" style="animation-duration:{d:.2f}s;animation-delay:-{delay:.2f}s"/>'
        )

    # Perspective floor
    vpx, vpy, floor_top = 600, 290, 318
    vlines = []
    for i in range(-14, 15):
        xb = vpx + i * 95
        # intersect line (vp -> (xb, H)) with y=floor_top
        tt = (floor_top - vpy) / (H - vpy)
        xt = vpx + (xb - vpx) * tt
        vlines.append(f'<line x1="{xt:.1f}" y1="{floor_top}" x2="{xb:.1f}" y2="{H}"/>')
    hlines = []
    n_h = 7
    dur_h = 3.6
    for i in range(n_h):
        begin = -i * dur_h / n_h
        hlines.append(
            f'<line x1="0" x2="{W}" y1="{floor_top}" y2="{floor_top}">'
            f'<animate attributeName="y1" values="{floor_top};{H + 4}" dur="{dur_h}s" begin="{begin:.2f}s" '
            f'repeatCount="indefinite" calcMode="spline" keySplines="0.55 0 1 1" keyTimes="0;1"/>'
            f'<animate attributeName="y2" values="{floor_top};{H + 4}" dur="{dur_h}s" begin="{begin:.2f}s" '
            f'repeatCount="indefinite" calcMode="spline" keySplines="0.55 0 1 1" keyTimes="0;1"/>'
            f"</line>"
        )

    # Typing line
    fs = 25
    cw = fs * 0.6
    tx, ty = 368, 236
    dur, kt, widths, cursor = typing_schedule(PHRASES, cw)
    clips, texts = [], []
    for i, p in enumerate(PHRASES):
        full = round(len(p) * cw, 2)
        vals = ";".join(str(v) for v in widths[i])
        clips.append(
            f'<clipPath id="tp{i}"><rect x="{tx}" y="{ty - 30}" height="42" width="{full if i == 0 else 0}">'
            f'<animate attributeName="width" dur="{dur}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{kt}" values="{vals}"/></rect></clipPath>'
        )
        texts.append(
            f'<text x="{tx}" y="{ty}" class="mono" font-size="{fs}" fill="{c["text"]}" '
            f'textLength="{full}" lengthAdjust="spacingAndGlyphs" clip-path="url(#tp{i})">{escape(p)}</text>'
        )
    cur_vals = ";".join(str(tx + v + 3) for v in cursor)
    first_cursor = tx + len(PHRASES[0]) * cw + 3

    # Chips
    chip_svg = []
    x = 368
    for i, label in enumerate(CHIPS):
        w = len(label) * 7.9 + 30
        chip_svg.append(
            f'<g class="chip" style="animation-delay:-{i * 0.45:.2f}s">'
            f'<rect x="{x:.1f}" y="270" width="{w:.1f}" height="30" rx="15" fill="{c["chip_bg"]}" '
            f'fill-opacity="{c["chip_bg_op"]}" stroke="{c["chip_stroke"]}" stroke-opacity="{c["chip_stroke_op"]}"/>'
            f'<circle cx="{x + 14:.1f}" cy="285" r="3" fill="{[c["cyan"], c["violet"], c["pink"], c["green"]][i % 4]}"/>'
            f'<text x="{x + 23:.1f}" y="289.5" class="sans" font-size="13" font-weight="600" fill="{c["text"]}" '
            f'fill-opacity="0.88" textLength="{len(label) * 7.9 - 1:.1f}" lengthAdjust="spacingAndGlyphs">{escape(label)}</text></g>'
        )
        x += w + 10

    # Emblem orbit paths
    ex, ey = 190, 196
    orbit1 = f"M {ex - 128} {ey} a 128 46 0 1 0 256 0 a 128 46 0 1 0 -256 0"
    orbit2 = f"M {ex - 112} {ey} a 112 40 0 1 0 224 0 a 112 40 0 1 0 -224 0"

    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">Sanjay Kumar</title>
  <desc id="d">Creative Full-Stack Engineer and Digital Architect, building at Clever Crow, India.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c['bg0']}"/><stop offset="0.55" stop-color="{c['bg1']}"/><stop offset="1" stop-color="{c['bg2']}"/>
    </linearGradient>
    <linearGradient id="name" x1="0" y1="0" x2="1" y2="0" gradientUnits="objectBoundingBox" spreadMethod="reflect">
      <stop offset="0" stop-color="{c['cyan']}"/><stop offset="0.35" stop-color="{c['violet']}"/>
      <stop offset="0.7" stop-color="{c['pink']}"/><stop offset="1" stop-color="{c['cyan']}"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="0 0;1 0" dur="6s" repeatCount="indefinite"/>
    </linearGradient>
    <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c['cyan']}"/><stop offset="0.5" stop-color="{c['violet']}"/><stop offset="1" stop-color="{c['pink']}"/>
    </linearGradient>
    <linearGradient id="trace" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{c['cyan']}" stop-opacity="0"/><stop offset="0.5" stop-color="{c['violet']}"/><stop offset="1" stop-color="{c['pink']}" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="core" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{c['violet']}" stop-opacity="0.55"/><stop offset="1" stop-color="{c['violet']}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="floorFade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.45" stop-color="#fff" stop-opacity="0.6"/><stop offset="1" stop-color="#fff" stop-opacity="1"/>
    </linearGradient>
    <mask id="floorMask"><rect x="0" y="{floor_top}" width="{W}" height="{H - floor_top}" fill="url(#floorFade)"/></mask>
    <clipPath id="frame"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="28"/></clipPath>
    <radialGradient id="gv"><stop offset="0" stop-color="{c['violet']}"/><stop offset="0.45" stop-color="{c['violet']}" stop-opacity="0.45"/><stop offset="1" stop-color="{c['violet']}" stop-opacity="0"/></radialGradient>
    <radialGradient id="gc"><stop offset="0" stop-color="{c['cyan']}"/><stop offset="0.45" stop-color="{c['cyan']}" stop-opacity="0.45"/><stop offset="1" stop-color="{c['cyan']}" stop-opacity="0"/></radialGradient>
    <radialGradient id="gp"><stop offset="0" stop-color="{c['pink']}"/><stop offset="0.45" stop-color="{c['pink']}" stop-opacity="0.45"/><stop offset="1" stop-color="{c['pink']}" stop-opacity="0"/></radialGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    {''.join(clips)}
  </defs>
  <style>
    .sans {{ font-family: {SANS}; }}
    .mono {{ font-family: {MONO}; }}
    .blob {{ transform-box: fill-box; transform-origin: center; animation: drift 18s ease-in-out infinite alternate; }}
    .b2 {{ animation-duration: 22s; animation-direction: alternate-reverse; }}
    .b3 {{ animation-duration: 26s; }}
    @keyframes drift {{ 0% {{ transform: translate(0,0) scale(1); }} 50% {{ transform: translate(60px,24px) scale(1.12); }} 100% {{ transform: translate(-50px,-14px) scale(0.94); }} }}
    .tw {{ animation: tw 4s ease-in-out infinite; }}
    @keyframes tw {{ 0%,100% {{ opacity: .12; }} 50% {{ opacity: 1; }} }}
    .spin {{ transform-box: view-box; transform-origin: {ex}px {ey}px; animation: spin 26s linear infinite; }}
    .spin-r {{ animation-duration: 38s; animation-direction: reverse; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    .breathe {{ transform-box: fill-box; transform-origin: center; animation: breathe 4.5s ease-in-out infinite; }}
    @keyframes breathe {{ 0%,100% {{ transform: scale(.92); opacity: .65; }} 50% {{ transform: scale(1.08); opacity: 1; }} }}
    .pulse {{ transform-box: fill-box; transform-origin: center; animation: pulse 2s ease-out infinite; }}
    @keyframes pulse {{ 0% {{ transform: scale(1); opacity: .7; }} 100% {{ transform: scale(3.2); opacity: 0; }} }}
    .chip {{ animation: bob 5s ease-in-out infinite; }}
    @keyframes bob {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-3px); }} }}
    .blink {{ animation: blink 1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    .rise {{ animation: rise 1.1s cubic-bezier(.2,.8,.2,1) both; }}
    .d1 {{ animation-delay: .15s; }} .d2 {{ animation-delay: .3s; }} .d3 {{ animation-delay: .45s; }}
    @keyframes rise {{ from {{ transform: translateY(14px); opacity: 0; }} to {{ transform: translateY(0); opacity: 1; }} }}
  </style>

  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#bg)"/>
    <g opacity="{c['blob']}">
      <ellipse class="blob" cx="260" cy="110" rx="330" ry="220" fill="url(#gv)"/>
      <ellipse class="blob b2" cx="930" cy="80" rx="340" ry="210" fill="url(#gc)"/>
      <ellipse class="blob b3" cx="700" cy="390" rx="380" ry="190" fill="url(#gp)"/>
    </g>
    <g>{''.join(stars)}</g>
    <g mask="url(#floorMask)" stroke="{c['grid']}" stroke-opacity="{c['grid_op']}" stroke-width="1">
      {''.join(vlines)}
      {''.join(hlines)}
    </g>

    <!-- emblem -->
    <circle class="breathe" cx="{ex}" cy="{ey}" r="120" fill="url(#core)"/>
    <g class="spin"><circle cx="{ex}" cy="{ey}" r="98" fill="none" stroke="url(#ring)" stroke-width="1.2" stroke-dasharray="2 9" opacity="0.9"/></g>
    <g class="spin spin-r"><circle cx="{ex}" cy="{ey}" r="86" fill="none" stroke="url(#ring)" stroke-width="2" stroke-dasharray="60 24 8 24" opacity="0.8"/></g>
    <g transform="rotate(-22 {ex} {ey})">
      <path d="{orbit1}" fill="none" stroke="{c['cyan']}" stroke-opacity="0.35"/>
      <circle r="5" fill="{c['cyan']}" filter="url(#glow)"><animateMotion dur="7s" repeatCount="indefinite" path="{orbit1}"/></circle>
    </g>
    <g transform="rotate(28 {ex} {ey})">
      <path d="{orbit2}" fill="none" stroke="{c['pink']}" stroke-opacity="0.3"/>
      <circle r="4" fill="{c['pink']}" filter="url(#glow)"><animateMotion dur="9.5s" begin="-3s" repeatCount="indefinite" path="{orbit2}"/></circle>
    </g>
    <circle cx="{ex}" cy="{ey}" r="66" fill="{c['card0']}" fill-opacity="{c['panel_op']}" stroke="url(#ring)" stroke-width="2.5"/>
    <text x="{ex}" y="{ey + 19}" text-anchor="middle" class="sans" font-size="54" font-weight="800" fill="url(#ring)" letter-spacing="-2">SK</text>

    <!-- status pill -->
    <g class="rise">
      <rect x="368" y="62" width="318" height="34" rx="17" fill="{c['chip_bg']}" fill-opacity="{c['chip_bg_op']}" stroke="{c['green']}" stroke-opacity="0.45"/>
      <circle class="pulse" cx="389" cy="79" r="4.5" fill="{c['green']}"/>
      <circle cx="389" cy="79" r="4.5" fill="{c['green']}"/>
      <text x="403" y="84" class="sans" font-size="14" font-weight="600" fill="{c['text']}" fill-opacity="0.85">Building at @clevercroworg · India</text>
    </g>

    <!-- name -->
    <g class="rise d1">
      <text x="364" y="182" class="sans" font-size="80" font-weight="800" letter-spacing="-2.5" fill="url(#name)" textLength="530" lengthAdjust="spacingAndGlyphs">Sanjay Kumar</text>
    </g>

    <!-- typing -->
    <g class="rise d2">
      <text x="340" y="{ty}" class="mono" font-size="{fs}" font-weight="700" fill="{c['violet']}">&gt;</text>
      {''.join(texts)}
      <rect class="blink" x="{first_cursor}" y="{ty - 22}" width="12" height="27" rx="2" fill="{c['cyan']}">
        <animate attributeName="x" dur="{dur}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kt}" values="{cur_vals}"/>
      </rect>
    </g>

    <g class="rise d3">{''.join(chip_svg)}</g>

    <text x="{W - 34}" y="{H - 24}" text-anchor="end" class="mono" font-size="13" fill="{c['muted']}">// github.com/SaNjAy-bRo</text>
  </g>

  <!-- frame + travelling light -->
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="28" fill="none" stroke="{c['violet']}" stroke-opacity="0.25"/>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="28" fill="none" stroke="url(#ring)" stroke-width="2.5"
        pathLength="1000" stroke-dasharray="140 360" filter="url(#glow)">
    <animate attributeName="stroke-dashoffset" values="1000;0" dur="9s" repeatCount="indefinite"/>
  </rect>
</svg>
"""


# --------------------------------------------------------------------------
# Section header (theme neutral: mid-tone colours read on white and on #0d1117)
# --------------------------------------------------------------------------
NEUTRAL = dict(cyan="#06b6d4", violet="#8b5cf6", pink="#ec4899", muted="#8b93a7")


def section_header(num: str, title: str, kicker: str) -> str:
    c = NEUTRAL
    W, H = 1200, 96
    tw = len(title) * 18.5
    line_x = 112 + tw + 28
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(title)}">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{c['cyan']}"/><stop offset="0.5" stop-color="{c['violet']}"/><stop offset="1" stop-color="{c['pink']}"/>
    </linearGradient>
    <linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{c['violet']}" stop-opacity="0.7"/><stop offset="1" stop-color="{c['pink']}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="glint" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="{c['cyan']}"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <style>
    .sans {{ font-family: {SANS}; }}
    .mono {{ font-family: {MONO}; }}
    .in {{ animation: in .9s cubic-bezier(.2,.8,.2,1) both; }}
    @keyframes in {{ from {{ transform: translateX(-16px); opacity: 0; }} to {{ transform: none; opacity: 1; }} }}
    .spin {{ transform-box: fill-box; transform-origin: center; animation: spin 10s linear infinite; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  </style>
  <g class="in">
    <g transform="translate(44 50)">
      <rect class="spin" x="-26" y="-26" width="52" height="52" rx="14" fill="none" stroke="url(#g)" stroke-width="2" stroke-dasharray="10 6"/>
      <rect x="-19" y="-19" width="38" height="38" rx="10" fill="url(#g)" opacity="0.14"/>
      <text y="7" text-anchor="middle" class="mono" font-size="18" font-weight="800" fill="{c['violet']}">{num}</text>
    </g>
    <text x="104" y="34" class="mono" font-size="13" font-weight="700" letter-spacing="3" fill="{c['muted']}">{escape(kicker.upper())}</text>
    <text x="102" y="70" class="sans" font-size="32" font-weight="800" letter-spacing="-0.5" fill="url(#g)" textLength="{tw:.0f}" lengthAdjust="spacingAndGlyphs">{escape(title)}</text>
    <rect x="{line_x:.0f}" y="58" width="{W - line_x - 10:.0f}" height="2" rx="1" fill="url(#fade)"/>
    <rect x="{line_x:.0f}" y="57" width="120" height="4" rx="2" fill="url(#glint)">
      <animate attributeName="x" values="{line_x:.0f};{W - 130};{line_x:.0f}" dur="5s" repeatCount="indefinite" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1" keyTimes="0;.5;1"/>
    </rect>
  </g>
</svg>
"""


SECTIONS = [
    ("01", "About me", "whoami", "header-about.svg"),
    ("02", "Tech stack", "tools of the trade", "header-stack.svg"),
    ("03", "Featured work", "shipped & in production", "header-work.svg"),
    ("04", "GitHub pulse", "live · refreshed daily", "header-pulse.svg"),
    ("05", "Kind words", "from a client", "header-words.svg"),
    ("06", "Let's build", "say hello", "header-contact.svg"),
]


# --------------------------------------------------------------------------
# Animated divider
# --------------------------------------------------------------------------
def divider() -> str:
    c = NEUTRAL
    W, H = 1200, 28
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="presentation">
  <defs>
    <linearGradient id="l" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{c['cyan']}" stop-opacity="0"/><stop offset="0.2" stop-color="{c['cyan']}" stop-opacity="0.6"/>
      <stop offset="0.5" stop-color="{c['violet']}" stop-opacity="0.8"/><stop offset="0.8" stop-color="{c['pink']}" stop-opacity="0.6"/>
      <stop offset="1" stop-color="{c['pink']}" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="dot"><stop offset="0" stop-color="#fff"/><stop offset="0.4" stop-color="{c['violet']}"/><stop offset="1" stop-color="{c['violet']}" stop-opacity="0"/></radialGradient>
  </defs>
  <style>
    .d {{ transform-box: fill-box; transform-origin: center; animation: p 2.6s ease-in-out infinite; }}
    @keyframes p {{ 0%,100% {{ transform: rotate(45deg) scale(.8); }} 50% {{ transform: rotate(225deg) scale(1.15); }} }}
  </style>
  <rect x="0" y="13" width="{W}" height="2" fill="url(#l)"/>
  <circle cy="14" r="9" fill="url(#dot)">
    <animate attributeName="cx" values="60;{W - 60};60" dur="7s" repeatCount="indefinite" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1" keyTimes="0;.5;1"/>
  </circle>
  <rect class="d" x="{W / 2 - 6}" y="8" width="12" height="12" rx="2" fill="none" stroke="{c['violet']}" stroke-width="2"/>
</svg>
"""


# --------------------------------------------------------------------------
# Project cards
# --------------------------------------------------------------------------
PROJECTS = [
    dict(slug="healthtracker", name="HealthTracker", initials="HT", tag="NEW",
         kind="Healthcare · Mobile app",
         line="An app for doctors: patient records, PDF reports",
         line2="and a built-in AI assistant.",
         stack=["React Native", "Expo", "TypeScript"]),
    dict(slug="persona-keyboard", name="Persona Keyboard", initials="PK", tag="NEW",
         kind="Android · AI",
         line="An Android keyboard with AI personas, emoji,",
         line2="GIFs, stickers and autocorrect.",
         stack=["Kotlin", "Android"]),
    dict(slug="turbo-ride", name="Turbo Ride Supercars", initials="TR", tag="LIVE",
         kind="Luxury mobility",
         line="+185% bookings lift · sub-second checkout",
         line2="0.000 CLS",
         stack=["Next.js 15", "Stripe", "Django"]),
    dict(slug="cocofuse", name="COCO FUSE", initials="CF", tag="LIVE",
         kind="D2C 3D commerce",
         line="3-flavor liquid visualizer · 2.4x cart uplift",
         line2="60 FPS",
         stack=["React 19", "Shopify", "GLSL"]),
    dict(slug="ssquad", name="SSquad Global", initials="SQ", tag="LIVE",
         kind="Enterprise defense",
         line="Real-time threat HUD · sub-12ms telemetry",
         line2="Zero-trust SOC2",
         stack=["React 19", "TypeScript", "Cloud"]),
    dict(slug="yacht-club", name="Yacht Club India", initials="YC", tag="LIVE",
         kind="Luxury maritime",
         line="500+ luxury charters · Goa route planner",
         line2="4.9★ CSAT",
         stack=["Django", "FastAPI", "Framer Motion"]),
    dict(slug="tanubhi", name="Tanubhi Couture", initials="TC", tag="LIVE",
         kind="Haute couture & spa",
         line="Multi-stylist slot calendar",
         line2="under-20s reservation flow",
         stack=["Next.js 15", "Redis", "TypeScript"]),
    dict(slug="clever-crow", name="Clever Crow", initials="CC", tag="LIVE",
         kind="Studio website",
         line="Company site with landing pages",
         line2="and a leads dashboard.",
         stack=["Next.js", "TypeScript", "Vercel"]),
]


def project_card(p: dict, theme: str, idx: int) -> str:
    c = THEMES[theme]
    W, H = 600, 230
    accents = [(c["cyan"], c["violet"]), (c["violet"], c["pink"]), (c["pink"], c["amber"]), (c["green"], c["cyan"])]
    a1, a2 = accents[idx % 4]
    tag_col = c["green"] if p["tag"] == "LIVE" else c["amber"]
    chips, x = [], 28
    for s in p["stack"]:
        w = len(s) * 7.4 + 24
        chips.append(
            f'<rect x="{x:.1f}" y="176" width="{w:.1f}" height="28" rx="8" fill="{a1}" fill-opacity="0.10" stroke="{a1}" stroke-opacity="0.35"/>'
            f'<text x="{x + 12:.1f}" y="194.5" class="mono" font-size="12.5" font-weight="600" fill="{c["text"]}" fill-opacity="0.85">{escape(s)}</text>'
        )
        x += w + 8
    delay = idx * 0.9
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(p['name'])}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c['card0']}"/><stop offset="1" stop-color="{c['card1']}"/></linearGradient>
    <linearGradient id="ac" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a1}"/><stop offset="1" stop-color="{a2}"/></linearGradient>
    <linearGradient id="sh" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="{0.10 if theme == 'dark' else 0.6}"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="glow" cx="1" cy="0" r="0.9"><stop offset="0" stop-color="{a2}" stop-opacity="{0.35 if theme == 'dark' else 0.18}"/><stop offset="1" stop-color="{a2}" stop-opacity="0"/></radialGradient>
    <clipPath id="cl"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="22"/></clipPath>
  </defs>
  <style>
    .sans {{ font-family: {SANS}; }}
    .mono {{ font-family: {MONO}; }}
    .sweep {{ animation: sweep 7s ease-in-out infinite; animation-delay: {delay:.1f}s; }}
    @keyframes sweep {{ 0% {{ transform: translateX(-260px) skewX(-20deg); }} 35%,100% {{ transform: translateX({W + 60}px) skewX(-20deg); }} }}
    .gl {{ animation: gl 6s ease-in-out infinite alternate; }}
    @keyframes gl {{ from {{ opacity: .55; }} to {{ opacity: 1; }} }}
    .live {{ transform-box: fill-box; transform-origin: center; animation: lv 1.8s ease-out infinite; }}
    @keyframes lv {{ 0% {{ transform: scale(1); opacity: .8; }} 100% {{ transform: scale(3); opacity: 0; }} }}
  </style>
  <g clip-path="url(#cl)">
    <rect width="{W}" height="{H}" fill="url(#bg)"/>
    <rect class="gl" width="{W}" height="{H}" fill="url(#glow)"/>
    <rect class="sweep" x="0" y="-20" width="140" height="{H + 40}" fill="url(#sh)"/>
    <rect x="0" y="0" width="5" height="{H}" fill="url(#ac)"/>
  </g>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="22" fill="none" stroke="url(#ac)" stroke-opacity="0.5"/>

  <rect x="28" y="28" width="52" height="52" rx="14" fill="url(#ac)"/>
  <text x="54" y="61" text-anchor="middle" class="sans" font-size="20" font-weight="800" fill="#ffffff">{p['initials']}</text>
  <text x="96" y="52" class="sans" font-size="23" font-weight="800" fill="{c['text']}">{escape(p['name'])}</text>
  <text x="96" y="76" class="mono" font-size="12.5" font-weight="600" letter-spacing="1.5" fill="{c['muted']}">{escape(p['kind'].upper())}</text>

  <g transform="translate({W - 92} 30)">
    <rect width="66" height="26" rx="13" fill="{tag_col}" fill-opacity="0.12" stroke="{tag_col}" stroke-opacity="0.5"/>
    <circle class="live" cx="15" cy="13" r="3.5" fill="{tag_col}"/>
    <circle cx="15" cy="13" r="3.5" fill="{tag_col}"/>
    <text x="26" y="17.5" class="mono" font-size="11.5" font-weight="800" fill="{tag_col}">{p['tag']}</text>
  </g>

  <text x="28" y="122" class="sans" font-size="16" fill="{c['text']}" fill-opacity="0.9">{escape(p['line'])}</text>
  <text x="28" y="146" class="sans" font-size="16" fill="{c['text']}" fill-opacity="0.9">{escape(p['line2'])}</text>
  {''.join(chips)}
  <text x="{W - 28}" y="196" text-anchor="end" class="sans" font-size="20" font-weight="700" fill="{a2}">↗</text>
</svg>
"""


# --------------------------------------------------------------------------
# Footer wave
# --------------------------------------------------------------------------
def footer(theme: str) -> str:
    c = THEMES[theme]
    W, H = 1200, 170

    def wave(amp, y, phase):
        pts = [f"M 0 {H}"]
        for x in range(0, W * 2 + 1, 20):
            pts.append(f"L {x} {y + amp * math.sin(x / W * 4 * math.pi + phase):.1f}")
        pts.append(f"L {W * 2} {H} Z")
        return " ".join(pts)

    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Thanks for visiting">
  <defs>
    <linearGradient id="w1" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{c['cyan']}"/><stop offset="0.5" stop-color="{c['violet']}"/><stop offset="1" stop-color="{c['pink']}"/></linearGradient>
    <clipPath id="cl"><rect width="{W}" height="{H}" rx="24"/></clipPath>
  </defs>
  <style>
    .sans {{ font-family: {SANS}; }}
    .w {{ animation: w 9s linear infinite; }}
    .w2 {{ animation-duration: 14s; }}
    .w3 {{ animation-duration: 20s; }}
    @keyframes w {{ to {{ transform: translateX(-{W}px); }} }}
  </style>
  <g clip-path="url(#cl)">
    <path class="w w3" d="{wave(14, 92, 1.2)}" fill="url(#w1)" opacity="0.18"/>
    <path class="w w2" d="{wave(18, 108, 0.4)}" fill="url(#w1)" opacity="0.32"/>
    <path class="w" d="{wave(12, 126, 2.4)}" fill="url(#w1)" opacity="0.85"/>
  </g>
  <text x="{W / 2}" y="56" text-anchor="middle" class="sans" font-size="22" font-weight="700" fill="{c['text']}" fill-opacity="0.85">Thanks for stopping by · let's build something great</text>
</svg>
"""


def main() -> None:
    for t in THEMES:
        write(f"banner-{t}.svg", banner(t))
        write(f"footer-{t}.svg", footer(t))
        for i, p in enumerate(PROJECTS):
            write(f"project-{p['slug']}-{t}.svg", project_card(p, t, i))
    for num, title, kicker, fname in SECTIONS:
        write(fname, section_header(num, title, kicker))
    write("divider.svg", divider())


if __name__ == "__main__":
    main()
