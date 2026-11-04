"""Eigen getekende figuren voor Scheelt Weer. Alles is simpele SVG, zodat de agent er makkelijk nieuwe bij kan maken."""
K = dict(abrikoos="#F8D3B0", boter="#FFF1D6", pruim="#3A1E2C", groen="#2F6B57", framboos="#B8305A",
         mosterd="#E5A82E", mosterd2="#C98D1E", lucht="#A9CFCB", klei="#E9A679")

def svg(w, h, inhoud, cls="", stijl=""):
    return f'<svg class="hand {cls}" style="{stijl}" width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">{inhoud}</svg>'

def _gevel(w, h, soort):
    if soort == "trap":
        d = [(0,.42),(.14,.42),(.14,.30),(.28,.30),(.28,.18),(.42,.18),(.42,.06),(.58,.06),(.58,.18),(.72,.18),(.72,.30),(.86,.30),(.86,.42),(1,.42)]
    elif soort == "punt":
        d = [(0,.40),(.5,.08),(1,.40)]
    else:  # hals
        d = [(0,.44),(.18,.44),(.18,.26),(.32,.26),(.32,.08),(.68,.08),(.68,.26),(.82,.26),(.82,.44),(1,.44)]
    pts = [(0,1)] + d + [(1,1)]
    return " ".join(f"{x*w:.1f},{y*h:.1f}" for x, y in pts)

def huis(x, y, w, h, kleur, raam=K["boter"], deur=K["pruim"], soort="trap"):
    s = f'<g transform="translate({x},{y})"><polygon points="{_gevel(w,h,soort)}" fill="{kleur}"/>'
    rw, rh = w*.20, h*.13
    for ry in (.50, .68):
        for rx in (.17, .63):
            if ry == .68 and rx == .17:
                s += f'<rect x="{w*rx:.1f}" y="{h*.72:.1f}" width="{rw:.1f}" height="{h*.28:.1f}" rx="3" fill="{deur}"/>'
            else:
                s += f'<rect x="{w*rx:.1f}" y="{h*ry:.1f}" width="{rw:.1f}" height="{rh:.1f}" rx="2" fill="{raam}"/>'
    if soort != "punt":
        s += f'<rect x="{w*.42:.1f}" y="{h*.22:.1f}" width="{w*.16:.1f}" height="{h*.10:.1f}" rx="2" fill="{raam}"/>'
    return s + "</g>"

def straat(breedte, hoogte, kleuren, ramen=None, stijl=""):
    """Rij huizen, een kleur per huis. Handig als telbare grafiek: 9 van de 10."""
    n = len(kleuren); w = breedte / n
    soorten = ["trap", "hals", "punt", "trap", "punt", "hals", "trap", "hals", "punt", "trap"]
    hoogtes = [1, .9, .96, .86, 1, .92, .84, 1, .9, .96]
    s = ""
    for i, k in enumerate(kleuren):
        h = hoogte * hoogtes[i % 10]
        r = (ramen[i] if ramen else K["boter"])
        s += huis(i*w, hoogte-h, w+1, h, k, raam=r, soort=soorten[i % 10])
    return svg(int(breedte), int(hoogte), s, stijl=stijl)

def huisje(m=64, kleur=K["groen"]):
    return svg(m, m, huis(0, 0, m, m, kleur, soort="trap"), stijl="display:inline-block;vertical-align:-10px")

def tijdschrift(m=150):
    p, b, f, g = K["pruim"], K["boter"], K["framboos"], K["mosterd"]
    return svg(150, 150, f'<g transform="rotate(-7 75 75)"><rect x="30" y="14" width="94" height="124" rx="4" fill="{f}"/><rect x="22" y="14" width="10" height="124" fill="{p}"/>'
      f'<rect x="44" y="28" width="66" height="14" rx="3" fill="{b}"/><circle cx="77" cy="82" r="24" fill="{g}"/><rect x="44" y="116" width="44" height="7" rx="3" fill="{b}"/></g>')

def telefoon(m=150):
    p, b, g, gr, f = K["pruim"], K["boter"], K["mosterd"], K["groen"], K["framboos"]
    s = f'<rect x="42" y="8" width="68" height="134" rx="12" fill="{p}"/><rect x="49" y="20" width="54" height="104" rx="3" fill="{K["lucht"]}"/>'
    kl = [f, g, gr, b, gr, f, g, b, b]
    for i, k in enumerate(kl):
        s += f'<rect x="{54+(i%3)*16}" y="{28+(i//3)*17}" width="12" height="12" rx="3" fill="{k}"/>'
    return svg(150, 150, s + f'<rect x="66" y="129" width="20" height="5" rx="2" fill="{b}"/>')

def tv(m=150):
    p, b, f = K["pruim"], K["boter"], K["framboos"]
    return svg(150, 150, f'<path d="M58 10 L75 34 L92 10" stroke="{p}" stroke-width="6" fill="none" stroke-linecap="round"/><rect x="12" y="32" width="126" height="88" rx="10" fill="{p}"/><rect x="22" y="42" width="106" height="68" rx="4" fill="{K["lucht"]}"/><polygon points="62,58 62,94 94,76" fill="{f}"/><rect x="48" y="122" width="54" height="10" rx="4" fill="{p}"/>')

def prijskaartje(tekst, w=250):
    p, b = K["pruim"], K["boter"]
    return (f'<div class="kaartje"><svg class="hand" width="{w}" height="104" viewBox="0 0 {w} 104"><path d="M0 22 L28 2 H{w-6} a6 6 0 0 1 6 6 V96 a6 6 0 0 1 -6 6 H28 L0 82 Z" fill="{b}"/><circle cx="26" cy="52" r="9" fill="{K["abrikoos"]}"/></svg><span>{tekst}</span></div>')

def gezin(m=72):
    p, f, g, gr = K["pruim"], K["framboos"], K["mosterd"], K["groen"]
    def fig(x, h, k):
        r = h*.19; top = 104-h*.74
        return f'<circle cx="{x}" cy="{top-r*.95:.1f}" r="{r:.1f}" fill="{p}"/><rect x="{x-h*.2:.1f}" y="{top:.1f}" width="{h*.4:.1f}" height="{h*.74:.1f}" rx="{h*.16:.1f}" fill="{k}"/>'
    return svg(170, 110, fig(30, 84, gr)+fig(72, 78, f)+fig(112, 52, g)+fig(146, 42, K["lucht"]), stijl="display:block;flex:none")

def _munt(x, y, r=46, dik=20):
    return (f'<ellipse cx="{x}" cy="{y+dik}" rx="{r}" ry="{r*.34:.1f}" fill="{K["mosterd2"]}"/><rect x="{x-r}" y="{y}" width="{2*r}" height="{dik}" fill="{K["mosterd2"]}"/>'
            f'<ellipse cx="{x}" cy="{y}" rx="{r}" ry="{r*.34:.1f}" fill="{K["mosterd"]}"/>')

def stapel(aantal, r=46, stap=30):
    h = aantal*stap + 60; w = 2*r+6
    s = "".join(_munt(r+3, h-42-i*stap, r) for i in range(aantal))
    return svg(w, h, s, stijl="display:block")

def stapels(n, aantal, r=46, stap=30):
    h = aantal*stap + 60; w = n*(2*r+2)+6
    s = ""
    for k in range(n):
        s += "".join(_munt(k*(2*r+2)+r+3, h-42-i*stap, r) for i in range(aantal))
    return svg(w, h, s, stijl="display:block")

def fles(k=K["framboos"], m=200, etiket=K["boter"]):
    return svg(200, 320, f'<rect x="72" y="6" width="46" height="34" rx="6" fill="{K["pruim"]}"/><path d="M78 40 H112 C118 66 170 76 170 130 V286 a22 22 0 0 1 -22 22 H52 a22 22 0 0 1 -22 -22 V130 C30 76 72 66 78 40 Z" fill="{k}"/><rect x="48" y="150" width="104" height="98" rx="8" fill="{etiket}"/><circle cx="100" cy="199" r="26" fill="{k}"/>')

def spray(m=200):
    k, p = K["groen"], K["pruim"]
    return svg(200, 320, f'<path d="M40 26 H128 L150 44 L128 54 H112 L118 92 H84 L88 54 H60 Z" fill="{p}"/><path d="M84 92 H118 C134 118 150 128 150 160 V286 a22 22 0 0 1 -22 22 H62 a22 22 0 0 1 -22 -22 V160 C40 128 68 118 84 92 Z" fill="{k}"/><rect x="58" y="176" width="74" height="84" rx="8" fill="{K["boter"]}"/>')

def emmer(m=260):
    p, l, b = K["pruim"], K["lucht"], K["boter"]
    return svg(280, 280, f'<path d="M40 90 C40 0 240 0 240 90" fill="none" stroke="{p}" stroke-width="10"/><path d="M26 90 H254 L226 268 a12 12 0 0 1 -12 10 H66 a12 12 0 0 1 -12 -10 Z" fill="{l}"/><rect x="18" y="80" width="244" height="22" rx="10" fill="{p}"/><circle cx="96" cy="66" r="18" fill="{b}"/><circle cx="134" cy="56" r="24" fill="{b}"/><circle cx="178" cy="68" r="16" fill="{b}"/>')

def potlood(m=150):
    p, g, b, f = K["pruim"], K["mosterd"], K["boter"], K["framboos"]
    return svg(150, 150, f'<g transform="rotate(35 75 75)"><rect x="60" y="4" width="30" height="20" rx="4" fill="{f}"/><rect x="60" y="24" width="30" height="86" fill="{g}"/><polygon points="60,110 90,110 75,142" fill="{b}"/><polygon points="70,131 80,131 75,142" fill="{p}"/></g>')

def kalender(m=150):
    p, b, f = K["pruim"], K["boter"], K["framboos"]
    s = f'<rect x="16" y="24" width="118" height="112" rx="10" fill="{b}"/><path d="M16 56 V34 a10 10 0 0 1 10 -10 H124 a10 10 0 0 1 10 10 V56 Z" fill="{f}"/><rect x="42" y="12" width="10" height="26" rx="4" fill="{p}"/><rect x="98" y="12" width="10" height="26" rx="4" fill="{p}"/>'
    for r in range(3):
        for c in range(4):
            k = f if (r, c) == (1, 2) else K["klei"]
            s += f'<rect x="{30+c*24}" y="{68+r*21}" width="16" height="14" rx="3" fill="{k}"/>'
    return svg(150, 150, s)

def rekening(m=150):
    return telefoon(m)
