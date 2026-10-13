"""
R-01 Konstruktionsritning nock- och dalbalkar (F-01), A3 med ../ritningsmall:

    R-01.1  Elevationer och balkarnas lägen               1:50, 1:200
    R-01.2  Sektioner, detaljer och förteckningar           1:2,5, 1:5

Ritningen är tillverkningsunderlag för balkarna. Underlag: K-01 (indata.toml, resultat.json och hålbilderna
halbild_*.csv). Stöden ritas bara ut för orientering. Balkarnas lägen i planen ur K-03 (geometri.json), husets
kontur ur K-05 (bild/geometri.json).

Elevationerna ritas i balkens koordinater: x från balkens vänstra ände, z = 0 i balkens underkant. Sektionerna i
tvärsnittets: x från plåtens kant mot balkens framsida (som hålbilderna), z = 0 i underkant. Planen i K-05:s
koordinater. ritningsmall/ritning.py skalar till papperet.

Filen är uppdelad i:
    1. Underlag           K-01:s balkar, plåtar, stöd, skruvzoner och hål
    2. Placeringar        var balkarna, snitten och etiketterna står – ändra här
    3. Elevationer        en vy per balk (R-01.1)
    4. Plan               balkarnas lägen (R-01.1)
    5. Sektioner          A–A och B–B, detaljer C och D (R-01.2)
    6. Blad och main      högerkolumn, tabeller och ritningshuvud; skriver ritningar/R-01 Nock- och dalbalkar.pdf

    python beräkningar/R-01/ritningar.py
"""
import csv
import json
import math
import os
import sys
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
BER = os.path.dirname(HERE)
ROT = os.path.dirname(BER)
UT = os.path.join(ROT, "ritningar")
K01 = os.path.join(BER, "K-01")
sys.path.insert(0, os.path.join(BER, "ritningsmall"))
from ritning import Vy, Blad, huvud, sv, svm, PROJEKT  # noqa: E402

# ================================================================== 1. underlag
IN = tomllib.load(open(os.path.join(K01, "indata.toml"), "rb"))
R = json.load(open(os.path.join(K01, "resultat.json"), encoding="utf-8"))
G03 = json.load(open(os.path.join(BER, "K-03", "geometri.json"), encoding="utf-8"))
G05 = json.load(open(os.path.join(BER, "K-05", "bild", "geometri.json"), encoding="utf-8"))

NR = "R-01"
REV, DATUM = "A", "2026-10-13"
UNDERLAG = f"K-01 rev {IN['projekt']['revision']}"
REVISIONER = [dict(rev=REV, avser="Första utgåvan", datum=DATUM, sign=PROJEKT["signatur"])]

GEO, SK, ST, TR, LIM, DIST = IN["geometri"], IN["skruv"], IN["stal"], IN["tra"], IN["lim"], IN["distans"]
B, T, H, HW = float(GEO["b"]), float(GEO["t_pl"]), float(GEO["h_tot"]), float(GEO["h_tra"])   # 200, 10, 190, 170
GLIPA = float(DIST["glipa"])
RADER2, RADER3 = SK["rader2"], SK["rader3"]           # [45, 155], [45, 100, 155]
RHO = ST["densitet"] * 1e-9                            # kg/mm³

def tal(s):
    """K-01:s formaterade tal ("1 900", "−3,0") som float."""
    return float(str(s).replace("−", "-").replace(" ", "").replace(",", "."))


def intervall(s):
    """"5 600–6 120" → (5600.0, 6120.0)."""
    a, b = str(s).split("–")
    return tal(a), tal(b)


def halbild(namn):
    """Hålen per plåtbit ur K-01:s hålbild: {bit: dict(fran, till, hal=[(x, y_over, y_under)])}."""
    fil = os.path.join(K01, f"halbild_{namn.lower().replace(' ', '')}.csv")
    rader = [r for r in open(fil, encoding="utf-8").read().splitlines() if not r.startswith("#")]
    bitar = {}
    for r in csv.DictReader(rader, delimiter=";"):
        b = bitar.setdefault(int(r["bit"]), dict(fran=float(r["plat_fran"]), till=float(r["plat_till"]), hal=[]))
        b["hal"].append((float(r["x_mm"]), float(r["y_over"]), float(r["y_under"])))
    return bitar


def platvikt(L, n_hal):
    """Plåtens vikt efter håltagning [kg]."""
    return (L * B * T - n_hal * math.pi * (SK["hal"] / 2) ** 2 * T) * RHO


BALKAR = {}
for bi, br in zip(IN["balk"], R["balkar"]):
    assert bi["namn"] == br["namn"]
    nyckel = ("N" if bi["typ"] == "nock" else "D") + bi["namn"].split()[-1]          # N1, D2 … (K-03, K-05)
    kort = ("NB" if bi["typ"] == "nock" else "DB") + bi["namn"].split()[-1]         # NB1, DB2 … (plåtarnas namn)
    L = float(bi["total"])
    platar = [tuple(map(float, p)) for p in bi["platar"]]
    hal = halbild(bi["namn"])
    assert [(b["fran"], b["till"]) for _, b in sorted(hal.items())] == platar, bi["namn"]
    dist, x = [], 0.0                                   # distansreglar där plåt saknas, glipa mot plåtänden
    for a, b in platar:
        if a > x:
            dist.append((x + (GLIPA if x > 0 else 0.0), a - GLIPA))
        x = b
    if x < L:
        dist.append((x + GLIPA, L))
    stod = []                                           # stödens lägen (x eller väggens x0–x1), bara för orientering
    for s in br["stod"]:
        if s["vagg"]:
            stod.append(dict(x=None, vagg=intervall(s["x"])))
        else:
            stod.append(dict(x=tal(s["x"]), vagg=None))
    if bi.get("triangel"):                              # huvudstolpens strävor når balken på båda sidor om stolpen
        t = bi["triangel"]
        stod += [dict(x=t["x"] - t["e"], vagg=None), dict(x=t["x"] + t["e"], vagg=None)]
    zoner = [dict(bit=z["bit"], x=intervall(z["x"]), cc=int(z["cc"]), rader=int(z["rader"]), n=int(z["n"]))
             for z in br["zoner"]]
    for nr, b in hal.items():
        assert sum(z["n"] for z in zoner if z["bit"] == nr) == len(b["hal"]), (bi["namn"], nr)
    plan = next(g for g in G03["balkar"] if g["namn"] == nyckel)
    assert abs(plan["y1"] - plan["y0"] - L) < 1, nyckel
    BALKAR[kort] = dict(namn=bi["namn"], nyckel=nyckel, kort=kort, typ=bi["typ"], L=L, platar=platar, hal=hal,
                        dist=dist, stod=stod, zoner=zoner, plan=plan, n_skruv=br["n_balk"],
                        stal=sum(platvikt(b["till"] - b["fran"], len(b["hal"])) for b in hal.values()) * 2)

# ================================================================== 2. placeringar
ORDNING = ["NB1", "NB3", "NB5", "DB2", "DB4"]        # nockbalkarna överst, dalbalkarna under med planen bredvid
PLAC = dict(
    elev=dict(x=24.0, y0=14.0, dy=46.0, X0=-700.0),     # vyernas vänsterkant, första radens överkant, radavstånd
    # snitten: x i balken där A–A (med plåt) och B–B (utan plåt) markeras
    snitt={"NB1": dict(A=[8700], B=[2850]), "NB3": dict(A=[8500], B=[4000]), "NB5": dict(A=[2400, 9800], B=[6000]),
           "DB2": dict(A=[8400], B=[1200]), "DB4": dict(A=[4800], B=[1000])},
    plan=dict(x=246.0, y=158.0, X0=-600.0, Y1=16400.0,
              namn={"N1": 7600, "D2": 2300, "N3": 8600, "D4": 7400, "N5": 13200}),
    elev_rubrik=(24.0, 246.0),
)

# elevationernas nivåer över och under balken, i pappersmm
NIV = dict(platkedja=5.0, total=9.5, titel=13.5, topp=17.0, stod=2.2, zon=(5.0, 9.6))


# ================================================================== 3. elevationer (R-01.1)
def kedja(v, xs, Y, Yfran, texter=None, sz=6.4):
    """Vågrät måttkedja som Vy.mattx, men text som inte ryms i sitt mått flyttas ut till sidan eller upp."""
    g, f = 1.0 * v.s, 1.5 * v.s
    for x, y0 in zip(xs, Yfran):
        sg = 1 if Y > y0 else -1
        v.linje([(x, y0 + sg * g), (x, Y + sg * f)], "matt")
    v.linje([(xs[0] - f, Y), (xs[-1] + f, Y)], "matt")
    for x in xs:
        v._tick((x, Y), (1, 0), (0, 1))
    n = len(xs) - 1
    for i, (a, b) in enumerate(zip(xs[:-1], xs[1:])):
        t = texter[i] if texter else svm(b - a)
        bredd = len(t) * 0.19 * sz + 0.8                  # ungefärlig textbredd [pappersmm]
        if bredd < (b - a) / v.s:
            v.text((a + b) / 2, Y + 0.8 * v.s, t, a="cb", sz=sz)
        elif i == 0:
            v.text(a - 1.6 * v.s, Y + 0.8 * v.s, t, a="rb", sz=sz)
        elif i == n - 1:
            v.text(b + 1.6 * v.s, Y + 0.8 * v.s, t, a="lb", sz=sz)
        else:
            v.text((a + b) / 2, Y + 3.4 * v.s, t, a="cb", sz=sz)


def snittmarke(v, x, namn, z_under=0.0):
    """Snittmarkering tvärs balken: grova streck över och under balken, pil mot x = 0 (synriktningen) och bokstav."""
    s = v.s
    for z0, sg in ((H, 1), (z_under, -1)):
        za, zb = z0 + sg * 0.5 * s, z0 + sg * 2.9 * s
        v.linje([(x, za), (x, zb)], "snitt")
        v.linje([(x, zb), (x - 1.0 * s, zb)], "tunn")
        v.pil((x - 2.6 * s, zb), (-1, 0), langd=1.6, bredd=1.1)
        v.text(x + 0.7 * s, zb, namn, a="lm", sz=7.5, b=True)


def stodsymbol(v, x):
    s = v.s
    v.polygon([(x, 0), (x - 1.3 * s, -NIV["stod"] * s), (x + 1.3 * s, -NIV["stod"] * s)], fyll="vit", stil="tunn")


def elevation(k, ytopp):
    """En balk i elevation 1:50: limträ, plåtar och distansreglar, stöd, snitt, måttkedjor och skruvzoner."""
    b = BALKAR[k]
    L, s = b["L"], 50.0
    pe = PLAC["elev"]
    v = Vy(x=pe["x"], y=ytopp, w=300, h=45, skala=s, X0=pe["X0"], Y1=H + NIV["topp"] * s)
    # ---- balken
    with v.lager("balk"):
        v.rekt(0, 0, L, H, fyll="limtra", stil=None)
        for z in (0, H):
            for a, c in b["dist"]:
                v.linje([(a, z), (c, z)], "distans")
            for a, c in b["platar"]:
                v.linje([(a, z), (c, z)], "plat")
        v.linje([(0, 0), (0, H)], "normal")
        v.linje([(L, 0), (L, H)], "normal")
    # ---- stöd, bara för orientering
    with v.lager("stod"):
        for st in b["stod"]:
            if st["vagg"]:
                x0, x1 = st["vagg"]                      # vägg: skraffering under balken, som ett fast underlag
                v.rekt(x0, -NIV["stod"] * s, x1, -0.15 * s, fyll="stodyta", stil=None)
                v.linje([(x0, -0.15 * s), (x1, -0.15 * s)], "normal")
            else:
                stodsymbol(v, st["x"])
    # ---- snitt
    with v.lager("snitt"):
        for namn, xs in PLAC["snitt"][k].items():
            for x in xs:
                vagg = any(st["vagg"] and st["vagg"][0] <= x <= st["vagg"][1] for st in b["stod"])
                snittmarke(v, x, namn, z_under=-NIV["stod"] * s if vagg else 0.0)
    # ---- mått över balken: plåtar och total längd
    with v.lager("matt"):
        pts = sorted({0.0, L} | {p for ab in b["platar"] for p in ab})
        tx = []
        for a, c in zip(pts[:-1], pts[1:]):
            nr = next((n for n, h in b["hal"].items() if abs(h["fran"] - a) < 1 and abs(h["till"] - c) < 1), None)
            tx.append(f"plåt {k}-{nr}: {svm(c - a)}" if nr else svm(c - a))
        kedja(v, pts, H + NIV["platkedja"] * s, [H] * len(pts), tx)
        kedja(v, [0.0, L], H + NIV["total"] * s, [H + NIV["platkedja"] * s] * 2)
    # ---- skruvzoner under balken
    with v.lager("zoner"):
        z0, z1 = -NIV["zon"][0] * s, -NIV["zon"][1] * s
        for zn in b["zoner"]:
            a, c = zn["x"]
            v.rekt(a, z1, c, z0, fyll="zon" if zn["rader"] == 3 else "vit", stil="tunn")
            v.text((a + c) / 2, (z0 + z1) / 2, f"c/c {zn['cc']}\n{zn['n']} st", a="cm", sz=5.3)
        v.text(b["zoner"][0]["x"][0] - 0.8 * s, (z0 + z1) / 2, "skruv", a="rm", sz=5.8, col="gra", i=True)
    # ---- rubrik
    with v.lager("rubrik"):
        zt = H + NIV["titel"] * s
        v.text(0, zt, b["namn"].upper(), a="lb", sz=8.5, b=True)
        plt = " och ".join(f"{k}-{n}-O/U" for n in sorted(b["hal"]))
        v.text(27 * s, zt, f"{k} · L = {svm(L)} · plåtar {plt} · {b['n_skruv']} skruv",
               a="lb", sz=6.8, col="gra")
    return v


def rubrikvy():
    x, y = PLAC["elev_rubrik"]
    v = Vy(x=x, y=y, w=150, h=30, skala=50, X0=0, Y1=0)
    with v.lager("rubrik"):
        v.rubrik(0, -4.0 * 50, "ELEVATIONER  Nock- och dalbalkar", skala=50, sz=10)
        v.skalstock(0, -15.0 * 50, 4, 1)
    return v


# ================================================================== 4. plan (R-01.1)
def plan():
    p = PLAC["plan"]
    s = 200.0
    v = Vy(x=p["x"], y=p["y"], w=78, h=120, skala=s, X0=p["X0"], Y1=p["Y1"])
    with v.lager("hus"):
        v.polygon(G05["kontur"], fyll="#f4f2ee", stil="normal")
    with v.lager("balkar"):
        for k in ORDNING:
            b = BALKAR[k]
            g = b["plan"]
            x, y0, y1 = g["x"], g["y0"], g["y1"]
            v.rekt(x - 100, y0, x + 100, y1, fyll="stal", stil=None)
            # x = 0 och riktningen
            xa = x + 1.6 * s
            v.linje([(xa, y0), (xa, y0 + 1400)], "tunn")
            v.pil((xa, y0 + 1700), (0, 1), langd=1.5, bredd=1.0)
            v.text(xa + 0.5 * s, y0 + 900, "x", a="lm", sz=6.4, i=True)
            v.text(x - 1.0 * s, p["namn"][b["nyckel"]], k, a="cm", sz=6.6, b=True, rot=90, bg=True)
    with v.lager("rubrik"):
        v.rubrik(-500, -1500, "PLAN  Balkarnas lägen i huset", skala=200, sz=9)
        v.text(-500, -3100, "Pilen visar x från balkens vänstra ände (x = 0).", a="lt", sz=6.2, col="gra")
    return v


# ================================================================== 5. sektioner och detaljer (R-01.2)
def skruv(v, x, z0, ner=True, streckad=False):
    """Skruv HBS PLATE EVO 10×80 i sektion: huvud mot plåten, ansats i hålet, skaft och gänga."""
    sg = -1 if ner else 1
    d, Ls, hh = SK["d"], SK["langd"], SK["huvud"]
    dk, da, ds = SK["huvud_d"], SK["ansats"], SK["ds"]
    g0 = Ls - SK["b_ganga"]
    fy, stl = (None, "dold") if streckad else ("stal", "tunn")
    v.polygon([(x - dk / 2, z0), (x + dk / 2, z0), (x + dk / 2, z0 - sg * hh), (x - dk / 2, z0 - sg * hh)], fy, stl)
    prof = [(da / 2, 0), (da / 2, 4), (ds / 2, 12), (ds / 2, g0), (d / 2, g0), (d / 2, Ls - 6), (0, Ls)]
    kropp = [(x + r, z0 + sg * z) for r, z in prof] + [(x - r, z0 + sg * z) for r, z in reversed(prof[:-1])]
    v.polygon(kropp, fy, stl)
    if not streckad:
        z = g0 + 3
        while z < Ls - 8:
            v.linje([(x - d / 2, z0 + sg * z), (x + d / 2, z0 + sg * (z + 2.2))], "fin")
            z += 4.5


def tvarsnitt(v, med_plat):
    """Balkens tvärsnitt, x = 0 vid plåtens kant mot framsidan, z = 0 i underkant."""
    with v.lager("tra"):
        v.rekt(0, T, B, H - T, fyll="limtra", stil="normal")
        for k in range(1, 4):
            v.linje([(0, T + k * HW / 4), (B, T + k * HW / 4)], "fin")
    with v.lager("plat"):
        for z0 in (0, H - T):
            if med_plat:
                v.rekt(0, z0, B, z0 + T, fyll="stal", stil="normal")
            else:
                v.rekt(0, z0, B, z0 + T, fyll="distans", stil="tunn")
        if med_plat:
            v.linje([(0, T), (B, T)], "lim")
            v.linje([(0, H - T), (B, H - T)], "lim")


def etiketter(v, lst, x, z0, dz, sz=6.6):
    """Hänvisningar i en kolumn till höger, uppifrån och ned: (text, målpunkt); dz i pappersmm."""
    with v.lager("text"):
        for k, (txt, mal) in enumerate(lst):
            v.hanvisning(mal, (x, z0 - k * dz * v.s), txt, a="lm", sz=sz)


def sektion_a():
    """A–A: med plåt, skruv i båda raderna (den andra radens skruv streckad). 1:2,5"""
    v = Vy(x=24, y=12, w=148, h=115, skala=2.5, X0=-20, Y1=240)
    tvarsnitt(v, True)
    r0, r1 = RADER2
    with v.lager("skruv"):
        skruv(v, r0, H, ner=True)
        skruv(v, r1, H, ner=True, streckad=True)
        skruv(v, B - r0, 0, ner=False)
        skruv(v, B - r1, 0, ner=False, streckad=True)
        v.linje([(RADER3[1], -3), (RADER3[1], H + 3)], "axel")
    with v.lager("matt"):
        v.matt((0, H + SK["huvud"]), (B, H + SK["huvud"]), 5.0, sz=6.4)
        v.kedja([(0, -SK["huvud"]), (r0, -SK["huvud"]), (r1, -SK["huvud"]), (B, -SK["huvud"])], 4.0, sida=-1, sz=6.2)
        v.kedja([(B, 0), (B, T), (B, H - T), (B, H)], 3.5, sida=-1, sz=6.2)
        v.matt((B, 0), (B, H), 9.5, sida=-1, sz=6.4)
        v.matt((0, H), (0, H - SK["langd"]), 3.0, sida=-1, sz=6.0)
        v.matt((0, H - T), (0, H - SK["langd"]), 7.5, sida=-1, sz=6.0, txt=f"{SK['langd'] - T:.0f} i limträet")
    etiketter(v, [("överplåt 200×10 S355J2+N", (178, H - 4)),
                  ("epoxilim, heltäckande", (185, H - T)),
                  ("streckat: skruv i den\nandra raden", (r1 + 3, H - 45)),
                  (f"limträ {TR['kvalitet']} 200×170", (178, 120)),
                  ("mittraden (100) där skruv-\nzonen har tre rader (DB4)", (RADER3[1], 95)),
                  (f"skruv {SK['produkt'].split(' ', 1)[1]} eller\nlikvärdig i varje hål, hål Ø{SK['hal']:g}\n"
                   f"i plåten, förborrning i limträet", (B - r0 + 4, 45)),
                  ("underplåt 200×10 S355J2+N", (178, 4))], B + 44, H + 25, 13.4)
    with v.lager("rubrik"):
        v.rubrik(-15, -48, "SEKTION A–A  Med plåt", skala=2.5, sz=9)
    return v


def sektion_b():
    """B–B: utan plåt, distansreglar i över- och underkant. 1:2,5"""
    v = Vy(x=176, y=12, w=148, h=115, skala=2.5, X0=-20, Y1=240)
    tvarsnitt(v, False)
    with v.lager("matt"):
        v.matt((0, H), (B, H), 5.0, sz=6.4)
        v.kedja([(B, 0), (B, T), (B, H - T), (B, H)], 3.5, sida=-1, sz=6.2)
        v.matt((B, 0), (B, H), 9.5, sida=-1, sz=6.4)
    etiketter(v, [(f"distansregel 200×{DIST['tjocklek']}, trä\neller plywood, limmas eller\nhäftas, inte bärande", (170, H - 4)),
                  (f"limträ {TR['kvalitet']} 200×170", (178, 110)),
                  (f"distansregel 200×{DIST['tjocklek']}", (170, 4))], B + 44, H + 10, 26.0)
    with v.lager("rubrik"):
        v.rubrik(-15, -48, "SEKTION B–B  Utan plåt", skala=2.5, sz=9)
    return v


def _hal_i(k, bit, x0, x1):
    return sorted(h for h in BALKAR[k]["hal"][bit]["hal"] if x0 <= h[0] <= x1)


def plat_plan(v, k, bit, x0, x1, balkande=False):
    """Överplåten sedd uppifrån mellan x0 och x1 (balkens x), y från plåtens kant mot framsidan."""
    b = BALKAR[k]
    pf, pt = b["hal"][bit]["fran"], b["hal"][bit]["till"]
    with v.lager("plat"):
        a, c = max(x0, pf), min(x1, pt)
        v.rekt(a, 0, c, B, fyll="stal", stil=None)
        if pf > x0:                                       # distansregel före plåtänden, limträet i glipan
            v.rekt(x0, 0, pf - GLIPA, B, fyll="distans", stil="tunn")
            v.rekt(pf - GLIPA, 0, pf, B, fyll="limtra", stil=None)
            v.linje([(pf, 0), (pf, B)], "normal")
        v.linje([(x0, 0), (x1, 0)], "normal")
        v.linje([(x0, B), (x1, B)], "normal")
        if balkande:
            v.linje([(x1, 0), (x1, B)], "kontur")
        else:
            v.brott((x1, -25), (x1, B + 25), "tunn")
        v.brott((x0, -25), (x0, B + 25), "tunn")
    hal = _hal_i(k, bit, x0, x1)
    rader = sorted({h[1] for h in hal})
    with v.lager("skruv"):
        for y in rader:
            v.linje([(max(x0, pf) - 10, y), (min(x1, pt) - (0 if balkande else 10), y)], "axel")
        for x, y, _ in hal:
            v.cirkel(x, y, SK["hal"] / 2, fyll="vit", stil="tunn", modell=True)
    return hal, rader


def detalj_c():
    """C: plåtände inne på balken (NB1-1 vid x = 5 600), sedd från sidan och uppifrån. 1:5"""
    k, bit = "NB1", 1
    pf = BALKAR[k]["hal"][bit]["fran"]
    x0, x1 = pf - 100, pf + 330
    hal = _hal_i(k, bit, x0, x1)
    s_ = hal[1][0] - hal[0][0]
    # sedd från sidan
    v = Vy(x=24, y=134, w=148, h=56, skala=5, X0=x0 - 60, Y1=H + 75)
    with v.lager("tra"):
        v.rekt(x0, T, x1, H - T, fyll="limtra", stil=None)
        v.linje([(x0, T), (x1, T)], "normal"); v.linje([(x0, H - T), (x1, H - T)], "normal")
        for z0 in (0, H - T):
            v.rekt(x0, z0, pf - GLIPA, z0 + T, fyll="distans", stil="tunn")
            v.rekt(pf, z0, x1, z0 + T, fyll="stal", stil="normal")
        v.linje([(pf, T), (x1, T)], "lim"); v.linje([(pf, H - T), (x1, H - T)], "lim")
        v.brott((x0, -25), (x0, H + 25), "tunn"); v.brott((x1, -25), (x1, H + 25), "tunn")
    with v.lager("skruv"):
        for x, _, _ in hal:
            skruv(v, x, H, ner=True)
            skruv(v, x, 0, ner=False)
    with v.lager("text"):
        v.hanvisning((x0 + 40, H - 4), (x0 + 10, H + 55), f"distansregel, glipa {GLIPA:.0f} mot plåtänden", a="lm", sz=6.4)
        v.hanvisning((x1 - 4, 95), (x1 + 15, 95), "sedd från sidan", a="lm", sz=6.4, punkt=False)
    # sedd uppifrån
    w = Vy(x=24, y=192, w=148, h=60, skala=5, X0=x0 - 60, Y1=B + 40)
    hal, rader = plat_plan(w, k, bit, x0, x1)
    with w.lager("matt"):
        w.kedja([(x0, 0)] + [(x0, y) for y in rader] + [(x0, B)], 4.0, sida=1, sz=6.0)
        w.matt((pf, B), (hal[0][0], B), 4.0, sz=6.2)
        w.matt((hal[0][0], B), (hal[1][0], B), 4.0, sz=6.2, txt="s")
        w.matt((hal[1][0], B), (hal[2][0], B), 4.0, sz=6.2, txt="s")
        xa = [h[0] for h in hal if h[1] == hal[0][1]]
        w.matt((xa[0], 0), (xa[1], 0), 5.0, sida=-1, sz=6.2, txt=f"2s = {xa[1] - xa[0]:.0f}")
    with w.lager("text"):
        w.hanvisning((x1 - 4, 100), (x1 + 15, 100), "överplåten sedd\nuppifrån", a="lm", sz=6.4, punkt=False)
    with w.lager("rubrik"):
        w.rubrik(x0 - 55, -95, "DETALJ C  Plåtände inne på balken", skala=5, sz=9)
        w.text(x0 - 55, -95 - 8.0 * 5, f"Exempel: {k}-{bit} vid x = {svm(pf)}, två rader, s = {s_:.0f}. "
               "2s = c/c i varje rad.",
               a="lb", sz=6.4, col="gra")
    return [v, w]


def detalj_d():
    """D: plåten vid balkänden med tre rader (DB4-1 vid x = 7 480), sedd uppifrån. 1:5"""
    k, bit = "DB4", 1
    L = BALKAR[k]["L"]
    x0 = L - 420
    v = Vy(x=176, y=134, w=148, h=56, skala=5, X0=x0 - 60, Y1=B + 45)
    hal, rader = plat_plan(v, k, bit, x0, L, balkande=True)
    with v.lager("matt"):
        v.kedja([(L, 0)] + [(L, y) for y in rader] + [(L, B)], 4.0, sida=-1, sz=6.0)
        v.matt((hal[-1][0], B), (L, B), 4.0, sz=6.2)
        v.matt((hal[-2][0], B), (hal[-1][0], B), 4.0, sz=6.2, txt="s")
        xr = [h[0] for h in hal if h[1] == hal[-1][1]]
        v.matt((xr[-2], 0), (xr[-1], 0), 5.0, sida=-1, sz=6.2, txt=f"3s = {xr[-1] - xr[-2]:.0f}")
    with v.lager("rubrik"):
        v.rubrik(x0 - 55, -70, "DETALJ D  Tre rader vid balkänden", skala=5, sz=9)
        v.text(x0 - 55, -70 - 8.0 * 5, f"Exempel: {k}-{bit} vid balkänden x = {svm(L)}, s = {hal[-1][0] - hal[-2][0]:.0f}. "
               "3s = c/c i varje rad. Första skruv 100 från balkänden.", a="lb", sz=6.4, col="gra")
    return v


# ================================================================== 6. blad
BLADEN = [
    ("R-01.1", ["Nock- och dalbalkar", "Elevationer och lägen"], "1:50, 1:200", "R-01.1 Nock- och dalbalkar, elevationer"),
    ("R-01.2", ["Nock- och dalbalkar", "Sektioner, detaljer och förteckningar"], "1:2,5, 1:5",
     "R-01.2 Nock- och dalbalkar, sektioner och detaljer"),
]


def hd(nr):
    b = next(x for x in BLADEN if x[0] == nr)
    return huvud(nr, b[1], b[2], UNDERLAG, DATUM, REV)


def blad_elevationer():
    vyer = [elevation(k, PLAC["elev"]["y0"] + i * PLAC["elev"]["dy"]) for i, k in enumerate(ORDNING)]
    vyer += [plan(), rubrikvy()]
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=6.9, rader=[
            f"Limträ {TR['kvalitet']} 200×170 i hel längd. Plattstål 200×10 {ST['kvalitet']} i över- och underkant där "
            "plåt anges, limmat och skruvat. I övrigt distansreglar 200×10. Balkens höjd 190 mm. Sektioner och "
            "detaljer: R-01.2.",
            "x räknas från balkens vänstra ände (x = 0). Plåtarna och skruvzonerna är inte symmetriska. Balkens "
            "vänstra ände märks med balkens namn och x = 0, så att balken kan monteras åt rätt håll (planen).",
            "Skruvzonerna: c/c i varje rad och antal skruv per plåt (lika i över- och underplåt). Två rader om inget "
            "annat anges. Hålen laserskärs enligt hålbilderna (R-01.2), en skruv i varje hål.",
            "Stöden visas bara för orientering.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="yta", fyll="limtra", stil="tunn", text=f"limträ {TR['kvalitet']} 200×170"),
            dict(form="linje", stil="plat", text="plattstål 200×10, över- och underplåt"),
            dict(form="linje", stil="distans", text="distansregel 200×10"),
            dict(form="stod", text="stöd"),
            dict(form="yta", fyll="stodyta", stil="", text="stöd, vägg"),
            dict(form="yta", fyll="vit", stil="tunn", text="skruvzon, två rader"),
            dict(form="yta", fyll="zon", stil="tunn", text="skruvzon, tre rader")]),
        dict(typ="rubrik", text=f"Ritningsförteckning {NR}"),
        dict(typ="tabell", kolumner=["Ritning", "Innehåll", "Skala"], bredd=(0, 1, 0),
             rader=[[nr, ", ".join(t[1:]), sk] for nr, t, sk, _ in BLADEN], just=["l", "l", "l"], sz=6.6),
    ]
    return Blad(hd("R-01.1"), REVISIONER, kol, vyer)


def platforteckning():
    rader, tot_L, tot_n, tot_kg = [], 0.0, 0, 0.0
    for k in sorted(BALKAR, key=lambda q: int(q[2:])):
        b = BALKAR[k]
        for nr, h in sorted(b["hal"].items()):
            L = h["till"] - h["fran"]
            for lage, txt in (("O", "över"), ("U", "under")):
                kg = platvikt(L, len(h["hal"]))
                rader.append([f"{k}-{nr}-{lage}", txt, f"{svm(h['fran'])}–{svm(h['till'])}", svm(L), str(len(h["hal"])),
                              sv(kg, 1)])
                tot_L += L; tot_n += len(h["hal"]); tot_kg += kg
    rader.append(["Summa", f"{len(rader)} plåtar", "", svm(tot_L), str(tot_n), sv(tot_kg, 0)])
    return dict(typ="tabell", kolumner=["Plåt", "Läge", "x i balken (mm)", "L (mm)", "Hål", "Vikt efter håltagning (kg)"],
                bredd=(0, 0, 1, 0, 0, 0), rader=rader, just=["l", "l", "l", "r", "r", "r"], sz=6.4)


def balkforteckning():
    rader = []
    for k in sorted(BALKAR, key=lambda q: int(q[2:])):
        b = BALKAR[k]
        rader.append([k, svm(b["L"]), ", ".join(f"{svm(a)}–{svm(c)}" for a, c in b["platar"]),
                      ", ".join(f"{svm(a)}–{svm(c)}" for a, c in b["dist"]), str(b["n_skruv"])])
    rader.append(["Summa", svm(sum(b["L"] for b in BALKAR.values())), "", "",
                  str(sum(b["n_skruv"] for b in BALKAR.values()))])
    return dict(typ="tabell", kolumner=["Balk", "L", "Plåt, x", "Distansregel, x", "Skruv"],
                bredd=(0, 0, 1, 1, 0), rader=rader, just=["l", "r", "l", "l", "r"], sz=6.0)


def blad_sektioner():
    vyer = [sektion_a(), sektion_b(), *detalj_c(), detalj_d()]
    block = [dict(x=178, y=218, w=144, innehall=[
        dict(typ="rubrik", text="Plåtar, S355J2+N 200×10 (modeller/balkplattor)"), platforteckning()])]
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=6.9, rader=[
            f"Limträ {TR['kvalitet']} enligt {TR['standard']}, 200×170 i hel längd. Fuktkvot {TR['fuktkvot']}. "
            "Klimatklass 1.",
            f"Plåtar: plattstål 200×10 {ST['kvalitet']} enligt {ST['standard']}, laserskurna enligt DXF- och STEP-filerna "
            "i modeller/balkplattor/, en fil per plåt. Bitarna skarvas inte.",
            f"Hål Ø{SK['hal']:g} genomgående, cylindriska, utan försänkning. Varje plåt märks med sitt namn, en pil mot "
            "balkens vänstra ände och framsidans kant (y = 0). Över- och underplåt har speglade hålbilder och kan inte bytas.",
            f"{ST['korrosion']} Limytorna på stålet blästras eller slipas och avfettas. Träytan ska vara ren och torr.",
            "Lim: tvåkomponents strukturepoxi för limning av stål (t.ex. Sikadur-30), heltäckande fog mot båda plåtarna "
            f"i hela plåtlängden. Härdning {LIM['hardning']}.",
            f"Skruv: {SK['produkt']} ({SK['kod']}, {SK['eta']}), C4 EVO, eller likvärdig. En skruv i varje hål, "
            "vinkelrätt mot plåten.",
            f"Likvärdig skruv: skruv för stålplåt mot trä med ETA, d = {SK['d']} mm, kärndiameter minst {sv(SK['d1'], 1)} mm, "
            f"längd {SK['langd']} mm, gänga minst {R['l_ef']} mm i limträet, ansats under huvudet som fyller hålet "
            f"Ø{SK['hal']:g}, karakteristiskt flytmoment minst {SK['My_Rk']:g} Nm, utdragsparameter minst "
            f"{sv(SK['fax_k'], 1)} MPa vid densiteten {SK['rho_a']} kg/m³, korrosivitetsklass C4.",
            f"Förborra genom plåthålen enligt skruvtillverkaren ({SK['produkt'].split(' ', 1)[1]}: Ø{SK['forborr']:g}), "
            "lika djupt som skruven.",
            "Skruvarna dras medan limmet är färskt, i ett drag tills huvudet ligger an mot plåten, med "
            f"momentbegränsare eller momentnyckel ({SK['produkt'].split(' ', 1)[1]}: högst {SK['moment']} Nm), "
            "inte med slagskruvdragare.",
            f"Distansreglar 200×{DIST['tjocklek']} där plåt saknas: {DIST['material'].lower()}. "
            f"{DIST['fastsattning']}. Glipa {GLIPA:.0f} mm mot plåtänden.",
            "Annat lim eller ändrade hål kräver ny kontroll enligt K-01.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="yta", fyll="limtra", stil="tunn", text=f"limträ {TR['kvalitet']}"),
            dict(form="yta", fyll="stal", stil="tunn", text=f"stål {ST['kvalitet']}"),
            dict(form="yta", fyll="distans", stil="tunn", text="distansregel"),
            dict(form="linje", stil="lim", text="epoxilim"),
            dict(form="linje", stil="dold", text="skruv i den andra raden"),
            dict(form="linje", stil="axel", text="skruvrad")]),
        dict(typ="rubrik", text="Balkar"), balkforteckning(),
    ]
    return Blad(hd("R-01.2"), REVISIONER, kol, vyer, block)


SERIE = "R-01 Nock- och dalbalkar"          # ritningsseriens pdf i ritningar/, ett blad per sida


def main(dolj=()):
    os.makedirs(UT, exist_ok=True)
    bladmapp = os.path.join(HERE, "blad")    # bladen var för sig (versionshanteras inte)
    os.makedirs(bladmapp, exist_ok=True)
    fn = {"R-01.1": blad_elevationer, "R-01.2": blad_sektioner}
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
