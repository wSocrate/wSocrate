from pathlib import Path

W, H = 880, 300
WATER_Y = 214
SHORE_Y = 254
SNOWLINE = 152
OUT = Path(__file__).resolve().parent.parent / "assets" / "header.svg"

C = {
    "sky0": "#1d6cc0",
    "sky1": "#3f92d9",
    "sky2": "#82c0ea",
    "sky3": "#cbe6f7",
    "cloud": "#ffffff",
    "cloud_mid": "#e6f0fa",
    "cloud_shadow": "#c2d7ea",
    "far": "#91a8bf",
    "far_d": "#748ca6",
    "snow": "#f6fafd",
    "snow_d": "#d3e3f0",
    "near": "#5c7f68",
    "near_d": "#48674f",
    "forest": "#2c5436",
    "forest_l": "#3b6e44",
    "water0": "#2f86ab",
    "water1": "#144463",
    "shimmer": "#cdeaf5",
    "shore": "#cbb78f",
    "meadow0": "#71b052",
    "meadow1": "#4d8837",
    "grass_d": "#3f7530",
    "grass_l": "#93c96a",
    "wheat": "#e8c96f",
    "wheat_d": "#c29e47",
    "trunk": "#4a3526",
    "sun": "#ffe9a8",
    "sun_core": "#fffae4",
    "bird": "#22405e",
    "text": "#ffffff",
    "muted": "#eaf4fc",
    "accent": "#f2c14e",
    "border": "#2c5f8d",
    "petal": "#fdfdf2",
}

FONT = {
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
}

CLOUD_ART = [
    "...#####....",
    "..########..",
    ".###########",
    "############",
    ".##########.",
]

CLOUDS = [
    (60, 34, 7, 0.0, 17),
    (286, 22, 5, 2.4, 23),
    (452, 58, 4, 1.1, 19),
    (676, 24, 6, 3.2, 26),
    (150, 92, 4, 4.0, 21),
]

BIRDS = [(520, 78, 0.0), (566, 62, 1.6), (600, 88, 2.9)]

# (center x, base y, half width, summit y)
FAR_PEAKS = [
    (40, 208, 130, 192),
    (190, 208, 140, 184),
    (350, 208, 150, 176),
    (500, 208, 150, 146),
    (648, 208, 150, 98),
    (784, 208, 150, 120),
    (880, 208, 120, 148),
]

NEAR_PEAKS = [
    (0, WATER_Y, 120, 188),
    (150, WATER_Y, 130, 194),
    (310, WATER_Y, 140, 186),
    (460, WATER_Y, 130, 192),
    (610, WATER_Y, 140, 184),
    (750, WATER_Y, 130, 190),
    (870, WATER_Y, 110, 192),
]

SHIP = [
    ".........v.......",
    "........vvv......",
    ".........v.......",
    "....ccccccccc....",
    "....sssssssss....",
    "....ccccccccc....",
    "....sssssssss....",
    "....ccccccccc....",
    "....ttttttttt....",
    ".........m.......",
    "d........m......d",
    "dd.......m.....dd",
    ".ddddddddddddddd.",
    "..ooooooooooooo..",
    "...ddddddddddd...",
]

SHIP_COLORS = {
    "v": "#b5503f",
    "c": "#f0e2c4",
    "s": "#b5503f",
    "t": "#d6c4a3",
    "m": "#6b4a33",
    "d": "#4a3526",
}


def rect(x, y, w, h, fill, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" {extra}/>'


def noise(n, span):
    return (n * 7919 + (n // 3) * 104729) % span


def mountains(peaks, step, body, dark, snow=False):
    out = []
    for k, x in enumerate(range(0, W, step)):
        mid = x + step / 2
        best = None
        for p in peaks:
            cx, base, half, summit = p
            if abs(mid - cx) <= half:
                top = summit + (base - summit) * (abs(mid - cx) / half)
                top = int(top // step) * step
                if best is None or top < best[0]:
                    best = (top, p)
        if best is None:
            continue
        top, (cx, base, half, summit) = best
        out.append(rect(x, top, step, H - top, body))
        if mid > cx:
            out.append(rect(x, top, step, H - top, dark, 'opacity=".35"'))
        out.append(rect(x, top, step, step, dark, 'opacity=".5"'))
        if snow and summit < SNOWLINE:
            cap = min(SNOWLINE, summit + (base - summit) * 0.42)
            cap = int(cap // step) * step + noise(k, 2) * step
            if cap - top >= step * 2:
                out.append(rect(x, top, step, cap - top, C["snow"]))
                out.append(rect(x, cap - step, step, step, C["snow_d"]))
                if mid > cx:
                    out.append(rect(x, top, step, cap - top, C["snow_d"], 'opacity=".45"'))
    return out


def pine(x, base, px, body, tip):
    out = [rect(x - max(1, px // 3), base - px * 2, max(2, px - px // 3), px * 2, C["trunk"])]
    for j in range(5):
        half = (j + 1) * px
        out.append(rect(x - half, base - px * 2 - (5 - j) * px, half * 2, px, body if j % 2 else tip))
    return out


def art(rows, ox, oy, px, color):
    out = []
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            fill = color(ch, i, j, len(rows))
            if fill:
                out.append(rect(ox + i * px, oy + j * px, px, px, fill))
    return out


def cloud_color(ch, i, j, n):
    if ch != "#":
        return None
    if j == n - 1:
        return C["cloud_shadow"]
    if j == n - 2:
        return C["cloud_mid"]
    return C["cloud"]


def ship_color(ch, i, j, n):
    if ch == "o":
        return C["accent"] if i % 2 else SHIP_COLORS["c"]
    return SHIP_COLORS.get(ch)


def pixel_text(word, ox, oy, px, fill):
    out = []
    x = ox
    for letter in word:
        for j, row in enumerate(FONT[letter]):
            for i, ch in enumerate(row):
                if ch == "#":
                    out.append(rect(x + i * px, oy + j * px, px, px, fill))
        x += 6 * px
    return out, x - ox


parts = []
parts.append(
    f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Socrate, building Walyverse">'
)
parts.append(f"""<style>
  .drift {{ animation: drift 18s ease-in-out infinite; }}
  @keyframes drift {{ 0%,100% {{ transform: translateX(0) }} 50% {{ transform: translateX(16px) }} }}
  .fl {{ animation: fl 6s ease-in-out infinite; }}
  @keyframes fl {{ 0%,100% {{ transform: translateY(0) }} 50% {{ transform: translateY(-5px) }} }}
  .row {{ animation: row 11s ease-in-out infinite; }}
  @keyframes row {{ 0%,100% {{ transform: translate(0,0) }} 50% {{ transform: translate(10px,-3px) }} }}
  .sw {{ animation: sw 5s ease-in-out infinite; transform-origin: bottom; }}
  @keyframes sw {{ 0%,100% {{ transform: skewX(0deg) }} 50% {{ transform: skewX(-5deg) }} }}
  .tw {{ animation: tw 3.4s ease-in-out infinite; }}
  @keyframes tw {{ 0%,100% {{ opacity:.2 }} 50% {{ opacity:.62 }} }}
  .gl {{ animation: gl 7s ease-in-out infinite; }}
  @keyframes gl {{ 0%,100% {{ opacity:.13 }} 50% {{ opacity:.26 }} }}
  .sub {{ font: 500 15px ui-monospace, 'Cascadia Code', Consolas, monospace; }}
</style>""")

parts.append(f'''<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{C['sky0']}"/>
    <stop offset=".44" stop-color="{C['sky1']}"/>
    <stop offset=".76" stop-color="{C['sky2']}"/>
    <stop offset="1" stop-color="{C['sky3']}"/>
  </linearGradient>
  <linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{C['water0']}"/>
    <stop offset="1" stop-color="{C['water1']}"/>
  </linearGradient>
  <linearGradient id="meadow" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{C['meadow1']}"/>
    <stop offset="1" stop-color="{C['meadow0']}"/>
  </linearGradient>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="12"/></clipPath>
</defs>''')

parts.append('<g clip-path="url(#card)">')
parts.append(rect(0, 0, W, WATER_Y, "url(#sky)"))

sun_x, sun_y, sun_r, px = 790, 52, 32, 6
parts.append(f'<circle cx="{sun_x}" cy="{sun_y}" r="76" fill="{C["sun"]}" class="gl"/>')
for j in range(-(sun_r // px), sun_r // px + 1):
    y = sun_y + j * px
    half = int(((sun_r ** 2 - (j * px) ** 2) ** 0.5) // px) * px
    if half:
        parts.append(rect(sun_x - half, y, half * 2, px, C["sun_core"] if abs(j) < 2 else C["sun"]))

for (cx, cy, cpx, delay, dur) in CLOUDS:
    parts.append(
        f'<g transform="translate({cx},{cy})" class="drift" '
        f'style="animation-delay:{delay}s;animation-duration:{dur}s" opacity=".95">'
        f'{"".join(art(CLOUD_ART, 0, 0, cpx, cloud_color))}</g>'
    )

for (x, y, d) in BIRDS:
    g = [rect(0, 3, 4, 3, C["bird"]), rect(4, 0, 4, 3, C["bird"]), rect(8, 3, 4, 3, C["bird"])]
    parts.append(
        f'<g transform="translate({x},{y})" class="fl" style="animation-delay:{d}s" opacity=".5">{"".join(g)}</g>'
    )

parts.extend(mountains(FAR_PEAKS, 8, C["far"], C["far_d"], snow=True))
parts.extend(mountains(NEAR_PEAKS, 6, C["near"], C["near_d"]))

for k in range(-6, W + 18, 11):
    scale = 4 + noise(k, 3)
    parts.extend(pine(k, WATER_Y + 3 + noise(k, 6), scale, C["forest"], C["forest_l"]))

parts.append(rect(0, WATER_Y, W, SHORE_Y - WATER_Y, "url(#water)"))

ship_px = 6
ship_x, hull_bottom = 574, WATER_Y + 8
ship_y = hull_bottom - len(SHIP) * ship_px
parts.append(f'<g class="row">{"".join(art(SHIP, ship_x, ship_y, ship_px, ship_color))}</g>')

for k in range(26):
    x = (k * 173 + 29) % (W - 60)
    y = WATER_Y + 5 + noise(k, SHORE_Y - WATER_Y - 11)
    parts.append(rect(x, y, 12 + noise(k, 16), 3, C["shimmer"], f'class="tw" style="animation-delay:{k * 0.17:.2f}s"'))

parts.append(rect(0, SHORE_Y, W, H - SHORE_Y, "url(#meadow)"))
parts.append(rect(0, SHORE_Y, W, 5, C["shore"], 'opacity=".9"'))
parts.append(rect(0, SHORE_Y + 5, W, 3, C["grass_d"], 'opacity=".4"'))

for k in range(54):
    x = (k * 149 + 21) % (W - 12)
    y = SHORE_Y + 14 + noise(k, H - SHORE_Y - 22)
    parts.append(rect(x, y, 3, 8, C["grass_d"] if k % 2 else C["grass_l"], 'opacity=".8"'))
for k in range(20):
    x = (k * 233 + 47) % (W - 20)
    y = SHORE_Y + 16 + noise(k, H - SHORE_Y - 28)
    parts.append(rect(x + 1, y + 6, 3, 14, C["wheat_d"]))
    parts.append(rect(x, y, 5, 8, C["wheat"]))
    parts.append(rect(x + 5, y + 3, 2, 4, C["wheat_d"]))
for k in range(7):
    x = (k * 311 + 91) % (W - 24)
    parts.append(rect(x, SHORE_Y + 20 + noise(k, 16), 4, 4, C["petal"], 'opacity=".9"'))

for (x, base, scale, op) in [(826, H + 4, 11, "1"), (24, H + 20, 10, ".97")]:
    parts.append(
        f'<g class="sw" style="animation-delay:{x % 5}s" opacity="{op}">'
        f'{"".join(pine(x, base, scale, C["forest"], C["forest_l"]))}</g>'
    )

shadow, _ = pixel_text("SOCRATE", 67, 61, 7, "#10395f")
parts.append(f'<g opacity=".32">{"".join(shadow)}</g>')
title, tw = pixel_text("SOCRATE", 64, 58, 7, C["text"])
parts.extend(title)
parts.append(rect(64 + tw + 6, 58 + 4 * 7, 7, 3 * 7, C["accent"]))

parts.append(
    f'<text x="66" y="140" class="sub" fill="{C["muted"]}">crafting '
    f'<tspan fill="{C["accent"]}">Walyverse</tspan>, a French Minecraft universe</text>'
)
parts.append(f'<text x="66" y="164" class="sub" fill="{C["muted"]}" opacity=".82">walyverse.fr</text>')

parts.append("</g>")
parts.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{C["border"]}"/>')
parts.append("</svg>")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(parts), encoding="utf-8")
print(f"OK -> {OUT}")
