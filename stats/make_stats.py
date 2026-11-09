"""Builds assets/stats.svg: a stats card in the same style as the banner.

Runs in GitHub Actions with GITHUB_TOKEN (no outside service needed).
Usage:  python stats/make_stats.py <username>
        python stats/make_stats.py --demo   (sample data, for previewing)
"""
import json
import os
import sys
import urllib.request
from collections import Counter
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "stats.svg"

QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, first: 100, isFork: false) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection { contributionCalendar { totalContributions } }
  }
}"""

# Notebooks are Python work; count them as Python so the bar reflects the language used.
MERGE = {"Jupyter Notebook": "Python"}
COLORS = {"Python": "#58e1ff"}


def fetch(login):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(f"GraphQL error: {data['errors']}")
    u = data["data"]["user"]
    langs, colors = Counter(), {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            name = MERGE.get(e["node"]["name"], e["node"]["name"])
            langs[name] += e["size"]
            colors.setdefault(name, e["node"]["color"] or "#8b949e")
    return {
        "repos": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "contributions": u["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "langs": langs, "colors": colors,
    }


def demo():
    return {"repos": 30, "stars": 4, "contributions": 148,
            "langs": Counter({"Python": 900, "Julia": 40, "HTML": 30, "Java": 25}),
            "colors": {"Julia": "#a270ba", "HTML": "#e34c26", "Java": "#b07219"}}


def render(d):
    W, H = 900, 200
    total = sum(d["langs"].values()) or 1
    top = [(n, v) for n, v in d["langs"].most_common(5) if v / total >= 0.01]
    stats = [("📦", "Public repos", d["repos"]),
             ("⚡", "Contributions (last year)", d["contributions"]),
             ("🧩", "Languages used", len(d["langs"]))]

    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <style>
    .t {{ font-family: 'Segoe UI', Helvetica, Arial, sans-serif; fill: #c9d1d9; }}
    .m {{ font-family: Consolas, 'Fira Code', Menlo, monospace; }}
    .n {{ font-size: 26px; font-weight: 700; }}
    .l {{ font-size: 14px; fill: #8b949e; }}
    .fade {{ opacity: 0; animation: in .6s ease forwards; }}
    @keyframes in {{ to {{ opacity: 1; }} }}
  </style>
  <defs>
    <linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#58e1ff"/><stop offset=".5" stop-color="#a78bfa"/><stop offset="1" stop-color="#f472b6"/></linearGradient>
    <clipPath id="bar"><rect x="470" y="70" width="400" height="12" rx="6"/></clipPath>
  </defs>
  <rect width="{W}" height="{H}" rx="14" fill="#0d1117" stroke="#30363d"/>
  <text x="30" y="38" class="t m" font-size="15"><tspan fill="#58e1ff">murali@ai-lab</tspan>:<tspan fill="#a78bfa">~</tspan>$ ./stats --github</text>
  <line x1="450" y1="60" x2="450" y2="175" stroke="#30363d"/>''']

    for i, (icon, label, value) in enumerate(stats):
        y = 82 + i * 40
        parts.append(f'''  <g class="fade" style="animation-delay:{0.2 + i * 0.25}s">
    <text x="30" y="{y}" font-size="20">{icon}</text>
    <text x="66" y="{y}" class="t n" fill="url(#g)">{value}</text>
    <text x="140" y="{y}" class="t l">{escape(label)}</text>
  </g>''')

    parts.append('  <text x="470" y="56" class="t l">Most used languages</text>')
    parts.append('  <g clip-path="url(#bar)"><rect x="470" y="70" width="400" height="12" fill="#161b22"/>')
    x = 470.0
    for name, size in top:
        w = 400 * size / total
        col = COLORS.get(name, d["colors"].get(name, "#8b949e"))
        parts.append(f'    <rect x="{x:.1f}" y="70" width="{w:.1f}" height="12" fill="{col}"/>')
        x += w
    parts.append('  </g>')

    for i, (name, size) in enumerate(top):
        col, row = i % 2, i // 2
        lx, ly = 470 + col * 200, 112 + row * 26
        c = COLORS.get(name, d["colors"].get(name, "#8b949e"))
        parts.append(f'''  <g class="fade" style="animation-delay:{0.9 + i * 0.15}s">
    <circle cx="{lx + 6}" cy="{ly - 5}" r="6" fill="{c}"/>
    <text x="{lx + 20}" y="{ly}" class="t" font-size="15">{escape(name)} <tspan fill="#8b949e">{100 * size / total:.1f}%</tspan></text>
  </g>''')

    parts.append("</svg>\n")
    return "\n".join(parts)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "MuraliKrishnaGR"
    OUT.write_text(render(demo() if arg == "--demo" else fetch(arg)), encoding="utf-8")
    print(f"wrote {OUT}")
