"""
AR-02 Utsättning: egen arbetsritning för utförandet (F-01 avsnitt 6), A3 med ../ritningsmall:

    AR-02.1  Plan med utsättningspunkter och koordinater     1:100, 1:10
    AR-02.2  Sektion med höjder                              1:50

Underlag: indata.toml (koordinatsystemets passning ur passning.py, fasadens skikt, höjderna ur bygglovet),
K-05:s bild/geometri.json (mellanbjälklagets kontur) och R-05:s kallare.py (bottenplattans kontur). Planen ritas i
K-05:s koordinater (mm, y uppåt), sektionen med y = höjden i RH2000 i mm. ritningsmall/ritning.py skalar till
papperet.

Filen är uppdelad i:
    1. Underlag           konturer, punkter, koordinater och höjder
    2. Vyer               plan, detalj och sektion
    3. Blad               högerkolumn, tabeller och ritningshuvud
    4. main               skriver AR-02.x.json och PDF:en i ritningar/

    python beräkningar/AR-02/ritningar.py
"""
import math
import os
import sys
import tomllib

import numpy as np
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient

HERE = os.path.dirname(os.path.abspath(__file__))
BER = os.path.dirname(HERE)
ROT = os.path.dirname(BER)
UT = os.path.join(ROT, "ritningar")
sys.path.insert(0, os.path.join(BER, "R-05"))
sys.path.insert(0, os.path.join(BER, "ritningsmall"))
import kallare as K  # noqa: E402   (R-05; läser K-05:s och K-06:s källfiler)
from ritning import Vy, Blad, huvud, sv, svm, PROJEKT  # noqa: E402

# ================================================================== 1. underlag
IN = tomllib.loads(open(os.path.join(HERE, "indata.toml"), encoding="utf-8").read())
REV, DATUM = IN["projekt"]["revision"], IN["projekt"]["datum"]
UNDERLAG = "Bygglov, K-05, R-05"
REVISIONER = [dict(rev=REV, avser="Första utgåvan", datum=DATUM, sign=PROJEKT["signatur"])]

KO = IN["koordinater"]
TH, E0, N0 = math.radians(KO["theta"]), KO["E0"], KO["N0"]
REGEL, BEKL = IN["fasad"]["regel"], IN["fasad"]["beklad"]
assert REGEL == K.KI, "väggens ytterliv ska vara mellanbjälklagets kantisolering (K-06 KI)"
FASAD_UT = REGEL + BEKL                                      # 95: fasadens utsida utanför mellanbjälklagets kant

KONTUR = Polygon(K.G["kontur"])
FASAD = KONTUR.buffer(FASAD_UT, join_style=2)
BOTTEN = K.KALLARE                                           # bottenplattans kant = källarväggarnas ytterliv
PLATTA = KONTUR.intersection(box(-500, BOTTEN.bounds[1], BOTTEN.bounds[2], 16500)).difference(BOTTEN)


def sweref(x, y):
    """K-05 (mm) → SWEREF 99 12 00 (N, E i m)."""
    return (N0 + (x * math.sin(TH) + y * math.cos(TH)) / 1000, E0 + (x * math.cos(TH) - y * math.sin(TH)) / 1000)


def horn(poly, start):
    """Polygonens hörn medurs, med början i hörnet närmast start."""
    c = [tuple(map(float, p)) for p in orient(poly.simplify(0.1), -1).exterior.coords[:-1]]
    i = min(range(len(c)), key=lambda k: math.dist(c[k], start))
    return c[i:] + c[:i]


F = horn(FASAD, (-1e4, 2e4))                                 # F1 längst upp till vänster, medurs
B = horn(BOTTEN, (-1e4, 1e4))                                # B1 vid plattan på mark, medurs
P = [p for p in horn(PLATTA.buffer(0.01, join_style=2).buffer(-0.01, join_style=2), (-1e4, 2e4))
     if BOTTEN.exterior.distance(Polygon([(p[0] - 1, p[1] - 1), (p[0] + 1, p[1] - 1), (p[0] + 1, p[1] + 1),
                                          (p[0] - 1, p[1] + 1)])) > 1]   # plattan på marks fria hörn
PUNKTER = [(f"F{i}", p) for i, p in enumerate(F, 1)] + [(f"B{i}", p) for i, p in enumerate(B, 1)] + \
          [(f"P{i}", p) for i, p in enumerate(P, 1)]

# höjder (RH2000, m → mm i sektionen)
H = IN["hojder"]
Z_FG = H["fg"] * 1000
Z_MB = Z_FG - H["golv"] * 1000                               # mellanbjälklagets överkant
Z_MB_U = Z_MB - H["h_bjalklag"] * 1000
Z_BP = Z_MB_U - H["h_kallare"] * 1000                        # bottenplattans överkant
Z_BP_U = Z_BP - H["h_platta"] * 1000
Z_MAK = Z_BP_U - H["t_cellplast"] * 1000                     # makadamens överkant
Z_BERG = Z_MAK - H["t_makadam"] * 1000                       # sprängbotten, högst
Z_MMN = H["mmn"] * 1000
Z_S = (H["mmn"] + H["byggnadshojd"]) * 1000                  # skärningspunkt fasad/takplan
TAN = math.tan(math.radians(H["takvinkel"]))
Z_MARK_NV, Z_MARK_SO = H["ny_mark_nv"] * 1000, H["ny_mark_so"] * 1000

# sektion A–A vid y = y_snitt: fasaderna och byggnadernas (vingarnas) gränser längs x
Y_SN = IN["hojder"]["y_snitt"]
XS_F = sorted({round(p[0], 1) for p in F})                   # −95, 4 405, 9 405, 13 905
X_V, X_H = XS_F[0], XS_F[-1]
VINGAR = list(zip(XS_F[:-1], XS_F[1:]))
NOCKAR = [((a + b) / 2, Z_S + (b - a) / 2 * TAN) for a, b in VINGAR]
Z_TOPP = max(z for _, z in NOCKAR)
assert abs(Z_S - (H["mmn"] + H["nockhojd"]) * 1000 + min(b - a for a, b in VINGAR) / 2 * TAN) < 2, \
    "bygglovets nockhöjd ska vara sidobyggnadernas nock"

# källarväggarna och plattan i sektionen (K-06): väggens ytterliv 30 utanför mellanbjälklagets kant
T_EPS, T_KARNA = K.T_EPS, K.T_KARNA
XB_V, XB_H = BOTTEN.bounds[0], BOTTEN.bounds[2]              # −30, 13 840
XK_V, XK_H = KONTUR.bounds[0], KONTUR.bounds[2]              # 0, 13 810

STEN = "#cfc9bf"
PANEL = "#e2cfa6"
PLATTA_F = "#dcd8cf"


# ================================================================== 2. vyer
def bisektris(c, i, inat=True):
    """Enhetsvektor längs hörnets bisektris, in i (eller ut ur) den medurs ordnade polygonen c."""
    a, b, d = np.array(c[i - 1]), np.array(c[i]), np.array(c[(i + 1) % len(c)])
    t1, t2 = (b - a) / np.linalg.norm(b - a), (d - b) / np.linalg.norm(d - b)
    n = np.array([t1[1], -t1[0]]) + np.array([t2[1], -t2[0]])      # högernormalerna = inåt för medurs
    n /= np.linalg.norm(n)
    return n if inat else -n


def plan():
    v = Vy(x=22, y=12, w=182, h=212, skala=100, X0=-2300, Y1=18600)
    with v.lager("ytor"):
        v.polygon(list(FASAD.exterior.coords), fyll="vit", stil=None)
        v.polygon(list(BOTTEN.exterior.coords), fyll="betong", stil="dold")
        v.polygon(list(PLATTA.exterior.coords), fyll=PLATTA_F, stil="dold")
    with v.lager("fasad"):
        v.polygon(list(FASAD.exterior.coords), fyll=None, stil="kontur")
    with v.lager("punkter"):
        for c, pre, inat, b in ((F, "F", False, True), (B, "B", True, False), (P, "P", True, False)):
            for i, p in enumerate(c):
                v.cirkel(*p, 0.45, fyll="svart", stil=None)
                if pre == "P":
                    j = PLATTA_HORN.index(p)
                    n = bisektris(PLATTA_HORN, j, True)
                else:
                    n = bisektris(c, i, inat)
                q = np.array(p) + n * v.m(3.6)
                v.text(q[0], q[1], f"{pre}{i + 1}", a="cm", sz=6.8 if b else 6.2, b=b, bg=True)
    with v.lager("matt"):
        # vid inåtgående hörn korsar de två måtten varandra: det ena (inåtgående hörnets "golv") läggs inuti huset
        def vanster(i):                                        # medurs: inåtgående hörn svänger vänster
            a, b, c = np.array(F[i - 1]), np.array(F[i]), np.array(F[(i + 1) % len(F)])
            u, w = b - a, c - b
            return u[0] * w[1] - u[1] * w[0] > 0
        konkav = [i for i in range(len(F)) if vanster(i)]
        inne = set()
        for i in konkav:                                       # kanten före eller efter hörnet, den som inte är längst
            a, b = (i - 1) % len(F), i
            la, lb = math.dist(F[a], F[i]), math.dist(F[i], F[(i + 1) % len(F)])
            inne.add(a if la < lb else b)
        for i, p in enumerate(F):
            q = F[(i + 1) % len(F)]
            if i in inne:
                v.matt(p, q, 7.5, sida=-1, sz=6.8)
            else:
                v.matt(p, q, 7.5, sz=6.8)
    with v.lager("snitt"):
        v.snittpil((X_V - v.m(8), Y_SN), (X_H + v.m(8), Y_SN), "A", sida=1)
    with v.lager("norr"):
        c = np.array([12300, 15600])
        d = np.array([math.sin(TH), math.cos(TH)])                 # norr i K-05:s koordinater
        v.linje([tuple(c - d * v.m(7)), tuple(c + d * v.m(5))], "normal")
        v.pil(tuple(c + d * v.m(7)), d, langd=3.2, bredd=2.4)
        q = c + d * v.m(10.5)
        v.text(q[0], q[1], "N", a="cm", sz=9, b=True)
        v.text(c[0] + v.m(5), c[1] - v.m(9), "SWEREF 99 12 00", a="cm", sz=6.4, col="gra")
    v.rubrik(-2000, 18100, "Plan, utsättningspunkter", 100)
    return v


PLATTA_HORN = horn(PLATTA.buffer(0.01, join_style=2).buffer(-0.01, join_style=2), (-1e4, 2e4))


def detalj():
    """Hörnet F12/B12 i plan: mellanbjälklagets kant, väggens ytterliv (= bottenplattans kant) och fasadens utsida."""
    xk, yk = XK_V, F[-1][1] + FASAD_UT                       # mellanbjälklagets hörn vid F12
    v = Vy(x=22, y=228, w=182, h=57, skala=10, X0=xk - 1420, Y1=yk + 260)
    with v.lager("ytor"):
        v.polygon([(xk, yk), (xk + 560, yk), (xk + 560, yk + 250), (xk, yk + 250)], fyll="betong", stil=None)
        v.polygon([(xk - REGEL, yk - REGEL), (xk + 560, yk - REGEL), (xk + 560, yk), (xk, yk), (xk, yk + 250),
                   (xk - REGEL, yk + 250)], fyll="eps", stil=None)
        v.polygon([(xk - FASAD_UT, yk - FASAD_UT), (xk + 560, yk - FASAD_UT), (xk + 560, yk - REGEL),
                   (xk - REGEL, yk - REGEL), (xk - REGEL, yk + 250), (xk - FASAD_UT, yk + 250)], fyll=PANEL, stil=None)
        skikt = np.cumsum([10, 12, 21])                        # utvändig gips, spikläkt, bärläkt, panel
        for s in skikt:
            o = REGEL + s
            v.linje([(xk - o, yk + 250), (xk - o, yk - o), (xk + 560, yk - o)], "fin")
    with v.lager("linjer"):
        for o, st in ((FASAD_UT, "kontur"), (REGEL, "normal"), (0, "normal")):
            v.linje([(xk - o, yk + 250), (xk - o, yk - o), (xk + 560, yk - o)], st)
    with v.lager("matt"):
        v.mattx([xk - FASAD_UT, xk - REGEL, xk], yk + 190, [yk + 150] * 3, sz=6.4)
        v.matty([yk - FASAD_UT, yk - REGEL, yk], xk + 470, [xk + 420] * 3, sz=6.4)
    with v.lager("text"):
        tx = xk - 700                                          # textens högra ände, vågräta hänvisningar
        for txt, mal in (("F  fasadens utsida", (xk - FASAD_UT, yk + 170)),
                         ("B  bottenplattans kant = väggens ytterliv", (xk - REGEL, yk + 95)),
                         ("mellanbjälklagets och plattan på marks kant", (xk, yk + 20))):
            v.hanvisning(mal, (tx, mal[1]), None)
            v.text(tx - v.m(1), mal[1], txt, a="rm", sz=6.6, bg=True)
        mal = (xk + 300, yk - FASAD_UT + 30)
        v.hanvisning(mal, (tx, yk - 150), None)
        v.text(tx - v.m(1), yk - 150, "beklädnad: utvändig gips 10, spikläkt 12, bärläkt 21, panel 22", a="rm", sz=6.6,
               bg=True)
    v.rubrik(xk + 900, yk + 160, "Detalj 1, hörnet F12/B12", 10)
    v.text(xk + 900, yk + 160 - 75, "lika runt huset", a="lt", sz=7.0, col="gra")
    return v


def niva(v, x, z, txt, a="l", under=False):
    """Nivåmärke: öppen triangel med spetsen på nivån, kort nivålinje och text (a = "l" text till höger)."""
    s = v.s
    h, b = 2.0 * s, 1.2 * s
    sg = -1 if under else 1
    v.polygon([(x, z), (x - b, z + sg * h), (x + b, z + sg * h)], fyll="vit", stil="tunn")
    L = 16 * s
    v.linje([(x - (3 * s if a == "l" else L), z), (x + (L if a == "l" else 3 * s), z)], "tunn")
    tz = z + sg * (h + 0.5 * s)
    v.text(x + (1.8 * s if a == "l" else -1.8 * s), tz, txt, a=("l" if a == "l" else "r") + ("b" if not under else "t"),
           sz=7.0, bg=True)


def sektion():
    v = Vy(x=20, y=14, w=306, h=170, skala=50, X0=X_V - 650, Y1=13500)
    s = v.s
    # mark utanför och makadam under plattan
    with v.lager("mark"):
        v.polygon([(XB_V - 350, Z_BERG), (XB_H + 350, Z_BERG), (XB_H + 350, Z_MAK), (XB_V - 350, Z_MAK)],
                  fyll="grus", stil="tunn")
        for sg, xe, xs, zm in ((1, X_V - 650, XB_V, Z_MARK_SO), (-1, X_H + 650, XB_H, Z_MARK_NV)):
            v.polygon([(xe, Z_BERG), (xs - sg * 350, Z_BERG), (xs - sg * 350, Z_MAK), (xs, Z_MAK), (xs, zm), (xe, zm)],
                      fyll="jord", stil=None)
        v.linje([(X_V - 650, Z_MARK_SO), (X_V, Z_MARK_SO)], "normal")
        v.linje([(X_H, Z_MARK_NV), (X_H + 650, Z_MARK_NV)], "normal")
        v.linje([(X_V - 650, Z_BERG), (X_H + 650, Z_BERG)], "tunn")
    # bottenplattan: cellplast 200 och betong 100, L-elementen i kanterna (K-06, R-04)
    with v.lager("bottenplatta"):
        v.rekt(XB_V, Z_MAK, XB_H, Z_BP, fyll="eps", stil="tunn")
        lb, bb = K.L_BEN, K.B_BALK
        v.polygon([(XB_V + lb, Z_MAK + K.T_FOT), (XB_V + lb + bb, Z_MAK + K.T_FOT), (XB_V + lb + bb, Z_BP_U),
                   (XB_H - lb - bb, Z_BP_U), (XB_H - lb - bb, Z_MAK + K.T_FOT), (XB_H - lb, Z_MAK + K.T_FOT),
                   (XB_H - lb, Z_BP), (XB_V + lb, Z_BP)], fyll="betong", stil="tunn")
    # källarväggar, mellanbjälklag, golv
    with v.lager("stomme"):
        for x0, sg in ((XB_V, 1), (XB_H, -1)):
            xs = [x0, x0 + sg * T_EPS, x0 + sg * (T_EPS + T_KARNA), x0 + sg * (2 * T_EPS + T_KARNA)]
            v.rekt(xs[0], Z_BP, xs[1], Z_MB_U, fyll="eps", stil="tunn")
            v.rekt(xs[1], Z_BP, xs[2], Z_MB_U, fyll="betong", stil="tunn")
            v.rekt(xs[2], Z_BP, xs[3], Z_MB_U, fyll="eps", stil="tunn")
            v.rekt(x0, Z_MB_U, x0 + sg * REGEL, Z_MB, fyll="eps", stil="tunn")
        v.rekt(XK_V, Z_MB_U, XK_H, Z_MB, fyll="betong", stil="tunn")
        v.linje([(XK_V + 65, Z_FG), (XK_H - 65, Z_FG)], "normal")
    # fasad: sten på källarväggarna, regelvägg och beklädnad på plan 1, upp till takplanet
    with v.lager("fasad"):
        for xf, xr, zm, sg in ((X_V, XB_V, Z_MARK_SO, 1), (X_H, XB_H, Z_MARK_NV, -1)):
            v.rekt(xf, zm - 50, xr, Z_MB, fyll=STEN, stil="tunn")
            zt_f, zt_r = Z_S, Z_S + abs(xr - xf) * TAN
            xi = xr + sg * 95
            zt_i = Z_S + abs(xi - xf) * TAN
            v.polygon([(xf, Z_MB), (xr, Z_MB), (xr, zt_r), (xf, zt_f)], fyll=PANEL, stil="tunn")
            v.polygon([(xr, Z_MB), (xi, Z_MB), (xi, zt_i), (xr, zt_r)], fyll="vit", stil="tunn")
    # takplanet
    with v.lager("tak"):
        pts = [(X_V, Z_S)]
        for (a, b), (xn, zn) in zip(VINGAR, NOCKAR):
            pts += [(xn, zn), (b, Z_S)]
        v.linje(pts, "kontur")
        for x in (X_V, X_H):
            v.cirkel(x, Z_S, 0.9, fyll="vit", stil="normal")
        v.linje([(X_V - 650, Z_MMN), (X_H + 650, Z_MMN)], "axel")
    # nivåer
    with v.lager("nivaer"):
        xm = NOCKAR[1][0]
        niva(v, xm, Z_TOPP, f"+{sv(Z_TOPP / 1000, 3)} högsta punkt", "l")
        for xn, zn in (NOCKAR[0], NOCKAR[2]):
            niva(v, xn, zn, f"+{sv(zn / 1000, 3)} nock", "l")
        niva(v, X_V + 2 * s, Z_S, f"+{sv(Z_S / 1000, 3)} skärningspunkt fasad/takplan", "l", under=True)
        niva(v, X_H - 2 * s, Z_S, f"+{sv(Z_S / 1000, 3)} skärningspunkt fasad/takplan", "r", under=True)
        for xd, _ in VINGAR[1:]:
            niva(v, xd, Z_S, f"+{sv(Z_S / 1000, 3)} dal", "l", under=True)
        niva(v, 1600, Z_FG, f"+{sv(Z_FG / 1000, 3)} FG, färdigt golv", "l")
        niva(v, 12300, Z_MB, f"+{sv(Z_MB / 1000, 3)} bjälklagets ök", "r", under=True)
        niva(v, 1600, Z_BP, f"+{sv(Z_BP / 1000, 3)} bottenplattans ök", "l")
        niva(v, 3200, Z_MMN, f"MMN +{sv(Z_MMN / 1000, 3)}", "l")
        niva(v, X_V - 330, Z_MARK_SO, f"+{sv(Z_MARK_SO / 1000, 3)}", "r")
        niva(v, X_H + 330, Z_MARK_NV, f"+{sv(Z_MARK_NV / 1000, 3)}", "l")
        for z, txt, x in ((Z_MAK, f"+{sv(Z_MAK / 1000, 3)} makadamens ök (cellplastens uk)", 4300),
                          (Z_BERG, f"+{sv(Z_BERG / 1000, 3)} sprängbotten, högst (makadam minst 150)", 9300)):
            niva(v, x, z, txt, "l", under=True)
    # mått från MMN
    with v.lager("matt"):
        xb = X_H - 1500
        v.matty([Z_MMN, Z_S], xb, [xb - 400, X_H - 120], texter=[f"byggnadshöjd {svm(Z_S - Z_MMN)}"])
        xn = NOCKAR[1][0] - 700
        v.matty([Z_MMN, Z_TOPP], xn, [xn - 400, NOCKAR[1][0] - 60], texter=[f"nockhöjd {svm(round(Z_TOPP - Z_MMN))}"])
        xk = 800
        v.matty([Z_MAK, Z_BP, Z_MB_U, Z_MB, Z_S], xk, [xk + 400] * 5)
    v.rubrik(X_V - 600, 13250, f"Sektion A–A, y = {svm(Y_SN)} (princip)", 50)
    return v


# ================================================================== 3. blad
BLADEN = [
    ("AR-02.1", ["Utsättning", "Plan och koordinater"], "1:100, 1:10", "AR-02.1 Utsättning, plan och koordinater"),
    ("AR-02.2", ["Utsättning", "Sektion och höjder"], "1:50", "AR-02.2 Utsättning, sektion och höjder"),
]


def hd(nr):
    b = [x for x in BLADEN if x[0] == nr][0]
    return huvud(nr, b[1], b[2], UNDERLAG, DATUM, REV)


def tabell(pre):
    rader = []
    for namn, (x, y) in PUNKTER:
        if namn.startswith(pre):
            n, e = sweref(x, y)
            rader.append([namn, svm(x), svm(y), sv(n, 3), sv(e, 3)])
    return dict(typ="tabell", kolumner=["Punkt", "x", "y", "N", "E"], bredd=(0.8, 1, 1, 1.9, 1.6),
                just=["l", "r", "r", "r", "r"], rader=rader, sz=6.8)


def blad_plan():
    block = [dict(x=210, y=12, w=112, innehall=[
        dict(typ="rubrik", text="Utsättningspunkter, SWEREF 99 12 00"),
        dict(typ="text", sz=6.8, rader=["x, y i mm (K-05), N, E i m."]),
        dict(typ="rubrik", text="Fasadens utsida (F)"), tabell("F"),
        dict(typ="rubrik", text="Bottenplattans kant (B)"), tabell("B"),
        dict(typ="rubrik", text="Plattan på marks kant (P)"), tabell("P"),
    ])]
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            "Koordinater i SWEREF 99 12 00 (Tanums kommun), höjder i RH2000 (AR-02.2). Mått i mm. x, y är husets "
            "koordinater i K-05, med origo i mellanbjälklagets kanter.",
            "Utstakning och lägeskontroll görs av certifierad mättekniker (krav i bygglovet BYGG.2025.2278).",
            f"Läget är passat mot bygglovets situationsplan (ritning 200): husets kontur är vriden och flyttad så att "
            f"den täcker husets yta i planen. Läget är därför inte noggrannare än situationsplanen, cirka ±0,1 m. "
            f"Måtten mellan punkterna är exakta. Kontrollera läget mot den reviderade situationsplanen före "
            f"utstakningen.",
            f"E = E0 + (x cos θ − y sin θ)/1 000, N = N0 + (x sin θ + y cos θ)/1 000, med θ = "
            f"{sv(KO['theta'], 4)}°, E0 = {sv(E0, 3)}, N0 = {sv(N0, 3)}.",
            f"Fasadens utsida (F) ligger {FASAD_UT} mm utanför mellanbjälklagets kant runt hela huset, även på "
            f"gavlarna: regeln {REGEL} och beklädnaden {BEKL} (detalj 1). Fasadstenen på källarväggarna har sin "
            f"framsida i samma liv (AR-01). Måtten över regelstommen är {2 * BEKL} mm mindre än fasadens.",
            f"Bottenplattans kant (B) ligger i källarväggarnas ytterliv, {BEKL} mm innanför fasaden. B1–B3 är "
            f"plattans kant mot plattan på mark, under källarväggarna V3 och V20.",
            f"Plattan på mark (P, tillbyggnaden) har sin kant i mellanbjälklagets kant, {FASAD_UT} mm innanför "
            f"fasaden. Den ansluter till källarväggarna mot B1–B3.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="linje", stil="kontur", text="fasadens utsida (F)"),
            dict(form="yta", fyll="betong", stil="dold", text="bottenplattan (B), källaren"),
            dict(form="yta", fyll=PLATTA_F, stil="dold", text="plattan på mark (P)"),
            dict(form="punkt", text="utsättningspunkt"),
        ]),
    ]
    return Blad(hd("AR-02.1"), REVISIONER, kol, [plan(), detalj()], block)


def blad_sektion():
    zn_lov = (H["mmn"] + H["nockhojd"]) * 1000
    m = lambda z: sv(z / 1000, 3)
    rader = [
        ["Högsta punkt, mittenbyggnadens nock", "+" + m(Z_TOPP),
         f"skärningspunkten + {svm((VINGAR[1][1] - VINGAR[1][0]) / 2)} · tan {H['takvinkel']}°; "
         f"{svm(round(Z_TOPP - Z_MMN))} över MMN"],
        ["Sidobyggnadernas nock", "+" + m(NOCKAR[0][1]),
         f"skärningspunkten + {svm((VINGAR[0][1] - VINGAR[0][0]) / 2)} · tan {H['takvinkel']}°; bygglovets "
         f"nockhöjd {svm(H['nockhojd'] * 1000)} över MMN (+{m(zn_lov)})"],
        ["Skärningspunkt fasad/takplan, takfot och dalar", "+" + m(Z_S),
         f"MMN + byggnadshöjd {svm(H['byggnadshojd'] * 1000)} (bygglov), nordvästra fasaden"],
        ["FG, färdigt golv plan 1", "+" + m(Z_FG), "bygglov"],
        ["Mellanbjälklagets överkant", "+" + m(Z_MB), f"FG − golv {svm(H['golv'] * 1000)}"],
        ["Ny mark, nordvästra fasaden", "+" + m(Z_MARK_NV), "bygglov (sektion E)"],
        ["MMN, medelmarknivå", "+" + m(Z_MMN), "bygglov"],
        ["Ny mark, sydöstra fasaden", "+" + m(Z_MARK_SO), "bygglov (sektion E)"],
        ["Bottenplattans överkant, golv i källaren", "+" + m(Z_BP),
         f"bjälklagets uk − {svm(H['h_kallare'] * 1000)} (K-06); bygglovet anger +{sv(H['kallargolv_bygglov'], 1)}"],
        ["Makadamens överkant, cellplastens underkant", "+" + m(Z_MAK),
         f"− platta {svm(H['h_platta'] * 1000)} − cellplast {svm(H['t_cellplast'] * 1000)} (R-04)"],
        ["Sprängbotten, högst", "+" + m(Z_BERG), f"makadam minst {svm(H['t_makadam'] * 1000)} (U-01)"],
    ]
    block = [dict(x=24, y=190, w=298, innehall=[
        dict(typ="rubrik", text="Höjder, RH2000"),
        dict(typ="tabell", kolumner=["Nivå", "RH2000 (m)", "Underlag"], bredd=(1.5, 0.6, 2.6),
             just=["l", "r", "l"], rader=rader, sz=6.8)])]
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            "Höjder i RH2000 (m), mått i mm. Sektionen är en principskiss: takets uppbyggnad, takfoten och "
            "stommen visas inte. Snittets läge: AR-02.1.",
            f"FG +{sv(H['fg'], 3)} är färdigt golv på plan 1. Mellanbjälklagets överkant ligger "
            f"{svm(H['golv'] * 1000)} mm lägre (golvet).",
            "Skärningspunkten mellan fasadens utsida och takplanets ovansida ligger på samma höjd runt hela huset "
            f"och i dalarna. Taklutning {H['takvinkel']}°.",
            f"Mittenbyggnaden är {svm(VINGAR[1][1] - VINGAR[1][0])} mm bred och sidobyggnaderna "
            f"{svm(VINGAR[0][1] - VINGAR[0][0])} mm, så mittenbyggnadens nock blir {svm(round(Z_TOPP - NOCKAR[0][1]))} "
            f"mm högre än sidobyggnadernas. Bygglovets nockhöjd ({svm(H['nockhojd'] * 1000)}) är sidobyggnadernas.",
            f"Byggnadshöjden mäts från MMN vid den nordvästra fasaden, där marken är högst (+{sv(H['ny_mark_nv'], 3)}).",
            f"Under plattan: minst {svm(H['t_makadam'] * 1000)} mm makadam på sprängt och avjämnat berg. "
            f"Plattans cellplast ligger direkt på makadamen.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="linje", stil="kontur", text="takplanets ovansida"),
            dict(form="linje", stil="axel", text="MMN"),
            dict(form="yta", fyll="betong", stil="tunn", text="betong"),
            dict(form="yta", fyll="eps", stil="tunn", text="cellplast"),
            dict(form="yta", fyll=STEN, stil="tunn", text="fasadsten (AR-01)"),
            dict(form="yta", fyll=PANEL, stil="tunn", text="beklädnad, plan 1"),
            dict(form="yta", fyll="grus", stil="tunn", text="makadam"),
            dict(form="yta", fyll="jord", stil=None, text="mark"),
        ]),
    ]
    return Blad(hd("AR-02.2"), REVISIONER, kol, [sektion()], block)


# ================================================================== 4. main
SERIE = "AR-02 Utsättning"


def main(dolj=()):
    os.makedirs(UT, exist_ok=True)
    bladmapp = os.path.join(HERE, "blad")
    os.makedirs(bladmapp, exist_ok=True)
    fn = {"AR-02.1": blad_plan, "AR-02.2": blad_sektion}
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
    for namn, (x, y) in PUNKTER:
        n, e = sweref(x, y)
        print(f"  {namn:4s} x {x:8.0f} y {y:8.0f}   N {n:.3f}  E {e:.3f}")


if __name__ == "__main__":
    main()
