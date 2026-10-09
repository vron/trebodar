"""
Laster på mellanbjälklaget: utbredda laster (F-01) och alla laster från trästommen på plan 1 (K-01 och ytterväggar).

Punktlaster heter efter balken de kommer från, numrerade från balkens början (lägsta y): LN1_1, LN1_2, ... för
nockbalkar och LD2_1, ... för dalbalkar. Hörnstolparna under gavlarnas takstolar heter LA1–LA10. Linjelaster:
qD2 (dalbalk 2 via bärande vägg), qY1–qY12 (ytterväggar på plan 1), qT (trappan på trapphålets kant).

Laster som står över en Lecavägg förs i FE-modellen direkt till väggens upplagslinje (ger ingen böjning i
plattan, men ingår i väggens reaktion). Övriga laster verkar på plattan där de står.

    python laster.py      -> lastsammanställning (kontroll)
"""
import json
import math
import os

import numpy as np
from shapely.geometry import LineString, Point, Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
G = json.load(open(os.path.join(HERE, "bild", "geometri.json"), encoding="utf-8"))

# ------------------------------------------------------------------ indata
# Utbredda laster på bjälklaget [kN/m²] (F-01)
H_PLATTA = 150.0          # mm
G_BETONG = 25.0 * H_PLATTA / 1000      # 3,75, armerad betong 25 kN/m³ (SS-EN 1991-1-1 tabell A.1)
G_GOLV = 0.5              # golvuppbyggnad (trägolv ca 0,15, klinker i våtrum ca 0,5)
Q_NYTTIG = 2.0            # kategori A (EKS tabell C-1)
Q_VAGG = 0.7              # lätta mellanväggar, läggs till nyttig last (SS-EN 1991-1-1 6.3.1.2(8))

# Tak och väggar på plan 1
G_TAK = 0.56              # takets egenvikt per m² takyta (F-01: 57 kg/m²)
TAKVINKEL = 30.0
G_TAK_H = G_TAK / math.cos(math.radians(TAKVINKEL))     # per m² horisontell yta
S_K = 1.5                 # snö, formfaktor 1,0 (på säker sida mot 0,8), som K-01
G_VAGG = 0.6              # ytterväggens egenvikt per m² väggyta, fönster räknas som vägg (på säker sida)
H_VAGG = 2.5              # väggens höjd från bjälklaget till takfot [m]
UTSPRANG = 0.2            # takutsprång vid takfot och gavel, horisontellt [m]
CC_TAKBALK = 0.6          # takbalkarnas delning [m]
G_TAKSTOL = 0.25          # gaveltakstolens egenvikt per fot [kN] (2 × 45×220 och underramstycke ≈ 45 kg)
VAGG_IN = 17.5            # ytterväggens centrum innanför plattans kant [mm]: stommen 95 mm står från 30 mm utanför
                          # till 65 mm innanför kanten, över Lecans yttre skikt (Onshape-modellen)

# Dalbalk 2:s bärande vägg (träregelverk med gips på båda sidor): egentyngd utöver 0,7 kN/m² för lätta väggar.
# Väggen har en dörröppning mot trappan vid trapphålet; karmstolparna står vid hålets två långsidor.
G_D2VAGG = G_VAGG * H_VAGG                 # 1,5 kN/m
KARM = (95.0, 90.0)                        # karmstolpens upplagsyta: väggens tjocklek (x) × 2 × 45 (y) [mm]
STOLPE = (95.0, 90.0)                      # minsta stolpe 2 × 45×95 [mm]
STOLPE_B = (115.0, 115.0)                  # stolpe B (LD4_1), 115×115 GL30h
FOTPLAT_B = (250.0, 250.0, 15.0)           # stolpe B står på en fotplåt 250×250×15 S355 med förankring [mm]
HAVARM_B = 95.0                            # dalbalk 4 vilar på stolpe B med 95 mm hävarm; mittakstolen centriskt [mm]
AVST_P17 = 280.0                           # LN1_1 står 280 mm från P17 i y-led
# Trappan (trä) hänger på trapphålets kortsida. Vilken kortsida är inte bestämt: lasten läggs på båda.
TRAPPA = dict(langd=3.0, bredd=0.83, g=1.0, q=2.0)       # horisontell längd [m], bredd [m], kN/m² i plan

# K-01: stödreaktioner, dimensionerande R_max (6.10b) och R_min (vindlyft 1,0 G + γd 1,5 W) [kN]
# x från balkens vänstra ände; balkens läge i plan enligt geometri.json (balkar)
K01 = {
    "N1": dict(typ="nock", stod={"A": (0, 7.4, -3.0), "B": (1900, 19.9, -6.6), "C": (3800, 9.9, -17.3),
                                  "D": (5700, 49.3, -12.3), "E": (11570, 21.5, -6.3)}),
    "D2": dict(typ="dal", stod={"B": (10070, 21.2, -4.5)}, vagg_lyft=-18.6, vagg=(0, 6487)),
    "N3": dict(typ="nock", stod={"A": (85, 8.0, -3.4), "B": (2185, 23.9, -7.2), "C": (5985, 36.7, -9.4),
                                  "D": (10985, 18.9, -6.2)}),
    "D4": dict(typ="dal", stod={"A": (90, 14.0, -3.8), "B": (2340, 54.2, -9.0), "C": (7390, 31.0, -6.0)}),
    "N5": dict(typ="nock", stod={"A": (95, 17.5, -6.1), "B": (4675, 31.0, -7.1), "C": (7375, 32.6, -7.4),
                                  "D": (12275, 18.6, -6.4)}),
}
# Balkarnas last per meter i K-01 (G och S, kN/m): ger fördelningen G/S av en reaktion
K01_LAST = {"nock": (2.01, 3.75), "dal": (1.93, 7.13)}
GD = 0.91
# Snö per huskropp (för ojämn snö: snö på en eller två huskroppar). Dalbalkarna bär från båda sidor.
KROPPAR = ("V", "M", "H")               # vänster, mittre, höger huskropp (figur 1)
KROPP = {"N1": {"H": 1.0}, "N3": {"M": 1.0}, "N5": {"V": 1.0}, "D2": {"M": 0.5, "H": 0.5}, "D4": {"V": 0.5, "M": 0.5}}


def _kropp(S, fordelning):
    return {k: S * fordelning.get(k, 0.0) for k in KROPPAR}


def dela(Rd, typ):
    """Rd = γd (1,2 Gk + 1,5 Sk) med Sk/Gk som balkens last i K-01 -> (Gk, Sk)."""
    g, s = K01_LAST[typ]
    Gk = Rd / (GD * (1.2 + 1.5 * s / g))
    return Gk, Gk * s / g


def rd(Gk, Sk):
    return GD * (1.2 * Gk + 1.5 * Sk)


def rd_alla(Gk, Sk, Qk=0.0):
    """Största dimensionerande värde av 6.10a och 6.10b (Q eller S huvudlast)."""
    return max(GD * (1.35 * Gk + 1.5 * 0.7 * Qk + 1.5 * 0.6 * Sk), GD * (1.2 * Gk + 1.5 * Qk + 1.5 * 0.6 * Sk),
               GD * (1.2 * Gk + 1.5 * 0.7 * Qk + 1.5 * Sk))


def stod(namn, bok):
    b = K01[namn]
    x, Rmax, Rmin = b["stod"][bok]
    Gk, Sk = dela(Rmax, b["typ"])
    return dict(Gk=Gk, Sk=Sk, Wd=Rmin, ref=f"{namn} {bok}", Sb=_kropp(Sk, KROPP[namn]))


def strip(a, takfot=True):
    """Gaveltakstolens egen takremsa till en fot: (c/c/2 + utsprång) × (a + utsprång vid takfot) [m²]."""
    return (CC_TAKBALK / 2 + UTSPRANG) * (a + (UTSPRANG if takfot else 0.0))


# ------------------------------------------------------------------ punktlaster
def _summa(delar, x, y, namn, urspr, strip_a=None, takfot=True, extra_g=0.0, kropp=None):
    Gk = sum(f * d["Gk"] for f, d in delar) + extra_g
    Sk = sum(f * d["Sk"] for f, d in delar)
    Sb = {k: sum(f * d["Sb"][k] for f, d in delar) for k in KROPPAR}
    Wd = sum(f * d["Wd"] for f, d in delar)
    txt = [(("½ " if abs(f - 0.5) < 1e-9 else "") + d["ref"]) for f, d in delar]
    if strip_a is not None:
        A = strip(strip_a, takfot)
        Gk += G_TAK_H * A + G_TAKSTOL
        Sk += S_K * A
        Sb[kropp] += S_K * A
        txt.append("takstolens takremsa")
    return dict(namn=namn, x=float(x), y=float(y), Gk=Gk, Sk=Sk, Sb=Sb, Wd=Wd, urspr=urspr, delar=" + ".join(txt))


def punktlaster():
    st = {(s["urspr"]): s for s in G["stolpar"]}
    pos = lambda u: (st[u]["x"], st[u]["y"])
    aL, aM = 2.155, 2.405          # horisontellt avstånd nock–takfot: vänster/höger huskropp, mittre
    aD = 2.375                     # nock–dal (K-01 dalbalk: (2,50 + 2,25)/2)
    n3c = stod("N3", "C")
    sD2_1 = st["D2 vid trapphålet + ½ N3 C"]["Sk"]
    sD2_2 = st["D2, väggände"]["Sk"]
    (hx0, hy0), (hx1, hy1) = G["hal"][0], G["hal"][2]
    xD2 = G["linjelaster"][0]["x"]
    y_karm1, y_karm2 = hy0 - KARM[1] / 2 - 3, hy1 + KARM[1] / 2 + 3      # karmstolparnas mitt
    l_dorr = 0.5 * (y_karm2 - y_karm1) / 1000 + KARM[1] / 2000             # halva dörröppningen + karmen [m]
    gq = G["linjelaster"][0]
    y_slut2 = G["linjelaster"][1]["y0"]                                   # qD2 börjar igen efter öppningen
    l_mellan = (y_slut2 - y_karm2) / 1000 - KARM[1] / 2000                 # vägg mellan karm och qD2
    pel = G["pelare"]
    x17, y17 = pel[16]
    xB, yB = st["D4 stöd B + ½ N3 C"]["x"], st["D4 stöd B + ½ N3 C"]["y"]
    x10, y10 = pel[9]
    ev = np.array([xB - x10, yB - y10]); ev /= np.linalg.norm(ev)       # bort från P10
    # excentricitet i stolpe B ur dagens laster: hela dalbalk 4:s reaktion på hävarmen, mittakstolen centriskt
    d4b = stod("D4", "B")
    Rd_d4b, Rd_n3c = rd(d4b["Gk"], d4b["Sk"]), rd(0.5 * n3c["Gk"], 0.5 * n3c["Sk"])
    e_B = Rd_d4b * HAVARM_B / (Rd_d4b + Rd_n3c)
    L = [
        _summa([(1, stod("N1", "B"))], x17, y17 + AVST_P17, "LN1_1", "nockbalk 1, stöd B"),
        _summa([(1, stod("N1", "C"))], *pos("N1 stöd C"), "LN1_2", "nockbalk 1, stöd C"),
        _summa([(1, stod("N1", "D"))], *pos("N1 stöd D"), "LN1_3", "nockbalk 1, stöd D (dubbeltriangel)"),
        # D2: bärande vägg med dörröppning vid trapphålet. Karmstolparna bär väggen och dalbalken över öppningen.
        dict(namn="LD2_1", x=xD2, y=y_karm1, Gk=(gq["gk"] + G_D2VAGG) * l_dorr, Sk=gq["sk"] * l_dorr,
             Sb={"V": 0.0, "M": 0.5 * gq["sk"] * l_dorr, "H": 0.5 * gq["sk"] * l_dorr},
             Wd=K01["D2"]["vagg_lyft"] / 6.487 * l_dorr, yta=KARM,
             urspr="dalbalk 2, karmstolpe vid dörröppningen", delar="karm: D2 och vägg över halva öppningen"),
        dict(namn="LD2_2", x=xD2, y=y_karm2, Gk=st["D2 vid trapphålet + ½ N3 C"]["Gk"] + G_D2VAGG * (l_dorr + l_mellan),
             Sk=sD2_1, Sb={"V": 0.0, "M": 0.5 * (sD2_1 - 0.5 * n3c["Sk"]) + 0.5 * n3c["Sk"],
                           "H": 0.5 * (sD2_1 - 0.5 * n3c["Sk"])}, Wd=0.5 * n3c["Wd"] + K01["D2"]["vagg_lyft"] / 6.487 * 1.83,
             yta=KARM, urspr="dalbalk 2, karmstolpe vid dörröppningen + ½ nockbalk 3, stöd C via mittakstolen",
             delar="karm: D2 och vägg vid öppningen + ½ N3 C"),
        dict(namn="LD2_3", x=xD2, y=7280.0, Gk=st["D2, väggände"]["Gk"], Sk=sD2_2,
             Sb={"V": 0.0, "M": 0.5 * sD2_2, "H": 0.5 * sD2_2}, Wd=0.0,
             urspr="dalbalk 2, bärande väggs ände", delar="D2 vägg, största värde inom 0,5 m från väggänden"),
        _summa([(1, stod("D2", "B")), (0.5, stod("N3", "D"))], *pos("D2 stöd B"), "LD2_4",
               "dalbalk 2, stöd B + ½ nockbalk 3, stöd D (gaveltakstol)", strip_a=aD, takfot=False, kropp="M"),
        _summa([(1, stod("N3", "B"))], *pos("N3 stöd B"), "LN3_1", "nockbalk 3, stöd B"),
        dict(_summa([(1, stod("D4", "B")), (0.5, n3c)], xB + e_B * ev[0], yB + e_B * ev[1], "LD4_1",
                    "dalbalk 4, stöd B + ½ nockbalk 3, stöd C via mittakstolen"),
             yta=FOTPLAT_B[:2], mitt=(xB, yB), e=e_B, M_d=Rd_d4b * HAVARM_B / 1e3),
        _summa([(1, stod("D4", "C")), (0.5, stod("N3", "D"))], *pos("D4 stöd C"), "LD4_2",
               "dalbalk 4, stöd C + ½ nockbalk 3, stöd D (gaveltakstol)", strip_a=aD, takfot=False, kropp="M"),
        _summa([(1, stod("N5", "B"))], *pos("N5 stöd B"), "LN5_1", "nockbalk 5, stöd B"),
        _summa([(1, stod("N5", "C"))], *pos("N5 stöd C"), "LN5_2", "nockbalk 5, stöd C"),
    ]
    e = VAGG_IN
    hörn = [  # (x, y, delar, a, text)
        (4500 + e, 0 + e, [(0.5, stod("N3", "A"))], aM, "mittre huskroppen, nedre gaveln"),
        (9310 - e, 0 + e, [(0.5, stod("N3", "A"))], aM, "mittre huskroppen, nedre gaveln"),
        (9370, 1000 + e, [(0.5, stod("N1", "A"))], aL, "högra huskroppen, nedre gaveln (dalbalk 2:s ände)"),
        (13810 - e, 1000 + e, [(0.5, stod("N1", "A"))], aL, "högra huskroppen, nedre gaveln"),
        (0 + e, 3590 + e, [(0.5, stod("N5", "A"))], aL, "vänstra huskroppen, nedre gaveln"),
        (4530, 3590 + e, [(0.5, stod("N5", "A")), (1, stod("D4", "A"))], aL,
         "vänstra huskroppen, nedre gaveln + dalbalk 4, stöd A"),
        (9500 + e, 12510 - e, [(0.5, stod("N1", "E"))], aL, "högra huskroppen, övre gaveln"),
        (13810 - e, 12510 - e, [(0.5, stod("N1", "E"))], aL, "högra huskroppen, övre gaveln"),
        (0 + e, 15900 - e, [(0.5, stod("N5", "D"))], aL, "vänstra huskroppen, övre gaveln"),
        (4310 - e, 15900 - e, [(0.5, stod("N5", "D"))], aL, "vänstra huskroppen, övre gaveln"),
    ]
    for i, (x, y, d, a, t) in enumerate(hörn, 1):
        kr = "M" if "mittre" in t else ("H" if "högra" in t else "V")
        L.append(_summa(d, x, y, f"LA{i}", "hörnstolpe: " + t, strip_a=a, kropp=kr))
    for p in L:
        p.setdefault("yta", STOLPE)
        p.setdefault("mitt", (p["x"], p["y"]))          # upplagsytans mitt (lasten kan ligga excentriskt)
        p["Rd"] = rd(p["Gk"], p["Sk"])
        p["plats"] = plats(p["x"], p["y"])
    return L


# ------------------------------------------------------------------ var står lasten?
MARK = Polygon(G["mark"])


def over_vagg(x, y, marg=175.0):
    """Står punkten ovanpå en källarvägg (inom väggens tjocklek, ändarna förlängda 175 mm)?"""
    for ax, c, a, bb, *_ in G["vagg"]:
        if ax == "h" and a - marg <= x <= bb + marg and abs(y - c) <= marg:
            return True
        if ax == "v" and a - marg <= y <= bb + marg and abs(x - c) <= marg:
            return True
    return False


FRIA = [LineString(k) for k in G.get("fria_kanter", [])]      # plattkant över källarens öppningar


def plats(x, y):
    for k in FRIA:                      # över en öppning: lasten står på plattans fria kant
        s = k.project(Point(x, y))
        if 0 < s < k.length and k.distance(Point(x, y)) < 200:
            return "platta"
    if over_vagg(x, y):
        return "vägg"
    if MARK.buffer(1).contains(Point(x, y)):
        return "mark"
    return "platta"


# ------------------------------------------------------------------ ytterväggar på plan 1
def ytterväggar():
    """Ytterväggarnas linjelaster. Takfotsväggar: tak och snö från takbalkarna (halva spännvidden + utsprång)
    plus egenvikt. Gavelväggar: egenvikt inklusive gavelspetsen (taket går via gaveltakstolen till hörnen)."""
    e = VAGG_IN
    t = lambda a: a / 2 + UTSPRANG          # takfotsväggens lastbredd [m]
    W = [  # namn, p0, p1, typ, (lastbredd) eller (nockens läge och avstånd nock–lägsta takkant längs väggen)
        ("qY1", (4500, e), (9310, e), "gavel", dict(nock=6905, dr=2405), "mittre huskroppen, nedre gaveln"),
        ("qY2", (9310 - e, 0), (9310 - e, 1000), "takfot", dict(t=t(2.405)), "mittre huskroppen, högra långsidan"),
        ("qY3", (9310, 1000 + e), (13810, 1000 + e), "gavel", dict(nock=11655, dr=2375), "högra huskroppen, nedre gaveln"),
        ("qY4", (13810 - e, 1000), (13810 - e, 12510), "takfot", dict(t=t(2.155)), "högra huskroppen, högra långsidan"),
        ("qY5", (9500, 12510 - e), (13810, 12510 - e), "gavel", dict(nock=11655, dr=2155), "högra huskroppen, övre gaveln"),
        ("qY6", (9500 + e, 11010), (9500 + e, 12510), "takfot", dict(t=t(2.155)), "högra huskroppen, vänstra långsidan"),
        ("qY7", (4310, 11010 - e), (9500, 11010 - e), "gavel", dict(nock=6905, dr=2375), "mittre huskroppen, övre gaveln"),
        ("qY8", (4310 - e, 11010), (4310 - e, 15900), "takfot", dict(t=t(2.155)), "vänstra huskroppen, högra långsidan"),
        ("qY9", (0, 15900 - e), (4310, 15900 - e), "gavel", dict(nock=2155, dr=2155), "vänstra huskroppen, övre gaveln"),
        ("qY10", (0 + e, 3590), (0 + e, 15900), "takfot", dict(t=t(2.155)), "vänstra huskroppen, vänstra långsidan"),
        ("qY11", (0, 3590 + e), (4500, 3590 + e), "gavel", dict(nock=2155, dr=2375), "vänstra huskroppen, nedre gaveln"),
        ("qY12", (4500 + e, 0), (4500 + e, 3590), "takfot", dict(t=t(2.405)), "mittre huskroppen, vänstra långsidan"),
    ]
    tan = math.tan(math.radians(TAKVINKEL))
    out = []
    for namn, p0, p1, typ, par, txt in W:
        L = LineString([p0, p1])
        horis = p0[1] == p1[1]

        def last(s, par=par, typ=typ, p0=p0, horis=horis):
            """(gk, sk) [kN/m] i punkten s mm från p0."""
            if typ == "takfot":
                return G_VAGG * H_VAGG + G_TAK_H * par["t"], S_K * par["t"]
            u = (p0[0] + s) if horis else (p0[1] + s)
            h = H_VAGG + tan * max(par["dr"] - abs(u - par["nock"]), 0.0) / 1000
            return G_VAGG * h, 0.0
        n = int(math.ceil(L.length / 50))
        s = (np.arange(n) + 0.5) * L.length / n
        ds = L.length / n
        pts = [L.interpolate(si).coords[0] for si in s]
        gs = np.array([last(si) for si in s])
        var = [plats(*p) for p in pts]
        kr = "M" if "mittre" in txt else ("H" if "högra" in txt else "V")
        prov = [dict(x=p[0], y=p[1], G=g * ds / 1000, S=sk * ds / 1000, plats=v, kropp=kr)
                for p, (g, sk), v in zip(pts, gs, var)]
        d = dict(namn=namn, p0=p0, p1=p1, typ=typ, text=txt, langd=L.length, prov=prov,
                 Gk=float(gs[:, 0].sum() * ds / 1000), Sk=float(gs[:, 1].sum() * ds / 1000),
                 gk_max=float(gs[:, 0].max()), sk_max=float(gs[:, 1].max()), gk_min=float(gs[:, 0].min()))
        for v in ("vägg", "platta", "mark"):
            d["L_" + v] = sum(ds for x in var if x == v)
        if typ == "takfot":
            d["t"] = par["t"]
        out.append(d)
    return out


# ------------------------------------------------------------------ övriga linjelaster
def linjelaster():
    """qD2 från dalbalk 2 via bärande vägg på plan 1 (K-01), och trappan på trapphålets kortsidor."""
    ll = G["linjelaster"]
    L = []
    lyft = K01["D2"]["vagg_lyft"] / (K01["D2"]["vagg"][1] / 1000)      # kN/m
    (hx0, hy0), (hx1, hy1) = G["hal"][0], G["hal"][2]
    for i, l in enumerate(ll):
        y1 = min(l["y1"], hy0 - KARM[1] - 3) if l["y0"] < hy0 else l["y1"]   # slutar vid karmstolpen
        L.append(dict(namn="qD2", pl=[(l["x"], l["y0"]), (l["x"], y1)], gk=l["gk"] + G_D2VAGG, sk=l["sk"], qk=0.0, wd=lyft,
                      skropp={"M": 0.5, "H": 0.5},
                      text="dalbalk 2 via bärande vägg på plan 1"))
    (x0, y0), (x1, y1) = G["hal"][0], G["hal"][2]
    tr = TRAPPA
    gk = 0.5 * tr["langd"] * tr["g"] * tr["bredd"] / (abs(y1 - y0) / 1000)
    qk = 0.5 * tr["langd"] * tr["q"] * tr["bredd"] / (abs(y1 - y0) / 1000)
    for x in (x0, x1):
        L.append(dict(namn="qT", pl=[(x, y0), (x, y1)], gk=gk, sk=0.0, qk=qk, wd=0.0, skropp={},
                      text="trappan, halva trappan hänger på hålets kortsida"))
    return L


def alla():
    return dict(punkter=punktlaster(), vaggar=ytterväggar(), linjer=linjelaster())


if __name__ == "__main__":
    A = alla()
    print(f"tak {G_TAK_H:.3f} kN/m² horisontellt, snö {S_K}")
    for p in A["punkter"]:
        print(f"{p['namn']:6s} ({p['x']:6.0f},{p['y']:6.0f}) {p['plats']:6s} Gk {p['Gk']:5.1f} Sk {p['Sk']:5.1f} "
              f"Rd {p['Rd']:5.1f} Wd {p['Wd']:6.1f}  {p['delar']}")
    for w in A["vaggar"]:
        print(f"{w['namn']:5s} {w['typ']:6s} L {w['langd']:6.0f}  gk {w['gk_min']:.2f}–{w['gk_max']:.2f} sk {w['sk_max']:.2f}"
              f"  ΣGk {w['Gk']:5.1f} ΣSk {w['Sk']:5.1f}  vägg {w['L_vägg']:.0f} platta {w['L_platta']:.0f} mark {w['L_mark']:.0f}")
    for l in A["linjer"]:
        print(l["namn"], l["pl"], round(l["gk"], 2), round(l["sk"], 2), round(l["qk"], 2), round(l["wd"], 2))
    tot_g = sum(p["Gk"] for p in A["punkter"]) + sum(w["Gk"] for w in A["vaggar"])
    tot_s = sum(p["Sk"] for p in A["punkter"]) + sum(w["Sk"] for w in A["vaggar"])
    print(f"summa punkter+väggar: Gk {tot_g:.0f} Sk {tot_s:.0f} kN (+ qD2)")
