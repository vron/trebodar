"""
R-03 Konstruktionsritning mellanbjälklag (F-01), A3 med ../ritningsmall:

    R-03.1  Översikt och yttermått                       plan 1:100
    R-03.2  Armering i underkant                         plan 1:50
    R-03.3  Armering i överkant                          plan 1:50
    R-03.4  Sektioner, detaljer och stålförteckning      1:5, 1:10, 1:20

Underlag: K-05 (geometri i bild/geometri.json, armering i resultat.json) och K-06 (källarväggarna av Sundolitt
Kub 350-150 och vinkeljärnen från väggarna till bjälklaget). Allt ritas i verkliga koordinater i mm enligt K-05 (origo i skärningen mellan plattkanterna
x = 0 och y = 0, y uppåt); ritningsmall/ritning.py skalar till papperet.

Filen är uppdelad i:
    1. Underlag           geometri, armering och detaljmått
    2. Placeringar        var etiketter, symboler och snitt står (verkliga koordinater, mm) – ändra här
    3. Lager              en funktion per lager; varje funktion ritar bara sitt lager i en vy
    4. Blad               sätter ihop vy, lager, högerkolumn och ritningshuvud
    5. main               skriver R-03.x.json och PDF:erna i ritningar/

    python beräkningar/R-03/ritningar.py
"""
import json
import math
import os
import sys

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
BER = os.path.dirname(HERE)
K05 = os.path.join(BER, "K-05")
ROT = os.path.dirname(BER)
UT = os.path.join(ROT, "ritningar")
sys.path.insert(0, K05)
sys.path.insert(0, os.path.join(BER, "ritningsmall"))
from ritning import Vy, Blad, huvud, sv, PROJEKT  # noqa: E402
import figurer as F05  # noqa: E402   (väggband och inåtgående hörn, samma som i K-05)

# ================================================================== 1. underlag
G = json.load(open(os.path.join(K05, "bild", "geometri.json"), encoding="utf-8"))
R = json.load(open(os.path.join(K05, "resultat.json"), encoding="utf-8"))
K05P = json.load(open(os.path.join(K05, "rapport", "projekt.json"), encoding="utf-8"))

NR = "R-03"
REV, DATUM = "A", "2026-10-08"
K06P = json.load(open(os.path.join(BER, "K-06", "rapport", "projekt.json"), encoding="utf-8"))
R06 = json.load(open(os.path.join(BER, "K-06", "resultat.json"), encoding="utf-8"))
S14 = {v["namn"]: v["arm"][1] for v in R06["vaggar"] if "arm" in v}   # vinkeljärnen: väggens lodräta järn (K-06)
UNDERLAG = f"K-05 rev {K05P['revision']}, K-06 rev {K06P['revision']}"
REVISIONER = [dict(rev=REV, avser="Första utgåvan", datum=DATUM, sign=PROJEKT["signatur"])]

IND = R["indata"]
H = IND["h"]                                # plattans tjocklek 150
C_UK, C_OK = IND["c_uk"], IND["c_ok"]       # täckskikt 20 / 25
C_KANT = 25.0                               # täckskikt mot kanter och hålkanter
DU, SU = IND["nat_uk"]                      # Ø10 s150
DO, SO = IND["nat_ok"]                      # Ø8 s150
YU1 = C_UK + DU / 2                         # yttre lagret i underkant (järnen i valfri ordning)
YU2 = C_UK + DU + DU / 2                    # inre lagret i underkant
YO1 = H - C_OK - DO / 2                     # yttre lagret i överkant
YO2 = H - C_OK - DO - DO / 2                # inre lagret i överkant
ROR = [(p["namn"], *p["yta"]) for p in R["pelare"]]   # rörens lastyta (x0, y0, x1, y1); P7 är två rör (K-05)

KONTUR = Polygon(G["kontur"])
HAL = Polygon(G["hal"])
PLATTA = KONTUR.difference(HAL)
MARK = Polygon(G["mark"])
XMAX, YMAX = KONTUR.bounds[2], KONTUR.bounds[3]   # 13 810, 15 900
YCUT = 12450.0                              # plattan på mark bryts här i planerna 1:50
VIKT = {8: 0.395, 10: 0.617, 12: 0.888}     # kg/m

# K-06: vinkeljärn från ytterväggarnas betongkärna till bjälklaget (ben ned i väggen + ben in i bjälklaget, under
# överkantsnätet) och väggens skikt (Kub 350-150)
POS14 = dict(d=10, s=200, ben=650, in_=500)
VAGG_UTE = 30.0                             # väggens ytterliv 30 mm utanför plattkanten
KUB = (100.0, 150.0, 100.0)                 # cellplast, betongkärna, cellplast
X_LODRAT = KUB[0] + KUB[1] - 25 - 10 - 5    # väggens lodräta järn på insidan, från ytterlivet (K-06)
H_GJUT1 = 1800.0                            # väggarnas första gjutning, över bottenplattan (K-06)
H_VAGG = 2100.0


def lb_rqd(d):
    """Grundvärde för förankringslängd, SS-EN 1992-1-1 8.4.3, goda förhållanden, C25/30: (φ/4)(f_yd/f_bd)."""
    return d / 4 * 435 / (2.25 * 1.8 / 1.5)


SKARV = {d: int(math.ceil(1.5 * lb_rqd(d) / 50) * 50) for d in (8, 10, 12)}   # 500 / 650 / 750


def langd(L):
    return int(math.ceil(L / 50.0) * 50)


def vagg(namn):
    return G["vagg"][int(namn[1:]) - 1]


def zonjarn(zn):
    """Tilläggsjärnen i en zon: linjer i x- och y-led med avståndet s, klippta mot plattan minus täckskikt."""
    x0, y0, x1, y1 = zn["bounds"]
    d, s = zn["tillagg"]
    yta = box(x0, y0, x1, y1).intersection(PLATTA.buffer(-C_KANT, join_style=2))
    ut = {"x": [], "y": []}
    for rikt in ("x", "y"):
        a0, a1 = (y0, y1) if rikt == "x" else (x0, x1)
        n = max(int(round((a1 - a0) / s)), 1)
        for k in range(n):
            t = (a0 + a1) / 2 + (k - (n - 1) / 2) * s
            ln = LineString([(x0 - 10, t), (x1 + 10, t)]) if rikt == "x" else LineString([(t, y0 - 10), (t, y1 + 10)])
            g = ln.intersection(yta)
            for seg in getattr(g, "geoms", [g]):
                if seg.length > 100:
                    ut[rikt].append(seg)
    return yta, ut


def diagonaljarn():
    """2 Ø10 L = 1200 i överkant, 150 och 250 mm in från plattans inåtgående hörn och trapphålets hörn."""
    hal = np.array(G["hal"], float)
    hornen = list(F05.inatgaende_horn(G["kontur"]))
    hornen += [(p, (p - hal.mean(axis=0)) / np.linalg.norm(p - hal.mean(axis=0))) for p in hal]
    ut = []
    for b, bis in hornen:
        t = np.array([-bis[1], bis[0]])
        for off in (150, 250):
            c = np.asarray(b) + bis * off
            ut.append((tuple(c - t * 600), tuple(c + t * 600)))
    return ut, len(hornen)


# ================================================================== 2. placeringar (verkliga koordinater, mm)
PLAC = dict(
    # nätsymbolerna: hörnet där x- och y-järnet möts, och järnens längd i symbolen
    nat=(300.0, 10300.0), nat_l=1800.0,                   # i plattan på mark, där det är fritt i båda lagren
    pos3=((11060.0, 2525.0), (10000.0, 1700.0)),         # från P17:s järn till bubblan
    pos13=((4500.0, 3590.0), (3600.0, 3250.0)),          # hörnet vars diagonaljärn får etiketten, bubblan
    pos14=dict(y=(9000.0, 9600.0, 10200.0), bubbla=(12500.0, 9900.0)),
    fri_text=((10390.0, 1000.0), (11500.0, 450.0)),       # fri kant mot det fria: från kanten till texten
    mark_text=(2700.0, 11250.0),
    snitt=dict(A=((12950, 8000), (13870, 8000), -1), B=((11660, 7150), (11660, 6100), -1),
               C=((8700, 6300), (8700, 5780), -1), D=((9150, 9300), (10150, 9300), -1)),
    rubrik=(150.0, 2750.0), skalstock=(150.0, 1450.0),
)


# ================================================================== 3. lager
def lager_plattan(v, klipp=True):
    """Plattans kontur (klippt vid YCUT i planerna 1:50), trapphålet och text för plattan på mark."""
    with v.lager("plattan"):
        k = KONTUR.intersection(box(-1e4, -1e4, 1e5, YCUT)) if klipp else KONTUR
        pts = list(k.exterior.coords)
        for a, b in zip(pts[:-1], pts[1:]):
            if klipp and abs(a[1] - YCUT) < 1 and abs(b[1] - YCUT) < 1:
                continue
            v.linje([a, b], "kontur")
        if klipp:
            v.brott((-250, YCUT), (4310 + 250, YCUT), "tunn")
            v.ptext(4310 + 300, YCUT - 250, 1.0, 0, "Plattan fortsätter till y = 15\u00a0900,\nsamma armering",
                    a="lm", sz=6.6, col="gra", i=True)
        hx = [p[0] for p in G["hal"]]; hy = [p[1] for p in G["hal"]]
        v.polygon(G["hal"], fyll="hal", stil="kontur")
        v.linje([(min(hx), min(hy)), (max(hx), max(hy))], "tunn")
        v.linje([(min(hx), max(hy)), (max(hx), min(hy))], "tunn")
        v.text(*PLAC["mark_text"], "Platta på mark\n(400 mm cellplast, K-06)", a="cm", sz=7.0, col="gra", i=True)


def lager_vaggar(v, namn=True):
    """Källarväggarna (Kub 350-150) under plattan, streckade, och deras namn (namn=False: namnen ritas senare med
    lager_vaggnamn, ovanpå zonerna)."""
    with v.lager("vaggar"):
        band = unary_union([F05.vaggband(w, G["E"], G["vagg"])[1] for w in G["vagg"]])
        for g in getattr(band, "geoms", [band]):
            v.linje(list(g.exterior.coords), "dold")
            for hh in g.interiors:
                v.linje(list(hh.coords), "dold")
    if namn:
        lager_vaggnamn(v)


def lager_vaggnamn(v):
    with v.lager("vaggnamn"):
        for i, w in enumerate(G["vagg"], 1):
            ax_, c, a, b = w[:4]
            m = (a + b) / 2
            if ax_ == "h":
                v.text(m, c, f"V{i}", a="cm", sz=5.8, col="gra", bg=True)
            else:
                v.text(c, m, f"V{i}", a="cm", sz=5.8, col="gra", rot=90, bg=True)


def _etikettbox(xt, yt, a, txt, v, sz=6.6):
    """Ungefärlig ruta (modellens mm) för en text med ankaret a ("lb", "rt" …) i (xt, yt)."""
    w = (1.45 * len(txt) + 0.6) * sz / 6.6 * v.s
    h = (0.3528 * sz + 0.7) * v.s
    x0 = xt - {"l": 0, "c": w / 2, "r": w}[a[0]]
    y0 = yt - {"b": 0, "m": h / 2, "t": h}[a[1]]
    return box(x0, y0, x0 + w, y0 + h)


def _hinder(v):
    """Linjer som namn inte ska ligga på: trapphålets kant och kryss, diagonaljärnen och (i 1:100) hålets måttlinjer."""
    hx0, hy0, hx1, hy1 = HAL.bounds
    lin = [HAL.exterior, LineString([(hx0, hy0), (hx1, hy1)]), LineString([(hx0, hy1), (hx1, hy0)])]
    if getattr(v, "med_diagonaler", False):         # bara på bladet där diagonaljärnen ritas (R-03.3)
        lin += [LineString(d) for d in diagonaljarn()[0]]
    if v.s >= 100:                                  # som i lager_yttermatt
        yk, xk = hy0 - 950, hx1 + 800
        lin += [LineString([(0, yk), (XMAX, yk)]), LineString([(hx0, hy0), (hx0, yk)]),
                LineString([(hx1, hy0), (hx1, yk)]), LineString([(xk, 1000), (xk, 12510)]),
                LineString([(hx1, hy0), (xk, hy0)]), LineString([(hx1, hy1), (xk, hy1)])]
    return unary_union(lin)


def fri_text(v, kandidater, txt, sz=6.6, **kw):
    """Skriver texten i den första kandidaten (x, y, ankare) vars ruta inte korsar hindren eller tidigare namn."""
    if not hasattr(v, "_namnrutor"):
        v._namnrutor, v._hindret = [], _hinder(v).buffer(0.8 * v.s)      # 0,8 mm marginal på papperet
    def krock(r):
        return r.intersection(v._hindret).area + sum(r.intersection(q).area for q in v._namnrutor)
    for xt, yt, a in kandidater:
        r = _etikettbox(xt, yt, a, txt, v, sz)
        if krock(r) == 0:
            break
    else:                                           # ingen helt fri plats: minst överlapp
        xt, yt, a = min(kandidater, key=lambda k: krock(_etikettbox(*k, txt, v, sz)))
        r = _etikettbox(xt, yt, a, txt, v, sz)
    v._namnrutor.append(r)
    v.text(xt, yt, txt, a=a, sz=sz, **kw)


def lager_ror(v, namn=True):
    """Stålrören (80×80) och deras namn. Namnet står snett ovanför till höger om röret, eller i den första lediga
    av de andra hörnen om det skulle hamna på trapphålets kant, diagonaljärnen eller en måttlinje."""
    with v.lager("ror"):
        for _, x0, y0, x1, y1 in ROR:
            for xa in np.arange(x0, x1 - 1, 80.0):          # ett dubbelrör ritas som två rör
                v.rekt(xa, y0, xa + 80, y1, fyll="stal", stil=None)
        if namn:
            for i, (x, y) in enumerate(G["pelare"], 1):
                k = sorted(((x + dx, y + dy, ("l" if dx > 0 else "r") + ("b" if dy > 0 else "t"))
                            for dx in (170, -170, 450, -450, 700, -700) for dy in (170, -170, 450, -450)),
                           key=lambda t: abs(t[0] - x) + abs(t[1] - y))      # närmast först; uppe till höger först
                fri_text(v, k, f"P{i}", sz=6.6, b=True, bg=True)


def lager_yttermatt(v):
    """Plattans alla yttermått och trapphålets läge (R-03.1)."""
    with v.lager("matt"):
        o1, o2 = 700, 1300                       # måttkedjornas avstånd från närmaste kant (verkliga mm)
        # under: x = 0, 4 500, 9 310, 13 810
        v.mattx([0, 4500, 9310, XMAX], -o1, [3590, 0, 0, 1000])
        v.mattx([0, XMAX], -o2, [-o1, -o1])
        # över: x = 0, 4 310, 9 500, 13 810
        v.mattx([0, 4310, 9500, XMAX], YMAX + o1, [YMAX, YMAX, 12510, 12510])
        v.mattx([0, XMAX], YMAX + o2, [YMAX + o1, YMAX + o1])
        # vänster: y = 0, 3 590, 15 900
        v.matty([0, 3590, YMAX], -o1, [4500, 0, 0])
        v.matty([0, YMAX], -o2, [-o1, -o1])
        # höger: y = 0, 1 000, 11 010, 12 510, 15 900
        v.matty([0, 1000, 11010, 12510, YMAX], XMAX + o1, [9310, XMAX, 9500, XMAX, 4310])
        v.matty([0, YMAX], XMAX + o2, [XMAX + o1, XMAX + o1])
        # trapphålets läge och storlek
        hx = sorted({p[0] for p in G["hal"]}); hy = sorted({p[1] for p in G["hal"]})
        yk = hy[0] - 950                          # vågrät kedja under hålet, under rörnamnen
        v.mattx([0, hx[0], hx[1], XMAX], yk, [yk, hy[0], hy[0], yk], sz=6.4)
        xk = hx[1] + 800                          # lodrät kedja till höger om hålet
        v.matty([1000, hy[0], hy[1], 12510], xk, [xk, hx[1], hx[1], xk], sz=6.4)


def lager_origo(v):
    with v.lager("origo"):
        L = 900
        v.linje([(0, 0), (L, 0)], "tunn"); v.pil((L + 150, 0), (1, 0), langd=2.2, bredd=1.0)
        v.linje([(0, 0), (0, L)], "tunn"); v.pil((0, L + 150), (0, 1), langd=2.2, bredd=1.0)
        v.ptext(L + 150, 0, 1.0, 0, "x", a="lm", sz=7.5, i=True)
        v.ptext(0, L + 150, 0, 1.0, "y", a="cb", sz=7.5, i=True)
        v.ptext(0, 0, 1.0, -1.0, "origo (0; 0)", a="lt", sz=6.4, col="gra")


def lager_rubrik(v, titel, skala, pos=None, skalstock=None):
    with v.lager("rubrik"):
        x, y = pos or PLAC["rubrik"]
        v.rubrik(x, y, titel, skala=skala, sz=11)
        sx, sy = skalstock or PLAC["skalstock"]
        v.skalstock(sx, sy, 4 if skala <= 50 else 5, 1)


def lager_snitt(v):
    with v.lager("snitt"):
        for namn, (p0, p1, sida) in PLAC["snitt"].items():
            v.snittpil(p0, p1, namn, sida=sida)


def natsymbol(v, pos_x, pos_y, d, s, stil, text):
    """Symbol för ett nät över hela plattan: ett kort x-järn och ett kort y-järn från samma hörn, med positioner."""
    X, Y = PLAC["nat"]; L = PLAC["nat_l"]
    v.linje([(X, Y), (X + L, Y)], stil)
    v.linje([(X, Y), (X, Y + L)], stil)
    for p in ((X + L, Y), (X, Y + L)):
        v.cirkel(*p, 0.5, fyll="svart", stil=None)
    v.bubbla(X + L + 2.6 * v.s, Y, pos_x)
    v.text(X + L + 5.2 * v.s, Y, f"Ø{d} s{s} x-led", a="lm", sz=7.0, bg=True)
    v.bubbla(X, Y + L + 2.6 * v.s, pos_y)
    v.text(X + 2.6 * v.s, Y + L + 2.6 * v.s, f"Ø{d} s{s} y-led", a="lm", sz=7.0, bg=True)
    v.text(X + 1.5 * v.s, Y + 1.5 * v.s, text, a="lb", sz=6.6, col="gra", i=True)


def vaggspann(namn):
    """Väggnamn i nummerordning med följder ihopslagna: V8, V9, V10, V12 -> "V8–V10, V12"."""
    nr = sorted(int(n[1:]) for n in namn)
    ut, i = [], 0
    while i < len(nr):
        j = i
        while j + 1 < len(nr) and nr[j + 1] == nr[j] + 1:
            j += 1
        ut.append(f"V{nr[i]}" if j - i < 2 else f"V{nr[i]}–V{nr[j]}")
        if j - i == 1:
            ut[-1] = f"V{nr[i]}, V{nr[j]}"
        i = j + 1
    return ", ".join(ut)


def pos3_jarn():
    """2 + 2 Ø10 över varje rör (pos 3), L = 1 200 centrerade på röret. Vid trapphålet slutar järnen 25 mm från
    hålkanten och går minst skarvlängden (650) bort från hålet. [(p0, p1, rör)]"""
    yta = PLATTA.buffer(-C_KANT, join_style=2)
    ut = []
    for namn, x0, y0, x1, y1 in ROR:
        x, y = (x0 + x1) / 2, (y0 + y1) / 2
        for o in (-25.0, 25.0):
            for a, b in (((x - 600, y + o), (x + 600, y + o)), ((x + o, y - 600), (x + o, y + 600))):
                g = LineString([a, b]).intersection(yta)
                seg = min((q for q in getattr(g, "geoms", [g]) if q.length > 1), key=lambda q: q.distance(Point(x, y)))
                p0, p1 = seg.coords[0], seg.coords[-1]
                if seg.length < 1199.0:
                    L = max(seg.length, SKARV[10])
                    if math.dist(p0, a) < 1 or math.dist(p0, b) < 1:      # p1 är klippt mot hålet: förläng p0
                        ux, uy = (p0[0] - p1[0]) / seg.length, (p0[1] - p1[1]) / seg.length
                        p0 = (p1[0] + ux * L, p1[1] + uy * L)
                    else:
                        ux, uy = (p1[0] - p0[0]) / seg.length, (p1[1] - p0[1]) / seg.length
                        p1 = (p0[0] + ux * L, p0[1] + uy * L)
                ut.append((p0, p1, namn))
    return ut


def lager_uk(v):
    """Underkant: nätet (pos 1, 2), 2 + 2 Ø10 över varje rör (pos 3) och täckskiktet vid de fria kanterna mot det
    fria (öppningarna i källarens ytterväggar)."""
    with v.lager("fri_kant"):
        mal, till = PLAC["fri_text"]
        v.hanvisning(mal, till, f"fria kanter mot det fria (öppningarna i källarens\nytterväggar): täckskikt {C_KANT:.0f} mm mot kanten", a="lm", sz=6.6)
    with v.lager("armering_uk"):
        natsymbol(v, 1, 2, DU, SU, "uk", "hela plattan")
        for p0, p1, _ in pos3_jarn():
            v.linje([p0, p1], "uk_tunn")
        mal, till = PLAC["pos3"]
        v.hanvisning(mal, till, f"2+2 Ø10 L = 1\u00a0200 över varje rör (vid trapphålet {SKARV[10]})", bubbla=3, a="lm")


def lager_zoner(v):
    """Överkant: zonerna (Ö1 …) med tilläggsjärnen. Returnerar raderna till zontabellen."""
    rader = []
    with v.lager("zoner"):
        for zn in R["zoner"]:
            yta, jarn = zonjarn(zn)
            for g in getattr(yta, "geoms", [yta]):
                v.polygon(list(g.exterior.coords), fyll="zon", stil="zon_kant")
            for seg in jarn["x"] + jarn["y"]:
                v.linje(list(seg.coords), "ok_tunn")
            x0, y0, x1, y1 = zn["bounds"]
            hornen = [(hx + du * v.s, hy + dv * v.s, a_)
                      for (hx, hy, a_, du, dv) in ((x0, y1, "lt", 0.6, -0.6), (x1, y1, "rt", -0.6, -0.6),
                                                   (x0, y0, "lb", 0.6, 0.6), (x1, y0, "rb", -0.6, 0.6))
                      if yta.buffer(1).contains(Point(hx + du * v.s * 2, hy + dv * v.s * 2))]
            if hornen:
                fri_text(v, hornen, zn["namn"], sz=6.6, b=True, bg=True, col="ok")
            dz, sz_ = zn["tillagg"]

            def grupp(lst):
                L = sorted(langd(g.length) for g in lst)
                if not L:
                    return "–"
                return f"{len(L)} × {sv(L[0])}" if L[0] == L[-1] else f"{len(L)} st, {sv(L[0])}–{sv(L[-1])}"
            rader.append([zn["namn"], f"Ø{dz} s{sz_}", grupp(jarn["x"]), grupp(jarn["y"]),
                          f"{sv(x0 / 1000, 2)}–{sv(x1 / 1000, 2)}", f"{sv(y0 / 1000, 2)}–{sv(y1 / 1000, 2)}"])
    return rader


def lager_ok(v):
    """Överkant: nätet (pos 11, 12), diagonaljärn (pos 13) och vinkeljärnen från ytterväggarna (pos 14)."""
    with v.lager("armering_ok"):
        natsymbol(v, 11, 12, DO, SO, "ok", "hela plattan")
        diag, nh = diagonaljarn()
        for p0, p1 in diag:
            if max(p0[1], p1[1]) < YCUT:
                v.linje([p0, p1], "ok")
        hornet, bubbla = PLAC["pos13"]
        near = min(diag, key=lambda q: np.hypot((q[0][0] + q[1][0]) / 2 - hornet[0], (q[0][1] + q[1][1]) / 2 - hornet[1]))
        mid = ((near[0][0] + near[1][0]) / 2, (near[0][1] + near[1][1]) / 2)
        v.hanvisning(mid, bubbla, f"2 Ø10 L = 1\u00a0200 diagonalt, alla inåtgående\nhörn och trapphålets hörn ({nh} hörn)",
                     bubbla=13, a="rm", sz=7.0)
        c14 = vagg("V14")[1]
        xv = c14 + G["E"] + VAGG_UTE - X_LODRAT                # vinkeljärnets lodräta ben (V14: insidan åt −x)
        for yy in PLAC["pos14"]["y"]:
            v.linje([(xv, yy), (xv - POS14["in_"], yy)], "ok")
            v.linje([(xv, yy - 60), (xv, yy + 60)], "ok_tunn")
        ys = PLAC["pos14"]["y"]
        v.fordelning((xv - 100, ys[0] - 300), (xv - 100, ys[-1] + 300))
        v.hanvisning((xv - POS14["in_"], ys[1]), PLAC["pos14"]["bubbla"],
                     f"vinkeljärn Ø{POS14['d']} s{POS14['s']} längs\nytterväggarna (s{max(S14.values())} i "
                     f"{vaggspann([n for n, x in S14.items() if x != POS14['s']])}),\nsektion A", bubbla=14, a="rm")


# ---------------------------------------------------------------- sektioner (lokala koordinater, mm)
def platta_snitt(v, x0, x1, langs="x", kant0=False, kant1=False):
    """Plattan 150 mm mellan x0 och x1 (y = 0 i underkant) med näten; järnen i riktningen langs syns som linjer."""
    with v.lager("betong"):
        v.rekt(x0, 0, x1, H, fyll="betong", stil=None)
        v.linje([(x0, 0), (x1, 0)], "normal"); v.linje([(x0, H), (x1, H)], "normal")
        for x, k in ((x0, kant0), (x1, kant1)):
            if k:
                v.linje([(x, 0), (x, H)], "normal")
            else:
                v.brott((x, -40), (x, H + 40), "tunn")
    with v.lager("armering"):
        a = x0 + (C_KANT if kant0 else 0)
        b = x1 - (C_KANT if kant1 else 0)
        yl_u, yp_u, yl_o, yp_o = (YU1, YU2, YO1, YO2) if langs == "x" else (YU2, YU1, YO2, YO1)
        v.linje([(a, yl_u), (b, yl_u)], "uk")
        v.linje([(a, yl_o), (b, yl_o)], "ok")
        for x in np.arange(math.ceil((x0 + 60) / SU) * SU, x1 - 40, SU):
            v.cirkel(x, yp_u, DU / 2, fyll="#2c4a6e", stil=None, modell=True)
        for x in np.arange(math.ceil((x0 + 60) / SO) * SO + 75, x1 - 40, SO):
            v.cirkel(x, yp_o, DO / 2, fyll="#b5463a", stil=None, modell=True)


def kub(v, x0, y0, y1, gips=True):
    """Kub 350-150 (cellplast 100 + betongkärna 150 + cellplast 100) från y0 till y1, x0 i det ena livet."""
    e, k, _ = KUB
    with v.lager("vagg"):
        v.rekt(x0, y0, x0 + e, y1, fyll="eps", stil="tunn")
        v.rekt(x0 + e, y0, x0 + e + k, y1, fyll="karna", stil=None)
        v.linje([(x0 + e, y0), (x0 + e, y1)], "tunn"); v.linje([(x0 + e + k, y0), (x0 + e + k, y1)], "tunn")
        v.rekt(x0 + e + k, y0, x0 + 350, y1, fyll="eps", stil="tunn")
        if gips:
            v.rekt(x0 + 350, y0, x0 + 363, y1, fyll="vit", stil="tunn")
        v.brott((x0 - 60, y0), (x0 + 420, y0), "tunn")


def etiketter(v, lst, x, y0, dy, sz=6.8):
    """Etiketter i en kolumn uppifrån och ned: (text, målpunkt, bubbla eller None); dy i pappersmm."""
    with v.lager("text"):
        for k, (txt, mal, bub) in enumerate(lst):
            y = y0 - k * dy * v.s
            if bub is not None:
                v.hanvisning(mal, (x + 2.1 * v.s, y), txt, bubbla=bub, a="lm", sz=sz)
            else:
                v.hanvisning(mal, (x, y), txt, a="lm", sz=sz)


def sektion_a():
    """A–A: yttervägg mot jord (V14), Kub 350-150, och bjälklagets kant. x = 0 i väggens ytterliv, inåt positivt;
    y = 0 i plattans underkant. 1:20"""
    v = Vy(x=24, y=86, w=165, h=112, skala=20, X0=-450, Y1=380)
    hf = 0.8 + 1.0 * (8000.0 - 1145.0) / 11220.0                     # fyllningen vid snittet (K-06), m
    ym = hf * 1000 - H_VAGG                                          # markytan
    ylo = -1250.0
    e, k, _ = KUB
    with v.lager("mark"):
        v.polygon([(-400, ylo), (-60, ylo), (-60, ym), (-400, ym - 7)], fyll="jord", stil=None)
        v.linje([(-400, ym - 7), (-60, ym)], "normal")
        v.linje([(-6, ylo), (-6, ym + 60)], "dold")
        v.rekt(-55, ym - 50, -15, H, fyll="#c9c3b8", stil="tunn")
        v.rekt(-15, ym - 50, 0, H, fyll="vit", stil="tunn")
    kub(v, 0, ylo, 0)
    platta_snitt(v, VAGG_UTE, 1400, "x", kant0=True)
    with v.lager("vagg"):
        v.rekt(0, 0, VAGG_UTE, H, fyll="eps", stil="tunn")                      # kantisolering
        v.rekt(e + 0.5, -2, e + k - 0.5, 2, fyll="betong", stil=None)           # kärnan och plattan i ett
        v.linje([(e, H_GJUT1 - H_VAGG), (e + k, H_GJUT1 - H_VAGG)], "dold")     # gjutfogen vid 1 800
    with v.lager("armering"):
        yb = YO2 - DO / 2 - 5 - POS14["d"] / 2                                  # vinkeljärnets ben under nätet
        xa = X_LODRAT - 14
        v.linje([(X_LODRAT, ylo + 20), (X_LODRAT, yb + 8)], "ok_tunn")
        v.linje([(xa, yb - POS14["ben"]), (xa, yb), (xa + POS14["in_"], yb)], "ok")
        for yy in (H_GJUT1 - H_VAGG - 25, H_GJUT1 - H_VAGG - 325, H_GJUT1 - H_VAGG - 625, -60):
            if yy > ylo + 20:
                for x in (e + 30 + 5, e + k - 25 - 5):
                    v.cirkel(x, yy, 5, fyll="svart", stil=None, modell=True)
    with v.lager("matt"):
        v.matt((1300, 0), (1300, H), 2.5, sida=-1, sz=6.2)
        v.matt((0, ylo + 220), (e, ylo + 220), 2.5, sida=-1, sz=6.0, txt=sv(e))
        v.matt((e, ylo + 220), (e + k, ylo + 220), 2.5, sida=-1, sz=6.0, txt=sv(k))
        v.matt((e + k, ylo + 220), (350, ylo + 220), 2.5, sida=-1, sz=6.0, txt=sv(KUB[2]))
        v.matt((0, H), (VAGG_UTE, H), 2.0, sz=5.8, txt=sv(VAGG_UTE))
        v.matt((xa, yb), (xa + POS14["in_"], yb), 3.0, sz=5.8, txt=sv(POS14["in_"]))
        v.matt((xa, yb - POS14["ben"]), (xa, yb), 3.0, sida=1, sz=5.8, txt=sv(POS14["ben"]))
        v.matt((420, H_GJUT1 - H_VAGG), (420, 0), 2.5, sida=-1, sz=5.8, txt=sv(H_VAGG - H_GJUT1))
    etiketter(v, [(f"vinkeljärn Ø{POS14['d']} s{POS14['s']}, under nätet", (xa + 300, yb), 14),
                  ("Ø8 s150, överkant", (900, YO1), 11), ("Ø8 s150, överkant", (1200, YO2), 12),
                  ("Ø10 s150, underkant", (1100, YU2), 2), ("Ø10 s150, underkant", (1000, YU1), 1),
                  ("kärnan gjuts med bjälklaget (K-06)", (e + k / 2, -150), None),
                  ("gjutfog 300 under bjälklaget (K-06)", (e + 20, -300), None),
                  ("Kub 350-150, betongkärna 150 (K-06)", (e + 40, -500), None),
                  (f"väggens lodräta järn Ø10 s{POS14['s']} (K-06)", (X_LODRAT, -750), None)], 1500, 340, 4.4)
    with v.lager("text"):
        v.hanvisning((15, 100), (-90, 300), "kantisolering 30", a="rm", sz=6.4)
        v.text(-70, -250, "fasadsten\n(AR-01)", a="rb", sz=6.0, col="gra", i=True)
        v.text(-230, -1000, "fyllning\n(K-06)", a="cm", sz=6.0, col="gra", i=True, bg=True)
    with v.lager("rubrik"):
        v.rubrik(-400, ylo - 180, "SEKTION A–A  Yttervägg mot jord (V14)", skala=20, sz=9)
    return v


def sektion_b():
    """B–B: vid rör (P5) med topplåt, pos 3 och zonen kring röret. x = 0 i rörets mitt, y = 0 i underkant. 1:10"""
    zp5 = next(z for z in R["zoner"] if "P5" in z["pelare"])
    v = Vy(x=194, y=14, w=130, h=70, skala=10, X0=-420, Y1=270)
    platta_snitt(v, -400, 400, "x")
    with v.lager("armering"):
        for x in np.arange(-300, 400, 150):
            v.cirkel(x, YO2, 4, fyll="#b5463a", stil=None, modell=True)
        for x in (-25, 25):
            v.cirkel(x, YU2, 5, fyll="#2c4a6e", stil="tunn", modell=True)
    with v.lager("stal"):
        v.rekt(-40, 0, 40, 8, fyll="stal", stil=None)
        v.rekt(-40, -330, 40, 0, fyll="#9aa0a8", stil="tunn")
        v.rekt(-36, -330, 36, 0, fyll="vit", stil=None)
        v.linje([(-40, -330), (-40, 0)], "tunn"); v.linje([(40, -330), (40, 0)], "tunn")
        v.brott((-90, -330), (90, -330), "tunn")
    with v.lager("matt"):
        v.matt((-40, -250), (40, -250), 3.0, sida=-1, sz=6.2)
        v.matt((-330, 0), (-330, H), 3.0, sida=1, sz=6.2)
        v.matt((-230, 0), (-230, C_UK), 1.5, sida=1, sz=5.6, txt=f"{C_UK:.0f}")
        v.matt((-230, H - C_OK), (-230, H), 1.5, sida=1, sz=5.6, txt=f"{C_OK:.0f}")
    etiketter(v, [("Ø8 s150, överkant", (150, YO1), 11),
                  (f"{zp5['namn']}: Ø{zp5['tillagg'][0]} s{zp5['tillagg'][1]}, båda riktningarna", (225, YO2), None),
                  ("2 + 2 Ø10 L = 1\u00a0200 över röret", (25, YU2), 3),
                  ("Ø10 s150, underkant", (150, YU1), 1),
                  ("topplåt 80×80×8 kant i kant med\nunderkanten (P7: två rör)", (40, 4), None),
                  ("rör VKR 80×80×4 S235", (40, -180), None)], 450, 250, 4.6)
    with v.lager("rubrik"):
        v.rubrik(-400, -410, "SEKTION B–B  Vid rör (P5)", skala=10, sz=9)
    return v


def sektion_c():
    """C–C: trapphålets kant. x = 0 i hålkanten, y = 0 i underkant. 1:10"""
    v = Vy(x=24, y=212, w=165, h=40, skala=10, X0=-160, Y1=250)
    platta_snitt(v, 0, 700, "y", kant0=True)
    with v.lager("text"):
        v.text(-30, H / 2, "trapphål", a="rm", sz=6.6, col="gra", i=True)
    with v.lager("matt"):
        v.matt((0, H), (C_KANT, H), 2.0, sz=5.6, txt=f"{C_KANT:.0f}")
    etiketter(v, [("båda näten går ut till hålkanten, täckskikt 25", (C_KANT + 5, YO2), None),
                  ("diagonaljärn vid hålets hörn, se R-03.3", (400, YO1), 13)], 800, 220, 4.6)
    with v.lager("rubrik"):
        v.rubrik(-150, -120, "SEKTION C–C  Trapphålets kant", skala=10, sz=9)
    return v


def sektion_d():
    """D–D: innervägg (V15, Kub 350-150) med glidskikt på krönet. x = 0 i väggens mitt, y = 0 i underkant. 1:20"""
    v = Vy(x=24, y=14, w=165, h=62, skala=20, X0=-620, Y1=300)
    kub(v, -175, -760, -5, gips=False)
    with v.lager("vagg"):
        v.rekt(-175, -5, 175, 0, fyll="papp", stil=None)
    platta_snitt(v, -600, 600, "x")
    with v.lager("matt"):
        v.matt((-175, -560), (175, -560), 2.5, sida=-1, sz=6.2)
    etiketter(v, [("glidskikt (byggpapp) på krönet; bjälklaget förankras inte i innerväggarna", (120, -3), None),
                  ("innervägg Kub 350-150 (K-06)", (0, -400), None)], 700, 150, 4.6)
    with v.lager("rubrik"):
        v.rubrik(-600, -880, "SEKTION D–D  Innervägg (V15)", skala=20, sz=9)
    return v


def detalj_e():
    """E: armeringens lägen i plattan. x längs plattan, y = 0 i underkant. 1:5"""
    v = Vy(x=196, y=210, w=128, h=55, skala=5, X0=-190, Y1=215)
    B_ = 300
    with v.lager("betong"):
        v.rekt(0, 0, B_, H, fyll="betong", stil=None)
        v.linje([(0, 0), (B_, 0)], "normal"); v.linje([(0, H), (B_, H)], "normal")
        v.brott((0, -30), (0, H + 30), "tunn"); v.brott((B_, -30), (B_, H + 30), "tunn")
    with v.lager("armering"):
        v.rekt(15, C_UK, B_ - 15, C_UK + DU, fyll="#2c4a6e", stil=None)
        v.rekt(15, H - C_OK - DO, B_ - 15, H - C_OK, fyll="#b5463a", stil=None)
        for x in (75, 225):
            v.cirkel(x, YU2, DU / 2, fyll="#2c4a6e", stil=None, modell=True)
        v.cirkel(150, YO2, DO / 2, fyll="#b5463a", stil=None, modell=True)
    with v.lager("matt"):
        v.matt((0, 0), (0, H), 8.0, sida=1, sz=6.2)
        v.matt((0, 0), (0, C_UK), 3.0, sida=1, sz=5.8, txt=f"{C_UK:.0f}")
        v.matt((0, H - C_OK), (0, H), 3.0, sida=1, sz=5.8, txt=f"{C_OK:.0f}")
    etiketter(v, [("Ø8, lager 1", (270, H - C_OK - DO / 2), 11), ("Ø8, lager 2", (150, YO2), 12),
                  ("Ø10, lager 2", (225, YU2), 2), ("Ø10, lager 1", (270, C_UK + DU / 2), 1)], 345, 175, 4.6)
    with v.lager("rubrik"):
        v.rubrik(-180, -60, "DETALJ E  Armeringens lägen", skala=5, sz=9)
    return v


def stalforteckning():
    """Positioner, antal och vikt. Näten räknas med alla järn i plattan (även plattan på mark) och en skarv per
    12 m stång."""
    rader, tot = [], {}

    def lagg(pos, d, form, s, n, L, total_m, anm=""):
        kg = total_m * VIKT[d]
        tot[d] = tot.get(d, 0) + kg
        rader.append([str(pos), f"Ø{d}", form, s, str(n), L, sv(total_m, 0), sv(kg, 0), anm])
    yta = PLATTA.buffer(-C_KANT, join_style=2)
    minx, miny, maxx, maxy = KONTUR.bounds

    def nat(d, sc, rikt):
        n, tl = 0, 0.0
        rng = np.arange(miny + C_KANT + sc / 2, maxy, sc) if rikt == "x" else np.arange(minx + C_KANT + sc / 2, maxx, sc)
        for t in rng:
            ln = LineString([(minx - 1, t), (maxx + 1, t)]) if rikt == "x" else LineString([(t, miny - 1), (t, maxy + 1)])
            g = ln.intersection(yta)
            for seg in getattr(g, "geoms", [g]):
                if seg.length > 100:
                    n += 1
                    tl += seg.length + math.floor(seg.length / 12000) * SKARV[d]
        return n, tl / 1000
    for pos, d, sc, rikt in ((1, DU, SU, "x"), (2, DU, SU, "y"), (11, DO, SO, "x"), (12, DO, SO, "y")):
        n, tl = nat(d, sc, rikt)
        lagg(pos, d, "rak", f"s{sc}", n, "var.", tl, ("UK " if pos < 10 else "ÖK ") + f"{rikt}-led")
    p3 = {}
    for p0, p1, _ in pos3_jarn():
        L = langd(math.dist(p0, p1) - 1)
        p3[L] = p3.get(L, 0) + 1
    for L in sorted(p3, reverse=True):
        lagg(3, 10, "rak", "–", p3[L], sv(L), p3[L] * L / 1000, "UK över rören" + ("" if L >= 1200 else ", vid trapphålet"))
    _, nh = diagonaljarn()
    lagg(13, 10, "rak", "–", 2 * nh, "1\u00a0200", 2 * nh * 1.2, "ÖK diagonalt")
    n14 = int(sum(math.floor(abs(w[3] - w[2]) / S14.get(f"V{i}", POS14["s"])) + 1
                  for i, w in enumerate(G["vagg"], 1) if w[4] == "yttre"))
    L14 = POS14["ben"] + POS14["in_"]
    lagg(14, 10, f"L {POS14['ben']}+{POS14['in_']}", "/".join(f"s{x}" for x in sorted(set(S14.values()))), n14,
         sv(L14), n14 * L14 / 1000, "vinkeljärn")
    zon = {}
    for zn in R["zoner"]:
        _, jarn = zonjarn(zn)
        z = zon.setdefault(zn["tillagg"][0], [0, 0.0])
        for seg in jarn["x"] + jarn["y"]:
            z[0] += 1; z[1] += langd(seg.length) / 1000
    for dz in sorted(zon):
        lagg(f"Ö-Ø{dz}", dz, "rak", "–", zon[dz][0], "var.", zon[dz][1], "zoner R-03.3")
    rader.append(["", "", "", "", "", "", "Summa", sv(sum(tot.values()), 0),
                  " + ".join(f"Ø{d}: {sv(k, 0)}" for d, k in sorted(tot.items()))])
    return dict(typ="tabell", kolumner=["Pos", "Ø", "Form", "s", "Antal", "L (mm)", "Total (m)", "Vikt (kg)", "Anm"],
                bredd=(0, 0, 0, 0, 0, 0, 0, 0, 1), rader=rader, just=["l", "l", "l", "l", "r", "r", "r", "r", "l"], sz=6.8)


# ================================================================== 4. blad
BLADEN = [
    ("R-03.1", ["Mellanbjälklag", "Översikt och yttermått"], "1:100", "R-03.1 Mellanbjälklag, översikt och yttermått"),
    ("R-03.2", ["Mellanbjälklag", "Armering i underkant"], "1:50", "R-03.2 Mellanbjälklag, armering i underkant"),
    ("R-03.3", ["Mellanbjälklag", "Armering i överkant"], "1:50", "R-03.3 Mellanbjälklag, armering i överkant"),
    ("R-03.4", ["Mellanbjälklag", "Sektioner, detaljer och stålförteckning"], "1:5, 1:10, 1:20",
     "R-03.4 Mellanbjälklag, sektioner och stålförteckning"),
]


def hd(nr):
    b = [x for x in BLADEN if x[0] == nr][0]
    return huvud(nr, b[1], b[2], UNDERLAG, DATUM, REV)


def anvisningar():
    return [
        "Betong C25/30, exponeringsklass XC1, livslängd 50 år. Armering B500B. Bjälklaget får gjutas med "
        "källarväggarnas betong, B30 enligt Sundolitt (K-06, R-04).",
        f"Täckskikt: underkant {C_UK:.0f} mm, överkant {C_OK:.0f} mm, kanter och hålkanter {C_KANT:.0f} mm, även "
        "mot de fria kanterna vid öppningarna i källarens ytterväggar.",
        f"Skarvlängd: Ø8 {SKARV[8]}, Ø10 {SKARV[10]}, Ø12 {SKARV[12]} mm. Skarvar förskjuts minst 1,3 × skarvlängden.",
        "Järnen i varje nät läggs i valfri ordning. Tilläggsjärn läggs i nätets lager.",
        "Koordinater i mm enligt K-05; origo i skärningen mellan plattkanterna x = 0 och y = 0. Mått, se R-03.1.",
    ]


def planvy():
    """Planvy 1:50: modellfönstret täcker plattan till y = 12 660 och plats för origo nere till vänster."""
    return Vy(x=24, y=12, w=300, h=273, skala=50, X0=-950, Y1=12660)


def blad_oversikt():
    v = Vy(x=82, y=30, w=200, h=210, skala=100, X0=-2200, Y1=18300)
    lager_plattan(v, klipp=False)
    lager_vaggar(v)
    lager_ror(v)
    lager_yttermatt(v)
    lager_origo(v)
    lager_rubrik(v, "PLAN – ÖVERSIKT OCH YTTERMÅTT", 100, pos=(-2000, -2300), skalstock=(-2000, -3300))
    forteckning = [[nr, ", ".join(t[1:]), sk] for nr, t, sk, _ in BLADEN]
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", rader=anvisningar() + [
            "Plattans kontur och trapphålets läge enligt denna ritning. Rörens lägen, se tabell på R-03.2.",
            "Källarväggarna (Kub 350-150, R-04) under plattan streckade."]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="linje", stil="kontur", text="plattans kant"),
            dict(form="linje", stil="dold", text="källarvägg under plattan"),
            dict(form="ruta", fyll="stal", text="stålrör VKR 80×80×4 (K-05)")]),
        dict(typ="rubrik", text=f"Ritningsförteckning {NR}"),
        dict(typ="tabell", kolumner=["Ritning", "Innehåll", "Skala"], bredd=(0, 1, 0), rader=forteckning,
             just=["l", "l", "l"], sz=6.8),
    ]
    return Blad(hd("R-03.1"), REVISIONER, kol, [v])


def blad_uk():
    v = planvy()
    lager_plattan(v)
    lager_vaggar(v)
    lager_ror(v)
    lager_uk(v)
    lager_snitt(v)
    lager_origo(v)
    lager_rubrik(v, "PLAN – ARMERING I UNDERKANT", 50)
    rader = [[n, sv(x0 + 40) if x1 - x0 < 100 else f"{sv(x0 + 40)} och {sv(x1 - 40)}", sv((y0 + y1) / 2),
              "80×80×8" if x1 - x0 < 100 else "två rör tätt intill varandra, 80×80×8 på vart"]
             for n, x0, y0, x1, y1 in ROR]
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", rader=anvisningar() + [
            "Underkantsnätet läggs på distanser 20 mm, högst 0,8 m isär.",
            "Minst två underkantsjärn i vardera riktningen ska passera över varje rör (SS-EN 1992-1-1 9.4.1(3)): "
            f"pos 3, bundna till nätet. Vid trapphålet ({', '.join(sorted({n for p0, p1, n in pos3_jarn() if math.dist(p0, p1) < 1199}, key=lambda q: int(q[1:])))}) "
            f"slutar järnen mot hålet 25 mm från hålkanten, L = {SKARV[10]}.",
            "Överkant, se R-03.3. Sektioner A–D, se R-03.4."]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="linje", stil="uk", text="armering i underkant"),
            dict(form="bubbla", txt="1", text="positionsnummer (stålförteckning R-03.4)"),
            dict(form="linje", stil="dold", text="källarvägg under plattan"),
            dict(form="ruta", fyll="stal", text="stålrör VKR 80×80×4 (K-05)")]),
        dict(typ="rubrik", text="Rör och topplåtar"),
        dict(typ="tabell", kolumner=["Rör", "x", "y", "Topplåt"], bredd=(0, 0, 0, 1), rader=rader,
             just=["l", "r", "r", "l"], sz=6.6),
    ]
    return Blad(hd("R-03.2"), REVISIONER, kol, [v])


def blad_ok():
    v = planvy()
    lager_plattan(v)
    lager_vaggar(v, namn=False)
    v.med_diagonaler = True
    zrader = lager_zoner(v)
    lager_vaggnamn(v)
    lager_ror(v)
    lager_ok(v)
    lager_origo(v)
    lager_rubrik(v, "PLAN – ARMERING I ÖVERKANT", 50)
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", rader=[
            "Allmänt, se R-03.2. Mått R-03.1, sektioner R-03.4.",
            "Överkantsnätet läggs på armeringsstolar, högst 0,8 m isär.",
            f"Tilläggsjärnen i zonerna {R['zoner'][0]['namn']}–{R['zoner'][-1]['namn']} läggs i båda riktningarna i nätets lager och binds till nätet "
            "(s150: mitt emellan nätets järn). Där zonen når plattans kant förs järnen ut till kanten.",
            "Vinkeljärnen pos 14 sätts i ytterväggarnas betongkärna, bundna till väggens lodräta järn och med samma "
            "avstånd (R-04.2), innan ytterväggarnas översta skift och bjälklaget gjuts (sektion A, K-06)."]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="linje", stil="ok", text="armering i överkant"),
            dict(form="yta", fyll="zon", stil="zon_kant", text="zon med tilläggsjärn i överkant"),
            dict(form="fordelning", text="fördelning av järn med samma position"),
            dict(form="linje", stil="dold", text="källarvägg under plattan"),
            dict(form="ruta", fyll="stal", text="stålrör VKR 80×80×4 (K-05)")]),
        dict(typ="rubrik", text="Tilläggsjärn i överkant (antal × längd)"),
        dict(typ="tabell", kolumner=["Zon", "Järn", "x-led", "y-led", "x (m)", "y (m)"], bredd=(0, 0, 0, 0, 0, 0),
             rader=zrader, just=["l", "l", "r", "r", "r", "r"], sz=6.1),
    ]
    return Blad(hd("R-03.3"), REVISIONER, kol, [v])


def blad_sektioner():
    vyer = [sektion_a(), sektion_b(), sektion_d(), sektion_c(), detalj_e()]
    block = [dict(x=196, y=160, w=128, innehall=[
        dict(typ="rubrik", text="Stålförteckning, B500B"), stalforteckning(),
        dict(typ="text", sz=6.4, rader=[
            "",
            f"Näten räknade över hela plattan (även plattan på mark) med en skarv per 12 m stång. "
            f"Skarvlängd Ø8 {SKARV[8]}, Ø10 {SKARV[10]}, Ø12 {SKARV[12]} mm."])])]
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", rader=anvisningar()[:4] + [
            "Rörens topplåt gjuts in kant i kant med plattans underkant. Röret centreras under plåten. "
            "Rörens mitt enligt tabellen på R-03.2 och R-04.1; P7 är två rör tätt intill varandra.",
            "Överkantsarmeringens höjd kontrolleras före gjutning, särskilt vid rören.",
            "Ytterväggarnas översta halva skift gjuts samtidigt med bjälklaget, i den ordning K-06 anger. "
            "Bjälklagets form och stämp står för sig själva och hänger inte i Kub-elementen. "
            "Pos 14 binds till väggens lodräta järn före gjutning.",
            "Innerväggarna gjuts i hela höjden före bjälklaget och får glidskikt (byggpapp) på krönet (R-04).",
            "Formrivning tidigast när betongen nått cirka 70 % av fck (provkroppar eller mognadsberäkning). "
            "Last under byggtiden högst 5 kN/m², punktlaster över rör eller vägg.",
            "Trägolv limmas först när betongens relativa fuktighet är under golvlimmets gräns (mätt enligt RBK). "
            "Våtrum får sprickupptagande tätskikt.",
            "Plan: underkant R-03.2, överkant R-03.3."]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="linje", stil="uk", text="armering i underkant"),
            dict(form="linje", stil="ok", text="armering i överkant"),
            dict(form="yta", fyll="betong", stil="tunn", text="betong C25/30"),
            dict(form="yta", fyll="karna", stil="tunn", text="betongkärna, Kub 350-150 (K-06)"),
            dict(form="yta", fyll="eps", stil="tunn", text="cellplast"),
            dict(form="yta", fyll="jord", stil="tunn", text="fyllning"),
            dict(form="yta", fyll="stal", stil=None, text="stål")]),
    ]
    return Blad(hd("R-03.4"), REVISIONER, kol, vyer, block)


# ================================================================== 5. main
SERIE = "R-03 Mellanbjälklag"            # ritningsseriens pdf i ritningar/, ett blad per sida


def main(dolj=()):
    os.makedirs(UT, exist_ok=True)
    bladmapp = os.path.join(HERE, "blad")    # bladen var för sig (versionshanteras inte)
    os.makedirs(bladmapp, exist_ok=True)
    fn = {"R-03.1": blad_oversikt, "R-03.2": blad_uk, "R-03.3": blad_ok, "R-03.4": blad_sektioner}
    pdfer = []
    for nr, _, _, filnamn in BLADEN:
        b = fn[nr]()
        jp = os.path.join(HERE, f"{nr}.json")
        b.spara(jp)
        pdfer.append(os.path.join(bladmapp, filnamn + ".pdf"))
        b.kompilera(jp, pdfer[-1], ROT, dolj=dolj)
        print("blad/" + filnamn + ".pdf")
    Blad.serie(pdfer, os.path.join(UT, SERIE + ".pdf"))
    print(f"ritningar/{SERIE}.pdf ({len(pdfer)} sidor)")


if __name__ == "__main__":
    main()
