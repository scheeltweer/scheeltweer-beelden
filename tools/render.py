#!/usr/bin/env python3
"""Maakt de beelden van een post uit posts/<map>/post.json.
Gebruik: python3 tools/render.py posts/<map> [--stil seconde,seconde]"""
import json, subprocess, sys, html, pathlib, tempfile, os
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent
FPS = 30
ENC = ["-c:v","libx264","-crf","19","-preset","veryfast","-pix_fmt","yuv420p","-r",str(FPS)]
e = html.escape

def regel(r):
    if r == "-": return '<hr class="streep">'
    cls = r[2] if len(r) > 2 else ""
    return f'<div class="rij {cls}"><span class="l">{e(r[0])}</span><span class="r">{e(r[1])}</span></div>'

def bon(s):
    kop = ""
    if s.get("bonkop"):
        kop = f'<div class="merk">{e(s["bonkop"])}</div>' + (f'<div class="sub">{e(s["sub"])}</div>' if s.get("sub") else "") + '<hr class="streep">'
    rijen = "".join(regel(r) for r in s.get("regels", []))
    tot = ""
    if s.get("totaal"):
        l, r = s["totaal"]
        tot = f'<div class="totaal rood"><span class="l">{e(l)}</span><span class="r">{e(r)}</span></div>'
    return f'<div class="bonwrap"><div class="papier" data-tand>{kop}{rijen}{tot}</div></div>'

def slide(s):
    t = s["sjabloon"]
    merk = '<div class="merk">Scheelt Weer</div>'
    bron = f'<div class="bron">{e(s["bron"])}</div>' if s.get("bron") else ""
    if t == "groot":
        g = "<br>".join(e(x) for x in s["groot"])
        return f'<section class="vel c t-groot">{merk}<div class="groot">{g}</div><div class="tekst">{e(s["tekst"])}</div>{bron}</section>'
    if t == "bon":
        return f'<section class="vel c t-bon"><div class="kop">{e(s["kop"])}</div>{bon(s)}{bron}</section>'
    if t == "stappen":
        st = "".join(f'<div class="stap"><span class="n">{i+1}</span><span>{e(x)}</span></div>' for i, x in enumerate(s["stappen"]))
        return f'<section class="vel c t-stappen"><div class="kop">{e(s["kop"])}</div><div class="bonwrap"><div class="papier" data-tand>{st}</div></div><div class="groot slot">Scheelt weer.</div>{bron}</section>'
    raise ValueError(t)

def scene(s):
    t = s["sjabloon"]
    merk = '<div class="merk">Scheelt Weer</div>'
    bron = f'<div class="bron">{e(s["bron"])}</div>' if s.get("bron") else ""
    if t == "hook":
        blok = "".join(f'<span class="groot">{e(g)}</span><div class="tekst">{e(x)}</div>' for g, x in s["paren"])
        return f'<section class="vel r">{merk}<div class="hook">{blok}</div>{bron}</section>'
    if t == "print":
        kop = f'<div class="kop printkop">{e(s["kop"])}</div>' if s.get("kop") else ""
        return f'<section class="vel r"><div class="schacht">{kop}{bon(s)}</div><div class="printer"></div></section>'
    if t == "eind":
        return f'<section class="vel r">{merk}<div class="eind"><div class="kop">{e(s["kop"])}</div><div class="tekst">{e(s["tekst"])}</div></div>{bron}</section>'
    if t == "slot":
        return f'<section class="vel r">{merk}<div class="groot slot">{"<br>".join(e(x) for x in s["groot"])}</div>{bron}</section>'
    raise ValueError(t)

TAND = """() => document.querySelectorAll('[data-tand]').forEach(p => {
  const w = p.offsetWidth, h = p.offsetHeight, b = 26, d = 13, pts = [];
  for (let x = 0; x <= w; x += b) pts.push(`${x}px ${(x / b) % 2 ? 0 : d}px`);
  pts.push(`${w}px ${d}px`);
  for (let x = w; x >= 0; x -= b) pts.push(`${x}px ${(Math.round(x / b)) % 2 ? h : h - d}px`);
  p.style.clipPath = `polygon(${pts.join(',')})`;
})"""

def pagina(pg, inner):
    doc = f'<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="{(ROOT/"sjabloon.css").as_uri()}"><body>{inner}'
    tmp = ROOT / ".tijdelijk.html"
    tmp.write_text(doc, encoding="utf-8")
    pg.goto(tmp.as_uri())
    pg.evaluate("document.fonts.ready")
    pg.evaluate(TAND)
    tmp.unlink()

def ffmpeg(args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)

def stil(png, duur, uit):
    t = uit.with_suffix(".tmp.mp4")
    ffmpeg(["-framerate", str(FPS), "-i", str(png), "-vf", f"format=yuv420p,loop=-1:1,trim=duration={duur}", *ENC, str(t)])
    t.rename(uit)

def print_scene(pg, s, uit, tmp):
    """Papier komt regel voor regel uit de printer, per regel een korte duw."""
    info = pg.evaluate("""() => { const p = document.querySelector('.schacht .bonwrap'), r = p.getBoundingClientRect();
      const el = [...p.querySelectorAll('.merk,.sub,.streep,.rij,.totaal')];
      return {h: r.height, ond: el.map(x => x.getBoundingClientRect().bottom - r.top)}; }""")
    H, SLOT = info["h"], 1400
    stops = [o + 16 for o in info["ond"]] + [H]
    duw, wacht = s.get("duw", .22), s.get("wacht", .3)
    kf, t, gevoed = [(0, 0)], 0, 0
    for st in stops:
        kf.append((t + duw, st)); kf.append((t + duw + wacht, st)); t += duw + wacht
    eind = t + s.get("vast", 2.4)
    def gevoed_op(tt):
        for (a, x), (b, y) in zip(kf, kf[1:]):
            if a <= tt <= b:
                f = (tt - a) / (b - a) if b > a else 1
                return x + (y - x) * f
        return H
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-", *ENC, str(uit.with_suffix(".tmp.mp4"))], stdin=subprocess.PIPE)
    n = int(eind * FPS)
    for i in range(n):
        y = SLOT - gevoed_op(i / FPS)
        pg.evaluate("y => document.querySelector('.schacht .bonwrap').style.top = y + 'px'", y)
        p.stdin.write(pg.screenshot(type="jpeg", quality=92))
    p.stdin.close(); p.wait()
    if p.returncode: raise SystemExit("ffmpeg faalde")
    uit.with_suffix(".tmp.mp4").rename(uit)
    return eind

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
                hoogte = pg.evaluate("[...document.querySelectorAll('.bonwrap')].map(x=>Math.round(x.getBoundingClientRect().bottom))")
                print(f"slide {i}: bon-onderkant {hoogte}")
        else:
            pg = b.new_page(viewport={"width": 1080, "height": 1920})
            with tempfile.TemporaryDirectory() as td:
                td = pathlib.Path(td); delen = []
                for i, s in enumerate(post["scenes"]):
                    pagina(pg, scene(s))
                    uit = td / f"s{i}.mp4"
                    if s["sjabloon"] == "print":
                        print_scene(pg, s, uit, td)
                    else:
                        png = td / f"s{i}.png"; pg.screenshot(path=str(png))
                        if i == 0: pg.screenshot(path=str(map_ / "omslag.jpg"), type="jpeg", quality=92)
                        stil(png, s["duur"], uit)
                    delen.append(uit)
                lijst = td / "lijst.txt"
                lijst.write_text("".join(f"file '{d}'\n" for d in delen))
                beeld = td / "beeld.mp4"
                ffmpeg(["-f", "concat", "-safe", "0", "-i", str(lijst), "-c", "copy", str(beeld)])
                ffmpeg(["-i", str(beeld), "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(map_ / "reel.mp4")])
        b.close()

if __name__ == "__main__":
    main()
