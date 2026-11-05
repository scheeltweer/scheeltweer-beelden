#!/usr/bin/env python3
"""Maakt de beelden van een post uit posts/<map>/post.json.
Gebruik: python3 tools/render.py posts/<map>"""
import json, subprocess, sys, html, pathlib, tempfile
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import figuren as F

FPS = 30
ENC = ["-c:v", "libx264", "-crf", "19", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", str(FPS)]
e = html.escape
DEFS = '<svg width="0" height="0" style="position:absolute"><filter id="hand" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency=".022" numOctaves="2" seed="7" result="r"/><feDisplacementMap in="SourceGraphic" in2="r" scale="6"/></filter></svg>'
MERK = f'<div class="merk">{F.huisje(52)}Scheelt Weer</div>'
FIG = {"tijdschrift": F.tijdschrift, "telefoon": F.telefoon, "tv": F.tv, "potlood": F.potlood, "kalender": F.kalender, "polis": F.polis, "pleister": F.pleister, "kinderen": F.kinderen, "kopje": F.kopje, "envelop": F.envelop, "modem": F.modem_slaapt}

def bron(s):
    return f'<div class="bron">{e(s["bron"])}</div>' if s.get("bron") else ""

def wie(s):
    if s.get("wie_bron"):
        return f'<div class="wie"><span>{e(s["wie_bron"])}</span></div>'
    return f'<div class="wie">{F.gezin()}<span>{e(s["wie"])}</span></div>' if s.get("wie") else ""

def slide(s):
    t = s["sjabloon"]
    if t == "straat":
        kl = [F.K["framboos"]] * s["geteld"] + [F.K["boter"]] * (s["totaal"] - s["geteld"])
        rm = [F.K["boter"]] * s["geteld"] + [F.K["klei"]] * (s["totaal"] - s["geteld"])
        g = "<br>".join(e(x) for x in s["groot"])
        maat = f' style="font-size:{s["groot_maat"]}px;top:176px;white-space:nowrap"' if s.get("groot_maat") else ""
        tk = ' style="top:610px"' if s.get("groot_maat") else ""
        br = bron(s).replace('class="bron"', 'class="bron" style="top:820px"') if s.get("groot_maat") else bron(s)
        return f'<section class="vel c t-straat">{MERK}<div class="titel groot"{maat}>{g}</div><div class="tekst"{tk}>{e(s["tekst"])}</div>{br}{F.straat(1080, 340, kl, rm)}</section>'
    if t == "lijst":
        it = "".join(f'<div class="item">{FIG[i["figuur"]]()}<div class="naam">{e(i["naam"])}</div>{F.prijskaartje(e(i["prijs"]))}</div>' for i in s["items"])
        l, r = s["som"]
        return f'<section class="vel c t-lijst"><div class="titel kop">{e(s["kop"])}</div><div class="lijst">{it}</div><div class="lijn"></div><div class="som"><span class="l">{e(l)}</span><span class="r"{(' style="font-size:%dpx"' % s["som_maat"]) if s.get("som_maat") else ""}>{e(r)}</span></div>{wie(s)}</section>'
    if t == "munten":
        k = s["kolommen"]
        return (f'<section class="vel c t-munten"><div class="titel kop">{e(s["kop"])}</div><div class="sub">{e(s["sub"])}</div>'
                f'<div class="munten"><div>{F.stapel(1, 44, 40)}</div><div>{F.stapel(12, 44, 40)}</div><div>{F.stapels(5, 12, 44, 40)}</div></div>'
                f'<div class="bij"><div><b>{e(k[0][0])}</b>{e(k[0][1])}</div><div><b>{e(k[1][0])}</b>{e(k[1][1])}</div><div class="groot-b"><b>{e(k[2][0])}</b>{e(k[2][1])}</div></div>{wie(s)}</section>')
    if t == "stappen":
        st = "".join(f'<div class="stap">{FIG[x["figuur"]]()}<div class="t"><span class="n">{i+1}.</span>{e(x["tekst"])}</div></div>' for i, x in enumerate(s["stappen"]))
        straat = F.straat(1080, 150, [F.K["groen"]]*10).replace('class="hand ', 'class="hand straatje ')
        return f'<section class="vel c t-stappen"><div class="titel kop">{e(s["kop"])}</div><div class="stappen">{st}</div><div class="titel slot">Scheelt weer.</div>{straat}</section>'
    raise ValueError(t)

def scene(s):
    t = s["sjabloon"]
    if t == "flessen":
        a, b = s["paren"]
        fa, fb = (getattr(F, n)() for n in s["figuren"]) if s.get("figuren") else (F.fles(F.K["framboos"]), F.fles(F.K["groen"]))
        kop = f'<div class="titel kop" style="top:270px;font-size:92px">{e(s["kop"])}</div>' if s.get("kop") else ""
        ta, tb = (490, 900) if s.get("kop") else (300, 790)
        return (f'<section class="vel r">{MERK}{kop}<div class="paar" style="top:{ta}px"><div><div class="titel groot">{e(a[0])}</div><div class="lab">{e(a[1])}</div></div>{fa}</div>'
                f'<div class="paar" style="top:{tb}px"><div><div class="titel groot">{e(b[0])}</div><div class="lab">{e(b[1])}</div></div>{fb}</div>{bron(s)}</section>')
    if t == "pot":
        u = "<br>".join(e(x) for x in s["uitleg"])
        return (f'<section class="vel r pot"><div class="titel kop">{e(s["kop"])}</div><div class="uitleg">{u}</div>'
                f'<div class="teller"><span class="wk" id="wk"></span><span class="bd" id="bd"></span></div>'
                f'<svg class="hand" id="potsvg" width="1080" height="1920" style="position:absolute;left:0;top:0" viewBox="0 0 1080 1920"></svg></section>')
    if t == "eind":
        prent = "".join(FIG[n]() for n in s["figuren"]) if s.get("figuren") else f'{F.fles(F.K["framboos"])}{F.spray()}{F.emmer()}'
        kl = " groot" if s.get("figuren") else ""
        return (f'<section class="vel r">{MERK}<div class="titel kop">{e(s["kop"])}</div><div class="tekst" style="top:{s.get("tekst_top", 700)}px">{e(s["tekst"])}</div>'
                f'<div class="prent{kl}" style="left:72px;top:{s.get("prent_top", 900)}px">{prent}</div></section>')
    if t == "slot":
        g = "<br>".join(e(x) for x in s["groot"])
        straat = F.straat(1080, 380, [F.K["groen"]]*10).replace('class="hand ', 'class="hand straatje ')
        return f'<section class="vel r">{MERK}<div class="titel slot">{g}</div>{straat}{bron(s)}</section>'
    raise ValueError(t)

def pagina(pg, inner):
    doc = f'<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="{(ROOT/"sjabloon.css").as_uri()}"><body>{DEFS}{inner}'
    tmp = ROOT / ".tijdelijk.html"
    tmp.write_text(doc, encoding="utf-8")
    pg.goto(tmp.as_uri())
    pg.evaluate("document.fonts.ready")
    tmp.unlink()

def ffmpeg(args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)

def stil(png, duur, uit):
    t = uit.with_suffix(".tmp.mp4")
    ffmpeg(["-framerate", str(FPS), "-i", str(png), "-vf", f"format=yuv420p,loop=-1:1,trim=duration={duur}", *ENC, str(t)])
    t.rename(uit)

POT_JS = """
(cfg) => {
  const K = cfg.K, S = document.getElementById('potsvg');
  const X = 300, Y = 720, W = 460, H = 600, R = 40, n = cfg.n, per = cfg.per, rx = cfg.rx, ry = cfg.rx * 13 / 40, stap = cfg.stap, dx = cfg.dx;
  const pos = i => { const rij = Math.floor(i / per), kol = i % per; return {x: X + (W - per*dx)/2 + dx/2 + kol*dx + (rij % 2 ? 9 : -9), y: Y + H - 50 - rij * stap}; };
  window.potFrame = (t) => {
    let s = `<defs><clipPath id="c"><rect x="${X+8}" y="${Y-400}" width="${W-16}" height="${H+392}" rx="${R}"/></clipPath></defs>`;
    s += `<rect x="${X}" y="${Y}" width="${W}" height="${H}" rx="${R}" fill="${K.boter}" opacity=".62"/>`;
    const munt = (x, y) => `<ellipse cx="${x}" cy="${y+18}" rx="${rx}" ry="${ry}" fill="${K.mosterd2}"/><rect x="${x-rx}" y="${y}" width="${2*rx}" height="18" fill="${K.mosterd2}"/><ellipse cx="${x}" cy="${y}" rx="${rx}" ry="${ry}" fill="${K.mosterd}"/>`;
    let geland = 0;
    for (let i = 0; i < n; i++) {
      const start = cfg.aanloop + i * cfg.tik, val = .34, p = pos(i), f = (t - start) / val;
      if (f < 0) break;
      if (f >= 1) { geland = i + 1; s += munt(p.x, p.y); }
      else { const y0 = Y - 16; s += munt(p.x, y0 + (p.y - y0) * f * f); }
    }
    s += `<rect x="${X}" y="${Y}" width="${W}" height="${H}" rx="${R}" fill="none" stroke="${K.pruim}" stroke-width="10"/>`;
    s += `<rect x="${X-18}" y="${Y-24}" width="${W+36}" height="${40}" rx="12" fill="${K.pruim}" opacity="${t < cfg.aanloop + (n-1)*cfg.tik + .34 ? 0 : 1}"/>`;
    S.innerHTML = s;
    document.getElementById('wk').textContent = geland ? (geland == n ? 'Per jaar' : cfg.eenheid + ' ' + geland) : '';
    document.getElementById('bd').textContent = geland ? '\\u20ac ' + geland * cfg.perWeek : '';
  };
}
"""

def pot_scene(pg, s, uit):
    cfg = {"K": F.K, "n": s.get("weken", s.get("aantal")), "perWeek": s.get("per_week", s.get("per_stap")), "aanloop": s.get("aanloop", .7), "tik": s.get("tik", .1),
           "eenheid": s.get("eenheid", "Week"), "per": s.get("per_rij", 5), "rx": s.get("munt", 40), "stap": s.get("munt_stap", 42), "dx": s.get("munt_dx", 78)}
    pg.evaluate(POT_JS, cfg)
    eind = cfg["aanloop"] + (cfg["n"]-1)*cfg["tik"] + .34 + s.get("vast", 2.6)
    tmp = uit.with_suffix(".tmp.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-", *ENC, str(tmp)], stdin=subprocess.PIPE)
    for i in range(int(eind*FPS)):
        pg.evaluate("t => window.potFrame(t)", i/FPS)
        p.stdin.write(pg.screenshot(type="jpeg", quality=92))
    p.stdin.close(); p.wait()
    if p.returncode: raise SystemExit("ffmpeg faalde")
    tmp.rename(uit)

def main():
    map_ = pathlib.Path(sys.argv[1]).resolve()
    post = json.loads((map_ / "post.json").read_text(encoding="utf-8"))
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        if post["type"] == "carrousel":
            pg = b.new_page(viewport={"width": 1080, "height": 1350})
            for i, s in enumerate(post["slides"], 1):
                pagina(pg, slide(s))
                pg.screenshot(path=str(map_ / f"slide-{i}.png"))
        else:
            pg = b.new_page(viewport={"width": 1080, "height": 1920})
            with tempfile.TemporaryDirectory() as td:
                td = pathlib.Path(td); delen = []
                for i, s in enumerate(post["scenes"]):
                    pagina(pg, scene(s))
                    uit = td / f"s{i}.mp4"
                    if s["sjabloon"] == "pot":
                        pot_scene(pg, s, uit)
                    else:
                        png = td / f"s{i}.png"; pg.screenshot(path=str(png))
                        if i == 0: pg.screenshot(path=str(map_ / "omslag.jpg"), type="jpeg", quality=92)
                        stil(png, s["duur"], uit)
                    delen.append(uit)
                lijst = td / "lijst.txt"
                lijst.write_text("".join(f"file '{d}'\n" for d in delen))
                beeld = td / "beeld.mp4"
                ffmpeg(["-f", "concat", "-safe", "0", "-i", str(lijst), "-c", "copy", str(beeld)])
                ffmpeg(["-i", str(beeld), "-c:v", "copy", "-movflags", "+faststart", str(map_ / "reel.mp4")])
                import muziek
                muziek.zet_onder(map_ / "reel.mp4")
        b.close()

if __name__ == "__main__":
    main()
