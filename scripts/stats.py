"""Gera dist/stats.svg com os números do perfil, no mesmo estilo dos outros cards.

Roda no GitHub Actions (workflow "perfil"). Usa o GITHUB_TOKEN do próprio workflow.
Para testar sem internet: STATS_FAKE=1 python scripts/stats.py
"""
import json, os, urllib.request
from datetime import datetime, timezone, timedelta
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

BG, D, M, G = "#000000", "#0E260F", "#217C3E", "#2AA344"
W, H = 900, 170
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = {
    "disp": TTFont(os.path.join(ROOT, "fonts/chakra-petch-latin-700-normal.woff")),
    "mono": TTFont(os.path.join(ROOT, "fonts/jetbrains-mono-latin-500-normal.woff")),
}

def text_w(s, font, size, track=0):
    f = FONTS[font]; cmap = f.getBestCmap(); upm = f["head"].unitsPerEm
    return sum(f["hmtx"][cmap[ord(c)]][0] for c in s) * size / upm + track * max(len(s) - 1, 0)

def text(s, x, y, font, size, fill, track=0):
    f = FONTS[font]; cmap = f.getBestCmap(); gs = f.getGlyphSet(); sc = size / f["head"].unitsPerEm
    pen = SVGPathPen(gs); cx = x
    for c in s:
        g = cmap[ord(c)]
        gs[g].draw(TransformPen(pen, (sc, 0, 0, -sc, cx, y)))
        cx += gs[g].width * sc + track
    return f'<path fill="{fill}" d="{pen.getCommands()}"/>'

def fetch(login):
    if os.environ.get("STATS_FAKE"):
        return {"contrib": 412, "repos": 60, "stars": 8, "followers": 3}
    q = """query($login:String!){user(login:$login){
      followers{totalCount}
      repositories(ownerAffiliations:OWNER,privacy:PUBLIC,first:100){totalCount nodes{stargazerCount}}
      contributionsCollection{contributionCalendar{totalContributions}}}}"""
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"})
    u = json.load(urllib.request.urlopen(req))["data"]["user"]
    return {"contrib": u["contributionsCollection"]["contributionCalendar"]["totalContributions"],
            "repos": u["repositories"]["totalCount"],
            "stars": sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
            "followers": u["followers"]["totalCount"]}

def fmt(n):
    return f"{n:,}".replace(",", ".")

def main():
    login = os.environ.get("GITHUB_USER", "ldb2010chefinho")
    s = fetch(login)
    c = 22
    plate = f"1,1 {W-1-c},1 {W-1},{1+c} {W-1},{H-1} {1+c},{H-1} 1,{H-1-c}"
    b = [f'<polygon fill="{BG}" stroke="{D}" stroke-width="2" points="{plate}"/>']
    items = [("CONTRIBUIÇÕES", "no último ano", s["contrib"]), ("REPOSITÓRIOS", "públicos", s["repos"]),
             ("ESTRELAS", "recebidas", s["stars"]), ("SEGUIDORES", "no GitHub", s["followers"])]
    cw = (W - 72) / 4
    for i, (label, sub, n) in enumerate(items):
        x = 36 + i * cw
        if i:
            b.append(f'<line x1="{x-18}" y1="34" x2="{x-18}" y2="{H-34}" stroke="{D}" stroke-width="2"/>')
        b.append(text(label, x, 50, "mono", 12, M, track=2))
        b.append(f'<rect x="{x}" y="60" width="28" height="3" fill="{G}"/>')
        b.append(text(fmt(n), x, 118, "disp", 48, G))
        b.append(text(sub, x, 142, "mono", 12, M))
    hoje = datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y")
    upd = f"atualizado em {hoje}"
    b.append(text(upd, W - 36 - text_w(upd, "mono", 10), H - 12, "mono", 10, M))
    title = (f"{fmt(s['contrib'])} contribuições no último ano, {s['repos']} repositórios públicos, "
             f"{s['stars']} estrelas, {s['followers']} seguidores")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'role="img" aria-label="{title}"><title>{title}</title>{"".join(b)}</svg>')
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    open(os.path.join(ROOT, "dist/stats.svg"), "w").write(svg)
    print(title)

if __name__ == "__main__":
    main()
