# Generates assets/stats.svg, the hand-drawn stats card, refreshed nightly by the Action.
# Usage: GH_TOKEN=xxx py scripts/render_stats.py [--demo]
#   --demo: render the card with fake data (to test the layout without a token)

import json
import os
import sys
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

LOGIN = "wSocrate"
OUT = Path(__file__).resolve().parent.parent / "assets" / "stats.svg"

W, H = 880, 260

C = {
    "bg0": "#0d1b2a",
    "bg1": "#0f2438",
    "border": "#24435c",
    "text": "#f2ede3",
    "muted": "#8ea8ba",
    "accent": "#ff8f6b",
    "empty": "#142c3d",
    "levels": ["#0f5257", "#0e7c6b", "#16b89a", "#7ce3c3"],
}

QUERY = """
query($login: String!) {
  user(login: $login) {
    repositoriesContributedTo(
      includeUserRepositories: true
      contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]
      first: 1
    ) { totalCount }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
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


def demo_data():
    # about a year of fake contributions, deterministic pattern
    days = []
    d = date.today().toordinal() - 364
    for i in range(365):
        n = (i * 7919 + (i // 7) * 104729) % 17
        count = 0 if n < 6 else n - 5
        days.append({"date": date.fromordinal(d + i).isoformat(), "contributionCount": count})
    weeks = [{"contributionDays": days[i:i + 7]} for i in range(0, 365, 7)]
    total = sum(x["contributionCount"] for x in days)
    return {
        "repositoriesContributedTo": {"totalCount": 12},
        "contributionsCollection": {
            "totalCommitContributions": total - 40,
            "restrictedContributionsCount": 0,
            "contributionCalendar": {"totalContributions": total, "weeks": weeks},
        },
    }


def streaks(days):
    cur = best = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        best = max(best, run)
    # current streak: walk back from the end (today may still be empty)
    tail = list(reversed(days))
    if tail and tail[0]["contributionCount"] == 0:
        tail = tail[1:]
    for d in tail:
        if d["contributionCount"] > 0:
            cur += 1
        else:
            break
    return cur, best


def level(count, quartiles):
    if count == 0:
        return None
    for i, q in enumerate(quartiles):
        if count <= q:
            return C["levels"][i]
    return C["levels"][-1]


def render(user):
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    total = cal["totalContributions"]
    repos = user["repositoriesContributedTo"]["totalCount"]
    cur, best = streaks(days)

    counts = sorted(c["contributionCount"] for c in days if c["contributionCount"] > 0)
    if counts:
        quart = [counts[min(len(counts) - 1, len(counts) * (i + 1) // 4)] for i in range(4)]
    else:
        quart = [1, 2, 3, 4]

    p = []
    p.append(f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GitHub stats for {LOGIN}">')
    p.append(f"""<style>
      .num {{ font: 700 30px ui-monospace, 'Cascadia Code', Consolas, monospace; }}
      .lbl {{ font: 500 12px ui-monospace, 'Cascadia Code', Consolas, monospace; }}
      .ft  {{ font: 500 11px ui-monospace, 'Cascadia Code', Consolas, monospace; }}
      .cell {{ animation: pop .5s ease-out backwards; }}
      @keyframes pop {{ from {{ opacity: 0 }} to {{ opacity: 1 }} }}
    </style>""")
    p.append(f'''<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{C['bg0']}"/><stop offset="1" stop-color="{C['bg1']}"/>
    </linearGradient></defs>''')
    p.append(f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>')
    p.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{C["border"]}"/>')

    stats = [
        (f"{total:,}", "contributions this year"),
        (str(cur), "current daily streak"),
        (str(best), "best daily streak"),
        (str(repos), "repos contributed to"),
    ]
    for i, (num, lbl) in enumerate(stats):
        x = 64 + i * 195
        p.append(f'<text x="{x}" y="62" class="num" fill="{C["text"]}">{num}</text>')
        p.append(f'<text x="{x}" y="84" class="lbl" fill="{C["muted"]}">{lbl}</text>')

    # heatmap
    hx, hy = 64, 112
    cell, gap = 11, 3
    for wi, w in enumerate(weeks):
        for di, d in enumerate(w["contributionDays"]):
            fill = level(d["contributionCount"], quart) or C["empty"]
            delay = wi * 0.012
            p.append(
                f'<rect x="{hx + wi * (cell + gap)}" y="{hy + di * (cell + gap)}" '
                f'width="{cell}" height="{cell}" rx="2.5" fill="{fill}" '
                f'class="cell" style="animation-delay:{delay:.3f}s"/>'
            )

    stamp = datetime.now(timezone.utc).strftime("%b %d, %Y")
    p.append(f'<text x="{W-64}" y="{H-20}" text-anchor="end" class="ft" fill="{C["muted"]}">refreshed {stamp} by scripts/render_stats.py</text>')
    p.append(f'<rect x="64" y="{H-30}" width="8" height="8" rx="2" fill="{C["accent"]}"/>')
    p.append(f'<text x="78" y="{H-22}" class="ft" fill="{C["muted"]}">one year of contributions</text>')
    p.append("</svg>")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(p), encoding="utf-8")
    print(f"OK -> {OUT}")


if __name__ == "__main__":
    render(demo_data() if "--demo" in sys.argv else fetch())
