import json
import math
import os
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

LOGIN = "wSocrate"
OUT = Path(__file__).resolve().parent.parent / "assets" / "profile.svg"

W, H = 880, 600
PAD = 56
INNER = W - PAD * 2

C = {
    "bg0": "#0b1018",
    "bg1": "#141d2a",
    "grid": "#ffffff",
    "rule": "#1e2733",
    "link": "#3f7ba8",
    "node": "#9fd8cd",
    "halo": "#58c2b0",
    "text": "#f4f6fa",
    "muted": "#aeb9c9",
    "faint": "#6b7684",
    "gold": "#f2c14e",
    "empty": "#18202c",
    "levels": ["#12525a", "#12796c", "#17b89a", "#7ce3c3"],
}

MONO = "ui-monospace, 'Cascadia Code', 'SF Mono', Consolas, monospace"

FONT = {
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
}

NODES = [
    (128, 52), (196, 118), (150, 176), (268, 74), (316, 146), (352, 50),
    (404, 108), (438, 172), (486, 62), (520, 108), (566, 94), (588, 166),
    (624, 42), (652, 122), (712, 80), (724, 160), (782, 114), (796, 48),
    (838, 158), (846, 86),
]
HUBS = {10, 15, 17}
LINK_RANGE = 96

LINES = [
    ("The gameplay", "the plugins and systems players actually play with"),
    ("The network", "a whole fleet of servers, kept in sync and live for real players"),
    ("The infrastructure", "Ferry, my own deployment platform"),
    ("The web", "the dashboards, the site, the store"),
]

QUERY = """
query($login: String!) {
  user(login: $login) {
    repositoriesContributedTo(
      includeUserRepositories: true
      contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]
      first: 1
    ) { totalCount }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GH_TOKEN missing (or run with --demo)")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        payload = json.load(r)
    if "errors" in payload:
        sys.exit(f"GraphQL: {payload['errors']}")
    return payload["data"]["user"]


def profile_views():
    try:
        req = urllib.request.Request(
            f"https://komarev.com/ghpvc/?username={LOGIN}",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            svg = r.read().decode()
        nums = re.findall(r">([\d,]+)<", svg)
        return int(nums[-1].replace(",", "")) if nums else None
    except OSError:
        return None


def demo_data():
    days = []
    start = date.today().toordinal() - 364
    for i in range(365):
        n = (i * 7919 + (i // 7) * 104729) % 17
        days.append({"date": date.fromordinal(start + i).isoformat(),
                     "contributionCount": 0 if n < 6 else n - 5})
    weeks = [{"contributionDays": days[i:i + 7]} for i in range(0, 365, 7)]
    return {
        "repositoriesContributedTo": {"totalCount": 27},
        "contributionsCollection": {
            "contributionCalendar": {
                "totalContributions": sum(d["contributionCount"] for d in days),
                "weeks": weeks,
            }
        },
    }


def streaks(days):
    best = run = cur = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        best = max(best, run)
    tail = list(reversed(days))
    if tail and tail[0]["contributionCount"] == 0:
        tail = tail[1:]
    for d in tail:
        if d["contributionCount"] > 0:
            cur += 1
        else:
            break
    return cur, best


def rect(x, y, w, h, fill, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" {extra}/>'


def label(x, y, size, fill, body, anchor="start", weight="500", extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" {extra}>{body}</text>')


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


def render(user, views=None, placeholder=False):
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    cur, best = streaks(days)

    p = []
    p.append(
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
        'role="img" aria-label="Socrate, building Walyverse">'
    )
    p.append("""<style>
  .bl { animation: bl 1.2s steps(1) infinite; }
  @keyframes bl { 0%,49% { opacity:1 } 50%,100% { opacity:0 } }
  .pu { animation: pu 7s ease-in-out infinite; }
  @keyframes pu { 0%,100% { opacity:.2 } 50% { opacity:.6 } }
  .ha { animation: ha 5s ease-in-out infinite; }
  @keyframes ha { 0%,100% { opacity:.1 } 50% { opacity:.32 } }
</style>""")
    p.append(f'''<defs>
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
    <stop offset="1" stop-color="{C['bg0']}" stop-opacity=".96"/>
  </linearGradient>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="12"/></clipPath>
</defs>''')
    p.append('<g clip-path="url(#card)">')
    p.append(rect(0, 0, W, H, "url(#bg)"))

    for gy in range(16, H, 28):
        for gx in range(16, W, 28):
            p.append(rect(gx, gy, 2, 2, C["grid"], 'opacity=".05"'))

    edges = [(i, j) for i, a in enumerate(NODES) for j, b in enumerate(NODES)
             if j > i and math.hypot(a[0] - b[0], a[1] - b[1]) < LINK_RANGE]
    for k, (i, j) in enumerate(edges):
        x1, y1 = NODES[i]
        x2, y2 = NODES[j]
        p.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{C["link"]}" '
                 f'stroke-width="1.5" class="pu" style="animation-delay:{(k % 8) * 0.6:.1f}s"/>')
    for i, (x, y) in enumerate(NODES):
        if i in HUBS:
            p.append(f'<circle cx="{x}" cy="{y}" r="15" fill="{C["halo"]}" class="ha" '
                     f'style="animation-delay:{i * 0.5:.1f}s"/>')
            p.append(rect(x - 5, y - 5, 10, 10, C["gold"]))
        else:
            p.append(rect(x - 4, y - 4, 8, 8, C["node"], 'opacity=".85"'))

    p.append(rect(0, 0, W, 200, "url(#scrimx)"))
    p.append(rect(0, 150, W, 90, "url(#scrimy)"))
    p.append(rect(0, 200, W, H - 200, C["bg0"], 'opacity=".96"'))
    p.append(rect(0, 0, W, 3, C["gold"], 'opacity=".9"'))

    px = 10
    title, tw = pixel_text("SOCRATE", PAD, 52, px, C["text"])
    p.extend(title)
    p.append(rect(PAD + tw + px * 2, 52 + 6 * px, px, px, C["gold"], 'class="bl"'))

    p.append(rect(PAD, 148, 130, 4, C["gold"]))
    p.append(label(PAD, 186, 16, C["muted"],
                   f'building <tspan fill="{C["gold"]}">Walyverse</tspan>, '
                   f'a French Minecraft universe'))

    p.append(rect(PAD, 216, INNER, 1, C["rule"]))

    y = 252
    for name, body in LINES:
        p.append(label(PAD, y, 14, C["text"], name, weight="600"))
        p.append(label(PAD + 176, y, 14, C["muted"], body))
        y += 34

    p.append(rect(PAD, 384, INNER, 1, C["rule"]))

    stats = [
        (f'{cal["totalContributions"]:,}', "contributions this year"),
        (str(cur), "current streak"),
        (str(best), "best streak"),
        (str(user["repositoriesContributedTo"]["totalCount"]), "repos contributed to"),
        (f"{views:,}" if views else "—", "profile views"),
    ]
    if placeholder:
        stats = [("—", name) for _, name in stats]
    for i, (num, name) in enumerate(stats):
        x = PAD + i * (INNER // 5)
        p.append(label(x, 430, 26, C["text"], num, weight="700"))
        p.append(label(x, 450, 10, C["faint"], name))

    window = 16
    weekly = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks][-window:]
    if placeholder:
        weekly = [0] * window
    top = max(weekly) if any(weekly) else 1
    nonzero = sorted(v for v in weekly if v > 0)
    quart = ([nonzero[min(len(nonzero) - 1, len(nonzero) * (i + 1) // 4)] for i in range(4)]
             if nonzero else [1, 2, 3, 4])
    peak = max(range(len(weekly)), key=lambda i: (weekly[i], i)) if any(weekly) else -1

    base, gap = 552, 6
    n = len(weekly)
    bw = (INNER - (n - 1) * gap) // n
    for i, v in enumerate(weekly):
        if v == 0:
            bh, fill = 3, C["empty"]
        elif i == peak:
            bh, fill = 78, C["gold"]
        else:
            bh = max(6, round(math.sqrt(v / top) * 78))
            fill = C["levels"][min(3, next(k for k, q in enumerate(quart) if v <= q))]
        p.append(rect(PAD + i * (bw + gap), base - bh, bw, bh, fill,
                      'rx="3"'))
    p.append(rect(PAD, base + 4, INNER, 1, C["rule"]))

    p.append(label(PAD, 578, 13, C["gold"], "walyverse.com", extra='opacity=".9"'))
    p.append(label(W - PAD, 578, 12, C["faint"], "x.com/Seiiiki_ · discord @seiiki_", anchor="end"))

    p.append("</g>")
    p.append("</svg>")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(p), encoding="utf-8")
    print(f"OK -> {OUT}")


if __name__ == "__main__":
    if "--placeholder" in sys.argv:
        render(demo_data(), placeholder=True)
    elif "--demo" in sys.argv:
        render(demo_data(), views=1024)
    else:
        render(fetch(), views=profile_views())
