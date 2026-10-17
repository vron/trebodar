"""
R-04 Konstruktionsritning källarstomme (F-01), A3 med ../ritningsmall:

    R-04.1  Plan, mått och rör                               1:50
    R-04.2  Väggarnas armering, plan                          1:50
    R-04.3  Väggar med öppningar och V3, elevationer          1:50
    R-04.4  Sektioner och detaljer                            1:10, 1:20
    R-04.5  Rör och stålförteckning                           1:5, 1:10

Källarväggar av Sundolitt Kub 350-150 (K-06) och stålrör VKR 80×80×4 (K-05). Geometrin ur kallare.py (K-05:s
geometri.json och K-06:s indata). Allt ritas i K-05:s koordinater (mm, origo i skärningen mellan mellanbjälklagets
kanter x = 0 och y = 0, y uppåt); höjder z från bottenplattans överkant.

Filen är uppdelad i:
    1. Underlag           ur kallare.py
    2. Placeringar        var måttkedjor, etiketter, snitt och tabeller står (verkliga koordinater, mm) – ändra här
    3. Lager              en funktion per lager
    4. Blad               vyer, högerkolumn och ritningshuvud
    5. main               skriver R-04.x.json och ritningar/R-04 Källarstomme.pdf

    python beräkningar/R-04/ritningar.py
"""
import json
import math
import os
import sys

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kallare as K  # noqa: E402
from ritning import Vy, Blad, huvud, sv, svm, PROJEKT  # noqa: E402

BER, ROT = K.BER, K.ROT
UT = os.path.join(ROT, "ritningar")

# ================================================================== 1. underlag
NR = "R-04"
REV, DATUM = "A", "2026-10-16"


def revision(nr):
    """Beräkningens revision ur dess rapport/projekt.json, t.ex. "K-06 rev A"."""
    p = json.load(open(os.path.join(BER, nr, "rapport", "projekt.json"), encoding="utf-8"))
    return f"{nr} rev {p['revision']}"


UNDERLAG = f"{revision('K-05')}, {revision('K-06')}"
REVISIONER = [dict(rev=REV, avser="Första utgåvan", datum=DATUM, sign=PROJEKT["signatur"])]

V, VAGG, OPPN, ROR = K.VAGGAR, K.VAGG, K.OPPNINGAR, K.ROR
H, HMB = K.H_VAGG, K.H_MB
VIKT = {6: 0.222, 8: 0.395, 10: 0.617, 12: 0.888}     # kg/m


def ytterliv(n):
    return VAGG[n]["ytterliv"]


def innerliv(n):
    """Innerväggens eller ytterväggens insida mot källaren; för innerväggar den sida som anges med tecknet."""
    return VAGG[n]["innerliv"]


def liv(n, sida):
    """Väggens yta: sida +1 eller −1 från centrumlinjen."""
    return VAGG[n]["c"] + sida * K.T_VAGG / 2


# ================================================================== 2. placeringar (verkliga koordinater, mm)
PLAN = dict(x=20.0, y=10.0, w=306, h=277, X0=-580.0, Y1=13265.0)     # planvyerna 1:50: hela ritytan
PLAC = dict(
    rubrik=(-200.0, 2500.0), skalstock=(-200.0, 1550.0),
    # rörens lägen: måttkedjor (riktning, kedjans läge, [(mått, hjälplinjens början)]) från väggarnas insidor eller
    # ett rör till rörens mitt
    rorkedjor=[
        ("y", 12230.0, [(VAGG["V9"]["innerliv"], 12230.0), (2545.0, 11670.0), (4685.0, 11670.0), (6625.0, 11670.0),
                        (8625.0, 11670.0), (10625.0, 11670.0), (VAGG["V1"]["innerliv"], 12230.0)]),
        ("x", 3200.0, [(11670.0, 2545.0), (VAGG["V14"]["innerliv"], 3200.0)]),
        ("y", 8900.0, [(VAGG["V13"]["innerliv"], 8900.0), (2190.0, 9070.0), (3590.0, 9070.0), (4990.0, 9070.0)]),
        ("x", 4400.0, [(liv("V18", 1), VAGG["V7"]["innerliv"]), (5770.0, 4990.0), (6870.0, 4990.0),
                       (7970.0, 4990.0), (9070.0, 4990.0)]),
        ("x", 2700.0, [(liv("V18", 1), 2700.0), (6990.0, 2190.0), (9070.0, 2190.0)]),
        ("x", 6350.0, [(VAGG["V21"]["innerliv"], 6350.0), (1931.0, 5820.0), (3231.0, 5820.0), (4531.0, 5820.0)]),
        ("y", 1300.0, [(VAGG["V7"]["innerliv"], 1300.0), (5820.0, 1931.0)]),
        ("x", 8250.0, [(VAGG["V21"]["innerliv"], 8250.0), (2870.0, 7675.0)]),
        ("y", 2350.0, [(7675.0, 2870.0), (VAGG["V3"]["innerliv"], 2350.0)]),
        ("x", 6400.0, [(6870.0, 4990.0), (7420.0, 5950.0)]),
        ("y", 7350.0, [(5950.0, 7420.0), (liv("V5", -1), 7350.0)]),
        ("x", 6550.0, [(9070.0, 4990.0), (9470.0, 5950.0), (9550.0, 5950.0)]),
        ("y", 9950.0, [(5950.0, 9550.0), (liv("V6", -1), 9800.0)]),
        ("x", 9700.0, [(VAGG["V20"]["innerliv"], 9700.0), (7101.659, 9154.763)]),
        ("y", 6600.0, [(9154.763, 7101.659), (VAGG["V2"]["innerliv"], 6600.0)]),
    ],
    tabell_ror=(-200.0, 12300.0),
    snitt=dict(A=((6000.0, 10350.0), (6000.0, 11450.0), -1), B=((9150.0, 8700.0), (10150.0, 8700.0), -1)),
)


# ================================================================== 3. lager
def lager_vaggar(v, z_snitt=1600.0, namn=True):
    """Väggarna i plan, snitt z_snitt över bottenplattan: cellplast och betongkärna; under öppningar med bröstning
    under snittet ritas bröstningen sedd uppifrån."""
    with v.lager("vaggar"):
        for g in getattr(K.HEL, "geoms", [K.HEL]):
            v.polygon(list(g.exterior.coords), fyll="eps", stil="normal")
            for hh in g.interiors:
                v.polygon(list(hh.coords), fyll="vit", stil="normal")
        for g in getattr(K.KARNA, "geoms", [K.KARNA]):
            v.polygon(list(g.exterior.coords), fyll="karna", stil="tunn")
        for o in OPPN:
            if 0 < o["z0"] < z_snitt:                      # bröstningen syns under snittet
                c = o["c"]
                x0, x1 = o["x0"], o["x1"]
                v.rekt(x0, c - K.T_VAGG / 2, x1, c + K.T_VAGG / 2, fyll="vit", stil=None)
                v.linje([(x0, c - K.T_VAGG / 2), (x1, c - K.T_VAGG / 2)], "tunn")
                v.linje([(x0, c + K.T_VAGG / 2), (x1, c + K.T_VAGG / 2)], "tunn")
                v.linje([(x0, c - K.T_KARNA / 2), (x1, c - K.T_KARNA / 2)], "fin")
                v.linje([(x0, c + K.T_KARNA / 2), (x1, c + K.T_KARNA / 2)], "fin")
    if namn:
        with v.lager("vaggnamn"):
            for w in V:
                m = (w["a"] + w["b"]) / 2
                c = w["c"]
                if namn == "bredvid":                # bredvid väggen, på rumssidan (armeringsplanen)
                    sida = -w["ute"] if w["ute"] else (-1 if w["ax"] == "h" else 1)
                    c = w["c"] + sida * (K.T_VAGG / 2 + 1.6 * v.s)
                if w["ax"] == "h":
                    v.text(m, c, w["namn"], a="cm", sz=5.8, col="gra", bg=True)
                else:
                    v.text(c, m, w["namn"], a="cm", sz=5.8, col="gra", rot=90, bg=True)


def lager_ror(v, namn=True, fotplat=False):
    with v.lager("ror"):
        for r in ROR:
            for x, y in r["ror"]:
                v.rekt(x - K.PLAT / 2, y - K.PLAT / 2, x + K.PLAT / 2, y + K.PLAT / 2, fyll="stal", stil=None)
            if fotplat:
                bx, by, _ = K.FOTPLAT[r["n"]]
                mx, my = r["mitt"]
                v.rekt(mx - bx / 2, my - by / 2, mx + bx / 2, my + by / 2, fyll=None, stil="dold")
        if namn:
            for r in ROR:
                mx, my = r["mitt"]
                dx, dy, a = PLAC_NAMN.get(r["namn"], (130.0, 130.0, "lb"))
                v.text(mx + dx, my + dy, r["namn"], a=a, sz=6.6, b=True, bg=True)


# rörnamnens placering (förskjutning från rörets mitt, ankare)
PLAC_NAMN = {"P7": (-130.0, 130.0, "rb"), "P6": (-130.0, 130.0, "rb"), "P14": (130.0, -130.0, "lt"),
             "P16": (130.0, 130.0, "lb"), "P10": (130.0, -130.0, "lt")}


def kedja(v, xs, Y, Yfran, texter=None, sz=6.2, ax="x", bg=False):
    """Måttkedja längs x (ax="x": linjen på höjden Y, hjälplinjer från (x, Yfran[i])) eller längs y (ax="y": linjen vid
    x = Y, hjälplinjer från (Yfran[i], y)). Text som inte ryms flyttas ut till sidan."""
    g, f = 1.0 * v.s, 1.5 * v.s
    P = (lambda t, u: (t, u)) if ax == "x" else (lambda t, u: (u, t))
    for t, u0 in zip(xs, Yfran):
        sg = 1 if Y > u0 else -1
        v.linje([P(t, u0 + sg * g), P(t, Y + sg * f)], "matt")
    v.linje([P(xs[0] - f, Y), P(xs[-1] + f, Y)], "matt")
    for t in xs:
        v._tick(P(t, Y), (1, 0) if ax == "x" else (0, 1), (0, 1) if ax == "x" else (-1, 0))
    n = len(xs) - 1
    for i, (a, b) in enumerate(zip(xs[:-1], xs[1:])):
        txt = texter[i] if texter else sv(b - a)
        if txt is None:
            continue
        bredd = len(txt) * 0.19 * sz + 0.8
        rot = 0 if ax == "x" else 90
        off = 0.8 * v.s
        # texten står normalt på den sida av måttlinjen som vetter mot det som mäts; ryms den inte, ställs den mitt
        # på måttet på andra sidan linjen (bort från det mätta)
        mot = (1 if Yfran[i] > Y else -1) if ax == "x" else (-1 if Yfran[i] < Y else 1)
        if bredd < abs(b - a) / v.s:
            pos, sida = (a + b) / 2, mot
        elif i in (0, n - 1):
            pos, sida = (a + b) / 2, -mot
        else:
            pos, sida = (a + b) / 2, mot
            off = 3.4 * v.s
        if ax == "x":
            v.text(pos, Y + sida * off, txt, a="cb" if sida > 0 else "ct", sz=sz, bg=bg)
        else:
            v.text(Y - sida * off, pos, txt, a="cb" if sida > 0 else "ct", sz=sz, rot=rot, bg=bg)


def lager_yttermatt(v, d1=4.0, d2=10.0):
    """Väggarnas ytterliv (= bottenplattans kant) runt källaren, med totalmått, och betongens öppningar. d1 och d2:
    måttkedjornas avstånd från ytterlivet (pappersmm)."""
    s = v.s
    with v.lager("matt"):
        # söder: fasaden med öppningarna F1–F3 och V8/V9 med D1
        f = [o for o in OPPN if o["c"] == VAGG["V10"]["c"]]
        xs = [ytterliv("V18")] + [p for o in f for p in (o["x0"], o["x1"])] + [ytterliv("V17")]
        kedja(v, xs, -30.0 - d1 * s, [-30.0] * len(xs))
        dorr = OPPN[3]
        xs2 = [ytterliv("V17"), dorr["x0"], dorr["x1"], ytterliv("V14")]
        kedja(v, xs2, ytterliv("V9") - d1 * s, [ytterliv("V9")] * len(xs2))
        # väster: V21 och lägena för V3, V2 och V1 (V7 och V3 från V21:s ytterliv)
        ys = [ytterliv("V7"), ytterliv("V3"), ytterliv("V2"), ytterliv("V1")]
        fr = [ytterliv("V21"), ytterliv("V21"), ytterliv("V20"), ytterliv("V16")]
        kedja(v, ys, -30.0 - d1 * s, fr, ax="y")
        # norr: V3, V2, V1 och totalmåttet i x
        xs3 = [-30.0, ytterliv("V20"), ytterliv("V16"), ytterliv("V14")]
        kedja(v, xs3, ytterliv("V1") + d1 * s, [ytterliv("V3"), ytterliv("V2"), ytterliv("V1"), ytterliv("V1")])
        kedja(v, [-30.0, ytterliv("V14")], ytterliv("V1") + d2 * s, [ytterliv("V1") + d1 * s] * 2)
        # öster: fasaden, V8/V9 och V1 med totalmåttet i y
        ys4 = [-30.0, ytterliv("V9"), ytterliv("V1")]
        kedja(v, ys4, ytterliv("V14") + d1 * s, [ytterliv("V17"), ytterliv("V14"), ytterliv("V14")], ax="y")
        kedja(v, [-30.0, ytterliv("V1")], ytterliv("V14") + d2 * s, [ytterliv("V14") + d1 * s] * 2, ax="y")
        # sydväst: V7 och V18
        kedja(v, [ytterliv("V21"), ytterliv("V18")], ytterliv("V7") - d1 * s, [ytterliv("V7")] * 2)
        kedja(v, [ytterliv("V10"), ytterliv("V7")], ytterliv("V18") - d1 * s, [ytterliv("V18")] * 2, ax="y")


def lager_innermatt(v):
    """Innerväggarna V4–V6 med dörröppningarna D2 och D3, och deras läge från V2."""
    s = v.s
    with v.lager("matt"):
        y = VAGG["V4"]["c"]
        xs = [liv("V19", 1), OPPN[4]["x0"], OPPN[4]["x1"], OPPN[5]["x0"], OPPN[5]["x1"], liv("V15", -1)]
        kedja(v, xs, y - K.T_VAGG / 2 - 3.5 * s, [y - K.T_VAGG / 2] * len(xs), bg=True)
        kedja(v, [liv("V5", 1), VAGG["V2"]["innerliv"]], 8750.0, [8750.0, 8750.0], ax="y")
        # väggens skikt (V21): cellplast 100, betongkärna 150, cellplast 100
        x0 = ytterliv("V21")
        v.hanvisning((x0 + K.T_VAGG / 2, 7100.0), (x0 + 900.0, 7350.0),
                     f"Kub {sv(K.T_VAGG)}: {sv(K.T_EPS)} + {sv(K.T_KARNA)} + {sv(K.T_EPS)}", a="lm", sz=5.8)


def lager_rorkedjor(v):
    """Rörens lägen: hjälplinjerna börjar i rörets mitt eller vid väggens yta."""
    with v.lager("rormatt"):
        for ax, lage, pts in PLAC["rorkedjor"]:
            kedja(v, [p for p, _ in pts], lage, [f for _, f in pts], sz=5.8, ax=ax, bg=True)


def lager_origo(v):
    with v.lager("origo"):
        L = 900
        v.linje([(0, 0), (L, 0)], "tunn"); v.pil((L + 150, 0), (1, 0), langd=2.2, bredd=1.0)
        v.linje([(0, 0), (0, L)], "tunn"); v.pil((0, L + 150), (0, 1), langd=2.2, bredd=1.0)
        v.ptext(L + 150, 0, 1.0, 0, "x", a="lm", sz=7.5, i=True)
        v.ptext(0, L + 150, 0, 1.0, "y", a="cb", sz=7.5, i=True)
        v.ptext(0, 0, 1.0, -1.0, "origo (0; 0)", a="lt", sz=6.4, col="gra")


def lager_rubrik(v, titel, skala=50):
    with v.lager("rubrik"):
        x, y = PLAC["rubrik"]
        v.rubrik(x, y, titel, skala=skala, sz=11)
        sx, sy = PLAC["skalstock"]
        v.skalstock(sx, sy, 4, 1)


def lager_oppningsnamn(v):
    with v.lager("oppningar"):
        for o in OPPN:
            m = (o["x0"] + o["x1"]) / 2
            ute = VAGG[o["vaggar"][0]]["ute"] or -1          # innerväggarna: namnet norr om väggen
            v.text(m, o["c"] - ute * (K.T_VAGG / 2 + 1.8 * v.s), o["namn"], a="cm", sz=7.0, b=True, col="ok",
                   bg=True)


def lager_snitt(v):
    with v.lager("snitt"):
        for namn, (p0, p1, sida) in PLAC["snitt"].items():
            v.snittpil(p0, p1, namn, sida=sida)


# ---------------------------------------------------------------- väggarnas armering (R-04.2)
POS = dict(hor=21, lod=22, horn=23, v3=24, t=25, opp_sida=26, opp_under=27, lod_under=28)


def tack(w, sida):
    """Täckskiktet till de vågräta järnen på väggens sida (+1/−1 från centrumlinjen): 30 mot jord, annars 25."""
    return K.C_UT if (w["ute"] is not None and sida == w["ute"]) else K.C_IN


def jarnlinje(w, sida):
    """Läget för de vågräta järnen vid väggens sida (koordinat vinkelrätt väggen)."""
    return w["c"] + sida * (K.T_KARNA / 2 - tack(w, sida) - 5.0)


def _kroppsida(o, w):
    """Den sida (+1/−1) av o:s centrumlinje där väggen w ligger (w ansluter mot o)."""
    m = (w["a"] + w["b"]) / 2
    return 1 if m > o["c"] else -1


def _partner(w, ande):
    """Den kolinjära vägg som fortsätter förbi w:s ände ande (tillsammans en genomgående vägg), annars None."""
    for x in V:
        if x is not w and x["ax"] == w["ax"] and x["c"] == w["c"] and (abs(x["a"] - ande) < 1 or abs(x["b"] - ande) < 1):
            return x
    return None


def _genom(o, w):
    """Går den vinkelräta väggen o igenom punkten där w ansluter, ensam eller tillsammans med en kolinjär vägg?"""
    return (o["a"] + 1 < w["c"] < o["b"] - 1) or _partner(o, w["c"]) is not None


def hor_jarn(w):
    """Väggens vågräta järn i plan, en linje per yta: [(sida, (p0, p1), (typ_a, typ_b))], där p0 och p1 är ändarnas
    järnlinjer. Ändarnas typ:
        "hörn"   hörn: till den vinkelräta väggens järn på samma sida (den konvexa sidan med den konvexa); vinkeljärn
                 (23) 750 + 750 skarvas 500 med de raka järnen;
        "T"      w ansluter mot en genomgående vägg: till den genomgående väggens bortre järn; vinkeljärn (25) 900 + 750
                 genom kärnan skarvas 500 med de raka järnen;
        "genom"  w är en del av en genomgående vägg där en annan vägg ansluter: på den bortre ytan går järnet 250
                 förbi anslutningen och skarvas 500 med den kolinjära väggens järn;
        "nära"   som "genom", men den yta där den anslutande väggen ligger: järnet slutar vid dess järn;
        "fri"    fri ände (öppning): 30 mm från kärnans ände."""
    ut = []
    for sida in (1, -1):
        e, typer = [], []
        for ande, o, rikt in ((w["a"], w["mot_a"], -1), (w["b"], w["mot_b"], 1)):
            if o is None:
                e.append(ande - rikt * 30.0)
                typer.append("fri")
                continue
            o_kropp = 1 if (o["a"] + o["b"]) / 2 > w["c"] else -1      # o:s kropp i w:s tvärled
            w_kropp = -rikt                                           # w:s kropp i o:s tvärled (bakåt längs w)
            if _partner(w, ande) is not None:
                if sida == -o_kropp:
                    e.append(ande + rikt * K.SKARV / 2)
                    typer.append("genom")
                else:
                    e.append(jarnlinje(o, w_kropp))
                    typer.append("nära")
            elif _genom(o, w):
                e.append(jarnlinje(o, -_kroppsida(o, w)))
                typer.append("T")
            else:
                konvex_w, konvex_o = -o_kropp, -w_kropp
                e.append(jarnlinje(o, konvex_o if sida == konvex_w else -konvex_o))
                typer.append("hörn")
        q = jarnlinje(w, sida)
        p0, p1 = ((e[0], q), (e[1], q)) if w["ax"] == "h" else ((q, e[0]), (q, e[1]))
        ut.append((sida, (p0, p1), tuple(typer)))
    return ut


BEN = {"hörn": K.VINKEL_HORN[0], "T": 900.0}      # vinkeljärnens ben längs väggen från ändens järnlinje


def raka(w):
    """De raka vågräta järnen (21, V3: 24) i w, ett per yta och lager: [(sida, t0, t1)] längs väggen. De skarvas 500
    med vinkeljärnen; där vinkeljärnen räcker över hela väggen (korta väggbitar vid öppningar) behövs inga raka järn."""
    ut = []
    for sida, (p0, p1), (ta, tb) in hor_jarn(w):
        i = 0 if w["ax"] == "h" else 1
        e0, e1 = p0[i], p1[i]
        ra, rb = BEN.get(ta, 0.0), BEN.get(tb, 0.0)
        L = e1 - e0
        if (ra and tb == "fri" and ra >= L) or (rb and ta == "fri" and rb >= L) or (ra and rb and ra + rb >= L + K.SKARV):
            continue
        t0 = e0 + (ra - K.SKARV if ra else 0.0)
        t1 = e1 - (rb - K.SKARV if rb else 0.0)
        ut.append((sida, t0, t1))
    return ut


def fri_gans(w, rikt):
    """Gränsen för järnen längs väggen w åt hållet rikt (+1 mot b, −1 mot a): 30 mm från kärnans ände vid en fri
    ände, annars None."""
    if rikt > 0:
        return None if w["mot_b"] else w["b"] - 30.0
    return None if w["mot_a"] else w["a"] + 30.0


def _klipp(t0, t, w, rikt):
    """Ben från t0 till t längs w, klippt vid en fri ände."""
    g = fri_gans(w, rikt)
    if g is None:
        return t
    return min(t, g) if rikt > 0 else max(t, g)


def lager_antal(namn):
    """Antal lager vågräta järn i väggen: 5, i V3 7 (s300 i hela höjden)."""
    return len(K.Z_HOR_V3) if namn == "V3" else len(K.Z_HOR)


def hornjarn():
    """Vinkeljärn 750 + 750 i hörnen (båda ytorna) och 900 + 750 vid anslutningarna mot en genomgående vägg:
    [(pos, polylinje, antal lager)]. Benen kortas till 30 mm från kärnans ände där väggen är kortare (väggbitar vid
    öppningar)."""
    ut = []
    L1, L2 = K.VINKEL_HORN
    for a_ in K.ANSLUTNINGAR:
        x, y = a_["x"], a_["y"]
        vs = [VAGG[n] for n in a_["vaggar"]]
        if a_["typ"] == "hörn":
            w1, w2 = vs
            h, vv = (w1, w2) if w1["ax"] == "h" else (w2, w1)
            n = max(lager_antal(h["namn"]), lager_antal(vv["namn"]))
            # riktningarna in längs väggarna från hörnet
            dx = 1 if (h["a"] + h["b"]) / 2 > x else -1
            dy = 1 if (vv["a"] + vv["b"]) / 2 > y else -1
            for sida_h in (1, -1):
                yq = jarnlinje(h, sida_h)
                konvex = (sida_h == -dy)
                xq = jarnlinje(vv, -dx if konvex else dx)
                ut.append((POS["horn"], [(_klipp(xq, xq + dx * L1, h, dx), yq), (xq, yq),
                                         (xq, _klipp(yq, yq + dy * L2, vv, dy))], n))
        else:
            gen = [VAGG[nn] for nn in a_["genom"]]
            w = next(q for q in vs if q not in gen)
            n = lager_antal(w["namn"])
            o = gen[0]
            bort = -_kroppsida(o, w)
            q_bort = jarnlinje(o, bort)
            rikt_w = 1 if (w["a"] + w["b"]) / 2 > (x if w["ax"] == "h" else y) else -1   # in längs w
            for sida in (1, -1):
                q = jarnlinje(w, sida)
                t1 = _klipp(q_bort, q_bort + rikt_w * BEN["T"], w, rikt_w)
                if w["ax"] == "h":
                    ut.append((POS["t"], [(t1, q), (q_bort, q), (q_bort, q + sida * L2)], n))
                else:
                    ut.append((POS["t"], [(q, t1), (q, q_bort), (q + sida * L2, q_bort)], n))
    return ut


def _fordela(t0, t1, s, med0=True, med1=True):
    """Lägen mellan t0 och t1 med lika avstånd, högst s; med0/med1: ändpunkterna tas med."""
    n = max(int(math.ceil((t1 - t0) / s - 1e-6)), 1)
    st = (t1 - t0) / n
    ts = [t0 + k * st for k in range(n + 1)]
    return ts[(0 if med0 else 1):(n + 1 if med1 else n)]


def lodrata_t(w):
    """Lägen längs ytterväggen w för de lodräta järnen Ø10 (22) på insidan, med väggens avstånd enligt K-06 (s200 eller
    TG 2216:s s300): från den vinkelräta väggens kärna
    + 50 vid hörn och anslutningar; vid en öppning fram till öppningens järn (26), 40 mm från kärnans ände."""
    if w["ute"] is None:
        return []
    t0, med0 = (w["mot_a"]["c"] + K.T_KARNA / 2 + 50.0, True) if w["mot_a"] else (w["a"] + 40.0, False)
    t1, med1 = (w["mot_b"]["c"] - K.T_KARNA / 2 - 50.0, True) if w["mot_b"] else (w["b"] - 40.0, False)
    return _fordela(t0, t1, K.ARM_V_VAGG[w["namn"]][1], med0, med1)


def lodrata_under(o):
    """Lodräta järn (22) under en bröstning, mellan öppningens järn (26) 40 mm utanför betongens öppning; de går upp
    till bröstningens järn (27)."""
    return _fordela(o["x0"] - 40.0, o["x1"] + 40.0, K.ARM_V_TG[1], False, False) if o["z0"] > 0 else []


def lodrata(w):
    """Lodräta järn Ø10 på insidan av en yttervägg: punkter i plan."""
    if w["ute"] is None:
        return []
    q = w["ytterliv"] - w["ute"] * K.X_LODRAT
    return [(t, q) if w["ax"] == "h" else (q, t) for t in lodrata_t(w)]


def oppningsjarn_plan(o):
    """2 Ø12 längs öppningens sidor: en vid var yta, 40 mm från kärnans ände, innanför de vågräta järnen."""
    w1, w2 = VAGG[o["vaggar"][0]], VAGG[o["vaggar"][1]]
    ut = []
    for w, t in ((w1, o["x0"] - 40.0), (w2, o["x1"] + 40.0)):
        for sida in (1, -1):
            q = jarnlinje(w, sida) - sida * 11.0
            ut.append((t, q) if w["ax"] == "h" else (q, t))
    return ut


def oppning_z(o):
    """Öppningens järn (26) i höjdled: från 600 under bröstningen (dörrar: från bottenplattan) upp under
    mellanbjälklagets överkantsnät i ytterväggarna och till 30 mm under krönet i innerväggarna (glidskikt)."""
    za = (o["z0"] - K.OPP["forankring"]) if o["z0"] > 0 else 0.0
    zb = K.L_LODRAT if o["typ"] == "yttre" else H - 30.0
    return za, zb


def lager_armering(v):
    with v.lager("armering"):
        for w in V:
            for sida, t0, t1 in raka(w):
                q = jarnlinje(w, sida)
                v.linje([(t0, q), (t1, q)] if w["ax"] == "h" else [(q, t0), (q, t1)], "tunn")
        for pos, pl, _ in hornjarn():
            v.linje(pl, "ok")
        for w in V:
            for x, y in lodrata(w):
                v.cirkel(x, y, 0.32, fyll="svart", stil=None)
        for o in OPPN:
            for x, y in oppningsjarn_plan(o):
                v.cirkel(x, y, 0.5, fyll="#b5463a", stil=None)


# ================================================================== 4. blad
BLADEN = [
    ("R-04.1", ["Källarstomme", "Plan, mått och rör"], "1:50", "R-04.1 Källarstomme, plan, mått och rör"),
    ("R-04.2", ["Källarstomme", "Väggarnas armering"], "1:50", "R-04.2 Källarstomme, väggarnas armering"),
    ("R-04.3", ["Källarstomme", "Väggar med öppningar, elevationer"], "1:50", "R-04.3 Källarstomme, elevationer"),
    ("R-04.4", ["Källarstomme", "Sektioner och detaljer"], "1:10, 1:20", "R-04.4 Källarstomme, sektioner och detaljer"),
    ("R-04.5", ["Källarstomme", "Rör och stålförteckning"], "1:5, 1:10", "R-04.5 Källarstomme, rör och stålförteckning"),
]


def hd(nr):
    b = next(x for x in BLADEN if x[0] == nr)
    return huvud(nr, b[1], b[2], UNDERLAG, DATUM, REV)


def planvy():
    return Vy(x=PLAN["x"], y=PLAN["y"], w=PLAN["w"], h=PLAN["h"], skala=50, X0=PLAN["X0"], Y1=PLAN["Y1"])


def anvisningar():
    return [
        "Källarväggar av Sundolitt Kub 350-150 (SINTEF TG 2216): cellplast EPS 100 + betongkärna 150 + cellplast 100. "
        "Betong B30 enligt Sundolitt (C30/37), armering B500B. Höjd 2\u00a0100 från bottenplattans överkant till "
        "mellanbjälklagets underkant: tre hela skift (1\u00a0800) och ett halvt (300). Ytterväggarnas halva skift gjuts med "
        "bjälklaget; innerväggarna (V4–V6, V15, V19) gjuts i hela höjden före bjälklaget och får glidskikt på krönet "
        "(K-06, R-03).",
        "Koordinater i mm enligt K-05; origo i skärningen mellan mellanbjälklagets kanter x = 0 och y = 0. Väggarnas "
        "ytterliv ligger 30 mm utanför bjälklagets kant. Höjder från bottenplattans överkant.",
        "Vid öppningarna ligger den färdiga öppningen 100 mm innanför betongen: sidorna och bröstningen får "
        "Sundolitts smyglist 100 × 350 med regel 45 × 195 (R-04.4 E), alltså tre sidor vid fönstren och två vid "
        "dörrarna. Ingen smyglist i överkant: öppningen går upp till mellanbjälklagets underkant. "
        "Måtten på planen avser betongens öppningar.",
        "I hörn och anslutningar går betongkärnorna ihop: cellplasten skärs bort där väggarna möts.",
    ]


def oppningstabell():
    rader = []
    for o in OPPN:
        f0, f1, fz = o["fardig"]
        brost = f"{sv(o['z0'])} ({sv(fz)})" if o["z0"] > 0 else "–"
        rader.append([o["namn"], " / ".join(o["vaggar"]), f"{sv(o['x0'])}–{sv(o['x1'])}",
                      f"{sv(o['bredd'])} ({sv(f1 - f0)})", brost, f"{sv(H - o['z0'])} ({sv(H - fz)})"])
    return dict(typ="tabell", kolumner=["", "Mellan", "x (betong)", "Bredd", "Bröstning", "Höjd"],
                bredd=(0, 0, 1, 0, 0, 0), rader=rader, just=["l", "l", "l", "r", "r", "r"], sz=6.2)


def rortabell():
    rader = []
    for r in ROR:
        xs = " och ".join(sv(x) for x, _ in r["ror"])
        rader.append([r["namn"], xs, sv(r["ror"][0][1]),
                      "två rör, fotplåt 280 × 200 eller 2 st 140 × 200" if r["n"] == 2 else ""])
    return dict(typ="tabell", kolumner=["Rör", "x", "y", ""], bredd=(0, 0, 0, 1), rader=rader,
                just=["l", "r", "r", "l"], sz=6.2)


def blad_plan():
    v = planvy()
    lager_vaggar(v)
    lager_ror(v)
    lager_oppningsnamn(v)
    lager_yttermatt(v)
    lager_innermatt(v)
    lager_rorkedjor(v)
    lager_snitt(v)
    lager_origo(v)
    lager_rubrik(v, "PLAN – MÅTT OCH RÖR")
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=6.8, rader=anvisningar() + [
            f"Rör {K.ROR_TEXT}, L = {sv(K.L_ROR)}, med topplåt 80×80×8 och fotplåt (R-04.5). P7: två rör tätt intill "
            "varandra i x-led på en gemensam fotplåt. Rörens mitt enligt tabellen, ±5 mm.",
            "Planen är ett snitt 1,6 m över bottenplattan; bröstningen under F1–F3 syns under snittet. Armering R-04.2, "
            "elevationer R-04.3, sektioner och detaljer R-04.4, rör och stålförteckning R-04.5. Bottenplatta och "
            "plintar: R-05."]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="yta", fyll="karna", stil="tunn", text="betongkärna 150, Kub 350-150"),
            dict(form="yta", fyll="eps", stil="tunn", text="cellplast EPS, 100 per sida och i smygen"),
            dict(form="ruta", fyll="stal", text="stålrör VKR 80×80×4 (K-05)")]),
        dict(typ="rubrik", text="Öppningar i betongen"),
        oppningstabell(),
        dict(typ="text", sz=6.0, rader=["", "Betongens mått, färdig öppning inom parentes (smyglist 100 mm vid sidorna "
                                          "och på bröstningen). Överkant i mellanbjälklagets underkant, 2\u00a0100 över "
                                          "bottenplattan."]),
        dict(typ="rubrik", text="Rörens lägen (mitt)"),
        rortabell(),
        dict(typ="rubrik", text=f"Ritningsförteckning {NR}"),
        dict(typ="tabell", kolumner=["Ritning", "Innehåll", "Skala"], bredd=(0, 1, 0),
             rader=[[nr, ", ".join(t[1:]), sk] for nr, t, sk, _ in BLADEN], just=["l", "l", "l"], sz=6.2),
    ]
    return Blad(hd("R-04.1"), REVISIONER, kol, [v])


def lodrat_vaggar(s):
    """Ytterväggarna med lodräta järn Ø10 s (K-06)."""
    return [w["namn"] for w in V if K.ARM_V_VAGG.get(w["namn"], (0, 0))[1] == s]


TAT, GLES = lodrat_vaggar(K.ARM_V[1]), lodrat_vaggar(K.ARM_V_TG[1])     # s200 och s300 (TG 2216)


def armeringstabell():
    inre = [w["namn"] for w in V if w["typ"] == "inre"]
    d, s_, st = K.ARM_H
    rader = [
        [", ".join(n for n in TAT if n != "V3"), f"Ø{K.ARM_V[0]} s{K.ARM_V[1]} ({POS['lod']})",
         f"2 Ø{d}/skift, s{s_}/s{st} ({POS['hor']})"],
        [", ".join(GLES), f"Ø{K.ARM_V_TG[0]} s{K.ARM_V_TG[1]} ({POS['lod']})", f"2 Ø{d}/skift, s{s_}/s{st} ({POS['hor']})"],
        ["V3", f"Ø{K.ARM_V[0]} s{K.ARM_V[1]} ({POS['lod']})", f"Ø{d} s300 båda ytorna ({POS['v3']})"],
        [", ".join(inre), "startjärn (R-05)", f"2 Ø{d}/skift, s{s_}/s{st} ({POS['hor']})"],
    ]
    return dict(typ="tabell", kolumner=["Väggar", "Lodrätt, insidan", "Vågrätt"], bredd=(1, 0, 0), rader=rader,
                just=["l", "l", "l"], sz=6.2)


def lager_armtext(v):
    """Positioner med hänvisningar till exempel på planen."""
    with v.lager("armtext"):
        w = VAGG["V14"]
        y = 7000.0
        v.hanvisning((jarnlinje(w, -1), y), (12300.0, y + 600.0), "2 Ø10 per skift, ett vid var yta", bubbla=POS["hor"],
                     a="rm", sz=6.6)
        pts = lodrata(VAGG["V14"])
        q = min(pts, key=lambda p: abs(p[1] - 6000.0))
        v.hanvisning(q, (12300.0, 5600.0), f"Ø10 s{K.ARM_V_VAGG['V14'][1]} lodrätt, insidan", bubbla=POS["lod"],
                     a="rm", sz=6.6)
        v.hanvisning((13665.0 - 40.0, 12365.0 - 500.0), (12300.0, 11300.0), "vinkeljärn 750 + 750", bubbla=POS["horn"],
                     a="rm", sz=6.6)
        t = sorted(lodrata_t(VAGG["V3"]))                  # det vågräta järnet mitt emellan två lodräta
        x3 = min(((p + q) / 2 for p, q in zip(t, t[1:])), key=lambda m: abs(m - 2200.0))
        v.hanvisning((x3, jarnlinje(VAGG["V3"], -1)), (x3, 8400.0), "V3: Ø10 s300, båda ytorna",
                     bubbla=POS["v3"], a="lm", sz=6.6)
        v.hanvisning((4545.0 - 300.0, jarnlinje(VAGG["V3"], 1)), (2900.0, 10300.0), "T-anslutning, vinkeljärn",
                     bubbla=POS["t"], a="lm", sz=6.6)
        o = OPPN[0]
        q = oppningsjarn_plan(o)[0]
        v.hanvisning(q, (5200.0, 1400.0), "2 Ø12 längs öppningarnas sidor", bubbla=POS["opp_sida"], a="lm", sz=6.6)


def blad_armering():
    v = planvy()
    lager_vaggar(v, namn="bredvid")
    lager_armering(v)
    lager_ror(v, namn=False)
    lager_oppningsnamn(v)
    lager_armtext(v)
    lager_origo(v)
    lager_rubrik(v, "PLAN – VÄGGARNAS ARMERING")
    d, s_, st = K.ARM_H
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=6.8, rader=[
            "Armering B500B, betong B30 (C30/37). Täckande betongskikt till de vågräta järnen: 25 mm mot insidan och "
            "30 mm mot utsidan; järnen ligger i bindarnas hållare (K-06).",
            f"Vågräta järn ({POS['hor']}): 2 Ø{d} per skift, ett vid var yta, s{s_} i de två nedre skiften och s{st} i "
            "de två översta, i alla väggar utom V3. Skarvlängd minst 500.",
            f"Lodräta järn ({POS['lod']}): Ø10 på insidan i alla ytterväggar, s{K.ARM_V[1]} där packningstrycket "
            f"kräver det och s{K.ARM_V_TG[1]} (TG 2216) i {', '.join(GLES)} (K-06, tabellen), från bottenplattan upp "
            "under mellanbjälklagets överkantsnät, innanför de vågräta järnen.",
            f"V3 ({POS['v3']}): Ø10 s300 i båda ytorna i hela höjden. V3 bär fyllningen innan mellanbjälklaget gjuts "
            "(K-06, byggskedet).",
            f"Hörn ({POS['horn']}): vinkeljärn Ø10, 750 + 750, vid båda ytorna i varje lager, skarv 500 med de raka "
            f"järnen. Anslutningar mot en genomgående vägg ({POS['t']}): vinkeljärn 900 + 750 genom kärnan och 750 "
            "längs den genomgående väggens bortre yta, där väggens egna järn skarvas 500 (R-04.4 C och D). Där väggen "
            "slutar vid "
            "en öppning kortas vinkeljärnets ben till 30 mm från kärnans ände; i "
            f"{', '.join(w['namn'] for w in V if not raka(w))} räcker vinkeljärnen och inga raka järn behövs.",
            f"Öppningar: 2 Ø12 längs sidorna ({POS['opp_sida']}) och under bröstningen ({POS['opp_under']}), "
            f"förankrade 600 förbi öppningen, och lodräta järn Ø10 s{K.ARM_V_TG[1]} under bröstningarna "
            f"({POS['lod_under']}). "
            "Över öppningarna är mellanbjälklaget (R-03). Elevationer: R-04.3.",
            "Startjärn från bottenplattan: R-05. Vinkeljärn från väggarna till mellanbjälklaget (pos 14): R-03.",
            "Lagren i höjdled: R-04.3 och sektionerna på R-04.4."]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="linje", stil="tunn", text="vågräta järn (planen visar ett lager)"),
            dict(form="linje", stil="ok", text="vinkeljärn i hörn och anslutningar"),
            dict(form="punkt", r=0.32, text="lodräta järn Ø10 på insidan (tabellen)"),
            dict(form="punkt", r=0.5, fyll="#b5463a", text="2 Ø12 längs öppningarnas sidor"),
            dict(form="bubbla", txt="21", text="positionsnummer (stålförteckning R-04.5)")]),
        dict(typ="rubrik", text="Väggarnas armering"),
        armeringstabell(),
    ]
    return Blad(hd("R-04.2"), REVISIONER, kol, [v])


# ---------------------------------------------------------------- elevationer (R-04.3)
ELEV = [
    # namn, rubrik, centrumlinje i y, väggarna på linjen och vyns övre vänstra hörn på papperet (mm)
    dict(namn="a", titel="FASADEN MED F1–F3 (V10–V13), sedd utifrån", c=VAGG["V10"]["c"],
         vaggar=("V10", "V11", "V12", "V13"), vy=(24.0, 12.0)),
    dict(namn="b", titel="V8 OCH V9 MED D1, sedd utifrån", c=VAGG["V8"]["c"], vaggar=("V8", "V9"), vy=(176.0, 12.0)),
    dict(namn="c", titel="V4–V6 MED D2 OCH D3, sedd från söder", c=VAGG["V4"]["c"], vaggar=("V4", "V5", "V6"),
         vy=(24.0, 103.0)),
    dict(namn="d", titel="V3, sedd inifrån (från söder)", c=VAGG["V3"]["c"], vaggar=("V3",), vy=(176.0, 103.0)),
    dict(namn="e", titel="V2, sedd inifrån (från söder): typisk yttervägg", c=VAGG["V2"]["c"], vaggar=("V2",),
         vy=(24.0, 194.0)),
]


def karna_langs(e):
    """Betongkärnans utbredning längs väggraden (väggarna på linjen, till hörnens och anslutningarnas kärna)."""
    b = unary_union([VAGG[n]["karna"] for n in e["vaggar"]]).bounds
    return b[0], b[2]


def oppningar_langs(e):
    """Öppningarna i väggraden."""
    return [o for o in OPPN if o["ax"] == VAGG[e["vaggar"][0]]["ax"] and o["c"] == e["c"]]


def lodrata_elev(e):
    """Lodräta järn längs väggraden: [(x, z0, z1, pos)]; i ytterväggarna (22) upp under mellanbjälklagets
    överkantsnät och under bröstningarna (28) upp till bröstningens järn (27)."""
    ut = [(t, 0.0, K.L_LODRAT, POS["lod"]) for n in e["vaggar"] for t in lodrata_t(VAGG[n])]
    for o in oppningar_langs(e):
        if o["typ"] == "yttre":
            ut += [(t, 0.0, o["z0"] - 40.0, POS["lod_under"]) for t in lodrata_under(o)]
    return sorted(ut)



def elevation(e):
    """Elevation 1:50 av en väggrad: betongkärnan (cellplasten inte ritad), skift, gjutfog, öppningar och armering."""
    s = 50.0
    c = e["c"]
    xa, xb = karna_langs(e)
    vx, vy = e["vy"]
    v = Vy(x=vx, y=vy, w=150, h=85, skala=s, X0=xa - 1300.0, Y1=H + HMB + 800.0)
    oppn = oppningar_langs(e)
    v3 = "V3" in e["vaggar"]
    ytter = any(VAGG[n]["typ"] == "yttre" for n in e["vaggar"])
    with v.lager("betong"):
        # bottenplattan och mellanbjälklaget, streckade
        v.rekt(xa - 400, -K.UTF["h_balk"], xb + 400, 0, fyll="betong", stil=None)
        v.linje([(xa - 400, 0), (xb + 400, 0)], "tunn")
        v.linje([(xa - 400, -K.UTF["h_balk"]), (xb + 400, -K.UTF["h_balk"])], "dold")
        v.rekt(xa - 400, H, xb + 400, H + HMB, fyll="betong", stil=None)
        v.linje([(xa - 400, H), (xb + 400, H)], "tunn")
        v.linje([(xa - 400, H + HMB), (xb + 400, H + HMB)], "tunn")
        for xx in (xa - 400, xb + 400):                # plattorna avbrutna, inget mellan dem
            v.brott((xx, -K.UTF["h_balk"] - 60), (xx, 60), "tunn")
            v.brott((xx, H - 60), (xx, H + HMB + 60), "tunn")
        # kärnan med öppningarna
        v.rekt(xa, 0, xb, H, fyll="karna", stil="normal")
        for o in oppn:
            v.rekt(o["x0"], o["z0"], o["x1"], H, fyll="vit", stil="normal")
            f0, f1, fz = o["fardig"]
            if o["z0"] > 0:
                v.linje([(f0, H), (f0, fz), (f1, fz), (f1, H)], "dold")
            else:                                   # dörr: smyglist bara vid sidorna
                for f in (f0, f1):
                    v.linje([(f, H), (f, 0.0)], "dold")
        for z in (K.SKIFT, 2 * K.SKIFT):
            for (p0, p1) in _utan_oppningar(xa, xb, z, oppn):
                v.linje([(p0, z), (p1, z)], "fin")
        if ytter:                                   # innerväggarna gjuts i hela höjden före bjälklaget
            for (p0, p1) in _utan_oppningar(xa, xb, K.H_GJUT1, oppn):
                v.linje([(p0, K.H_GJUT1), (p1, K.H_GJUT1)], "axel")
        else:
            v.rekt(xa, H - 12, xb, H, fyll="papp", stil=None)
    with v.lager("armering"):
        zs = K.Z_HOR_V3 if v3 else K.Z_HOR
        for z in zs:
            for (p0, p1) in _utan_oppningar(xa + 30, xb - 30, z, oppn, marg=30.0):
                v.linje([(p0, z), (p1, z)], "uk_tunn")
        for x, z0, z1, _ in lodrata_elev(e):
            v.linje([(x, z0 + 20), (x, z1)], "fordelning")
        for o in oppn:
            za, zb = oppning_z(o)
            for x in (o["x0"] - 40.0, o["x1"] + 40.0):
                v.linje([(x, za + 20), (x, zb)], "ok")
        for z, a_, b_, _, _ in brostningsjarn(oppn, xa, xb):
            v.linje([(a_, z), (b_, z)], "ok")
    with v.lager("matt"):
        xs = [xa] + [p for o in oppn for p in (o["x0"], o["x1"])] + [xb]
        kedja(v, xs, -K.UTF["h_balk"] - 6.5 * s, [-K.UTF["h_balk"]] * len(xs), sz=5.8)
        if len(e["vaggar"]) > 1:                  # väggbitarnas namn under bottenplattan
            for n in e["vaggar"]:
                b0, _, b1, _ = VAGG[n]["karna"].bounds
                v.text((max(b0, xa) + min(b1, xb)) / 2, -K.UTF["h_balk"] - 2.4 * s, n, a="cm", sz=5.8, col="gra")
        zs_k = [0.0, K.SKIFT, 2 * K.SKIFT, K.H_GJUT1, H]
        kedja(v, zs_k, xa - 6.0 * s, [xa] * len(zs_k), sz=5.8, ax="y")
        for i, o in enumerate(oppn):
            if o["z0"] > 0:                       # mitt i öppningen, mellan järnen under bröstningen
                xm = (o["x0"] + o["x1"]) / 2
                t = lodrata_under(o)
                if t:
                    xm = min(((p + q) / 2 for p, q in zip(t, t[1:])), key=lambda m: abs(m - xm), default=xm)
                kedja(v, [0.0, o["z0"], H], xm, [xm] * 3, sz=5.8, ax="y", bg=True)
    if not ytter:
        with v.lager("text"):
            v.hanvisning((xa + 250, H - 6), (xa + 250, H + HMB + 450), "glidskikt (byggpapp) på krönet, R-03",
                         a="lm", sz=6.0)
    with v.lager("rubrik"):
        v.rubrik(xa - 1250, -K.UTF["h_balk"] - 12.0 * s, e["titel"], skala=50, sz=8.5)
    return v


def _utan_oppningar(a, b, z, oppn, marg=0.0):
    """Sträckan a–b på höjden z, avbruten där en öppning skär höjden."""
    ut, x = [], a
    for o in sorted(oppn, key=lambda q: q["x0"]):
        if o["z0"] <= z <= H:
            if o["x0"] - marg > x:
                ut.append((x, o["x0"] - marg))
            x = o["x1"] + marg
    if b > x:
        ut.append((x, b))
    return ut


def brostningsjarn(oppn, xa, xb):
    """2 Ø12 (27) under öppningar med bröstning, 40 mm under betongens underkant, förankrade 600 förbi öppningen.
    Mot en annan öppning slutar järnet 30 mm från dess kärnände; vid hörnen, där väggen är kortare, bockas järnet in i
    den vinkelräta väggen med det ben som fattas till 600. Järn på samma höjd slås ihop. [(z, a, b, ben_a, ben_b)]"""
    F = K.OPP["forankring"]
    rader = {}
    for o in oppn:
        if o["z0"] <= 0:
            continue
        z = o["z0"] - 40.0
        a, b = o["x0"] - F, o["x1"] + F
        for q in oppn:
            if q is not o and q["z0"] <= z:                       # q är öppen på järnets höjd
                if q["x1"] <= o["x0"]:
                    a = max(a, q["x1"] + 30.0)
                elif q["x0"] >= o["x1"]:
                    b = min(b, q["x0"] - 30.0)
        rader.setdefault(z, []).append([max(a, xa + 30.0), min(b, xb - 30.0),
                                        max(xa + 30.0 - a, 0.0), max(b - (xb - 30.0), 0.0)])
    ut = []
    for z, iv in sorted(rader.items()):
        iv.sort()
        cur = list(iv[0])
        for nxt in iv[1:]:
            if nxt[0] <= cur[1]:
                if nxt[1] >= cur[1]:
                    cur[1], cur[3] = nxt[1], nxt[3]
            else:
                ut.append((z, *cur))
                cur = list(nxt)
        ut.append((z, *cur))
    return ut


def korta_forankringar():
    """Öppningar där järnet under bröstningen (27) når mindre än 600 förbi öppningen eftersom en annan öppning är
    nära: [(öppning, den andra öppningen, förankring)]."""
    ut = []
    for e in ELEV:
        oppn = oppningar_langs(e)
        for o in oppn:
            if o["z0"] <= 0:
                continue
            z = o["z0"] - 40.0
            for q in oppn:
                if q is not o and q["z0"] <= z:
                    if q["x0"] >= o["x1"] and q["x0"] - 30.0 - o["x1"] < K.OPP["forankring"]:
                        ut.append((o, q, q["x0"] - 30.0 - o["x1"]))
                    if q["x1"] <= o["x0"] and o["x0"] - q["x1"] - 30.0 < K.OPP["forankring"]:
                        ut.append((o, q, o["x0"] - q["x1"] - 30.0))
    return ut


def blad_elevationer():
    vyer = [elevation(e) for e in ELEV]
    d, s_, st = K.ARM_H
    ben = sorted({round(r[3]) for e in ELEV for r in brostningsjarn(oppningar_langs(e), *karna_langs(e)) if r[3] > 0} |
                 {round(r[4]) for e in ELEV for r in brostningsjarn(oppningar_langs(e), *karna_langs(e)) if r[4] > 0})
    korta = " ".join(f"Mellan {o['namn']} och {q['namn']} slutar järnet under {o['namn']} 30 mm före {q['namn']}, "
                     f"{sv(L)} förbi {o['namn']}." for o, q, L in korta_forankringar())
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=6.8, rader=[
            "Elevationerna visar betongkärnan; cellplasten är inte ritad. Måtten längs väggarna går till kärnans ändar. "
            "I hörn och anslutningar går kärnan in i den vinkelräta väggen, till 100 mm innanför dess bortre liv: i "
            "yttre hörn 100 mm innanför ytterlivet (som planen R-04.1 mäter till), i de inåtgående hörnen V8/V17, "
            "V3/V20 och V2/V16 250 mm förbi ytterlivet. Den "
            "färdiga öppningen (streckad) ligger 100 mm innanför betongen: Sundolitts smyglist med regel vid sidorna och "
            "på bröstningen (R-04.4 E). Ingen smyglist i överkant, som är mellanbjälklagets underkant.",
            f"Skift: tre hela (600) och ett halvt (300). I ytterväggarna gjuts de tre hela skiften först, upp till "
            f"{sv(K.H_GJUT1)} (gjutfog, streckprickad), och det halva skiftet med mellanbjälklaget (K-06). "
            "Innerväggarna (V4–V6) gjuts i hela höjden före bjälklaget och får glidskikt (byggpapp) på krönet.",
            f"Vågräta järn ({POS['hor']}): ett vid var yta i varje lager, på höjderna "
            f"{', '.join(sv(z) for z in K.Z_HOR)}. V3 ({POS['v3']}): s300 i hela höjden, "
            f"{', '.join(sv(z) for z in K.Z_HOR_V3)}. Järnen ligger i bindarnas hållare; höjderna kan avvika "
            "med elementens hållare.",
            f"Lodräta järn ({POS['lod']}): Ø10 på insidan av ytterväggarna, högst s{K.ARM_V[1]} eller "
            f"s{K.ARM_V_TG[1]} enligt R-04.2, L = {sv(K.L_LODRAT)}, från 50 mm innanför den vinkelräta väggens kärna "
            f"fram till öppningarnas järn ({POS['opp_sida']}). Under bröstningarna ({POS['lod_under']}) Ø10 högst "
            f"s{K.ARM_V_TG[1]} upp till bröstningens järn ({POS['opp_under']}). Innerväggarna har startjärn (R-05); "
            "startjärnen är inte ritade.",
            f"Öppningar: 2 Ø12 längs sidorna ({POS['opp_sida']}), från 600 under bröstningen (dörrar: från "
            "bottenplattan) upp under mellanbjälklagets överkantsnät, i innerväggarna till 30 mm under krönet. "
            f"Under bröstningen 2 Ø12 ({POS['opp_under']}), förankrade 600 förbi öppningen; vid hörnen bockas järnet in "
            f"i den vinkelräta väggen (ben {' / '.join(sv(x) for x in ben)}). {korta}",
            "Mått i mm, höjder från bottenplattans överkant. Plan R-04.1, armering i plan R-04.2, "
            "stålförteckning R-04.5."]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="yta", fyll="karna", stil="tunn", text="betongkärna 150 (Kub 350-150)"),
            dict(form="linje", stil="uk_tunn", text=f"vågräta järn, ett vid var yta ({POS['hor']}; V3: {POS['v3']})"),
            dict(form="linje", stil="fordelning",
                 text=f"lodräta järn Ø10, insidan ({POS['lod']}, {POS['lod_under']})"),
            dict(form="linje", stil="ok", text=f"2 Ø12 vid öppningarna ({POS['opp_sida']}, {POS['opp_under']})"),
            dict(form="linje", stil="axel", text="gjutfog, 1\u00a0800 (ytterväggarna)"),
            dict(form="linje", stil="dold", text="färdig öppning, smyglist 100 vid sidorna och bröstningen")]),
    ]
    return Blad(hd("R-04.3"), REVISIONER, kol, vyer)


# ---------------------------------------------------------------- sektioner och detaljer (R-04.4)
IND05 = K.R05["indata"]
H_MB, C_UK05, C_OK05 = IND05["h"], IND05["c_uk"], IND05["c_ok"]
DU05, SU05 = IND05["nat_uk"]
DO05, SO05 = IND05["nat_ok"]
Z_OK_NAT = H + H_MB - C_OK05 - DO05 - DO05 / 2          # mellanbjälklagets överkantsnät, inre lagret (R-03)
Z_POS14 = H + (Z_OK_NAT - H) - DO05 / 2 - 5 - 5          # vinkeljärnets vågräta ben under nätet (R-03.4 sektion A)
POS05 = dict(kant_uk=35, kant_ok=36, bygel=37, start_ute=40, start_inne=41)   # positioner på R-05
POS03 = 14                                                # vinkeljärn till mellanbjälklaget, R-03
HB = K.UTF["h_balk"]                                     # bottenplattans balkar och plintar: 200
EPS_PL = K.UTF["t_eps"]                                  # cellplast under plattan: 200


def etiketter(v, lst, x, z0, dz, sz=6.4):
    """Hänvisningar i en kolumn uppifrån och ned: (text, målpunkt, bubbla eller None); dz i pappersmm."""
    with v.lager("text"):
        for k, (txt, mal, bub) in enumerate(lst):
            z = z0 - k * dz * v.s
            if bub is not None:
                v.hanvisning(mal, (x + 2.1 * v.s, z), txt, bubbla=bub, a="lm", sz=sz)
            else:
                v.hanvisning(mal, (x, z), txt, a="lm", sz=sz)


def kub_snitt(v, x0, z0, z1, rikt=1, gips=True, kapad_ute=False, fog=True):
    """Kub 350-150 i sektion från höjden z0 till z1, x0 i det ena livet och väggen åt hållet rikt. kapad_ute: den
    yttre cellplasten slutar i mellanbjälklagets underkant. fog: gjutfogen vid 1 800 (ytterväggar)."""
    e, k = K.T_EPS, K.T_KARNA
    X = lambda t: x0 + rikt * t
    with v.lager("vagg"):
        v.rekt(X(0), z0, X(e), min(z1, H) if kapad_ute else z1, fyll="eps", stil="tunn")
        v.rekt(X(e), z0, X(e + k), z1, fyll="karna", stil=None)
        v.linje([(X(e), z0), (X(e), z1)], "tunn"); v.linje([(X(e + k), z0), (X(e + k), z1)], "tunn")
        v.rekt(X(e + k), z0, X(K.T_VAGG), min(z1, H), fyll="eps", stil="tunn")
        if gips:
            v.rekt(X(K.T_VAGG), z0, X(K.T_VAGG + 13), min(z1, H), fyll="vit", stil="tunn")
        for z in (K.SKIFT, 2 * K.SKIFT, K.H_GJUT1):
            if z0 < z < z1:
                v.linje([(X(0), z), (X(e), z)], "fin")
                v.linje([(X(e + k), z), (X(K.T_VAGG), z)], "fin")
        if fog and z0 < K.H_GJUT1 < z1:
            v.linje([(X(e), K.H_GJUT1), (X(e + k), K.H_GJUT1)], "dold")


Z_BALK_UK = -HB + 30 + 6 + 5            # balkens järn i underkant, på byglarna (täckskikt 30)
Z_BALK_OK = -25 - 6 - 6 - 5             # balkens järn i överkant, under överkantsnätets två lager (täckskikt 25)
Z_BYGEL = -HB + 30 + 3                  # byglarnas botten (centrum)
Z_NAT_UK = -K.H_PLATTA + 30 + 3         # underkantsnätet, nedre lagret (centrum)


def bottenplatta_snitt(v, xa, xb, balkar, kant=False, balkarm=True):
    """Bottenplattan L300 i sektion mellan xa och xb: platta 100 på 200 cellplast S100 (två skikt, plastfolie), balkar
    (x0, x1) 200 höga på 100 S300. Näten går genom balkarna. kant: plattans kant vid xa (annars avbrott). balkarm:
    balkens längsjärn och byglar (inte i plintar). z = 0 i plattans överkant."""
    hp = K.H_PLATTA
    with v.lager("bottenplatta"):
        v.rekt(xa, -hp - EPS_PL - 120, xb, -hp - EPS_PL, fyll="grus", stil=None)
        prof = []
        cur = xa
        for b0, b1 in sorted(balkar):
            if b0 > cur:
                prof += [(cur, -hp), (b0, -hp)]
            prof += [(max(b0, xa), -HB), (min(b1, xb), -HB)]
            cur = b1
        if cur < xb:
            prof += [(cur, -hp), (xb, -hp)]
        poly = [(xa, 0.0)] + [(prof[0][0], prof[0][1])] + prof[1:] + [(xb, prof[-1][1]), (xb, 0.0)]
        v.polygon(poly, fyll="betong", stil="normal")
        # cellplast: S100 under plattan i två skikt med plastfolie, S300 100 mm under balkarna
        cur = xa
        for b0, b1 in sorted(balkar):
            if b0 > cur:
                v.rekt(cur, -hp - EPS_PL, b0, -hp - EPS_PL / 2, fyll="eps", stil="tunn")
                v.rekt(cur, -hp - EPS_PL / 2, b0, -hp, fyll="eps", stil="tunn")
            v.rekt(max(b0, xa), -HB - K.T_FOT, min(b1, xb), -HB, fyll="eps2", stil="tunn")
            cur = b1
        if cur < xb:
            v.rekt(cur, -hp - EPS_PL, xb, -hp - EPS_PL / 2, fyll="eps", stil="tunn")
            v.rekt(cur, -hp - EPS_PL / 2, xb, -hp, fyll="eps", stil="tunn")
    with v.lager("bottenplatta_arm"):
        x0 = xa + (25.0 if kant else 0.0)
        v.linje([(x0, -25 - 3), (xb, -25 - 3)], "uk_tunn")                    # Ø6 s150 överkant (R-05)
        v.linje([(xa + (30.0 if kant else 0.0), Z_NAT_UK), (xb, Z_NAT_UK)], "uk_tunn")   # Ø6 s150 underkant
        for b0, b1 in (balkar if balkarm else []):
            for x in (b0 + K.BALK_JARN, b1 - K.BALK_JARN):
                v.cirkel(x, Z_BALK_UK, 5, fyll="#2c4a6e", stil=None, modell=True)
                v.cirkel(x, Z_BALK_OK, 5, fyll="#2c4a6e", stil=None, modell=True)
            s_ = K.BYGEL_SIDA
            v.linje([(b0 + s_, -28), (b0 + s_, Z_BYGEL), (b1 - s_, Z_BYGEL), (b1 - s_, -28)], "uk_tunn")


def mellanbjalklag_snitt(v, xa, xb, kant=None):
    """Mellanbjälklaget 150 (R-03) mellan xa och xb med näten; kant: x för plattans kant (annars avbrott)."""
    with v.lager("mellanbjalklag"):
        v.rekt(xa, H, xb, H + H_MB, fyll="betong", stil=None)
        v.linje([(xa, H), (xb, H)], "normal"); v.linje([(xa, H + H_MB), (xb, H + H_MB)], "normal")
        if kant is not None:
            v.linje([(kant, H), (kant, H + H_MB)], "normal")
        for x in (xa, xb):
            if kant is None or abs(x - kant) > 1:
                v.brott((x, H - 40), (x, H + H_MB + 40), "tunn")
    with v.lager("mellanbjalklag_arm"):
        a_ = (kant + 25) if kant is not None else xa
        v.linje([(a_, H + C_UK05 + DU05 / 2), (xb, H + C_UK05 + DU05 / 2)], "uk_tunn")
        v.linje([(a_, H + H_MB - C_OK05 - DO05 / 2), (xb, H + H_MB - C_OK05 - DO05 / 2)], "ok_tunn")


def sektion_a():
    """A–A: yttervägg mot jord (V2), Kub 350-150 på kantbalken, med bottenplattan och mellanbjälklaget. x = 0 i
    väggens ytterliv, inåt positivt; z = 0 i bottenplattans överkant. 1:20"""
    s = 20.0
    v = Vy(x=24, y=12, w=116, h=168, skala=s, X0=-440.0, Y1=H + H_MB + 300.0)
    hf = 2000.0                                                       # fyllning mot V2 (K-06)
    zl = -K.H_PLATTA - EPS_PL - 120
    with v.lager("mark"):
        v.polygon([(-420, zl), (-110, zl), (-110, hf), (-420, hf - 7)], fyll="jord", stil=None)
        v.linje([(-420, hf - 7), (-110, hf)], "normal")
        v.linje([(-8, -HB - K.T_FOT), (-8, hf + 60)], "dold")             # grundmursskiva
        v.rekt(-55, hf - 50, -15, H + H_MB, fyll="#c9c3b8", stil="tunn")   # fasadsten (AR-01)
        v.rekt(-15, hf - 50, 0, H + H_MB, fyll="vit", stil="tunn")
    bottenplatta_snitt(v, K.L_BEN, 900.0, [(K.L_BEN, K.B_L)], kant=True)
    with v.lager("bottenplatta"):
        v.rekt(0, -HB, K.L_BEN, 0, fyll="eps2", stil="tunn")              # L-elementets yttre ben, i väggens ytterliv
        v.rekt(0, -HB - K.T_FOT, K.B_L, -HB, fyll="eps2", stil="tunn")     # L-elementets fot
        v.linje([(0, -HB - K.T_FOT), (0, 0)], "normal")
        v.linje([(K.L_BEN, -HB), (K.L_BEN, 0)], "normal")
        v.brott((900, -K.H_PLATTA - EPS_PL - 40), (900, 40), "tunn")
    kub_snitt(v, 0.0, 0.0, H + H_MB, kapad_ute=True)
    with v.lager("vagg"):
        v.rekt(0, H, K.KI, H + H_MB, fyll="eps", stil="tunn")              # kantisolering 30
    mellanbjalklag_snitt(v, K.KI, 900.0, kant=K.KI)
    with v.lager("vagg"):
        v.rekt(K.T_EPS + 0.5, H - 2, K.T_EPS + K.T_KARNA - 0.5, H + 2, fyll="betong", stil=None)
    xa = K.X_LODRAT - 14
    st = K.STARTJARN
    with v.lager("armering"):
        for z in K.Z_HOR:
            for x in (K.X_H_UT, K.X_H_IN):
                v.cirkel(x, z, 5, fyll="svart", stil=None, modell=True)
        v.linje([(K.X_LODRAT, 20), (K.X_LODRAT, Z_POS14 + 8)], "ok_tunn")       # lodräta järn, insidan
        v.linje([(xa, Z_POS14 - K.POS14["ben"]), (xa, Z_POS14), (xa + K.POS14["in_"], Z_POS14)], "ok")
        v.linje([(K.X_START + 330, Z_BALK_UK), (K.X_START, Z_BALK_UK), (K.X_START, st["upp"])], "uk")   # startjärn,
        # foten 330 in i kantbalken (Sundolitt)
    with v.lager("matt"):
        kedja(v, [0.0, K.T_EPS, K.T_EPS + K.T_KARNA, K.T_VAGG], 1350.0, [1350.0] * 4, sz=5.6)
        zs = [0.0, K.SKIFT, 2 * K.SKIFT, K.H_GJUT1, H, H + H_MB]
        kedja(v, zs, 820.0, [K.T_VAGG + 13] * 5 + [820.0], sz=5.8, ax="y")
        v.text((K.T_VAGG + 13 + 820.0) / 2, K.H_GJUT1 + 25, "gjutfog", a="cb", sz=5.6)
        kedja(v, [-HB - K.T_FOT, -HB, -K.H_PLATTA, 0.0], 820.0, [900.0] * 4, sz=5.6, ax="y")
        kedja(v, [0.0, K.L_BEN, K.B_L], -HB - K.T_FOT - 3.5 * s, [-HB - K.T_FOT] * 3, sz=5.6, bg=True)
    lst = [(f"vinkeljärn Ø{K.POS14['d']} s{K.POS14['s']}, {K.POS14['ben']:.0f} + {K.POS14['in_']:.0f} "
            f"(R-03 pos {POS03})", (xa + 300, Z_POS14), None),
           ("mellanbjälklag 150 (R-03)", (700, H + 75), None),
           (f"Ø10 s{K.ARM_V_VAGG['V2'][1]}, insidan, L = {sv(K.L_LODRAT)}", (K.X_LODRAT, 1600), POS["lod"]),
           ("2 Ø10 per skift, ett vid var yta", (K.X_H_IN, K.Z_HOR[2]), POS["hor"]),
           ("Kub 350-150: 100 + 150 + 100", (175, 1050), None),
           ("gips 13", (K.T_VAGG + 6, 700), None),
           (f"startjärn Ø{st['d']} s{st['s']}, utsidan, foten in i balken (R-05 pos {POS05['start_ute']})",
            (K.X_START, 350), None),
           (f"L-element L300: ben {sv(K.L_BEN)} under väggens cellplast, fot under balken", (50, -150), None),
           (f"kantbalk {sv(K.B_BALK)} × {sv(HB)} (R-05)", (420, -100), None),
           (f"cellplast: {sv(EPS_PL)} S100 under plattan", (700, -230), None)]
    with v.lager("text"):
        v.text(-60, hf + 120, "fasadsten\n(AR-01)", a="rb", sz=5.8, col="gra", i=True)
        v.hanvisning((15, H + 135), (-70, H + 270), "kantisolering 30", a="rm", sz=5.8)
        v.text(-260, 900, "fyllning\n(K-06)", a="cm", sz=5.8, col="gra", i=True, bg=True)
        v.hanvisning((-8, 400), (-130, 470), "grundmursskiva", a="rm", sz=5.8)
    etiketter(v, lst, 980.0, H + H_MB + 200, 6.6, sz=6.2)
    with v.lager("rubrik"):
        v.rubrik(-420, zl - 8.0 * s, "SEKTION A–A  Yttervägg mot jord (V2)", skala=20, sz=9)
    return v


def sektion_b():
    """B–B: innervägg (V15) på balk i bottenplattan, glidskikt mot mellanbjälklaget. x = 0 i väggens mitt. 1:20"""
    s = 20.0
    v = Vy(x=144, y=12, w=102, h=168, skala=s, X0=-420.0, Y1=H + H_MB + 300.0)
    bb = K.B_BALK / 2
    bottenplatta_snitt(v, -400.0, 400.0, [(-bb, bb)])
    with v.lager("bottenplatta"):
        for x in (-400, 400):
            v.brott((x, -K.H_PLATTA - EPS_PL - 40), (x, 40), "tunn")
    kub_snitt(v, -K.T_VAGG / 2, 0.0, H, rikt=1, gips=False, fog=False)
    with v.lager("vagg"):
        v.rekt(-K.T_VAGG / 2 - 13, 0, -K.T_VAGG / 2, H, fyll="vit", stil="tunn")
        v.rekt(K.T_VAGG / 2, 0, K.T_VAGG / 2 + 13, H, fyll="vit", stil="tunn")
        v.rekt(-K.T_VAGG / 2, H - 5, K.T_VAGG / 2, H, fyll="papp", stil=None)        # glidskikt (R-03)
    mellanbjalklag_snitt(v, -400.0, 400.0)
    with v.lager("armering"):
        for z in K.Z_HOR:
            for x in (-45.0, 45.0):
                v.cirkel(x, z, 5, fyll="svart", stil=None, modell=True)
        v.linje([(0.0, Z_BALK_UK), (0.0, K.STARTJARN["upp"])], "uk")         # startjärn, foten längs balken
        v.cirkel(0.0, Z_BALK_UK, 5, fyll="#2c4a6e", stil=None, modell=True)
    with v.lager("matt"):
        kedja(v, [-bb, bb], -HB - K.T_FOT - 3.5 * s, [-HB - K.T_FOT] * 2, sz=5.6, bg=True)
        kedja(v, [-K.T_VAGG / 2, K.T_VAGG / 2], 1750.0, [1750.0] * 2, sz=5.6)
    lst = [("glidskikt (byggpapp) på krönet (R-03)", (100, H - 3), None),
           ("mellanbjälklag (R-03), inte förankrat", (250, H + 75), None),
           ("2 Ø10 per skift, ett vid var yta", (45, K.Z_HOR[3]), POS["hor"]),
           ("Kub 350-150, gjuts i hela höjden före bjälklaget", (0, 1300), None),
           (f"startjärn Ø10 s300 i kärnans mitt, fot längs balken (R-05 pos {POS05['start_inne']})", (0, 600), None),
           (f"balk {sv(K.B_BALK)} × {sv(HB)} (R-05)", (150, -60), None)]
    etiketter(v, lst, 480.0, H + H_MB + 200, 6.6, sz=6.2)
    with v.lager("rubrik"):
        v.rubrik(-400, -K.H_PLATTA - EPS_PL - 120 - 8.0 * s, "SEKTION B–B  Innervägg (V15)", skala=20, sz=9)
    return v


def detalj_horn():
    """C: yttre hörn i plan (t.ex. V21/V3), x = 0 och y = 0 i ytterlivet, väggarna inåt positivt. 1:20"""
    s = 20.0
    L_ = 1100.0
    v = Vy(x=252, y=104, w=74, h=80, skala=s, X0=-200.0, Y1=L_ + 100.0)
    e, k = K.T_EPS, K.T_KARNA
    with v.lager("vagg"):
        v.polygon([(0, 0), (L_, 0), (L_, K.T_VAGG), (K.T_VAGG, K.T_VAGG), (K.T_VAGG, L_), (0, L_)], fyll="eps",
                  stil="normal")
        v.polygon([(e, e), (L_, e), (L_, e + k), (e + k, e + k), (e + k, L_), (e, L_)], fyll="karna", stil="tunn")
        v.brott((L_, -40), (L_, K.T_VAGG + 40), "tunn")
        v.brott((-40, L_), (K.T_VAGG + 40, L_), "tunn")
    xo, xi = K.X_H_UT, K.X_H_IN
    L1, L2 = K.VINKEL_HORN
    with v.lager("armering"):
        for x_ in (xo, xi):
            v.linje([(x_ + L1, x_), (x_, x_), (x_, x_ + L2)], "ok")
        for x_, d in ((xo, 14.0), (xi, -14.0)):
            v.linje([(x_ + L1 - K.SKARV, x_ + d), (L_ - 20, x_ + d)], "normal")
            v.linje([(x_ + d, x_ + L2 - K.SKARV), (x_ + d, L_ - 20)], "normal")
    with v.lager("matt"):
        kedja(v, [xo, xo + L1], -4.6 * s, [xo] * 2, sz=5.6)
        kedja(v, [xo + L1 - K.SKARV, xo + L1], -2.2 * s, [xo + 14] * 2, sz=5.6)
    with v.lager("text"):
        v.text(-60, -60, "ute", a="rt", sz=6.0, col="gra", i=True)
        v.text(750, 750, "inne", a="cm", sz=6.0, col="gra", i=True)
        v.hanvisning((xo, 600.0), (530.0, 1050.0), "750 + 750, båda ytorna", bubbla=POS["horn"], a="lm", sz=6.0)
        v.hanvisning((950.0, xi - 14), (700.0, 520.0), "skarv 500", bubbla=POS["hor"], a="lm", sz=6.0)
        v.rubrik(-190, -330, "DETALJ C  Yttre hörn i plan", skala=20, sz=8.5)
    return v


def detalj_t():
    """D: anslutning mot en genomgående vägg i plan, V3 mot V19/V20 (lika V2 mot V15/V16), som i planen. x = 0 i den
    genomgående väggens mitt, y = 0 i V3:s mitt. 1:20"""
    s = 20.0
    v = Vy(x=252, y=12, w=74, h=88, skala=s, X0=-1220.0, Y1=760.0)
    t, k = K.T_VAGG / 2, K.T_KARNA / 2
    with v.lager("vagg"):
        v.polygon([(-t, -680), (t, -680), (t, 680), (-t, 680), (-t, t), (-1150, t), (-1150, -t), (-t, -t)],
                  fyll="eps", stil="normal")
        v.polygon([(-k, -680), (k, -680), (k, 680), (-k, 680), (-k, k), (-1150, k), (-1150, -k), (-k, -k)],
                  fyll="karna", stil="tunn")
        v.brott((-1150, -t - 40), (-1150, t + 40), "tunn")
        v.brott((-t - 40, 680), (t + 40, 680), "tunn")
        v.brott((-t - 40, -680), (t + 40, -680), "tunn")
    qb = k - K.C_IN - 5.0                                   # den genomgående väggens bortre järn (öster)
    y_n, y_s = k - K.C_UT - 5.0, -k + K.C_IN + 5.0          # V3:s järn mot fyllningen och mot källaren
    L2 = K.VINKEL_HORN[1]
    xt = qb - 24.0                                          # vinkeljärnens ben innanför den bortre ytans järn
    with v.lager("armering"):
        for y_, sida in ((y_n, 1), (y_s, -1)):
            v.linje([(xt - BEN["T"], y_), (xt, y_), (xt, sida * 640.0)], "ok")         # benet 750, avbrutet
            v.linje([(-1130.0, y_ - sida * 14), (xt - BEN["T"] + K.SKARV, y_ - sida * 14)], "normal")
        # den genomgående väggens bortre yta: V19:s och V20:s järn skarvas 500 i anslutningen
        v.linje([(qb, 660), (qb, -K.SKARV / 2)], "normal")
        v.linje([(qb - 12, -660), (qb - 12, K.SKARV / 2)], "normal")
        # den närmre ytan: järnen slutar vid V3:s järn
        v.linje([(-qb, -660), (-qb, y_s)], "normal")
        v.linje([(-qb, y_n), (-qb, 660)], "normal")
    with v.lager("text"):
        v.text(-650, 420, "fyllning", a="cm", sz=6.0, col="gra", i=True)
        v.text(-650, -420, "källare", a="cm", sz=6.0, col="gra", i=True)
        v.text(-t - 40, 600, "V20", a="rm", sz=5.8, col="gra")
        v.text(-t - 40, -600, "V19", a="rm", sz=5.8, col="gra")
        v.text(-1100, -t - 30, "V3", a="lt", sz=5.8, col="gra")
        v.hanvisning((xt, 450.0), (-1000.0, 230.0), "genom kärnan", bubbla=POS["t"], a="lm", sz=6.0)
        v.hanvisning((qb - 6, -150.0), (-1000.0, -330.0), "skarv 500", bubbla=POS["hor"], a="lm", sz=6.0)
        v.rubrik(-1210, -930, "DETALJ D  V3 mot V19/V20 i plan", skala=20, sz=8.5)
        v.text(-1210, -930 - 7.6 * s, "Samma vid V2 mot V15/V16.", a="lb", sz=6.0, col="gra")
    return v


SMYGLIST = dict(t=100.0, b=350.0, regel=(45.0, 195.0), spik=150.0)   # Sundolitt Kub U17 smyglist med regel 45 × 195


def smyglist(v, kant, mitt, rikt, langs, plan=True):
    """Sundolitts smyglist (100 × 350, kanal mot öppningen) med regel 45 × 195 i spåret och spik 150 genom regeln in
    i kärnan. kant: kärnans ände (koordinat längs rikt), mitt: väggens mitt i tvärled, rikt: +1 om öppningen ligger åt
    positivt håll. Tvärled är y i planen (plan=True) och x i sektionen."""
    t, b = SMYGLIST["t"], SMYGLIST["b"]
    tr, br = SMYGLIST["regel"]
    a0, a1 = sorted((kant, kant + rikt * t))
    r0, r1 = sorted((kant + rikt * (t - tr), kant + rikt * t))
    s0, s1 = sorted((kant - rikt * (SMYGLIST["spik"] - t), kant + rikt * t))
    R = (lambda a, b_, c, d: (a, c, b_, d)) if plan else (lambda a, b_, c, d: (c, a, d, b_))
    v.rekt(*R(a0, a1, mitt - b / 2, mitt + b / 2), fyll="eps", stil="normal")
    v.rekt(*R(r0, r1, mitt - br / 2, mitt + br / 2), fyll="#d9b77e", stil="tunn")      # regel 45 × 195
    v.linje([(s0, mitt), (s1, mitt)] if plan else [(mitt, s0), (mitt, s1)], "stal")      # spik 150, ingjuten


def detalj_oppning():
    """E: öppning F1, smygen i plan (snitt 1,6 m) och bröstningen i sektion, med Sundolitts smyglist. 1:10"""
    s = 10.0
    o = OPPN[0]
    # plan: x längs väggen, x = 0 i kärnans ände, y = 0 i väggens ytterliv (utsidan nedåt)
    v = Vy(x=24, y=186, w=70, h=60, skala=s, X0=-420.0, Y1=200.0)
    with v.lager("vagg"):
        v.rekt(-400, -K.T_VAGG, 0, 0, fyll="eps", stil="normal")
        v.rekt(-400, -K.T_VAGG + K.T_EPS, 0, -K.T_EPS, fyll="karna", stil="tunn")
        v.brott((-400, -K.T_VAGG - 30), (-400, 30), "tunn")
    with v.lager("smyg"):
        smyglist(v, 0.0, -K.T_VAGG / 2, 1, None, plan=True)
    with v.lager("armering"):
        for y_, dy in ((-K.T_EPS - K.C_UT - 5, -11.0), (-K.T_VAGG + K.T_EPS + K.C_IN + 5, 11.0)):
            v.linje([(-390, y_), (-30, y_)], "normal")
            v.cirkel(-40, y_ + dy, 6, fyll="#b5463a", stil=None, modell=True)
    with v.lager("matt"):
        kedja(v, [-40.0, 0.0, K.T_EPS], 60.0, [0.0] * 3, sz=5.6)
    with v.lager("text"):
        v.text(170, -175, "öppning", a="lm", sz=6.0, col="gra", i=True)
        v.hanvisning((80, -120), (170, 110), "smyglist 100 × 350 med regel 45 × 195,\nspik 150 ingjuten i kärnan",
                     a="lm", sz=6.0)
        v.text(-200, -K.T_VAGG - 40, "ute", a="ct", sz=6.0, col="gra", i=True)
        v.hanvisning((-40, -K.T_EPS - K.C_UT - 13), (-300, -470), "2 Ø12, en vid var yta", bubbla=POS["opp_sida"],
                     a="lm", sz=6.0)
        v.rubrik(-410, -640, "DETALJ E  Öppning F1: smyg i plan och bröstning", skala=10, sz=8.5)
    # bröstningen i sektion: z = 0 i bottenplattans överkant, x = 0 i ytterlivet
    w = Vy(x=130, y=186, w=60, h=60, skala=s, X0=-120.0, Y1=o["z0"] + 220.0)
    with w.lager("vagg"):
        w.rekt(0, o["z0"] - 320, K.T_VAGG, o["z0"], fyll="eps", stil="normal")
        w.rekt(K.T_EPS, o["z0"] - 320, K.T_EPS + K.T_KARNA, o["z0"], fyll="karna", stil="tunn")
        w.brott((-30, o["z0"] - 320), (K.T_VAGG + 30, o["z0"] - 320), "tunn")
    with w.lager("smyg"):
        smyglist(w, o["z0"], K.T_VAGG / 2, 1, None, plan=False)
    zb = o["z0"] - 40.0
    with w.lager("armering"):
        for x_ in (K.X_H_UT + 23, K.X_H_IN - 23):                 # innanför öppningens järn (26) vid sidorna
            w.cirkel(x_, zb, 6, fyll="#b5463a", stil=None, modell=True)
        z21 = max(z for z in K.Z_HOR if z < zb)
        for x_ in (K.X_H_UT, K.X_H_IN):
            w.cirkel(x_, z21, 5, fyll="svart", stil=None, modell=True)
        w.linje([(K.X_LODRAT, o["z0"] - 310), (K.X_LODRAT, zb - 6)], "ok_tunn")     # lodräta järn under bröstningen
    with w.lager("matt"):
        kedja(w, [zb, o["z0"], o["z0"] + K.T_EPS], -60.0, [0.0] * 3, sz=5.6, ax="y")
    with w.lager("text"):
        w.hanvisning((K.X_H_IN - 23, zb), (K.T_VAGG + 120, o["z0"] - 170), "2 Ø12",
                     bubbla=POS["opp_under"], a="lm", sz=6.0)
        w.hanvisning((K.X_LODRAT, o["z0"] - 250), (K.T_VAGG + 120, o["z0"] - 260), f"Ø10 s{K.ARM_V_TG[1]}",
                     bubbla=POS["lod_under"], a="lm", sz=6.0)
        w.text(-100, o["z0"] + K.T_EPS + 60, f"bröstning: betong {sv(o['z0'])}, färdig {sv(o['fardig'][2])}",
               a="lb", sz=6.0, col="gra")
        w.text(-30, o["z0"] - 250, "ute", a="rm", sz=6.0, col="gra", i=True)
        w.text(K.T_VAGG + 30, o["z0"] - 300, "inne", a="lm", sz=6.0, col="gra", i=True)
        w.hanvisning((K.T_VAGG / 2 + 60, o["z0"] + 80), (K.T_VAGG + 120, o["z0"] + 60),
                     "regel och smyglist med\ninspektionshål", a="lm", sz=6.0)
    return [v, w]


def blad_sektioner():
    vyer = [sektion_a(), sektion_b(), detalj_t(), detalj_horn(), *detalj_oppning()]
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=6.6, rader=[
            "Betong i väggarnas kärna B30 enligt Sundolitt (C30/37), största stenstorlek 16 mm, grov ballast minskad "
            "25 %, sättmått 180–200 mm. Armering B500B. Täckande skikt till de vågräta järnen 25 mm mot insidan och 30 mm mot utsidan.",
            "Montering: elementen staplas i förband med armeringen i bindarnas hållare och stagas enligt Sundolitts "
            "anvisning, vid hörn och öppningar och annars cirka var 2 m. Kapade element och kanter vid öppningar "
            "förstärks med plywood eller läkt. I hörn och anslutningar skärs cellplasten bort så att kärnorna går ihop. "
            "Öppningar enligt Sundolitt: smyglist Kub U17 vid sidorna och bröstningen (inte i överkant, som är "
            "mellanbjälklagets underkant), med regel 45 × 195 i spåret, "
            "fäst med grov spik 150 mm (förborra) som gjuts in i betongen, minst tre per sida och fler vid större "
            "öppningar. Smyglisterna stagas med tvärgående stag lodrätt och vågrätt. Bröstningens regel och smyglist "
            "får inspektionshål så att fyllningen kan kontrolleras (detalj E).",
            "Gjutning (K-06): pump med reducerat tryck, högst 1 m per timme och högst 2,4 m per gjutning, ingen "
            "vibrator i väggarna. Först ytterväggarnas tre hela skift, upp till 1\u00a0800, och innerväggarna i hela "
            "höjden, 2\u00a0100. Fogen ruggas och rengörs; innerväggarnas krön avjämnas och får glidskikt (byggpapp). "
            "Ytterväggarnas halva skift gjuts med mellanbjälklaget, med väggarnas betong (bjälklaget får gjutas med "
            "samma betong): fyll skiftet, vänta 30–60 min, fyll upp igen och gjut bjälklaget.",
            "Återfyllning först när betongens tryckhållfasthet nått 20 MPa (K-06, avsnitt 4.3). V3 och V20 fylls till 1,7 m "
            "före mellanbjälklaget, övriga väggar efter bjälklaget. Inom 1 m från väggen lager om högst 0,2 m och "
            "lätt vibroplatta (högst 100 kg).",
            "Insida: gips 13 mm på all cellplast, också i smygarna (REI 30 enligt TG 2216). Utsida: grundmursskiva "
            "och dränering enligt K-06, fasadsten ovan mark enligt AR-01.",
            "Plan R-04.1, armering R-04.2, elevationer R-04.3, rör och stålförteckning R-04.5."]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="yta", fyll="karna", stil="tunn", text="betongkärna, Kub 350-150"),
            dict(form="yta", fyll="betong", stil="tunn", text="betong, bottenplatta och mellanbjälklag"),
            dict(form="yta", fyll="eps", stil="tunn", text="cellplast"),
            dict(form="yta", fyll="eps2", stil="tunn", text="cellplast S300 (L-element, under balkar)"),
            dict(form="punkt", r=0.4, text="vågräta järn Ø10 (21)"),
            dict(form="linje", stil="ok", text="vinkeljärn, lodräta järn i väggen"),
            dict(form="linje", stil="uk", text="startjärn och armering i bottenplattan (R-05)")]),
    ]
    return Blad(hd("R-04.4"), REVISIONER, kol, vyer)


# ---------------------------------------------------------------- rör och stålförteckning (R-04.5)
def detalj_ror():
    """F: rör med topplåt och fotplåt i elevation med avbrott, z = 0 i plintens överkant. 1:10"""
    s = 10.0
    gap = (380.0, 1720.0)
    dz = gap[1] - gap[0] - 120.0
    Z = lambda z: z if z <= gap[0] + 60 else z - dz
    v = Vy(x=24, y=12, w=120, h=160, skala=s, X0=-300.0, Y1=Z(H + H_MB) + 250.0)
    bx, by, tf = K.FOTPLAT[1]
    with v.lager("betong"):
        v.rekt(-280, Z(H), 280, Z(H + H_MB), fyll="betong", stil=None)
        v.linje([(-280, Z(H)), (280, Z(H))], "normal")
        v.rekt(-280, -HB, 280, 0, fyll="betong", stil=None)
        v.linje([(-280, 0), (280, 0)], "normal")
        for x in (-280, 280):
            v.brott((x, -HB - 30), (x, 30), "tunn")
            v.brott((x, Z(H) - 30), (x, Z(H + H_MB) + 30), "tunn")
    with v.lager("stal"):
        for z0, z1 in ((0.0, gap[0]), (gap[1], H)):
            v.rekt(-K.PLAT / 2, Z(z0), K.PLAT / 2, Z(z1), fyll="#9aa0a8", stil="tunn")
            v.rekt(-K.PLAT / 2 + 4, Z(z0), K.PLAT / 2 - 4, Z(z1), fyll="vit", stil=None)
        v.brott((-90, Z(gap[0]) + 15), (90, Z(gap[0]) + 15), "tunn")
        v.brott((-90, Z(gap[1]) - 15), (90, Z(gap[1]) - 15), "tunn")
        v.rekt(-K.TOPPLAT[0] / 2, Z(H), K.TOPPLAT[0] / 2, Z(H) + K.TOPPLAT[2], fyll="stal", stil=None)
        v.rekt(-bx / 2, -tf, bx / 2, 0, fyll="stal", stil=None)
        for x in (-60.0, 60.0):
            v.linje([(x, -tf), (x, -tf - K.SVETSBULT[1] + 8)], "stal")
            v.rekt(x - 12, -tf - K.SVETSBULT[1], x + 12, -tf - K.SVETSBULT[1] + 8, fyll="stal", stil=None)
    with v.lager("matt"):
        v.text(K.PLAT / 2 + 60, (Z(gap[0]) + Z(gap[1])) / 2, f"L = {sv(K.L_ROR)}", a="lm", sz=6.4)
        kedja(v, [-bx / 2, bx / 2], -HB - 4.0 * s, [-tf] * 2, sz=5.8)
        kedja(v, [-tf - K.SVETSBULT[1], -tf], -bx / 2 - 3.0 * s, [-60.0, -bx / 2], sz=5.6, ax="y")
    with v.lager("text"):                         # texterna i höjd med det de visar
        for txt, mal, z in (("topplåt 80 × 80 × 8 S235, kant i kant med plattans undersida", (0, Z(H) + 4), Z(H) + 75),
                            ("kälsvets a3 runt om, båda ändarna (P7: tre sidor)", (K.PLAT / 2, Z(H) - 4), Z(H) - 70),
                            (f"rör {K.ROR_TEXT}", (K.PLAT / 2, Z(1900)), Z(1900)),
                            ("fotplåt 200 × 200 × 15 S355\n(P7: 280 × 200 × 15 eller 2 st 140 × 200 × 15)",
                             (bx / 2 - 20, -tf / 2), 70.0),
                            (f"4 svetsbultar Ø{K.SVETSBULT[0]:.0f}, L = {K.SVETSBULT[1]:.0f}", (60, -tf - 40), -60.0),
                            ("plint (R-05)", (220, -HB + 40), -HB + 40)):
            v.hanvisning(mal, (380.0, z), txt, a="lm", sz=6.2)
    with v.lager("rubrik"):
        v.rubrik(-290, -HB - 11.0 * s, "DETALJ F  Rör med topplåt och fotplåt", skala=10, sz=9)
    return v


def fotplatar():
    """G: fotplåtarna i plan, en för ett rör och P7:s för två rör, med svetsbultarna. 1:5"""
    ut = []
    for k, (n, x0) in enumerate(((1, 160.0), (2, 220.0))):
        s = 5.0
        bx, by, tf = K.FOTPLAT[n]
        v = Vy(x=x0 - 10 + (0 if n == 1 else 0), y=12, w=80, h=80, skala=s, X0=-bx / 2 - 60, Y1=by / 2 + 60)
        with v.lager("stal"):
            v.rekt(-bx / 2, -by / 2, bx / 2, by / 2, fyll="#c7cbd0", stil="normal")
            xs = (0.0,) if n == 1 else (-K.PLAT / 2, K.PLAT / 2)
            for xr in xs:
                v.rekt(xr - K.PLAT / 2, -K.PLAT / 2, xr + K.PLAT / 2, K.PLAT / 2, fyll="#9aa0a8", stil="tunn")
                v.rekt(xr - K.PLAT / 2 + 4, -K.PLAT / 2 + 4, xr + K.PLAT / 2 - 4, K.PLAT / 2 - 4, fyll="vit",
                       stil=None)
            for bxp, byp in K.BULT_LAGE[n]:
                v.cirkel(bxp, byp, K.SVETSBULT[0] / 2, fyll=None, stil="dold", modell=True)
            if n == 2:                                   # alternativt två plåtar 140 × 200, delade i mitten
                v.linje([(0, -by / 2 + 2), (0, by / 2 + 25)], "axel")
        with v.lager("matt"):
            xb = sorted({p[0] for p in K.BULT_LAGE[n]})
            yb = sorted({p[1] for p in K.BULT_LAGE[n]})
            kedja(v, [-bx / 2, xb[0], xb[1], bx / 2], -by / 2 - 4.0 * s, [-by / 2] * 4, sz=5.6)
            kedja(v, [-by / 2, yb[0], yb[1], by / 2], -bx / 2 - 4.0 * s, [-bx / 2] * 4, sz=5.6, ax="y")
        with v.lager("rubrik"):
            v.text(-bx / 2 - 55, by / 2 + 45, ("Fotplåt, ett rör" if n == 1 else "Fotplåt P7, två rör"), a="lb",
                   sz=7.4, b=True)
            v.text(-bx / 2 - 55, by / 2 + 45 - 4.0 * s, f"{sv(bx)} × {sv(by)} × {sv(tf)} S355, 1:5", a="lb",
                   sz=6.2, col="gra")
            if n == 2:
                v.text(-bx / 2 - 55, -by / 2 - 9.0 * s, f"alternativt 2 fotplåtar {sv(bx / 2)} × {sv(by)} × {sv(tf)}, "
                       "kant i kant vid streckprickad linje, 2 bultar var", a="lt", sz=6.0, col="gra")
        ut.append(v)
    return ut


def stalforteckning():
    """Väggarnas armering, positioner 21–28, ur samma funktioner som ritar järnen: raka vågräta järn (skarv 500 mot
    vinkeljärnen), vinkeljärn i hörn och anslutningar (ben som når en öppning kortade till 30 mm från kärnans ände),
    lodräta järn i ytterväggarna och under bröstningarna, järnen vid öppningarna."""
    rader, tot = [], {}

    def rad(pos, d, form, s_, n, L, m, anm):
        kg = m * VIKT[d]
        tot[d] = tot.get(d, 0.0) + kg
        rader.append([str(pos), f"Ø{d}", form, s_, str(n), L, sv(m, 0), sv(kg, 0), anm])
    m21 = m24 = 0.0
    n21 = n24 = 0
    for w in V:
        nl = lager_antal(w["namn"])
        for _, t0, t1 in raka(w):
            if w["namn"] == "V3":
                m24 += (t1 - t0) * nl; n24 += nl
            else:
                m21 += (t1 - t0) * nl; n21 += nl
    d, s_, st = K.ARM_H
    rad(POS["hor"], d, "rak", f"s{s_}/s{st}", n21, "var.", m21 / 1000, "vågräta, alla väggar utom V3")
    nl = sum(len(lodrata_t(w)) for w in V)
    rad(POS["lod"], K.ARM_V[0], "rak", f"s{K.ARM_V[1]}/s{K.ARM_V_TG[1]}", nl, sv(K.L_LODRAT), nl * K.L_LODRAT / 1000,
        "lodräta, ytterväggarnas insida")
    # vinkeljärn i hörnen, grupperade efter benens längd (kortade ben avrundade nedåt till 20 mm)
    grupper = {}
    for pos, pl, n in hornjarn():
        if pos != POS["horn"]:
            continue
        seg = min(zip(pl[:-1], pl[1:]), key=lambda ab: math.dist(*ab))          # det kortare benet
        kort = 20 * math.floor(math.dist(*seg) / 20 + 1e-6)
        vagg = _vagg_vid(*seg) if kort < K.VINKEL_HORN[0] else ""
        g = grupper.setdefault(kort, [0, set()])
        g[0] += n
        if vagg:
            g[1].add(vagg)
    for kort in sorted(grupper, reverse=True):
        n, vs = grupper[kort]
        L = K.VINKEL_HORN[1] + kort
        anm = "hörn" if not vs else "hörn, kortat ben i " + ", ".join(sorted(vs, key=lambda x: int(x[1:])))
        rad(POS["horn"], 10, f"L {sv(K.VINKEL_HORN[1])}+{sv(kort)}", "–", n, sv(L), n * L / 1000, anm)
    rad(POS["v3"], 10, "rak", "s300", n24, "var.", m24 / 1000, "V3, båda ytorna")
    nt = sum(n for pos, _, n in hornjarn() if pos == POS["t"])
    Lt = BEN["T"] + K.VINKEL_HORN[1]
    rad(POS["t"], 10, f"L {sv(BEN['T'])}+{sv(K.VINKEL_HORN[1])}", "–", nt, sv(Lt), nt * Lt / 1000, "anslutningar")
    sidor = {}
    for o in OPPN:
        za, zb = oppning_z(o)
        sidor.setdefault(zb - za, []).append(o["namn"])
    for L in sorted(sidor):
        n = 4 * len(sidor[L])
        rad(POS["opp_sida"], 12, "rak", "–", n, sv(L), n * L / 1000, "öppningarnas sidor, " + ", ".join(sidor[L]))
    for e in ELEV:
        oppn = oppningar_langs(e)
        for z, a_, b_, ba, bb in brostningsjarn(oppn, *karna_langs(e)):
            namn = ", ".join(o["namn"] for o in oppn if o["z0"] > 0 and abs(o["z0"] - 40.0 - z) < 1)
            L = (b_ - a_) + ba + bb
            form = "rak" if not (ba or bb) else ("L " + "+".join(sv(x) for x in (b_ - a_, ba, bb) if x))
            rad(POS["opp_under"], 12, form, "–", 2, sv(L), 2 * L / 1000, f"under bröstningen, {namn}")
    under = {}
    for o in OPPN:
        if o["typ"] == "yttre" and o["z0"] > 0:
            g = under.setdefault(o["z0"] - 40.0, [0, []])
            g[0] += len(lodrata_under(o))
            g[1].append(o["namn"])
    for L in sorted(under, reverse=True):
        n, namn = under[L]
        rad(POS["lod_under"], K.ARM_V_TG[0], "rak", f"s{K.ARM_V_TG[1]}", n, sv(L), n * L / 1000,
            "lodräta under bröstningen, " + ", ".join(namn))
    rader.append(["", "", "", "", "", "", "Summa", sv(sum(tot.values()), 0),
                  " + ".join(f"Ø{d}: {sv(k, 0)}" for d, k in sorted(tot.items()))])
    return dict(typ="tabell", kolumner=["Pos", "Ø", "Form", "s", "Antal", "L (mm)", "Total (m)", "Vikt (kg)", "Anm"],
                bredd=(0, 0, 0, 0, 0, 0, 0, 0, 1), rader=rader, just=["l", "l", "l", "l", "r", "r", "r", "r", "l"],
                sz=6.4)


def langsta_raka():
    """Det längsta raka vågräta järnet (mm)."""
    return max(t1 - t0 for w in V for _, t0, t1 in raka(w))


def _vagg_vid(p, q):
    """Namnet på den vägg vars kärna innehåller sträckan p–q (ett ben av ett vinkeljärn)."""
    ls = LineString([p, q])
    return max(V, key=lambda w: w["karna"].intersection(ls).length)["namn"]


def stal_ror():
    n_ror = sum(r["n"] for r in ROR)
    n1 = sum(1 for r in ROR if r["n"] == 1)
    n2 = sum(1 for r in ROR if r["n"] == 2)
    rader = [
        ["Rör", K.ROR_TEXT, str(n_ror), f"L = {sv(K.L_ROR)}"],
        ["Topplåt", "80 × 80 × 8, S235", str(n_ror), "svetsad på röret"],
        ["Fotplåt", "200 × 200 × 15, S355", str(n1), "ett rör"],
        ["Fotplåt", "280 × 200 × 15, S355", str(n2), "P7, två rör (alternativt 2 st 140 × 200 × 15)"],
        ["Svetsbult", f"Ø{K.SVETSBULT[0]:.0f}, L = {K.SVETSBULT[1]:.0f}", str(4 * (n1 + n2)), "fyra per fotplåt"],
    ]
    return dict(typ="tabell", kolumner=["Del", "Utförande", "Antal", "Anm"], bredd=(0, 1, 0, 1), rader=rader,
                just=["l", "l", "r", "l"], sz=6.4)


def blad_ror():
    vyer = [detalj_ror(), *fotplatar()]
    block = [dict(x=160, y=110, w=164, innehall=[
        dict(typ="rubrik", text="Stålförteckning, väggarnas armering, B500B"), stalforteckning(),
        dict(typ="text", sz=6.0, rader=["", f"Vågräta järn (21, 24) räknade längs väggarna med skarv 500 mot "
                                            f"vinkeljärnen; längsta raka järn {sv(langsta_raka() / 1000, 1)} m. "
                                            "Vinkeljärnens ben kortas till 30 mm från kärnans ände där väggen slutar "
                                            "vid en öppning."]),
        dict(typ="rubrik", text="Rör och plåtar"), stal_ror()])]
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=6.8, rader=[
            f"Rör {K.ROR_TEXT}, L = {sv(K.L_ROR)} från fotplåten till mellanbjälklagets underkant (K-05). Alla rör "
            "har samma tvärsnitt. P7 är två rör tätt intill varandra i x-led på en gemensam fotplåt; vart och ett "
            "har sin topplåt.",
            "Topplåt 80 × 80 × 8 S235, svetsad på röret och ingjuten kant i kant med mellanbjälklagets undersida "
            "(R-03). Över varje rör 2 + 2 Ø10 i underkant (R-03 pos 3).",
            "Fotplåt S355 med fyra svetsbultar under, ingjuten kant i kant med plintens överkant (R-05). P7: en "
            "fotplåt 280 × 200 × 15 eller alternativt 2 fotplåtar 140 × 200 × 15 kant i kant, med 2 svetsbultar var; "
            "bottenplattans nät läggs fritt från bultarna. Röret bär bara tryck; svetsen och bultarna håller det på "
            "plats.",
            "Svetsar: kälsvets a3 runt om mellan röret och plåtarna; vid P7, där rören ligger an mot varandra, på "
            "rörens tre fria sidor. Svetsbultarna svetsas på plåtens undersida (bultsvetsning).",
            "Rörens lägen: R-04.1. Montera rören på fotplåtarna innan mellanbjälklagets form byggs; topplåtens "
            "underkant i plattans underkant, 2\u00a0100 över bottenplattan.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="yta", fyll="betong", stil="tunn", text="betong"),
            dict(form="yta", fyll="stal", stil="tunn", text="stål, plåtar och bultar"),
            dict(form="yta", fyll="#9aa0a8", stil="tunn", text="rör VKR 80×80×4 (snitt)"),
            dict(form="linje", stil="dold", text="svetsbult under fotplåten")]),
    ]
    return Blad(hd("R-04.5"), REVISIONER, kol, vyer, block)


# ================================================================== 5. main
SERIE = "R-04 Källarstomme"


def main(dolj=(), blad=None):
    os.makedirs(UT, exist_ok=True)
    bladmapp = os.path.join(HERE, "blad")
    os.makedirs(bladmapp, exist_ok=True)
    fn = {"R-04.1": blad_plan, "R-04.2": blad_armering, "R-04.3": blad_elevationer, "R-04.4": blad_sektioner,
          "R-04.5": blad_ror}
    pdfer = []
    for nr, _, _, filnamn in BLADEN:
        if nr not in fn or (blad and nr not in blad):
            continue
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
