import math
from pathlib import Path

W, H = 880, 300
OUT = Path(__file__).resolve().parent.parent / "assets" / "header.svg"

C = {
    "bg0": "#0b1018",
    "bg1": "#141d2a",
    "grid": "#ffffff",
    "link": "#3f7ba8",
    "node": "#9fd8cd",
    "halo": "#58c2b0",
    "text": "#f4f6fa",
    "muted": "#aeb9c9",
    "faint": "#6b7684",
    "gold": "#f2c14e",
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

MONO = "ui-monospace, 'Cascadia Code', 'SF Mono', Consolas, monospace"

NODES = [
    (128, 62), (196, 128), (150, 186), (268, 84), (316, 156), (352, 60),
    (404, 118), (438, 182), (486, 72), (520, 118), (566, 104), (588, 176),
    (624, 52), (652, 132), (712, 90), (724, 170), (782, 124), (796, 58),
    (838, 168), (846, 96),
]
HUBS = {10, 15, 17}
LINK_RANGE = 96


def rect(x, y, w, h, fill, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" {extra}/>'


def pixel_text(word, ox, oy, px, fill):
    out = []
    x = ox
    for letter in word:
        for j, row in enumerate(FONT[letter]):
            for i, ch in enumerate(row):
                if ch == "#":
                    out.append(rect(x + i * px, oy + j * px, px, px, fill))
        x += 6 * px
    return out, x - ox - px


parts = []
parts.append(
    f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
    'role="img" aria-label="Socrate, building Walyverse">'
)
parts.append("""<style>
  .bl { animation: bl 1.2s steps(1) infinite; }
  @keyframes bl { 0%,49% { opacity:1 } 50%,100% { opacity:0 } }
  .pu { animation: pu 7s ease-in-out infinite; }
  @keyframes pu { 0%,100% { opacity:.2 } 50% { opacity:.6 } }
  .ha { animation: ha 5s ease-in-out infinite; }
  @keyframes ha { 0%,100% { opacity:.1 } 50% { opacity:.32 } }
</style>""")

parts.append(f'''<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{C['bg0']}"/><stop offset="1" stop-color="{C['bg1']}"/>
  </linearGradient>
  <linearGradient id="scrimx" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{C['bg0']}" stop-opacity=".97"/>
    <stop offset=".4" stop-color="{C['bg0']}" stop-opacity=".82"/>
    <stop offset=".72" stop-color="{C['bg0']}" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="scrimy" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{C['bg0']}" stop-opacity="0"/>
    <stop offset="1" stop-color="{C['bg0']}" stop-opacity=".95"/>
  </linearGradient>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="12"/></clipPath>
</defs>''')

parts.append('<g clip-path="url(#card)">')
parts.append(rect(0, 0, W, H, "url(#bg)"))

for gy in range(16, H, 28):
    for gx in range(16, W, 28):
        parts.append(rect(gx, gy, 2, 2, C["grid"], 'opacity=".05"'))

edges = []
for i, (x1, y1) in enumerate(NODES):
    for j, (x2, y2) in enumerate(NODES):
        if j > i and math.hypot(x1 - x2, y1 - y2) < LINK_RANGE:
            edges.append((i, j))
for k, (i, j) in enumerate(edges):
    x1, y1 = NODES[i]
    x2, y2 = NODES[j]
    parts.append(
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{C["link"]}" stroke-width="1.5" '
        f'class="pu" style="animation-delay:{(k % 8) * 0.6:.1f}s"/>'
    )
for i, (x, y) in enumerate(NODES):
    if i in HUBS:
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="15" fill="{C["halo"]}" class="ha" '
            f'style="animation-delay:{i * 0.5:.1f}s"/>'
        )
        parts.append(rect(x - 5, y - 5, 10, 10, C["gold"]))
    else:
        parts.append(rect(x - 4, y - 4, 8, 8, C["node"], 'opacity=".85"'))

parts.append(rect(0, 0, W, H, "url(#scrimx)"))
parts.append(rect(0, 184, W, H - 184, "url(#scrimy)"))
parts.append(rect(0, 0, W, 3, C["gold"], 'opacity=".9"'))

px = 11
title, tw = pixel_text("SOCRATE", 64, 84, px, C["text"])
parts.extend(title)
parts.append(rect(64 + tw + px * 2, 84 + 6 * px, px, px, C["gold"], 'class="bl"'))

parts.append(rect(64, 212, 148, 4, C["gold"]))
parts.append(
    f'<text x="64" y="256" font-family="{MONO}" font-size="16" font-weight="500" fill="{C["muted"]}">'
    f'building <tspan fill="{C["gold"]}">Walyverse</tspan>, a French Minecraft universe</text>'
)
parts.append(
    f'<text x="{W - 64}" y="256" text-anchor="end" font-family="{MONO}" font-size="14" fill="{C["faint"]}">'
    f'walyverse.fr</text>'
)

parts.append("</g>")
parts.append("</svg>")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(parts), encoding="utf-8")
print(f"OK -> {OUT}")
