import json
import math
import os
import re
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

LOGIN = "wSocrate"
OUT = Path(__file__).resolve().parent.parent / "assets" / "profile.svg"

W, H = 880, 672
PAD = 56
INNER = W - PAD * 2

C = {
    "ink0": "#070b14",
    "ink1": "#0e1524",
    "panel": "#0b111d",
    "rule": "#1a2334",
    "rule_soft": "#141c2a",
    "fg": "#f4f7fb",
    "fg2": "#c9d5e4",
    "fg3": "#97a6bc",
    "fg4": "#5c6a80",
    "accent": "#f2c14e",
    "empty": "#161e2c",
    "ramp": ["#3d3018", "#7d5c1f", "#bb8d2c", "#f2c14e"],
}

MONO = "ui-monospace, 'Cascadia Code', 'SF Mono', Menlo, Consolas, monospace"

# geometric display face: normalised polylines, stroked with round caps and joins
GLYPHS = {
    "S": [[(1, 0), (0, 0), (0, .5), (1, .5), (1, 1), (0, 1)]],
    "O": [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]],
    "C": [[(1, 0), (0, 0), (0, 1), (1, 1)]],
    "R": [[(0, 1), (0, 0), (.94, 0), (.94, .5), (0, .5)], [(.44, .5), (1, 1)]],
    "A": [[(0, 1), (.5, 0), (1, 1)], [(.17, .66), (.83, .66)]],
    "T": [[(0, 0), (1, 0)], [(.5, 0), (.5, 1)]],
    "E": [[(1, 0), (0, 0), (0, 1), (1, 1)], [(0, .5), (.78, .5)]],
}
GW, GH, TRACK = 44.0, 62.0, 18.0
STROKE = 9.0

NODES = [
    (588, 96), (646, 62), (628, 152), (700, 108), (688, 196), (744, 66),
    (762, 148), (800, 100), (818, 198), (836, 58),
]
HUBS = {3, 7}
LINK_RANGE = 84

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

SECTIONS = [
    ("01", "GAMEPLAY", "plugins &amp; systems"),
    ("02", "NETWORK", "a fleet of servers"),
    ("03", "INFRASTRUCTURE", "Ferry, deployment"),
    ("04", "WEB", "dashboards &amp; store"),
]

RECENT = ("recent: contributionsCollection { contributionCalendar { weeks { "
          "contributionDays { date contributionCount weekday } } } }")


def gql(token, query):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        payload = json.load(r)
    if "errors" in payload:
        sys.exit(f"GraphQL: {payload['errors']}")
    return payload["data"]["user"]


def fetch():
    """GitHub only serves one year of contributions per call, so walk the years
    since the account was opened and add them up."""
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GH_TOKEN missing (or run with --demo)")

    created = gql(token, "query($login: String!) { user(login: $login) { createdAt } }")["createdAt"]
    since = int(created[:4])
    now = datetime.now(timezone.utc)
    years = list(range(since, now.year + 1))

    windows = []
    for y in years:
        frm = f"{y}-01-01T00:00:00Z"
        to = f"{y}-12-31T23:59:59Z" if y < now.year else now.strftime("%Y-%m-%dT%H:%M:%SZ")
        windows.append(
            f'y{y}: contributionsCollection(from: "{frm}", to: "{to}") {{ contributionCalendar {{ '
            f"totalContributions weeks {{ contributionDays {{ date contributionCount }} }} }} }}"
        )
    user = gql(token, "query($login: String!) { user(login: $login) { "
                      + RECENT + " " + " ".join(windows) + " } }")

    total = 0
    seen = {}
    for y in years:
        cal = user[f"y{y}"]["contributionCalendar"]
        total += cal["totalContributions"]
        for week in cal["weeks"]:
            for d in week["contributionDays"]:
                # weeks overlap the window edges, and clipped days come back as 0
                seen[d["date"]] = max(seen.get(d["date"], 0), d["contributionCount"])

    cur, best = streaks(seen)
    return {
        "weeks": user["recent"]["contributionCalendar"]["weeks"],
        "total": total, "cur": cur, "best": best, "since": since,
        "active": sum(1 for v in seen.values() if v > 0),
    }


def streaks(seen):
    """Longest and current run of consecutive days with at least one contribution."""
    if not seen:
        return 0, 0
    day = date.fromisoformat(min(seen))
    last = date.today()
    best = run = 0
    while day <= last:
        run = run + 1 if seen.get(day.isoformat(), 0) > 0 else 0
        best = max(best, run)
        day += timedelta(days=1)
    cur = 0
    day = last
    if seen.get(day.isoformat(), 0) == 0:
        day -= timedelta(days=1)
    while seen.get(day.isoformat(), 0) > 0:
        cur += 1
        day -= timedelta(days=1)
    return cur, best


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
    start = date.today().toordinal() - 370
    start -= date.fromordinal(start).isoweekday() % 7
    days = []
    for i in range(371):
        n = (i * 7919 + (i // 7) * 104729) % 19
        d = date.fromordinal(start + i)
        days.append({"date": d.isoformat(), "weekday": d.isoweekday() % 7,
                     "contributionCount": 0 if n < 7 else n - 6})
    seen = {d["date"]: d["contributionCount"] for d in days}
    cur, best = streaks(seen)
    return {
        "weeks": [{"contributionDays": days[i:i + 7]} for i in range(0, 371, 7)],
        "total": sum(seen.values()) * 5, "cur": cur, "best": best, "since": 2020,
        "active": sum(1 for v in seen.values() if v > 0),
    }


def num(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def rect(x, y, w, h, fill, extra=""):
    return f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" fill="{fill}" {extra}/>'


def cell(x, y, size, fill, extra=""):
    return rect(x, y, size, size, fill, f'rx="{num(size / 3.4)}" {extra}')


def text(x, y, size, fill, body, anchor="start", weight="500", track=None, extra=""):
    ls = f'letter-spacing="{track}" ' if track else ""
    return (f'<text x="{num(x)}" y="{num(y)}" font-family="{MONO}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {ls}{extra}>{body}</text>')


def wordmark(word, ox, oy, scale=1.0):
    out = []
    w, h, track = GW * scale, GH * scale, TRACK * scale
    inset = STROKE * scale / 2
    x = ox
    for letter in word:
        for poly in GLYPHS[letter]:
            pts = " ".join(
                f"{num(x + inset + px * (w - 2 * inset))},{num(oy + inset + py * (h - 2 * inset))}"
                for px, py in poly
            )
            out.append(
                f'<polyline points="{pts}" fill="none" stroke="{C["fg"]}" '
                f'stroke-width="{num(STROKE * scale)}" stroke-linecap="round" stroke-linejoin="round"/>'
            )
        x += w + track
    return out, x - ox - track


def level_of(count, quart):
    if count <= 0:
        return -1
    for i, q in enumerate(quart):
        if count <= q:
            return i
    return 3


def render(data, views=None, placeholder=False):
    weeks = data["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    total, cur, best, since = data["total"], data["cur"], data["best"], data["since"]
    counts = sorted(d["contributionCount"] for d in days if d["contributionCount"] > 0)
    quart = ([counts[min(len(counts) - 1, len(counts) * (i + 1) // 4)] for i in range(4)]
             if counts else [1, 2, 3, 4])

    p = []
    p.append(
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
        'role="img" aria-label="Socrate, building Walyverse">'
    )
    p.append("""<style>
  .tdy { animation: tdy 2.6s ease-in-out infinite; }
  @keyframes tdy { 0%,100% { opacity:.4 } 50% { opacity:1 } }
  .brt { animation: brt 9s ease-in-out infinite; }
  @keyframes brt { 0%,100% { opacity:.5 } 50% { opacity:.9 } }
</style>""")
    p.append(f'''<defs>
  <linearGradient id="ground" x1="0" y1="0" x2=".35" y2="1">
    <stop offset="0" stop-color="{C['ink0']}"/><stop offset="1" stop-color="{C['ink1']}"/>
  </linearGradient>
  <radialGradient id="glow" cx=".5" cy=".5" r=".5">
    <stop offset="0" stop-color="{C['accent']}" stop-opacity=".13"/>
    <stop offset=".55" stop-color="{C['accent']}" stop-opacity=".04"/>
    <stop offset="1" stop-color="{C['accent']}" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="cool" cx=".5" cy=".5" r=".5">
    <stop offset="0" stop-color="#3f7bb0" stop-opacity=".16"/>
    <stop offset="1" stop-color="#3f7bb0" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{C['fg4']}" stop-opacity=".15"/>
    <stop offset="1" stop-color="{C['fg4']}" stop-opacity="0"/>
  </linearGradient>
  <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="3"/></filter>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="14"/></clipPath>
</defs>''')
    p.append('<g clip-path="url(#card)">')
    p.append(rect(0, 0, W, H, "url(#ground)"))
    p.append(f'<ellipse cx="742" cy="118" rx="330" ry="240" fill="url(#glow)"/>')
    p.append(f'<ellipse cx="180" cy="300" rx="300" ry="220" fill="url(#cool)"/>')

    # column guides: the grid the layout is built on, barely there
    for i in range(1, 12):
        gx = PAD + i * (INNER / 12)
        p.append(rect(gx, 56, 1, 250, "url(#fade)"))

    edges = [(i, j) for i, a in enumerate(NODES) for j, b in enumerate(NODES)
             if j > i and math.hypot(a[0] - b[0], a[1] - b[1]) < LINK_RANGE]
    net = []
    for i, j in edges:
        x1, y1 = NODES[i]
        x2, y2 = NODES[j]
        net.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{C["fg4"]}" '
                   f'stroke-width="1" opacity=".5"/>')
    for i, (x, y) in enumerate(NODES):
        if i in HUBS:
            net.append(f'<circle cx="{x}" cy="{y}" r="13" fill="{C["accent"]}" opacity=".08"/>')
            net.append(cell(x - 4, y - 4, 8, C["accent"], 'opacity=".85"'))
        else:
            net.append(cell(x - 3, y - 3, 6, C["fg3"], 'opacity=".55"'))
    p.append(f'<g opacity=".8">{"".join(net)}</g>')

    # ---- top rail
    p.append(cell(PAD, 27, 9, C["accent"]))
    p.append(text(PAD + 22, 35, 11, C["fg"], "SOCRATE", weight="600", track=".24em"))
    p.append(text(W - PAD, 35, 10, C["fg4"], "FRANCE", anchor="end", track=".24em"))
    p.append(rect(PAD, 56, INNER, 1, C["rule"]))

    # ---- hero
    p.append(text(PAD, 122, 10, C["accent"], "SOLO DEVELOPER", weight="600", track=".3em"))
    mark, mw = wordmark("SOCRATE", PAD, 146)
    p.extend(mark)
    p.append(cell(PAD + mw + 20, 146 + GH - 11, 11, C["accent"], 'class="brt"'))
    p.append(text(PAD, 254, 17, C["fg2"], "Building Walyverse, a French Minecraft universe."))
    p.append(rect(PAD, 282, 56, 2, C["accent"]))

    # ---- data panel
    py0, py1 = 318, 516
    p.append(rect(PAD, py0, INNER, py1 - py0, C["panel"],
                  f'rx="12" stroke="{C["rule"]}" stroke-width="1"'))
    px0 = PAD + 26
    pw = INNER - 52
    p.append(text(px0, py0 + 34, 10, C["fg4"],
                  "ALL TIME" if placeholder else f"SINCE {since}", weight="600", track=".22em"))
    if placeholder:
        meta = '<tspan fill="#5c6a80">AWAITING FIRST SYNC</tspan>'
    else:
        sep = f'<tspan fill="{C["rule"]}"> / </tspan>'
        gold = f'<tspan fill="{C["accent"]}" font-weight="700">'
        meta = (f'{gold}{total:,}</tspan> CONTRIBUTIONS{sep}'
                f'{gold}{data["active"]:,}</tspan> ACTIVE DAYS{sep}'
                f'{gold}{cur}</tspan> DAY STREAK, BEST {best}')
        if views:
            meta += f'{sep}{gold}{views:,}</tspan> VIEWS'
    p.append(text(PAD + INNER - 26, py0 + 34, 9.5, C["fg3"], meta, anchor="end", track=".11em"))

    step = pw / len(weeks)
    size = step - 3.2
    gtop = py0 + 64
    today = days[-1]["date"] if days else None
    for wi, week in enumerate(weeks):
        x = px0 + wi * step
        for d in week["contributionDays"]:
            y = gtop + d.get("weekday", 0) * step
            lv = -1 if placeholder else level_of(d["contributionCount"], quart)
            p.append(cell(x, y, size, C["empty"] if lv < 0 else C["ramp"][lv]))
            if d["date"] == today and not placeholder:
                p.append(cell(x, y, size, "none",
                              f'stroke="{C["accent"]}" stroke-width="1.6" class="tdy"'))

    ticks = []
    for wi, week in enumerate(weeks):
        month = int(week["contributionDays"][0]["date"][5:7])
        if not ticks or (month != ticks[-1][1] and wi - ticks[-1][0] >= 4):
            ticks.append((wi, month))
    for wi, month in ticks[1:]:
        p.append(text(px0 + wi * step, gtop - 10, 9, C["fg4"], MONTHS[month - 1], track=".16em"))

    leg_y = gtop + 7 * step + 22
    lx = PAD + INNER - 26
    p.append(text(lx, leg_y, 9, C["fg4"], "MORE", anchor="end", track=".16em"))
    for i in range(4):
        p.append(cell(lx - 42 - (3 - i) * 13, leg_y - 8, 9, C["ramp"][i]))
    p.append(cell(lx - 42 - 4 * 13, leg_y - 8, 9, C["empty"]))
    p.append(text(lx - 42 - 4 * 13 - 9, leg_y, 9, C["fg4"], "LESS", anchor="end", track=".16em"))
    p.append(text(px0, leg_y, 9, C["fg4"], "THE LAST YEAR, DAY BY DAY", track=".16em"))

    # ---- numbered sections
    col = INNER / 4
    for i, (n_, name, desc) in enumerate(SECTIONS):
        x = PAD + i * col
        if i:
            p.append(rect(x - 16, 548, 1, 62, C["rule_soft"]))
        p.append(text(x, 568, 10, C["accent"], n_, weight="700", track=".2em"))
        p.append(text(x + 30, 568, 11.5, C["fg"], name, weight="600", track=".14em"))
        p.append(text(x, 592, 11, C["fg4"], desc))

    # ---- footer
    p.append(rect(PAD, 626, INNER, 1, C["rule"]))
    p.append(text(PAD, 654, 12, C["accent"], "WALYVERSE.COM", weight="600", track=".2em"))
    p.append(text(W - PAD, 654, 11, C["fg4"], "X.COM/SEIIIKI_   ·   DISCORD @SEIIKI_",
                  anchor="end", track=".16em"))

    p.append(rect(0, 0, W, H, "#ffffff",
                  'filter="url(#grain)" opacity=".05" style="mix-blend-mode:soft-light"'))
    p.append("</g>")
    p.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="14" fill="none" stroke="{C["rule"]}"/>')
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
