"""
AR-02 Utsättning: egen arbetsritning för utförandet (F-01 avsnitt 6), A3 med ../ritningsmall:

    AR-02.1  Plan med utsättningspunkter och koordinater     1:100, 1:500
    AR-02.2  Sektion med höjder                              1:50

Underlag: indata.toml (koordinatsystemets passning ur passning.py, fasadens skikt, höjderna ur bygglovet),
K-05:s bild/geometri.json (mellanbjälklagets kontur) och R-05:s kallare.py (bottenplattans kontur). Planen ritas i
K-05:s koordinater (mm, y uppåt), sektionen med y = höjden i RH2000 i mm. ritningsmall/ritning.py skalar till
papperet.

Filen är uppdelad i:
    1. Underlag           konturer, punkter, koordinater och höjder
    2. Vyer               plan, översikt och sektion
    3. Blad               högerkolumn, tabeller och ritningshuvud
    4. main               skriver AR-02.x.json och PDF:en i ritningar/

    python beräkningar/AR-02/ritningar.py
"""
import math
import os
import sys
import tomllib

import numpy as np
from shapely.geometry import Point, Polygon, box
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
UNDERLAG = "Bygglov, NBK, K-05, R-05"
REVISIONER = [dict(rev=REV, avser="Första utgåvan", datum=DATUM, sign=PROJEKT["signatur"])]

KO = IN["koordinater"]
REGEL, BEKL = IN["fasad"]["regel"], IN["fasad"]["beklad"]
assert REGEL == K.KI, "väggens ytterliv ska vara mellanbjälklagets kantisolering (K-06 KI)"
FASAD_UT = REGEL + BEKL                                      # 95: fasadens utsida utanför mellanbjälklagets kant

KONTUR = Polygon(K.G["kontur"])
FASAD = KONTUR.buffer(FASAD_UT, join_style=2)
BOTTEN = K.KALLARE                                           # bottenplattans kant = källarväggarnas ytterliv
# plattan på mark byggs också med L-element: ytterkanten i väggarnas ytterliv, 30 mm utanför mellanbjälklagets kant
# (som bottenplattan och modellens mellanplatta med kantisolering)
PLATTA = KONTUR.buffer(REGEL, join_style=2).intersection(box(-500, BOTTEN.bounds[1], BOTTEN.bounds[2], 16500)) \
    .difference(BOTTEN)


def sweref(x, y):
    """K-05 (mm) → SWEREF 99 12 00 (N, E i m)."""
    return (N0 + (x * math.sin(TH) + y * math.cos(TH)) / 1000, E0 + (x * math.cos(TH) - y * math.sin(TH)) / 1000)


def lokal(n, e):
    """SWEREF 99 12 00 (N, E i m) → K-05 (mm)."""
    de, dn = (e - E0) * 1000, (n - N0) * 1000
    return (de * math.cos(TH) + dn * math.sin(TH), -de * math.sin(TH) + dn * math.cos(TH))




def rh(z):
    """Höjd i RH2000 (z i mm) som text, med tecken."""
    return ("+" if z >= 0 else "") + sv(z / 1000, 3)


def rel(z):
    """Höjd relativt fixpunkten (z i mm) som text."""
    d = round(z - Z_FIX)
    return f"{FIX['namn']} " + ("±0" if d == 0 else ("+" if d > 0 else "") + sv(d / 1000, 3))


def horn(poly, start):
    """Polygonens hörn medurs, med början i hörnet närmast start."""
    c = [tuple(map(float, p)) for p in orient(poly.simplify(0.1), -1).exterior.coords[:-1]]
    i = min(range(len(c)), key=lambda k: math.dist(c[k], start))
    return c[i:] + c[:i]


F = horn(FASAD, (2e4, 0))                                    # F1 = utsättningsdatans punkt 1, medurs
B = horn(BOTTEN, (2e4, 0))                                   # B1 innanför F1, medurs


def passa(lok, sw):
    """Vridning och förflyttning (minsta kvadrat) från K-05 (mm) till SWEREF (N, E i m): θ, E0, N0 och restfelen."""
    P = np.array(lok) / 1000
    Q = np.array([(e, n) for n, e in sw])
    pc, qc = P.mean(0), Q.mean(0)
    u, _, vt = np.linalg.svd((P - pc).T @ (Q - qc))
    r = (u @ vt).T
    assert np.linalg.det(r) > 0
    t = qc - r @ pc
    return math.atan2(r[1, 0], r[0, 0]), t[0], t[1], np.hypot(*((P @ r.T + t) - Q).T) * 1000


HORN_SW = [tuple(p) for p in KO["hornen"]]
assert len(HORN_SW) == len(F)
TH, E0, N0, RESTFEL = passa(F, HORN_SW)
assert RESTFEL.max() < KO["restfel_max"], f"utsättningsdatan avviker {RESTFEL.max():.1f} mm från fasadens mått"

FIX = IN["fixpunkt"]
P_FIX = lokal(FIX["N"], FIX["E"])
Z_FIX = FIX["hojd"] * 1000
P = [p for p in horn(PLATTA.buffer(0.01, join_style=2).buffer(-0.01, join_style=2), (-1e4, 2e4))
     if BOTTEN.exterior.distance(Polygon([(p[0] - 1, p[1] - 1), (p[0] + 1, p[1] - 1), (p[0] + 1, p[1] + 1),
                                          (p[0] - 1, p[1] + 1)])) > 1]   # plattan på marks fria hörn
# bottenplattans kant mot plattan på mark: hörnen på snittet mot plattan på mark (källarväggarna V3 och V20)
_ins = [i for i, p in enumerate(B) if PLATTA.distance(Point(p)) <= REGEL + 1]
B_MOT_P = f"B{min(_ins) + 1}–B{max(_ins) + 1}"
PUNKTER = [(f"F{i}", p) for i, p in enumerate(F, 1)] + [(f"B{i}", p) for i, p in enumerate(B, 1)] + \
          [(f"P{i}", p) for i, p in enumerate(P, 1)]

# höjder (RH2000, m → mm i sektionen)
H = IN["hojder"]
Z_FG = H["fg"] * 1000
Z_MB = Z_FG                                                  # mellanplattans överkant = FG (betonggolv)
Z_MB_U = Z_MB - H["h_bjalklag"] * 1000
Z_BP = Z_MB_U - H["h_kallare"] * 1000                        # bottenplattans överkant
Z_BP_U = Z_BP - H["h_platta"] * 1000
Z_MAK = Z_BP_U - H["t_cellplast"] * 1000                     # makadamens överkant
Z_BERG = Z_MAK - H["t_makadam"] * 1000                       # makadamens underkant (ritas bara)
Z_MAK_P = Z_MB - H["h_l_mark"] * 1000                         # plattan på mark: L-elementens uk, makadamens ök
Z_MMN = H["mmn"] * 1000
Z_S = (H["mmn"] + H["byggnadshojd"]) * 1000                  # skärningspunkt fasad/takplan (ritar taket)
# befintligt, inmätt (inmatning.toml): dräneringsbrunnen och dess utgående rör, avledningen för dränvattnet
INM = tomllib.loads(open(os.path.join(HERE, "inmatning.toml"), encoding="utf-8").read())
BRUNN, GOLV_G = INM["brunn"], INM["gammalt_golv"]
P_BRUNN = lokal(BRUNN["N"], BRUNN["E"])
Z_BRUNN = BRUNN["hojd"] * 1000
Z_DRAN_INM = Z_BRUNN - BRUNN["ror_under"] * 1000             # utgående rörets överkant, inmätt
Z_DRAN = Z_DRAN_INM + H["ror_marginal"] * 1000              # dimensionerande: marginal uppåt för mätosäkerheten
R_ROR = BRUNN["ror_d"] * 1000 / 2
Z_GOLV_G = GOLV_G["hojd"] * 1000
TAN = math.tan(math.radians(H["takvinkel"]))
Z_MARK_NV, Z_MARK_SO = H["ny_mark_nv"] * 1000, H["ny_mark_so"] * 1000

# sektion A–A vid y = y_snitt: fasaderna och byggnadernas (vingarnas) gränser längs x
Y_SN = IN["hojder"]["y_snitt"]
XS_F = sorted({round(p[0], 1) for p in F})                   # −95, 4 405, 9 405, 13 905
X_V, X_H = XS_F[0], XS_F[-1]
VINGAR = list(zip(XS_F[:-1], XS_F[1:]))
NOCKAR = [((a + b) / 2, Z_S + (b - a) / 2 * TAN) for a, b in VINGAR]

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
    with v.lager("brunn"):                                     # befintlig dräneringsbrunn (inmätt)
        x, y = P_BRUNN
        v.cirkel(x, y, 1.6, fyll="vit", stil="normal")
        v.cirkel(x, y, R_ROR, fyll="svart", stil=None, modell=True)
        v.hanvisning((x, y), (x - 2600, y + 1500), f"brunn, ök {rh(Z_BRUNN)}", punkt=False, sz=6.4)
    with v.lager("origo"):                                     # som R-05 och R-06
        L = 900
        v.linje([(0, 0), (L, 0)], "tunn"); v.pil((L + 150, 0), (1, 0), langd=2.2, bredd=1.0)
        v.linje([(0, 0), (0, L)], "tunn"); v.pil((0, L + 150), (0, 1), langd=2.2, bredd=1.0)
        v.ptext(L + 150, 0, 0, 0.8, "x", a="cb", sz=7.5, i=True)
        v.ptext(0, L + 150, 1.0, 0, "y", a="lm", sz=7.5, i=True)
        v.ptext(0, 0, 1.0, -1.0, "origo (0; 0)", a="lt", sz=6.4, col="gra")
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


def oversikt():
    """Husets läge mot fixpunkten, 1:500, med avstånden från fixpunkten till de närmaste hörnen."""
    v = Vy(x=212, y=142, w=108, h=142, skala=500, X0=-6000, Y1=P_FIX[1] + 9000)
    with v.lager("hus"):
        v.polygon(list(FASAD.exterior.coords), fyll="betong", stil="normal")
    with v.lager("fix"):
        x, y = P_FIX
        r = v.m(1.4)
        v.cirkel(x, y, 1.4, fyll="vit", stil="normal")
        k = r / math.sqrt(2)
        v.linje([(x - k, y - k), (x + k, y + k)], "normal"); v.linje([(x - k, y + k), (x + k, y - k)], "normal")
        v.ptext(x, y, 2.4, 1.2, f"{FIX['namn']} {rh(Z_FIX)}", a="lb", sz=7.0, b=True)
        n, e = FIX["N"], FIX["E"]
        for i, t in enumerate((f"N {sv(n, 3)}   E {sv(e, 3)}", f"x {svm(round(x))}   y {svm(round(y))}")):
            v.ptext(x, y, 2.4, -1.4 - i * 3.0, t, a="lt", sz=6.6)
        v.ptext(x, y, 2.4, -7.6, FIX["beskrivning"], a="lt", sz=6.4, col="gra")
    with v.lager("avstand"):
        hornen = [max((p for p in F if abs(p[0] - x) < 1), key=lambda p: p[1]) for x in (X_V, X_H)]  # övre hörnen
        for namn in [f"F{F.index(p) + 1}" for p in hornen]:
            q = dict(PUNKTER)[namn]
            v.linje([P_FIX, q], "axel")
            m = np.add(P_FIX, q) / 2
            d = np.subtract(q, P_FIX); ang = math.degrees(math.atan2(d[1], d[0]))
            ang = ang + 180 if ang > 90 or ang < -90 else ang
            nrm = np.array([-math.sin(math.radians(ang)), math.cos(math.radians(ang))])
            sid = 1 if dict(PUNKTER)[namn][0] > 0 else -1
            tp = m + nrm * v.m(1.0) * sid
            v.text(tp[0], tp[1], f"{sv(math.dist(P_FIX, q) / 1000, 1)} m", a="cb" if sid > 0 else "ct", sz=6.6,
                   rot=round(ang, 2), bg=True)
            v.ptext(*q, 1.5 * sid, 1.2, namn, a="lb" if sid > 0 else "rb", sz=6.6, b=True)
    with v.lager("norr"):
        c = np.array([P_FIX[0] - 2000, 6000])
        d = np.array([math.sin(TH), math.cos(TH)])
        v.linje([tuple(c - d * v.m(4)), tuple(c + d * v.m(3))], "normal")
        v.pil(tuple(c + d * v.m(4.5)), d, langd=2.4, bredd=1.8)
        q = c + d * v.m(7)
        v.text(q[0], q[1], "N", a="cm", sz=8, b=True)
    v.rubrik(-5500, P_FIX[1] + 4700, "Översikt, fixpunkt", 500)
    return v


def niva(v, x, z, txt, a="l", under=False, txt_x=None):
    """Nivåmärke: öppen triangel med spetsen på nivån, kort nivålinje och text (a = "l" text till höger). txt_x:
    texten står där i stället, med nivålinjen dragen dit (t.ex. genom en vägg)."""
    s = v.s
    h, b = 2.0 * s, 1.2 * s
    sg = -1 if under else 1
    v.polygon([(x, z), (x - b, z + sg * h), (x + b, z + sg * h)], fyll="vit", stil="tunn")
    L = 16 * s
    xt = x if txt_x is None else txt_x
    v.linje([(min(x, xt) - (3 * s if a == "l" else L), z), (max(x, xt) + (L if a == "l" else 3 * s), z)], "tunn")
    tz = z + sg * (h + 0.5 * s)
    v.text(xt + (1.8 * s if a == "l" else -1.8 * s), tz, txt, a=("l" if a == "l" else "r") + ("b" if not under else "t"),
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
    # bottenplattan: cellplast 300 och betong 100, L-elementen 400 i kanterna (K-06, R-04)
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
        v.linje([(X_V - 650, Z_MMN), (X_H + 650, Z_MMN)], "axel")
    # plattan på mark bakom snittet (bakom V3): L-elementens ytterkant och underkant, streckad
    with v.lager("platta_pa_mark"):
        xp0, xp1 = PLATTA.bounds[0], PLATTA.bounds[2]
        v.linje([(xp0, Z_MB), (xp0, Z_MAK_P), (xp1, Z_MAK_P), (xp1, Z_MB_U)], "dold")
    # nivåer
    with v.lager("nivaer"):
        t = lambda z, txt: f"{rh(z)} ({rel(z)}) {txt}"
        niva(v, 1600, Z_MB, t(Z_MB, "mellanplattans ök = FG"), "l")
        niva(v, 1600, Z_BP, t(Z_BP, "bottenplattans ök"), "l")
        niva(v, 6000, Z_MMN, f"MMN {rh(Z_MMN)} ({rel(Z_MMN)})", "l")
        niva(v, 1300, Z_MAK_P, t(Z_MAK_P, "plattan på mark bakom snittet, L-elementens uk"), "l", under=True)
        niva(v, 4300, Z_MAK, t(Z_MAK, "cellplastens uk under bottenplattan"), "l", under=True)
        niva(v, 9300, Z_DRAN, t(Z_DRAN, f"utgående rör ø110 ur brunnen, ök, dimensionerande (inmätt {rh(Z_DRAN_INM)} + {svm(H['ror_marginal'] * 1000)})"), "l", under=True)
    # utgående rör ur brunnen, i brunnens x (brunnen ligger vid y ≈ P_BRUNN[1], framför snittet)
    with v.lager("ror"):
        v.cirkel(P_BRUNN[0], Z_DRAN - R_ROR, R_ROR, fyll="vit", stil="normal", modell=True)
        v.linje([(P_BRUNN[0], Z_DRAN), (9300, Z_DRAN)], "tunn")
        xm = P_BRUNN[0] + 700                                  # rörets ök till cellplastens uk; texten bredvid
        v.matty([Z_DRAN, Z_MAK], xm, [P_BRUNN[0] + R_ROR] * 2, texter=[""])
        v.text(xm + 1.2 * s, (Z_DRAN + Z_MAK) / 2, svm(Z_MAK - Z_DRAN), a="lm", sz=6.8, bg=True)
    # mått från MMN
    with v.lager("matt"):
        xk = 800
        v.matty([Z_MAK, Z_BP, Z_MB_U, Z_MB], xk, [xk + 400] * 4)
    v.rubrik(X_V - 600, 13250, f"Sektion A–A, y = {svm(Y_SN)} (princip)", 50)
    return v


# ================================================================== 3. blad
BLADEN = [
    ("AR-02.1", ["Utsättning", "Plan och koordinater"], "1:100, 1:500", "AR-02.1 Utsättning, plan och koordinater"),
    ("AR-02.2", ["Utsättning", "Sektion och höjder"], "1:50", "AR-02.2 Utsättning, sektion och höjder"),
]


def hd(nr):
    b = [x for x in BLADEN if x[0] == nr][0]
    return huvud(nr, b[1], b[2], UNDERLAG, DATUM, REV)


def tabell(pre):
    rader = []
    for namn, (x, y) in PUNKTER + [(FIX["namn"], P_FIX)]:
        if namn.rstrip("0123456789") == pre:
            if pre == "F":                                     # utsättningsdatan som den är
                n, e = HORN_SW[int(namn[1:]) - 1]
            elif namn == FIX["namn"]:
                n, e = FIX["N"], FIX["E"]
            else:
                n, e = sweref(x, y)
            rader.append([namn, svm(x), svm(y), sv(n, 3), sv(e, 3)])
    return dict(typ="tabell", kolumner=["Punkt", "x", "y", "N", "E"], bredd=(0.8, 1, 1, 1.9, 1.6),
                just=["l", "r", "r", "r", "r"], rader=rader, sz=6.8)


def blad_plan():
    block = [dict(x=210, y=12, w=112, innehall=[
        dict(typ="rubrik", text="Utsättningspunkter, SWEREF 99 12 00"),
        dict(typ="text", sz=6.8, rader=[f"x, y i mm (K-05), N, E och höjder i m. Höjder i RH2000 och relativt "
                                         f"fixpunkten {FIX['namn']} ({rh(Z_FIX)})."]),
        dict(typ="rubrik", text="Fasadens utsida (F)"), tabell("F"),
        dict(typ="rubrik", text=f"Bottenplattans kant (B), L-elementens ytterkant, ök {rh(Z_BP)} ({rel(Z_BP)})"), tabell("B"),
        dict(typ="rubrik", text=f"Plattan på marks kant (P), L-elementens ytterkant, ök {rh(Z_MB)} ({rel(Z_MB)})"), tabell("P"),
        dict(typ="rubrik", text=f"Fixpunkt {FIX['namn']}, {rh(Z_FIX)}"), tabell(FIX["namn"]),
        dict(typ="rubrik", text=f"Dräneringsbrunnen (befintlig, inmätt), ök {rh(Z_BRUNN)}, utgående rör ø110 ök "
                                f"{rh(Z_DRAN)} (dimensionerande)"),
        dict(typ="tabell", kolumner=["Punkt", "x", "y", "N", "E"], bredd=(0.8, 1, 1, 1.9, 1.6),
             just=["l", "r", "r", "r", "r"], sz=6.8,
             rader=[["Brunn", svm(round(P_BRUNN[0])), svm(round(P_BRUNN[1])), sv(BRUNN["N"], 3), sv(BRUNN["E"], 3)]]),
    ])]
    # Underlag som inte står på ritningen:
    # - Höjderna mäts från dubben med avvägningsinstrument eller laser.
    # - F1–F12 är utsättningsdata 09_91, punkt 1–12; de stämmer med husets mått inom 1 mm (passa(), RESTFEL).
    # - Fasadens utsida ligger FASAD_UT = 95 mm utanför mellanbjälklagets kant runt hela huset, även på gavlarna:
    #   regeln 30 och beklädnaden 65 (utvändig gips 10, spikläkt 12, bärläkt 21, panel 22). Fasadstenen på
    #   källarväggarna har sin framsida i samma liv (AR-01). Måtten över regelstommen är 130 mm mindre än fasadens.
    # - Bottenplattans kant (B) ligger i källarväggarnas ytterliv, 65 mm innanför fasaden. B_MOT_P (B7–B9) är
    #   plattans kant mot plattan på mark, under källarväggarna V3 och V20.
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            "Koordinater i SWEREF 99 12 00 (Tanums kommun), höjder i RH2000 (AR-02.2). Mått i mm. x, y är husets "
            "koordinater, samma som i K-05 och på R-03–R-06: origo i skärningen mellan mellanbjälklagets kanter "
            "x = 0 och y = 0.",
            "Utstakning och lägeskontroll görs av certifierad mättekniker (krav i bygglovet BYGG.2025.2278).",
            f"Höjdreferens: fixpunkten {FIX['namn']}, byggfixen på nybyggnadskartan (2025-11-12): "
            f"{FIX['beskrivning']}, {rh(Z_FIX)}. Alla höjder anges i RH2000 och relativt dubben. Dubbens läge är "
            f"angivet i cm.",
            "Fasadens hörn F1–F12 är utsättningsdata. Bottenplattans (B) och plattan på marks (P) punkter är "
            "beräknade med samma läge:",
            f"E = E0 + (x cos θ − y sin θ)/1 000, N = N0 + (x sin θ + y cos θ)/1 000, med θ = "
            f"{sv(math.degrees(TH), 6)}°, E0 = {sv(E0, 4)}, N0 = {sv(N0, 4)}.",
            f"Plattan på mark (P, tillbyggnaden) byggs med L-element, {svm(H['h_l_mark'] * 1000)} mm höga. P är "
            f"L-elementens ytterkant, i linje med bottenplattans kant vid {B_MOT_P}.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="linje", stil="kontur", text="fasadens utsida (F)"),
            dict(form="yta", fyll="betong", stil="dold", text="bottenplattan (B), L-elementens ytterkant"),
            dict(form="yta", fyll=PLATTA_F, stil="dold", text="plattan på mark (P), L-elementens ytterkant"),
            dict(form="punkt", text="utsättningspunkt"),
            dict(form="bubbla", txt="•", text="dräneringsbrunn (befintlig, inmätt) med utgående rör ø110"),
        ]),
    ]
    return Blad(hd("AR-02.1"), REVISIONER, kol, [plan(), oversikt()], block)


def blad_sektion():
    rader = [
        ["Mellanplattans överkant = FG, färdigt golv plan 1", rh(Z_MB), rel(Z_MB)[len(FIX["namn"]) + 1:], "bygglov; betonggolv"],
        ["Plattan på mark: L-elementens och cellplastens underkant", rh(Z_MAK_P), rel(Z_MAK_P)[len(FIX["namn"]) + 1:],
         f"plattans ök − L-element {svm(H['h_l_mark'] * 1000)}"],
        [f"Fixpunkt {FIX['namn']}, {FIX['beskrivning']}", rh(Z_FIX), "±0", "nybyggnadskartan 2025-11-12 (byggfix)"],
        ["MMN, medelmarknivå", rh(Z_MMN), rel(Z_MMN)[len(FIX["namn"]) + 1:], "bygglov"],
        ["Dräneringsbrunnen (befintlig), överkant", rh(Z_BRUNN), rel(Z_BRUNN)[len(FIX["namn"]) + 1:],
         "inmätt 2026-11-01 (GNSS)"],
        ["Bottenplattans överkant", rh(Z_BP), rel(Z_BP)[len(FIX["namn"]) + 1:],
         f"mellanplattans ök − {svm(H['h_bjalklag'] * 1000)} − {svm(H['h_kallare'] * 1000)} (K-05, K-06)"],
        ["Cellplastens underkant under bottenplattan", rh(Z_MAK), rel(Z_MAK)[len(FIX["namn"]) + 1:],
         f"− platta {svm(H['h_platta'] * 1000)} − cellplast {svm(H['t_cellplast'] * 1000)} (R-04)"],
        ["Utgående rör ø110 ur brunnen, överkant: avledning för dränvattnet", rh(Z_DRAN),
         rel(Z_DRAN)[len(FIX["namn"]) + 1:], f"dimensionerande: inmätt {rh(Z_DRAN_INM)} (brunnens ök − {svm(BRUNN['ror_under'] * 1000)}) + "
         f"marginal {svm(H['ror_marginal'] * 1000)}"],
    ]
    rader.insert(1, ["Golvet i det gamla huset", rh(Z_GOLV_G), rel(Z_GOLV_G)[len(FIX["namn"]) + 1:],
                     "inmätt 2026-11-01 (GNSS)"])
    block = [dict(x=24, y=190, w=298, innehall=[
        dict(typ="rubrik", text="Höjder, RH2000"),
        dict(typ="tabell", kolumner=["Nivå", "RH2000 (m)", f"Relativt {FIX['namn']} (m)", "Underlag"],
             bredd=(1.6, 0.6, 0.7, 2.4), just=["l", "r", "r", "l"], rader=rader, sz=6.8)])]
    # Underlag som inte står på ritningen: sektionen visar inte takets uppbyggnad, takfoten och stommen; FG är
    # betonggolv utan golvbeläggning.
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            f"Höjder i RH2000 och relativt fixpunkten {FIX['namn']} ({rh(Z_FIX)}, gränsdubb i berg, se AR-02.1), i m. "
            "Mått i mm. Sektionen är en principskiss. Snittets läge: AR-02.1.",
            f"FG {rh(Z_FG)} är mellanplattans överkant.",
            "Bottenplattans cellplast läggs på avjämnad makadam (R-04).",
            f"Dräneringsbrunnen är befintlig och inmätt (läge AR-02.1, y = {svm(round(P_BRUNN[1]))}); dess utgående rör "
            f"ø110 är ritat i brunnens x. Överkant rör = brunnens överkant − {svm(BRUNN['ror_under'] * 1000)} = "
            f"{rh(Z_DRAN_INM)}; dimensionerande nivå {svm(H['ror_marginal'] * 1000)} mm högre, {rh(Z_DRAN)}, för "
            "mätosäkerheten.",
            f"Dräneringen runt källaren har överkanten i cellplastens underkant, {rh(Z_MAK)}, och faller mot brunnen "
            f"till rörets dimensionerande nivå: {svm(Z_MAK - Z_DRAN)} mm fall längs källaren (D-01).",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="linje", stil="kontur", text="takplanets ovansida"),
            dict(form="linje", stil="axel", text="MMN"),
            dict(form="linje", stil="dold", text=f"plattan på mark bakom snittet (L-element {svm(H['h_l_mark'] * 1000)})"),
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
