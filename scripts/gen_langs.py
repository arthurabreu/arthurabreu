#!/usr/bin/env python3
"""Gera assets/top-langs.svg somando linguagens de todos os repos (publicos e privados, sem forks)."""
import json, os, subprocess, urllib.request

OWNERS = {"arthurabreu", "AbreuApps"}
TOKEN =os.environ.get("GH_TOKEN") or subprocess.check_output(["gh", "auth", "token"], text=True).strip()
Q = """query($after:String){viewer{repositories(first:100,after:$after,
ownerAffiliations:[OWNER,COLLABORATOR,ORGANIZATION_MEMBER],isFork:false){
pageInfo{hasNextPage endCursor}
nodes{owner{login} languages(first:20,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}}}"""


def gql(after):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": Q, "variables": {"after": after}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}"},
    )
    return json.load(urllib.request.urlopen(req))["data"]["viewer"]["repositories"]


langs, after = {}, None
while True:
    page = gql(after)
    for repo in page["nodes"]:
        if repo["owner"]["login"] not in OWNERS:
            continue
        for e in repo["languages"]["edges"]:
            n = e["node"]["name"]
            s, c = langs.get(n, (0, e["node"]["color"] or "#888888"))
            langs[n] = (s + e["size"], c)
    if not page["pageInfo"]["hasNextPage"]:
        break
    after = page["pageInfo"]["endCursor"]

total = sum(s for s, _ in langs.values())
rows = sorted(langs.items(), key=lambda kv: -kv[1][0])
H = 70 + 26 * len(rows)
FONT = "Segoe UI,Ubuntu,sans-serif"
out = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="{H}" viewBox="0 0 420 {H}">',
    f'<rect width="420" height="{H}" rx="6" fill="#0d1117" stroke="#30363d"/>',
    f'<text x="20" y="32" font-family="{FONT}" font-size="18" font-weight="600" fill="#4285F4">Top Languages</text>',
]
x = 20
for n, (s, c) in rows:
    w = 380 * s / total
    out.append(f'<rect x="{x:.1f}" y="44" width="{w:.1f}" height="8" fill="{c}"/>')
    x += w
for i, (n, (s, c)) in enumerate(rows):
    y = 78 + 26 * i
    out.append(f'<circle cx="26" cy="{y - 4}" r="5" fill="{c}"/>')
    out.append(f'<text x="40" y="{y}" font-family="{FONT}" font-size="13" fill="#99ccff">{n} — {100 * s / total:.1f}%</text>')
out.append("</svg>")
os.makedirs("assets", exist_ok=True)
open("assets/top-langs.svg", "w").write("\n".join(out))
print({n: f"{100 * s / total:.1f}%" for n, (s, _) in rows})
