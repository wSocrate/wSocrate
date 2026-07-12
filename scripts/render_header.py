import math
from pathlib import Path

W, H = 880, 300
HORIZON = 190
SAND_Y = 252
OUT = Path(__file__).resolve().parent.parent / "assets" / "header.svg"

C = {
    "sky0": "#16102e",
    "sky1": "#472357",
    "sky2": "#a34a5e",
    "sky3": "#ffb26b",
    "border": "#3a2540",
    "sun": "#ffd97a",
    "sun_core": "#ffe9ad",
    "sea0": "#0d4a63",
    "sea1": "#0a2f45",
    "shimmer": "#7fd4c1",
    "shimmer_gold": "#ffcf8a",
    "sand": "#e0c08f",
    "sand_dark": "#cda878",
    "sand_wet": "#c39b70",
    "foam": "#f6e7c8",
    "text": "#fff3e2",
    "muted": "#ecd3b6",
    "accent": "#ff8f6b",
    "star": "#f5e6d0",
    "bird": "#2a1a2e",
    "O": "#1d1208",
    "B": "#96653c",
    "D": "#7b4f2c",
    "M": "#ecd2ab",
    "N": "#241a10",
    "wsk": "#e8d5b5",
    "L": "#1f7a4d",
    "l": "#2ea061",
    "T": "#7a5238",
    "t": "#8f6244",
    "coco": "#5c4330",
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

OTTER_HEAD = [
    ".OO....OO.",
    ".ODOOOODO.",
    "OOBBBBBBOO",
    "OBBBBBBBBO",
    "OBNBBBBNBO",
    "OBBMMMMBBO",
    "OBMMNNMMBO",
    ".OMMMMMMO.",
    "..OOOOOO..",
]
OTTER_BELLY = [
    "..OOOOOOOOOOOOOO..",
    ".OMMMMMMMMMMMMMMO.",
    "OBMMMMMMMMMMMMMMBO",
    "OBBBBBBBBBBBBBBBBO",
    ".OOOOOOOOOOOOOOOO.",
]
OTTER_FEET = [
    ".OO..OO..",
    "ODDOODDO.",
    ".OO..OO..",
]
COCONUT = [
    ".ccc.",
    "cchcc",
    "ccccc",
    ".ccc.",
]
STARFISH = [
    "..#..",
    ".###.",
    "#####",
    ".#.#.",
]

PALM = [
    "....lllll........",
    "..lllLLLLlll.....",
    ".llLLLLLLLLLll...",
    "llLL...TT...LLll.",
    "lL....lTTl....Ll.",
    "L.....TTTT.....L.",
    "......cTTc.......",
    ".......TT........",
    ".......TTt.......",
    ".......tTT.......",
    "........TT.......",
    "........TTt......",
    ".........TT......",
    ".........TT......",
    "........tTT......",
    "........TT.......",
]
PALM_COLORS = {"L": C["L"], "l": C["l"], "T": C["T"], "t": C["t"], "c": C["coco"]}
OTTER_COLORS = {k: C[k] for k in "OBDMN"}
OTTER_COLORS["c"] = C["coco"]
OTTER_COLORS["h"] = "#7a5a42"

STARS = [
    (60, 34, 0.0), (150, 62, 1.2), (238, 28, 2.1), (322, 52, 0.6),
    (410, 24, 1.8), (472, 66, 2.6), (540, 38, 0.3), (610, 20, 1.5),
    (688, 46, 2.3), (764, 26, 0.9), (826, 58, 1.1), (108, 88, 2.8),
]

SHIMMER = [
    (110, 208, 0.4), (190, 226, 1.6), (262, 214, 2.4), (348, 232, 0.9),
    (430, 210, 1.9), (500, 238, 0.2), (560, 218, 1.2), (598, 204, 0.7),
    (614, 222, 1.4), (632, 210, 2.1), (648, 236, 0.5), (664, 216, 1.8),
    (735, 230, 2.7), (60, 240, 1.0), (300, 244, 2.0),
]

BIRDS = [(392, 74, 0.0), (438, 58, 1.6)]


def rect(x, y, w, h, fill, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" {extra}/>'


def pixels(art, ox, oy, px, colormap):
    out = []
    for j, row in enumerate(art):
        for i, ch in enumerate(row):
            if ch in colormap:
                out.append(rect(ox + i * px, oy + j * px, px, px, colormap[ch]))
    return out


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
  .tw {{ animation: tw 3.4s ease-in-out infinite; }}
  @keyframes tw {{ 0%,100% {{ opacity:.12 }} 50% {{ opacity:.85 }} }}
  .fl {{ animation: fl 6s ease-in-out infinite; }}
  @keyframes fl {{ 0%,100% {{ transform: translateY(0) }} 50% {{ transform: translateY(-5px) }} }}
  .sub {{ font: 500 15px ui-monospace, 'Cascadia Code', Consolas, monospace; }}
</style>""")

parts.append(f'''<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{C['sky0']}"/>
    <stop offset=".5" stop-color="{C['sky1']}"/>
    <stop offset=".78" stop-color="{C['sky2']}"/>
    <stop offset="1" stop-color="{C['sky3']}"/>
  </linearGradient>
  <linearGradient id="sea" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{C['sea0']}"/>
    <stop offset="1" stop-color="{C['sea1']}"/>
  </linearGradient>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="12"/></clipPath>
  <clipPath id="abovewater"><rect width="{W}" height="236"/></clipPath>
</defs>''')

parts.append(f'<g clip-path="url(#card)">')

parts.append(rect(0, 0, W, HORIZON, "url(#sky)"))
parts.append(rect(0, HORIZON, W, SAND_Y - HORIZON, "url(#sea)"))
parts.append(rect(0, SAND_Y, W, H - SAND_Y, C["sand"]))

sun_x, sun_r, px = 620, 40, 6
for j in range(sun_r // px):
    y = HORIZON - (j + 1) * px
    half = math.sqrt(sun_r ** 2 - (j * px) ** 2)
    half = int(half // px) * px
    col = C["sun_core"] if j < 2 else C["sun"]
    parts.append(rect(sun_x - half, y, half * 2, px, col))
parts.append(f'<circle cx="{sun_x}" cy="{HORIZON}" r="72" fill="{C["sun"]}" opacity=".14"/>')

for (x, y, d) in STARS:
    parts.append(rect(x, y, 3, 3, C["star"], f'class="tw" style="animation-delay:{d}s" opacity=".5"'))

for (x, y, d) in BIRDS:
    g = [rect(0, 3, 4, 3, C["bird"]), rect(4, 0, 4, 3, C["bird"]),
         rect(8, 3, 4, 3, C["bird"])]
    parts.append(f'<g transform="translate({x},{y})" class="fl" style="animation-delay:{d}s" opacity=".7">{"".join(g)}</g>')

for (x, y, d) in SHIMMER:
    col = C["shimmer_gold"] if 575 <= x <= 670 else C["shimmer"]
    parts.append(rect(x, y, 6, 3, col, f'class="tw" style="animation-delay:{d}s" opacity=".4"'))

i = 0
while i < W:
    seg = 14 + (i * 7) % 22
    if (i // 20) % 3 != 2:
        parts.append(rect(i, SAND_Y - 3, seg, 3, C["foam"], 'opacity=".8"'))
    i += seg + 8
parts.append(rect(0, SAND_Y, W, 7, C["sand_wet"], 'opacity=".55"'))
for k in range(26):
    sx = (k * 137 + 43) % (W - 10)
    sy = SAND_Y + 14 + (k * 61) % (H - SAND_Y - 22)
    parts.append(rect(sx, sy, 5, 3, C["sand_dark"], 'opacity=".7"'))

palm_px = 7
palm_w = len(PALM[0]) * palm_px
palm_h = len(PALM) * palm_px
palm_x, palm_y = W - palm_w - 42, H - 16 - palm_h
parts.extend(pixels(PALM, palm_x, palm_y, palm_px, PALM_COLORS))

ot_px = 5
waterline = 236
bx, belly_y = 560, waterline - 24
head_x, head_y = bx - 32, belly_y - 35
otter = []
otter.extend(pixels(OTTER_BELLY, bx, belly_y, ot_px, OTTER_COLORS))
otter.extend(pixels(OTTER_HEAD, head_x, head_y, ot_px, OTTER_COLORS))
otter.append(rect(bx + 26, belly_y - 3, 7, 7, C["B"]))
otter.append(rect(bx + 54, belly_y - 3, 7, 7, C["B"]))
otter.extend(pixels(COCONUT, bx + 31, belly_y - 18, ot_px, OTTER_COLORS))
otter.extend(pixels(OTTER_FEET, bx + 96, waterline - 14, ot_px, OTTER_COLORS))
for (wx, wy, ww) in [(head_x - 9, head_y + 6 * ot_px + 1, 9), (head_x - 7, head_y + 7 * ot_px + 1, 7),
                     (head_x + 10 * ot_px, head_y + 6 * ot_px + 1, 9), (head_x + 10 * ot_px + 2, head_y + 7 * ot_px + 1, 7)]:
    otter.append(rect(wx, wy, ww, 2, C["wsk"], 'opacity=".85"'))
parts.append(f'<g clip-path="url(#abovewater)">{"".join(otter)}</g>')
for (rx, ry, rw, d) in [(bx - 46, waterline + 2, 22, 0.5), (bx - 12, waterline + 6, 16, 1.7),
                        (bx + 34, waterline + 3, 26, 0.1), (bx + 84, waterline + 7, 18, 2.2),
                        (bx + 118, waterline + 2, 14, 1.0)]:
    parts.append(rect(rx, ry, rw, 3, C["shimmer"], f'class="tw" style="animation-delay:{d}s" opacity=".45"'))

parts.extend(pixels(STARFISH, 690, 268, 4, {"#": C["accent"]}))

title, tw = pixel_text("SOCRATE", 64, 64, 7, C["text"])
parts.extend(title)
parts.append(rect(64 + tw + 6, 64 + 4 * 7, 7, 3 * 7, C["accent"], 'class="tw"'))

parts.append(f'<text x="66" y="150" class="sub" fill="{C["muted"]}">crafting <tspan fill="{C["accent"]}">Walyverse</tspan>, a French Minecraft universe</text>')
parts.append(f'<text x="66" y="174" class="sub" fill="{C["muted"]}" opacity=".8">walyverse.fr</text>')

parts.append("</g>")
parts.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{C["border"]}"/>')
parts.append("</svg>")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(parts), encoding="utf-8")
print(f"OK -> {OUT}")
