import json
import math
import os
import re
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

LOGIN = "wSocrate"
OUT = Path(__file__).resolve().parent.parent / "assets" / "card.svg"

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
    ("01", "CONTROL PLANE", "fleet scheduling, deploys"),
    ("02", "IDENTITY &amp; STATE", "one record, fleet wide"),
    ("03", "TRANSACTIONAL CORE", "ledger, market, payments"),
    ("04", "RUNTIME", "menus, locale, chat"),
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


# brand marks, drawn on a 24-unit box
X_MARK = ("M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835"
          "L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z")
DISCORD_MARK = (
    "M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447."
    "8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077."
    "077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-."
    "319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a."
    "0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.652"
    "8-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a"
    ".0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202"
    ".099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 0"
    "0-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5"
    "219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 "
    "00-.0312-.0286zM8.02 15.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189 2.157-2"
    ".4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.9555 2.4189-2.1569 2.4189zm7.9748 0c-1.182"
    "5 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2.156"
    "8 2.419 0 1.3332-.946 2.4189-2.1568 2.4189Z")


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


def mark(path, x, top, size, fill, opacity="1"):
    return (f'<g transform="translate({num(x)},{num(top)}) scale({num(size / 24)})" '
            f'fill="{fill}" opacity="{opacity}"><path d="{path}"/></g>')


def handles(right, baseline, items, size=11.5, icon=14, pad=8, gap=28):
    """Lay a row of brand mark + handle pairs out flush to the right edge."""
    widths = [len(h) * size * 0.6 for _, h in items]
    total = sum(widths) + len(items) * (icon + pad) + gap * (len(items) - 1)
    x = right - total
    out = []
    for (path, handle), w in zip(items, widths):
        out.append(mark(path, x, baseline - 11, icon, C["accent"], ".9"))
        out.append(text(x + icon + pad, baseline, size, C["fg3"], handle))
        x += icon + pad + w + gap
    return out


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
  .pu { animation: pu 7s ease-in-out infinite; }
  @keyframes pu { 0%,100% { opacity:.22 } 50% { opacity:.62 } }
  .ha { animation: ha 5.5s ease-in-out infinite; }
  @keyframes ha { 0%,100% { opacity:.05 } 50% { opacity:.2 } }
  .tw { animation: tw 4.2s ease-in-out infinite; }
  @keyframes tw { 0%,100% { opacity:.4 } 50% { opacity:.85 } }
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
    for k, (i, j) in enumerate(edges):
        x1, y1 = NODES[i]
        x2, y2 = NODES[j]
        net.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{C["fg4"]}" '
                   f'stroke-width="1" opacity=".4" class="pu" style="animation-delay:{(k % 5) * 0.8:.1f}s"/>')
    for i, (x, y) in enumerate(NODES):
        if i in HUBS:
            net.append(f'<circle cx="{x}" cy="{y}" r="13" fill="{C["accent"]}" opacity=".12" class="ha" '
                       f'style="animation-delay:{i * 0.7:.1f}s"/>')
            net.append(cell(x - 4, y - 4, 8, C["accent"], 'opacity=".85"'))
        else:
            net.append(cell(x - 3, y - 3, 6, C["fg3"],
                            f'opacity=".6" class="tw" style="animation-delay:{i * 0.55:.1f}s"'))
    p.append(f'<g opacity=".8">{"".join(net)}</g>')

    # ---- top rail
    p.append(cell(PAD, 27, 9, C["accent"]))
    p.append(text(PAD + 22, 35, 11, C["fg"], "SOCRATE", weight="600", track=".24em"))
    p.append(text(W - PAD, 35, 10, C["fg4"], "7+ YEARS LIVE · 50K+ PLAYERS",
                  anchor="end", track=".22em"))
    p.append(rect(PAD, 56, INNER, 1, C["rule"]))

    # ---- hero
    p.append(text(PAD, 122, 10, C["accent"], "FOUNDER, WALYVERSE", weight="600", track=".3em"))
    mark, mw = wordmark("SOCRATE", PAD, 146)
    p.extend(mark)
    p.append(cell(PAD + mw + 20, 146 + GH - 11, 11, C["accent"], 'class="brt"'))
    p.append(text(PAD, 254, 16.5, C["fg2"],
                  "Building the worlds people log into, and the platform they run on."))
    p.append(rect(PAD, 282, 56, 2, C["accent"]))

    # ---- data panel
    py0, py1 = 318, 516
    p.append(rect(PAD, py0, INNER, py1 - py0, C["panel"],
                  f'rx="12" stroke="{C["rule"]}" stroke-width="1"'))
    px0 = PAD + 26
    pw = INNER - 52
    p.append(text(px0, py0 + 34, 10, C["fg4"],
                  "ALL TIME" if placeholder else f"ON GITHUB SINCE {since}", weight="600", track=".22em"))
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

    # ---- numbered sections, on the same column span as the calendar above
    col = pw / 4
    for i, (n_, name, desc) in enumerate(SECTIONS):
        x = px0 + i * col
        if i:
            p.append(rect(x - 18, 536, 1, 74, C["rule_soft"]))
        p.append(text(x, 556, 10, C["accent"], n_, weight="700", track=".22em"))
        p.append(text(x, 578, 11.5, C["fg"], name, weight="600", track=".12em"))
        p.append(text(x, 600, 11, C["fg4"], desc))

    # ---- footer
    p.append(rect(PAD, 626, INNER, 1, C["rule"]))
    p.append(text(PAD, 654, 12, C["accent"], "WALYVERSE.COM", weight="600", track=".2em"))
    p.extend(handles(W - PAD, 654, [(X_MARK, "@Seiiiki_"), (DISCORD_MARK, "@seiiki_")]))

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
