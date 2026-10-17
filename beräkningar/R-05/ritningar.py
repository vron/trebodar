"""
R-05 Konstruktionsritning bottenplatta (F-01), A3 med ../ritningsmall:

    R-05.1  Plan, balkar, plintar och cellplast              1:50
    R-05.2  Armering                                          1:50
    R-05.3  Sektioner, detaljer och förteckningar             1:10, 1:20

Bottenplatta L300 (K-06): 100 mm betong C25/30 på 200 mm cellplast S100, kantbalkar i L-element och balkar under
innerväggarna 450 × 200 och plintar under rören, alla på 100 mm S300. L-elementen har ytterkanten i väggarnas
ytterliv och betongen börjar 100 mm innanför. Geometrin ur
../R-04/kallare.py (K-05:s geometri.json, K-06:s indata och resultat). Koordinater som K-05 (mm, origo i
skärningen mellan mellanbjälklagets kanter x = 0 och y = 0); höjder z från bottenplattans överkant.

    python beräkningar/K-06/berakning.py    # om K-06/resultat.json saknas
    python beräkningar/R-05/ritningar.py
"""
import importlib.util
import math
import os
import sys

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
R04 = os.path.join(os.path.dirname(HERE), "R-04")
sys.path.insert(0, R04)
import kallare as K  # noqa: E402
from ritning import Vy, Blad, huvud, sv, svm, PROJEKT  # noqa: E402

_spec = importlib.util.spec_from_file_location("ritningar_r04", os.path.join(R04, "ritningar.py"))
R4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R4)                     # R-04: måttkedjor, väggarna i plan, snitt genom bottenplattan
kedja, etiketter = R4.kedja, R4.etiketter

ROT = K.ROT
UT = os.path.join(ROT, "ritningar")

# ================================================================== 1. underlag
NR = "R-05"
REV, DATUM = "A", "2026-10-16"
UNDERLAG = f"{R4.revision('K-06')}, {R4.revision('K-05')}"
REVISIONER = [dict(rev=REV, avser="Första utgåvan", datum=DATUM, sign=PROJEKT["signatur"])]

V, VAGG, ROR = K.VAGGAR, K.VAGG, K.ROR
HP, HB, TF, EPS = K.H_PLATTA, K.UTF["h_balk"], K.T_FOT, K.UTF["t_eps"]          # 100, 200, 100, 200
BB = K.B_BALK                                                                    # 450
C_UK, C_OK = 30.0, 25.0         # täckskikt: mot cellplasten (distanser) och i överkant (K-06)
NAT = (6, 150)                  # Ø6 s150 i båda lagren (K-06)
BALK_ARM = dict(uk=(2, 10), ok=(2, 10), bygel=(6, 600))
PLINT_ARM = (8, 150)            # Ø8 s150 i underkant, båda riktningarna
DIAG = dict(n=2, d=10, L=1200.0, off=(150.0, 250.0))   # i överkant vid de inåtgående hörnen
START = K.STARTJARN             # Ø10 s300, 500 i balken, 1 200 upp
FOT_START = 330.0               # startjärnets fot längs balken, på byglarna: 500 i balken med den lodräta delen
UPP_START = 10 * round((START["upp"] - R4.Z_BALK_UK + 5) / 10)   # lodräta benet, till fotens underkant
VIKT = {6: 0.222, 8: 0.395, 10: 0.617, 12: 0.888}


def lb_rqd(d):
    """Grundvärde för förankringslängd, SS-EN 1992-1-1 8.4.3, goda förhållanden, C25/30 (som R-03)."""
    return d / 4 * 435 / (2.25 * 1.8 / 1.5)


SKARV = {d: int(math.ceil(1.5 * lb_rqd(d) / 50) * 50) for d in (6, 8, 10)}     # 400 / 500 / 650
POS = dict(uk_x=31, uk_y=32, ok_x=33, ok_y=34, balk_uk=35, balk_ok=36, bygel=37, plint=38, diag=39,
           start_ute=40, start_inne=41)

KALLARE = K.KALLARE             # väggarnas ytterliv = L-elementens ytterkant (modellens bottenplatta)
BETONG = K.BETONG               # bottenplattans betong, 100 mm innanför
KANT = K.kantbalk()
INRE = K.balkar_inre()
PLINTAR = K.plintar()
TJOCK = unary_union([KANT, INRE] + list(PLINTAR.values())).intersection(BETONG)

# ================================================================== 2. placeringar
PLAN = R4.PLAN
PLAC = dict(
    rubrik=(-200.0, 2500.0), skalstock=(-200.0, 1550.0),
    natsymbol=(900.0, 4400.0, 1600.0),          # hörnet där järnen i nätsymbolen möts och järnens längd
    snitt=dict(A=((13150.0, 6100.0), (13990.0, 6100.0), -1), B=((9150.0, 9900.0), (10150.0, 9900.0), -1),
               C=((6200.0, 2190.0), (7780.0, 2190.0), -1)),
)


def ytterliv(n):
    return VAGG[n]["ytterliv"]


# ================================================================== 3. lager
def lager_platta(v, fyll_balk=True):
    """Bottenplattans kontur: L-elementens ytterkant i väggarnas ytterliv, det yttre benet 100 och betongen innanför,
    med kantbalkar, balkar under innerväggarna och plintar."""
    with v.lager("platta"):
        v.polygon(list(KALLARE.exterior.coords), fyll="eps2", stil="kontur")
        v.polygon(list(BETONG.exterior.coords), fyll="betong", stil="tunn")
    with v.lager("balkar"):
        # balkarnas yta; hålen (plattan innanför kantbalken) ritas tillbaka med plattans fyllning
        for g in (KANT, INRE):
            for p in K.ytor(g):
                v.polygon(list(p.exterior.coords), fyll="zon" if fyll_balk else None, stil="tunn")
                for h in p.interiors:
                    v.polygon(list(h.coords), fyll="betong" if fyll_balk else None, stil="tunn")
        for namn, p in PLINTAR.items():
            v.polygon(list(p.exterior.coords), fyll="zon" if fyll_balk else None, stil="tunn")


def lager_vaggar_streckade(v):
    """Väggarna ovanpå bottenplattan, streckade (R-04)."""
    with v.lager("vaggar"):
        for g in getattr(K.HEL, "geoms", [K.HEL]):
            v.linje(list(g.exterior.coords), "dold")
            for h in g.interiors:
                v.linje(list(h.coords), "dold")


def lager_ror(v, fotplat=True, namn=True):
    with v.lager("ror"):
        for r in ROR:
            if fotplat:
                bx, by, _ = K.FOTPLAT[r["n"]]
                mx, my = r["mitt"]
                v.rekt(mx - bx / 2, my - by / 2, mx + bx / 2, my + by / 2, fyll="stal", stil=None)
            if namn:
                mx, my = r["mitt"]
                b = K.PLINT[r["namn"]]
                v.text(mx, my - b / 2 - 1.0 * v.s, f"{r['namn']}  {sv(b)}", a="ct", sz=6.0, b=True, bg=True)


def lager_yttermatt(v):
    """Som R-04.1: väggarnas ytterliv = L-elementens ytterkant."""
    R4.lager_yttermatt(v)


def lager_balkmatt(v):
    """Balkarnas bredd och läge."""
    s = v.s
    with v.lager("matt"):
        # kantbalken längs V21 och V14, balken under V15 och V19
        kedja(v, [ytterliv("V21"), ytterliv("V21") + K.L_BEN, ytterliv("V21") + K.B_L], 5300.0, [5300.0] * 3,
              sz=5.6)
        kedja(v, [ytterliv("V14") - K.B_L, ytterliv("V14") - K.L_BEN, ytterliv("V14")], 9000.0, [9000.0] * 3,
              sz=5.6)
        c15 = VAGG["V15"]["c"]
        kedja(v, [c15 - BB / 2, c15 + BB / 2], 9200.0, [9200.0] * 2, sz=5.6)
        c4 = VAGG["V4"]["c"]
        kedja(v, [c4 - BB / 2, c4 + BB / 2], 7000.0, [7000.0] * 2, sz=5.6, ax="y")


def lager_rubrik(v, titel):
    with v.lager("rubrik"):
        x, y = PLAC["rubrik"]
        v.rubrik(x, y, titel, skala=50, sz=11)
        sx, sy = PLAC["skalstock"]
        v.skalstock(sx, sy, 4, 1)


def lager_snitt(v):
    with v.lager("snitt"):
        for namn, (p0, p1, sida) in PLAC["snitt"].items():
            v.snittpil(p0, p1, namn, sida=sida)


# ---------------------------------------------------------------- armering i plan (R-05.2)
def natsymbol(v):
    X, Y, L = PLAC["natsymbol"]
    s = v.s
    for (st, dy, posx, posy, txt) in (("uk", 0.0, POS["uk_x"], POS["uk_y"], "underkant"),
                                      ("ok", 700.0, POS["ok_x"], POS["ok_y"], "överkant")):
        x0, y0 = X, Y + dy
        v.linje([(x0, y0), (x0 + L, y0)], st)
        v.linje([(x0, y0), (x0, y0 + L * 0.45)], st)
        v.bubbla(x0 + L + 2.6 * s, y0, posx)
        v.text(x0 + L + 5.2 * s, y0, f"Ø{NAT[0]} s{NAT[1]} x-led, {txt}", a="lm", sz=6.6, bg=True)
        v.bubbla(x0, y0 + L * 0.45 + 2.6 * s, posy)
        v.text(x0 + 2.6 * s, y0 + L * 0.45 + 2.6 * s, f"Ø{NAT[0]} s{NAT[1]} y-led", a="lm", sz=6.6, bg=True)
    v.text(X, Y - 1.5 * s, "hela plattan, även i balkar och plintar", a="lt", sz=6.4, col="gra", i=True)


def balkjarn():
    """Balkarnas längsjärn i plan (under- och överkantens järn sammanfaller): 60 mm innanför balkens kanter.
    Kantbalken längs hela konturen; innerbalkarnas järn går in i kantbalken eller den korsande balken."""
    ut = []
    for d in (K.BALK_JARN, BB - K.BALK_JARN):
        ut.append(list(BETONG.buffer(-d, join_style=2).exterior.coords))
    e = BB / 2 - K.BALK_JARN
    y4 = VAGG["V4"]["c"]
    for n, slut in (("V15", ytterliv("V2") - K.L_BEN - K.BALK_JARN), ("V19", ytterliv("V3") - K.L_BEN - K.BALK_JARN)):
        c = VAGG[n]["c"]
        for off in (-e, e):
            ut.append([(c + off, y4 - e), (c + off, slut)])
    x19, x15 = VAGG["V19"]["c"], VAGG["V15"]["c"]
    for off in (-e, e):
        ut.append([(x19 - e, y4 + off), (x15 + e, y4 + off)])
    return ut


def plintjarn(r):
    """Ø8 s150 i plintens underkant, båda riktningarna, 30 mm från plintens kanter."""
    p = PLINTAR[r["namn"]]
    x0, y0, x1, y1 = p.bounds
    ts = R4._fordela(0.0, x1 - x0 - 60, PLINT_ARM[1])                  # högst s150
    lx = [[(x0 + 30, y0 + 30 + t), (x1 - 30, y0 + 30 + t)] for t in ts]
    ly = [[(x0 + 30 + t, y0 + 30), (x0 + 30 + t, y1 - 30)] for t in ts]
    return lx + ly, len(ts)


def diagonaljarn():
    """2 Ø10 L = 1 200 i överkant, 150 och 250 mm in från plattans inåtgående hörn längs bisektrisen."""
    ut = []
    for (x, y) in K.HORN_IN_BETONG:
        # bisektrisen in i plattan
        best = None
        for bx in (1, -1):
            for by in (1, -1):
                q = (x + bx * 300.0, y + by * 300.0)              # bisektrisen: in i plattan, bort från det
                q_ut = (x - bx * 300.0, y - by * 300.0)           # saknade hörnet
                if BETONG.contains(Point(q)) and not BETONG.contains(Point(q_ut)):
                    best = (bx / math.sqrt(2), by / math.sqrt(2))
        t = (-best[1], best[0])
        for off in DIAG["off"]:
            c = (x + best[0] * off, y + best[1] * off)
            ut.append([(c[0] - t[0] * DIAG["L"] / 2, c[1] - t[1] * DIAG["L"] / 2),
                       (c[0] + t[0] * DIAG["L"] / 2, c[1] + t[1] * DIAG["L"] / 2)])
    return ut


def startjarn_rader():
    """Startjärnens rader: väggar som står på bottenplattan i ett stycke. Väggbitar vid öppningar med bröstning
    (F1–F3) hör till samma rad, eftersom väggen är hel under bröstningen; vid dörrar slutar raden.
    [(väggar, lo, hi)] med lo och hi längs raden."""
    rader = []
    for w in V:
        o_a = next((o for o in K.OPPNINGAR if o["vaggar"][1] == w["namn"]), None)
        if o_a is not None and o_a["z0"] > 0:
            continue                                             # fortsätter en rad som började tidigare
        rad = [w]
        while True:
            o_b = next((o for o in K.OPPNINGAR if o["vaggar"][0] == rad[-1]["namn"]), None)
            if o_b is None or o_b["z0"] <= 0:
                break
            rad.append(VAGG[o_b["vaggar"][1]])
        rader.append(rad)
    return rader


def startjarn():
    """Startjärn Ø10 högst s300: ytterväggarna vid utsidans järnläge (145 från ytterlivet), innerväggarna i kärnans
    mitt; också under bröstningarna. [(punkt, "ute"/"inne", första väggen i raden)]."""
    ut = []
    for rad in startjarn_rader():
        w0, w1 = rad[0], rad[-1]
        q = (w0["ytterliv"] - w0["ute"] * K.X_START) if w0["ute"] is not None else w0["c"]

        def grans(w, o, ande, rikt):
            if o is None:                                        # fri ände
                return ande + rikt * 50.0
            if w["ute"] is not None and o["ute"] is not None:    # hörn mellan ytterväggar: startjärnens linjer möts
                return o["ytterliv"] - o["ute"] * K.X_START + rikt * 100.0
            return o["c"] + rikt * (K.T_KARNA / 2 + 50.0)
        lo, hi = grans(w0, w0["mot_a"], w0["a"], 1), grans(w1, w1["mot_b"], w1["b"], -1)
        typ = "ute" if w0["ute"] is not None else "inne"
        for t in R4._fordela(lo, hi, START["s"]):
            ut.append(((t, q) if w0["ax"] == "h" else (q, t), typ, w0["namn"]))
    return ut


def lager_armering(v):
    with v.lager("armering"):
        natsymbol(v)
        for pl in balkjarn():
            v.linje(pl, "uk_tunn")
        for r in ROR:
            lines, _ = plintjarn(r)
            for l in lines:
                v.linje(l, "uk_tunn")
        for l in diagonaljarn():
            v.linje(l, "ok")
        for (x, y), typ, _ in startjarn():
            v.cirkel(x, y, 0.38, fyll="svart" if typ == "ute" else "#b5463a", stil=None)


def lager_armtext(v):
    s = v.s
    with v.lager("armtext"):
        q = (ytterliv("V14") - 60.0, 9500.0)
        v.hanvisning(q, (12200.0, 9850.0), "kantbalk: 2 Ø10 uk + 2 Ø10 ök,\nU-byglar Ø6 s600",
                     bubbla=POS["balk_uk"], a="rm", sz=6.4)
        r = K.ROR_D["P5"]
        p = PLINTAR["P5"]
        v.hanvisning((p.bounds[0] + 30, r["mitt"][1] + 300), (10700.0, 7300.0), "plint: Ø8 s150 uk, båda riktningarna",
                     bubbla=POS["plint"], a="rm", sz=6.4)
        dj = diagonaljarn()[0]
        m = ((dj[0][0] + dj[1][0]) / 2, (dj[0][1] + dj[1][1]) / 2)
        v.hanvisning(m, (6200.0, 2900.0), "2 Ø10 L = 1 200 diagonalt, överkant, inåtgående hörn", bubbla=POS["diag"],
                     a="lm", sz=6.4)
        st = [p_ for p_, typ, n in startjarn() if n == "V21"]
        v.hanvisning(st[len(st) // 2], (1300.0, 6900.0), "startjärn Ø10 s300, ytterväggarna", bubbla=POS["start_ute"],
                     a="lm", sz=6.4)
        st = [p_ for p_, typ, n in startjarn() if n == "V15"]
        v.hanvisning(st[len(st) // 2], (10200.0, 9330.0), "startjärn Ø10 s300, innerväggarna",
                     bubbla=POS["start_inne"], a="lm", sz=6.4)


# ---------------------------------------------------------------- sektioner (R-05.3)
def grund(v, xa, xb, balkar, s300=False):
    """Bottenplattan i sektion (R-04:s funktion) med L-elementets yttre ben vid x = 0 om en balk börjar där."""
    R4.bottenplatta_snitt(v, xa, xb, balkar)


def sektion_a():
    """A–A: kantbalken i L-element (V14) med väggens start. x = 0 i ytterlivet, inåt positivt. 1:10"""
    s = 10.0
    v = Vy(x=24, y=12, w=120, h=96, skala=s, X0=-260.0, Y1=520.0)
    with v.lager("mark"):
        v.rekt(-240, -HP - EPS - 120, 0, -HB - TF, fyll="grus", stil=None)
        v.rekt(-K.T_FOT, -HB, 0, 0, fyll="eps2", stil="tunn")                 # L-elementets yttre ben
        v.rekt(-K.T_FOT, -HB - TF, 0, -HB, fyll="eps2", stil="tunn")
    R4.bottenplatta_snitt(v, 0.0, 850.0, [(0.0, BB)], kant=True)
    with v.lager("bottenplatta"):
        v.linje([(0, -HB - TF), (0, 0)], "normal")
        v.brott((850, -HP - EPS - 40), (850, 40), "tunn")
    R4.kub_snitt(v, 0.0, 0.0, 420.0, gips=True)
    with v.lager("vagg"):
        v.brott((-40, 420), (K.T_VAGG + 60, 420), "tunn")
    with v.lager("armering"):
        v.linje([(K.X_START + FOT_START, R4.Z_BALK_UK), (K.X_START, R4.Z_BALK_UK), (K.X_START, 400)], "uk")
    with v.lager("matt"):
        kedja(v, [-K.T_FOT, 0.0, BB], -HB - TF - 4.0 * s, [-HB - TF] * 3, sz=5.8)
        kedja(v, [-HB - TF, -HB, -HP, 0.0], -K.T_FOT - 6.0 * s, [-K.T_FOT] * 4, sz=5.8, ax="y")
        kedja(v, [-HB, -HB + C_UK], 600.0, [BB] * 2, sz=5.4, ax="y")
        kedja(v, [0.0, K.X_START], -HB + 120, [-HB + 46] * 2, sz=5.4)
    lst = [(f"startjärn Ø{START['d']} s{START['s']}, {START['upp']} upp, foten {sv(FOT_START)} in i balken",
            (K.X_START, 250), POS["start_ute"]),
           ("2 Ø10 i överkant", (390, -41), POS["balk_ok"]),
           (f"Ø{NAT[0]} s{NAT[1]} i överkant, täckskikt {C_OK:.0f}", (800, -28), POS["ok_x"]),
           ("U-byglar Ø6 s600", (405, -110), POS["bygel"]),
           (f"Ø{NAT[0]} s{NAT[1]} i underkant, täckskikt {C_UK:.0f}", (800, -HP + C_UK + 3), POS["uk_x"]),
           ("2 Ø10 i underkant", (390, -HB + 41), POS["balk_uk"]),
           ("L-element L300: ben 100 under väggens cellplast, fot 100 S300", (275, -HB - 50), None),
           (f"cellplast S100, {sv(EPS)} i två skikt, plastfolie emellan", (800, -HP - EPS / 4), None),
           ("makadam på sprängt berg", (600, -HP - EPS - 60), None)]
    etiketter(v, lst, 1000.0, 480.0, 4.4, sz=6.0)
    with v.lager("rubrik"):
        v.rubrik(-250, -HP - EPS - 120 - 7.0 * s, "SEKTION A–A  Kantbalk i L-element (V14)", skala=10, sz=9)
    return v


def sektion_b():
    """B–B: balk under innervägg (V15). x = 0 i väggens mitt. 1:20"""
    s = 20.0
    v = Vy(x=226, y=12, w=100, h=96, skala=s, X0=-560.0, Y1=900.0)
    R4.bottenplatta_snitt(v, -540.0, 540.0, [(-BB / 2, BB / 2)])
    with v.lager("bottenplatta"):
        for x in (-540, 540):
            v.brott((x, -HP - EPS - 40), (x, 40), "tunn")
        v.rekt(-540, -HP - EPS - 120, 540, -HP - EPS, fyll="grus", stil=None)
    R4.kub_snitt(v, -K.T_VAGG / 2, 0.0, 420.0, gips=False)
    with v.lager("vagg"):
        v.brott((-K.T_VAGG / 2 - 40, 420), (K.T_VAGG / 2 + 40, 420), "tunn")
    with v.lager("armering"):
        v.linje([(0.0, R4.Z_BALK_UK), (0.0, 400)], "uk")                     # startjärn, foten 330 längs balken
        v.cirkel(0.0, R4.Z_BALK_UK, 5, fyll="#2c4a6e", stil=None, modell=True)
    with v.lager("matt"):
        kedja(v, [-BB / 2, BB / 2], -HB - TF - 4.0 * s, [-HB - TF] * 2, sz=5.8)
    lst = [(f"startjärn Ø{START['d']} s{START['s']} i kärnans mitt,\n{START['upp']} upp, foten {sv(FOT_START)} "
            "längs balken", (0, 250), POS["start_inne"]),
           ("2 Ø10 i överkant", (165, -41), POS["balk_ok"]),
           ("U-byglar Ø6 s600", (180, -110), POS["bygel"]),
           ("2 Ø10 i underkant", (165, -HB + 41), POS["balk_uk"]),
           ("cellplast S300, 100 under balken", (100, -HB - 50), None)]
    etiketter(v, lst, 600.0, 800.0, 6.0, sz=6.0)
    with v.lager("rubrik"):
        v.rubrik(-540, -HP - EPS - 120 - 7.0 * s, "SEKTION B–B  Balk under innervägg (V15)", skala=20, sz=9)
    return v


def sektion_c():
    """C–C: plint under rör (P18) med fotplåten. x = 0 i plintens mitt. 1:20"""
    s = 20.0
    b = K.PLINT["P18"]
    v = Vy(x=24, y=122, w=150, h=80, skala=s, X0=-b / 2 - 300.0, Y1=700.0)
    R4.bottenplatta_snitt(v, -b / 2 - 250, b / 2 + 250, [(-b / 2, b / 2)], balkarm=False)
    with v.lager("bottenplatta"):
        for x in (-b / 2 - 250, b / 2 + 250):
            v.brott((x, -HP - EPS - 40), (x, 40), "tunn")
        v.rekt(-b / 2 - 250, -HP - EPS - 120, b / 2 + 250, -HP - EPS, fyll="grus", stil=None)
    with v.lager("bottenplatta_arm"):
        # plintens Ø8 s150 i underkant, båda riktningarna
        for t in R4._fordela(0.0, b - 60, PLINT_ARM[1]):
            v.cirkel(-b / 2 + 30 + t, -HB + C_UK + 4, 4, fyll="#2c4a6e", stil=None, modell=True)
        v.linje([(-b / 2 + 30, -HB + C_UK + 12), (b / 2 - 30, -HB + C_UK + 12)], "uk_tunn")
    with v.lager("stal"):
        bx, by, tf = K.FOTPLAT[1]
        v.rekt(-bx / 2, -tf, bx / 2, 0, fyll="stal", stil=None)
        for x in (-60.0, 60.0):
            v.linje([(x, -tf), (x, -tf - K.SVETSBULT[1] + 8)], "stal")
            v.rekt(x - 12, -tf - K.SVETSBULT[1], x + 12, -tf - K.SVETSBULT[1] + 8, fyll="stal", stil=None)
        v.rekt(-K.PLAT / 2, 0, K.PLAT / 2, 420, fyll="#9aa0a8", stil="tunn")
        v.rekt(-K.PLAT / 2 + 4, 0, K.PLAT / 2 - 4, 420, fyll="vit", stil=None)
        v.brott((-80, 420), (80, 420), "tunn")
    with v.lager("matt"):
        kedja(v, [-b / 2, b / 2], -HB - TF - 4.0 * s, [-HB - TF] * 2, sz=5.8)
    lst = [("rör VKR 80×80×4 (R-04.5)", (K.PLAT / 2, 300), None),
           ("fotplåt 200 × 200 × 15 S355, kant i kant med plintens överkant", (bx / 2 - 20, -8), None),
           (f"4 svetsbultar Ø{K.SVETSBULT[0]:.0f}, L = {K.SVETSBULT[1]:.0f}", (60, -60), None),
           (f"plint: Ø{PLINT_ARM[0]} s{PLINT_ARM[1]} i underkant, båda riktningarna", (b / 2 - 100, -HB + 34),
            POS["plint"]),
           ("cellplast S300, 100 under plinten", (b / 2 - 100, -HB - 50), None)]
    etiketter(v, lst, b / 2 + 330, 650.0, 4.8, sz=6.0)
    with v.lager("rubrik"):
        v.rubrik(-b / 2 - 290, -HP - EPS - 120 - 7.0 * s, f"SEKTION C–C  Plint under rör (P18, {sv(b)})",
                 skala=20, sz=9)
    return v


def detalj_horn():
    """D: yttre hörn i plan (V1/V14): L-elementen med ytterkanten i väggarnas ytterliv, betongen 100 mm innanför,
    kantbalken och väggen ovanpå (streckad). x och y i K-05:s koordinater. 1:20"""
    s = 20.0
    x, y = ytterliv("V14"), ytterliv("V1")
    v = Vy(x=200, y=122, w=126, h=80, skala=s, X0=x - 1450.0, Y1=y + 280.0)
    vy = box(x - 1300, y - 1300, x, y)
    with v.lager("platta"):
        for g in K.ytor(KALLARE.intersection(vy)):
            v.polygon(list(g.exterior.coords), fyll="eps2", stil=None)
        for g in K.ytor(BETONG.intersection(vy)):
            v.polygon(list(g.exterior.coords), fyll="betong", stil="tunn")
        for p in K.ytor(KANT.intersection(vy)):
            v.polygon(list(p.exterior.coords), fyll="zon", stil="tunn")
        v.linje([(x - 1300, y), (x, y), (x, y - 1300)], "kontur")
        v.brott((x - 1300, y - K.B_L - 60), (x - 1300, y + 60), "tunn")
        v.brott((x - K.B_L - 60, y - 1300), (x + 60, y - 1300), "tunn")
    with v.lager("vaggar"):
        for g in K.ytor(K.HEL.intersection(vy)):
            v.linje(list(g.exterior.coords), "dold")
        for g in K.ytor(K.KARNA.intersection(vy)):
            v.linje(list(g.exterior.coords), "dold")
    with v.lager("matt"):
        kedja(v, [x - K.B_L, x - K.L_BEN, x], y + 3.0 * s, [y] * 3, sz=5.8)
        kedja(v, [y - K.B_L, y - K.L_BEN, y], x + 3.0 * s, [x] * 3, sz=5.8, ax="y")
        kedja(v, [x - K.T_VAGG, x - K.T_EPS - K.T_KARNA, x - K.T_EPS, x], y - 900.0, [y - 900.0] * 4, sz=5.4)
    with v.lager("text"):
        v.hanvisning((x - 50, y - 700), (x - 1250, y - 1000), "L-element, ytterkant i väggens ytterliv", a="lm",
                     sz=6.0)
        v.hanvisning((x - 300, y - 1150), (x - 1250, y - 1150), f"kantbalk {sv(BB)} på L-elementets fot", a="lm",
                     sz=6.0)
        v.hanvisning((x - 175, y - 450), (x - 1250, y - 850), "väggens kärna (streckad, R-04)", a="lm", sz=6.0)
        v.rubrik(x - 1430, y - 1300 - 6.0 * s, "DETALJ D  Yttre hörn i plan (V1/V14)", skala=20, sz=9)
        v.text(x - 1430, y - 1300 - 6.0 * s - 7.0 * s, "Samma vid alla hörn: L-elementets ytterkant i väggens ytterliv.",
               a="lb", sz=6.2, col="gra")
    return v


# ---------------------------------------------------------------- förteckningar
def stalforteckning():
    rader, tot = [], {}

    def rad(pos, d, form, s_, n, L, m, anm):
        kg = m * VIKT[d]
        tot[d] = tot.get(d, 0.0) + kg
        rader.append([str(pos), f"Ø{d}", form, s_, str(n), L, sv(m, 0), sv(kg, 0), anm])
    yta = BETONG.buffer(-30.0, join_style=2)
    minx, miny, maxx, maxy = BETONG.bounds

    def nat(rikt):
        n, tl = 0, 0.0
        sc = NAT[1]
        rng = ([miny + 30 + sc / 2 + k * sc for k in range(int((maxy - miny) / sc) + 1)] if rikt == "x" else
               [minx + 30 + sc / 2 + k * sc for k in range(int((maxx - minx) / sc) + 1)])
        for t in rng:
            ln = LineString([(minx - 1, t), (maxx + 1, t)]) if rikt == "x" else LineString([(t, miny - 1), (t, maxy + 1)])
            gg = ln.intersection(yta)
            for seg in getattr(gg, "geoms", [gg]):
                if seg.length > 100:
                    n += 1
                    tl += seg.length + math.floor(seg.length / 12000) * SKARV[NAT[0]]   # en skarv per 12 m stång
        return n, tl / 1000
    for pos, rikt, lag in ((POS["uk_x"], "x", "UK"), (POS["uk_y"], "y", "UK"), (POS["ok_x"], "x", "ÖK"),
                           (POS["ok_y"], "y", "ÖK")):
        n, tl = nat(rikt)
        rad(pos, NAT[0], "rak", f"s{NAT[1]}", n, "var.", tl, f"{lag} {rikt}-led, hela plattan")
    Lb = 0.0
    for pl in balkjarn():
        L = sum(math.dist(a, b) for a, b in zip(pl[:-1], pl[1:]))
        sluten = math.dist(pl[0], pl[-1]) < 1
        Lb += L + (math.ceil(L / 12000) if sluten else math.floor(L / 12000)) * SKARV[10]   # skarv per 12 m stång
    rad(POS["balk_uk"], 10, "rak", "–", "2 per balk", "var.", Lb / 1000, "balkar, underkant")
    rad(POS["balk_ok"], 10, "rak", "–", "2 per balk", "var.", Lb / 1000, "balkar, överkant")
    Lbalk = (KANT.area + INRE.area) / BB
    nb = int(Lbalk / BALK_ARM["bygel"][1]) + 1
    ben = -25 - (R4.Z_BYGEL - 3)                    # byglarnas ben, utvändigt: från botten till överkantens täckskikt
    bas = BB - 2 * K.BYGEL_SIDA + 6                 # utvändigt, benen 33 mm från balkens sidor (centrum)
    Lu = 50 * round((2 * ben + bas) / 50)
    rad(POS["bygel"], 6, f"U {sv(ben)}+{sv(bas)}+{sv(ben)}", f"s{BALK_ARM['bygel'][1]}", nb, sv(Lu),
        nb * Lu / 1000, "byglar i balkarna")
    npl, mpl = 0, 0.0
    for r in ROR:
        lines, n = plintjarn(r)
        npl += len(lines); mpl += sum(math.dist(*l) for l in lines)
    rad(POS["plint"], PLINT_ARM[0], "rak", f"s{PLINT_ARM[1]}", npl, "var.", mpl / 1000, "plintar, underkant")
    nd = len(diagonaljarn())
    rad(POS["diag"], DIAG["d"], "rak", "–", nd, sv(DIAG["L"]), nd * DIAG["L"] / 1000, "inåtgående hörn, ÖK")
    st = startjarn()
    Ls = UPP_START + FOT_START
    n_ute = sum(1 for _, t, _ in st if t == "ute")
    n_in = sum(1 for _, t, _ in st if t == "inne")
    rad(POS["start_ute"], START["d"], f"L {sv(UPP_START)}+{sv(FOT_START)}", f"s{START['s']}", n_ute, sv(Ls),
        n_ute * Ls / 1000, "ytterväggarna, utsidan")
    rad(POS["start_inne"], START["d"], f"L {sv(UPP_START)}+{sv(FOT_START)}", f"s{START['s']}", n_in,
        sv(Ls), n_in * Ls / 1000, "innerväggarna, mitt")
    rader.append(["", "", "", "", "", "", "Summa", sv(sum(tot.values()), 0),
                  " + ".join(f"Ø{d}: {sv(k, 0)}" for d, k in sorted(tot.items()))])
    return dict(typ="tabell", kolumner=["Pos", "Ø", "Form", "s", "Antal", "L (mm)", "Total (m)", "Vikt (kg)", "Anm"],
                bredd=(0, 0, 0, 0, 0, 0, 0, 0, 1), rader=rader, just=["l", "l", "l", "l", "r", "r", "r", "r", "l"],
                sz=6.2)


def cellplastlista():
    """Cellplast under bottenplattan: S100 under plattan (m², två skikt), S300 under innerbalkarna och plintarna (m²)
    och L-element längs kanten (m), med fot av S300."""
    a_100 = (BETONG.area - TJOCK.area) / 1e6
    a_200 = unary_union([INRE] + list(PLINTAR.values())).difference(KANT).area / 1e6
    L_l = KALLARE.exterior.length / 1000
    rader = [["S100", "2 × 100 mm, plastfolie emellan", sv(a_100, 1) + " m²", "under plattan"],
             ["S300", "100 mm", sv(a_200, 1) + " m²", "under innerbalkarna och plintarna"],
             ["L-element", "L300, 550 × 300, ben 100, fot S300", sv(L_l, 1) + " m",
              "längs hela kanten, ytterkant i väggarnas ytterliv"]]
    return dict(typ="tabell", kolumner=["", "Utförande", "Mängd", "Anm"], bredd=(0, 1, 0, 1), rader=rader,
                just=["l", "l", "r", "l"], sz=6.2)


def plinttabell():
    rader = []
    for r in ROR:
        mx, my = r["mitt"]
        rader.append([r["namn"], sv(K.PLINT[r["namn"]]), sv(mx), sv(my),
                      "två rör, fotplåt 280 × 200 alternativt 2 fotplåtar 140 × 200" if r["n"] == 2 else ""])
    return dict(typ="tabell", kolumner=["Plint", "Sida", "x", "y", ""], bredd=(0, 0, 0, 0, 1), rader=rader,
                just=["l", "r", "r", "r", "l"], sz=6.2)


# ================================================================== 4. blad
BLADEN = [
    ("R-05.1", ["Bottenplatta", "Plan, balkar, plintar och cellplast"], "1:50",
     "R-05.1 Bottenplatta, plan, balkar och plintar"),
    ("R-05.2", ["Bottenplatta", "Armering"], "1:50", "R-05.2 Bottenplatta, armering"),
    ("R-05.3", ["Bottenplatta", "Sektioner, detaljer och förteckningar"], "1:10, 1:20, 1:50",
     "R-05.3 Bottenplatta, sektioner och förteckningar"),
]


def hd(nr):
    b = next(x for x in BLADEN if x[0] == nr)
    return huvud(nr, b[1], b[2], UNDERLAG, DATUM, REV)


def planvy():
    return Vy(x=PLAN["x"], y=PLAN["y"], w=PLAN["w"], h=PLAN["h"], skala=50, X0=PLAN["X0"], Y1=PLAN["Y1"])


def anvisningar():
    return [
        f"Bottenplatta L300 (K-06): {sv(HP)} mm betong C25/30 på {sv(EPS)} mm cellplast S100 i två skikt med "
        f"åldringsbeständig plastfolie emellan. Kantbalkar {sv(BB)} × {sv(HB)} i L-element L300 med fot av S300 längs "
        f"hela kanten; balkar under innerväggarna {sv(BB)} × {sv(HB)} och plintar under rören, lika höga, på 100 mm "
        "S300. Bara två kvaliteter: S100 under plattan och S300 under balkar och plintar. Samma uppbyggnad i hela "
        "källaren.",
        f"L-elementens ytterkant ligger i väggarnas ytterliv (R-04.1), som planens mått går till. Betongen börjar "
        f"innanför L-elementets yttre ben, {sv(K.L_BEN)} mm, i kärnans yttre yta: väggens yttre cellplast står på benet "
        "och kärnan på kantbalken (detalj D, sektion A). Koordinater i mm enligt K-05, höjder från bottenplattans "
        "överkant.",
        "Plintarna är kvadratiska och centrerade under rörets mitt (P7: mitt mellan de två rören). Sida och mitt enligt "
        "tabellen; mått från väggarna till rörens mitt på R-04.1.",
    ]


def blad_plan():
    v = planvy()
    lager_platta(v)
    lager_vaggar_streckade(v)
    lager_ror(v)
    lager_yttermatt(v)
    lager_balkmatt(v)
    lager_snitt(v)
    R4.lager_origo(v)
    lager_rubrik(v, "PLAN – BALKAR, PLINTAR OCH CELLPLAST")
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=6.8, rader=anvisningar() + [
            "Underlag: makadam på sprängt berg, avjämnat och packat. Dränledningen läggs runt huset innan cellplasten "
            "läggs (K-06).",
            "Armering R-05.2, sektioner och förteckningar R-05.3. Fotplåtar och rör R-04.5."]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="yta", fyll="zon", stil="tunn", text=f"kantbalk, balk och plint, {sv(HB)} hög, på 100 S300"),
            dict(form="yta", fyll="betong", stil="tunn", text=f"platta {sv(HP)} på {sv(EPS)} S100"),
            dict(form="yta", fyll="eps2", stil="tunn", text="L-elementets yttre ben, 100, i väggarnas ytterliv"),
            dict(form="linje", stil="dold", text="väggarna (R-04)"),
            dict(form="ruta", fyll="stal", text="fotplåt (R-04.5)")]),
        dict(typ="rubrik", text="Plintar (sida och mitt)"),
        plinttabell(),
        dict(typ="rubrik", text=f"Ritningsförteckning {NR}"),
        dict(typ="tabell", kolumner=["Ritning", "Innehåll", "Skala"], bredd=(0, 1, 0),
             rader=[[nr, ", ".join(t[1:]), sk] for nr, t, sk, _ in BLADEN], just=["l", "l", "l"], sz=6.4),
    ]
    return Blad(hd("R-05.1"), REVISIONER, kol, [v])


def blad_armering():
    v = planvy()
    lager_platta(v, fyll_balk=False)
    lager_vaggar_streckade(v)
    lager_ror(v, namn=False)
    lager_armering(v)
    lager_armtext(v)
    R4.lager_origo(v)
    lager_rubrik(v, "PLAN – ARMERING")
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=6.8, rader=[
            f"Betong C25/30, armering B500B. Täckande skikt: {C_UK:.0f} mm mot cellplasten (distanser) och {C_OK:.0f} mm i överkant.",
            f"Nät Ø{NAT[0]} s{NAT[1]} i under- och överkant i hela plattan ({POS['uk_x']}–{POS['ok_y']}), också genom "
            f"balkarna och plintarna. Golvvärmeslangarna fästs i underkantsnätet. Skarvlängd Ø6 {SKARV[6]}.",
            f"Kantbalkar och balkar under innerväggarna: 2 Ø10 i underkant ({POS['balk_uk']}) på byglarna och 2 Ø10 i "
            f"överkant ({POS['balk_ok']}) under överkantsnätet, U-byglar Ø6 s600 ({POS['bygel']}). Skarvlängd Ø10 "
            f"{SKARV[10]}; i hörnen bockas järnen eller skarvas med vinkeljärn. Innerbalkarnas järn förs in i "
            "kantbalken och i den korsande balken.",
            f"Plintar: Ø{PLINT_ARM[0]} s{PLINT_ARM[1]} i underkant, båda riktningarna ({POS['plint']}). Fotplåten "
            "gjuts in kant i kant med plintens överkant (R-04.5); näten läggs fritt från svetsbultarna.",
            f"Inåtgående hörn: 2 Ø10, L = 1 200, i överkant diagonalt, 150 och 250 mm från hörnet ({POS['diag']}).",
            f"Startjärn Ø10 s300, {sv(START['upp'])} upp och {sv(START['ned'])} i balken: den lodräta delen och "
            f"foten, {sv(FOT_START)}, på byglarna. Ytterväggarna på utsidan ({POS['start_ute']}, svarta), med foten "
            "vinkelrätt in i kantbalken (Sundolitt), också under bröstningarna vid F1–F3; innerväggarna i kärnans mitt "
            f"({POS['start_inne']}, röda), med foten längs balken. Väggarnas armering: R-04.",
            "Ytan under väggarna ruggas före väggarnas gjutning (K-06)."]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="linje", stil="uk", text="armering i underkant / balkjärn"),
            dict(form="linje", stil="ok", text="armering i överkant (diagonaljärn)"),
            dict(form="punkt", r=0.38, text="startjärn, ytterväggarna"),
            dict(form="punkt", r=0.38, fyll="#b5463a", text="startjärn, innerväggarna"),
            dict(form="bubbla", txt="31", text="positionsnummer (stålförteckning R-05.3)")]),
    ]
    return Blad(hd("R-05.2"), REVISIONER, kol, [v])


def blad_sektioner():
    vyer = [sektion_a(), sektion_b(), sektion_c(), detalj_horn()]
    block = [dict(x=24, y=212, w=230, innehall=[
        dict(typ="rubrik", text="Stålförteckning, B500B"), stalforteckning()])]
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=6.8, rader=[
            "Utförande (K-06): spräng och avjämna berget och lägg makadam. Lägg dränledningen. Lägg L-elementen (fot "
            "S300) med ytterkanten i väggarnas ytterliv, S300 under innerbalkarna och plintarna och S100 under plattan "
            "i två skikt med plastfolie emellan. Skär ur cellplasten för balkar och plintar.",
            "Armera, lägg golvvärmeslangarna och fixera fotplåtarna i läge och höjd. Gjut bottenplattan med balkar och "
            "plintar i en gjutning; fotplåtarna gjuts in kant i kant med plintarnas överkant. Rugga ytan under "
            "väggarna.",
            "Kontrollera före gjutning: armeringens läge och täckskikt (distanser), plintarnas läge och storlek, "
            "fotplåtarnas läge och höjd (±5 mm), startjärnen.",
            "Plattan behöver inga fogar; golvbeläggning och tätskikt ska tåla krympsprickor (K-06).",
            "Plan R-05.1, armering R-05.2."]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="yta", fyll="betong", stil="tunn", text="betong C25/30"),
            dict(form="yta", fyll="eps", stil="tunn", text="cellplast S100"),
            dict(form="yta", fyll="eps2", stil="tunn", text="L-element (fot S300), S300 under balkar och plintar"),
            dict(form="yta", fyll="karna", stil="tunn", text="väggens betongkärna (R-04)"),
            dict(form="linje", stil="uk", text="armering")]),
        dict(typ="rubrik", text="Cellplast"),
        cellplastlista(),
    ]
    return Blad(hd("R-05.3"), REVISIONER, kol, vyer, block)


# ================================================================== 5. main
SERIE = "R-05 Bottenplatta"


def main(dolj=()):
    os.makedirs(UT, exist_ok=True)
    bladmapp = os.path.join(HERE, "blad")
    os.makedirs(bladmapp, exist_ok=True)
    fn = {"R-05.1": blad_plan, "R-05.2": blad_armering, "R-05.3": blad_sektioner}
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
