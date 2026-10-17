"""
Källarens geometri för R-04 (källarstomme) och R-05 (bottenplatta), i K-05:s koordinater (mm, origo i skärningen
mellan mellanbjälklagets kanter x = 0 och y = 0, y uppåt) och höjder z från bottenplattans överkant.

Underlag: K-05 (bild/geometri.json: väggarnas centrumlinjer, betongkärnans ändar vid öppningarna och rörens lägen;
resultat.json: rörens lastytor, P7 två rör), K-06 (indata.py: Kub 350-150, höjder, armering, bottenplattan L300;
resultat.json: plintarnas storlek). Inget läses ur modellen; källfilerna kontrolleras mot modellen med
verktyg/modellanalys/kontroll_geometri05.py och kontroll_r045.py.

Väggarna: en vägg är [riktning, centrumlinje, a, b, typ] ur K-05. a och b är den vinkelräta väggens centrumlinje i
hörn och anslutningar, och betongkärnans ände vid en fri ände (öppning). Där går väggens cellplast 100 mm längre ut
(isolerad smyg).
"""
import json
import math
import os
import sys

from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
BER = os.path.dirname(HERE)
ROT = os.path.dirname(BER)
K05 = os.path.join(BER, "K-05")
K06 = os.path.join(BER, "K-06")
sys.path.insert(0, K06)
sys.path.insert(0, os.path.join(BER, "ritningsmall"))
import indata as I06  # noqa: E402   (K-06; lägger K-05 i sys.path och läser K-05:s geometri.json)

G = I06.G05
R05 = json.load(open(os.path.join(K05, "resultat.json"), encoding="utf-8"))
R06 = json.load(open(os.path.join(K06, "resultat.json"), encoding="utf-8"))

# ------------------------------------------------------------------ mått (K-06)
T_VAGG, T_KARNA, T_EPS = I06.T_VAGG, I06.T_KARNA, I06.T_EPS_V        # 350, 150, 100
H_VAGG, H_MB, H_GJUT1 = I06.H_VAGG, I06.H_MB, I06.H_GJUT1           # 2 100, 150, 1 800
KI = I06.KI                     # mellanbjälklagets kant 30 mm innanför väggens ytterliv
SKIFT = 600.0                   # Kub-elementens höjd; det översta skiftet är ett halvt element, 300
C_IN, C_UT = I06.C_IN, I06.C_UT  # täckskikt till de vågräta järnen: insida 25, utsida 30
UTF = I06.UTFORANDEN["L300"]    # bottenplattan: H 300, cellplast 200, kantbalk 200 (inklusive plattan)
H_PLATTA, T_FOT, B_BALK = I06.H_PLATTA, I06.T_FOT, I06.B_BALK       # 100, 100 (S200 under balkarna), 450
L_BEN = I06.L_BEN               # L-elementets rygg nedtill, 100: ytterkanten i väggens ytterliv, betongen 100 mm innanför
FAS = I06.FAS                   # ryggens avfasning i ovankant, 50 (betongen fyller fasen)
B_L = I06.B_L                   # L-elementets bredd, 600
B_KANT = L_BEN + B_BALK         # kantbalkens inre kant från väggens ytterliv, 550
OMLOTT = I06.OMLOTT             # plattans övre cellplastskikt in över L-elementets fot, 50
L_ELEMENT = I06.L_ELEMENT
BYGEL_SIDA, BALK_JARN = 33.0, 41.0   # balkarnas byglar och längsjärn (centrum) från balkens sida: täckskikt 30
GLIPA_SMYG = T_EPS              # isolerad smyg vid öppningarna: cellplast 100 mellan kärnan och öppningen

# armeringens lägen i väggen, från väggens ytterliv (yttervägg) eller från ena ytan (innervägg)
X_H_UT = T_EPS + C_UT + 5.0                     # vågrätt järn vid utsidan, 135
X_H_IN = T_EPS + T_KARNA - C_IN - 5.0           # vågrätt järn vid insidan, 220
X_LODRAT = X_H_IN - 5.0 - 5.0                   # lodräta järn på insidan, innanför de vågräta, 210 (R-03)
X_START = L_BEN + BALK_JARN + 14.0              # startjärn på utsidan, innanför kantbalkens längsjärn, 155
# de vågräta järnens höjder: ett per skift (s600) i de två nedre skiften, s300 i de två översta (TG 2216, K-06);
# V3 s300 i hela höjden (byggskedet, K-06 4.2). Samma lägen som på R-03.4.
Z_HOR = (575.0, 1175.0, 1475.0, 1775.0, 2040.0)
Z_HOR_V3 = (275.0, 575.0, 875.0, 1175.0, 1475.0, 1775.0, 2040.0)
# lodräta järn: från bottenplattan upp under mellanbjälklagets överkantsnät (R-03.4 sektion A)
L_LODRAT = 2200.0
ARM_V = (10, 200)               # Ø10 s200 på insidan där packningstrycket kräver det (K-06)
ARM_V_TG = tuple(I06.ARM_V[0])  # Ø10 s300, TG 2216: övriga ytterväggar och under bröstningarna
# lodräta järn per yttervägg (K-06: den glesaste armering som räcker, minst TG 2216:s)
ARM_V_VAGG = {v["namn"]: tuple(v["arm"]) for v in R06["vaggar"] if "arm" in v}
ARM_H = (I06.ARM_H["d"], I06.ARM_H["s"], I06.ARM_H["s_topp"])          # Ø10 s600, s300 i de två översta skiften
STARTJARN = I06.STARTJARN       # Ø10 s300 på utsidan, 500 i kantbalken, 1 200 upp
VINKEL_HORN = (750.0, 750.0)    # vinkeljärn i hörn och anslutningar, båda ytorna, i varje lager
SKARV = I06.SKARV               # 500
OPP = I06.OPPNING               # 2 Ø12, förankras 600 förbi öppningen
POS14 = dict(d=10, s=200, ben=I06.VINKEL["ned"], in_=I06.VINKEL["in_"])   # R-03 pos 14: vinkeljärn till bjälklaget


# ------------------------------------------------------------------ väggarna
def _vaggrad(i, w):
    ax, c, a, b, typ = w[:5]
    return dict(nr=i, namn=f"V{i}", ax=ax, c=float(c), a=float(a), b=float(b), typ=typ)


VAGGAR = [_vaggrad(i, w) for i, w in enumerate(G["vagg"], 1)]
VAGG = {v["namn"]: v for v in VAGGAR}


def mot(v, ande):
    """Den vinkelräta vägg vars centrumlinje väggen v:s ände ligger på (hörn eller anslutning), annars None."""
    for o in VAGGAR:
        if o["ax"] != v["ax"] and abs(o["c"] - ande) < 1 and o["a"] - 1 <= v["c"] <= o["b"] + 1:
            return o
    return None


for v in VAGGAR:
    v["mot_a"], v["mot_b"] = mot(v, v["a"]), mot(v, v["b"])


def _linje(v, a, b):
    return LineString([(a, v["c"]), (b, v["c"])] if v["ax"] == "h" else [(v["c"], a), (v["c"], b)])


def band(v, halv, ut_hal, ut_fri):
    """Väggens band med halva bredden halv; ändarna förlängs ut_hal vid hörn och anslutningar och ut_fri vid fria
    ändar."""
    a = v["a"] - (ut_hal if v["mot_a"] else ut_fri)
    b = v["b"] + (ut_hal if v["mot_b"] else ut_fri)
    return _linje(v, a, b).buffer(halv, cap_style="flat")


for v in VAGGAR:
    v["karna"] = band(v, T_KARNA / 2, T_KARNA / 2, 0.0)              # betongkärnan, sammanhängande i hörnen
    v["hel"] = band(v, T_VAGG / 2, T_VAGG / 2, GLIPA_SMYG)           # hela väggen med cellplast och isolerad smyg

KARNA = unary_union([v["karna"] for v in VAGGAR])
HEL = unary_union([v["hel"] for v in VAGGAR])


def kallare():
    """Källarens kontur i väggarnas ytterliv (= L-elementens ytterkant och modellens bottenplatta), utan delen med
    platta på mark (K-06)."""
    k = Polygon(G["kontur"]).buffer(KI, join_style=2)
    ut = box(-500, VAGG["V3"]["c"] + T_VAGG / 2, VAGG["V20"]["c"] - T_VAGG / 2, 16500)
    return k.difference(ut)


KALLARE = kallare()
BETONG = KALLARE.buffer(-L_BEN, join_style=2)       # bottenplattans betong: kanten 100 mm innanför, i kärnans yttre yta
for v in VAGGAR:
    # utsidan: den sida av centrumlinjen som ligger utanför källaren (ytterväggar); för innerväggar None
    if v["typ"] == "yttre":
        m = (v["a"] + v["b"]) / 2
        p = (m, v["c"] + 300) if v["ax"] == "h" else (v["c"] + 300, m)
        v["ute"] = 1 if not KALLARE.contains(Polygon([(p[0] - 1, p[1] - 1), (p[0] + 1, p[1] - 1),
                                                       (p[0] + 1, p[1] + 1), (p[0] - 1, p[1] + 1)])) else -1
    else:
        v["ute"] = None
    v["ytterliv"] = v["c"] + v["ute"] * T_VAGG / 2 if v["ute"] else None
    v["innerliv"] = v["c"] - v["ute"] * T_VAGG / 2 if v["ute"] else None


def horn(poly=None):
    """Källarens yttre (konvexa) och inåtgående hörn i väggarnas ytterliv (eller i polygonen poly)."""
    poly = KALLARE if poly is None else poly
    c = list(poly.exterior.coords)[:-1]
    n = len(c)
    ccw = poly.exterior.is_ccw
    kon, ina = [], []
    for i in range(n):
        a, b, d = c[i - 1], c[i], c[(i + 1) % n]
        cr = (b[0] - a[0]) * (d[1] - b[1]) - (b[1] - a[1]) * (d[0] - b[0])
        (kon if (cr > 0) == ccw else ina).append((float(b[0]), float(b[1])))
    return kon, ina


HORN_UT, HORN_IN = horn()
_, HORN_IN_BETONG = horn(BETONG)                    # betongens inåtgående hörn (diagonaljärnen)


def anslutningar():
    """Väggarnas möten: (x, y, typ, väggar). typ: "hörn" (två väggar) eller "T" (en vägg mot en genomgående)."""
    punkter = {}
    for v in VAGGAR:
        for ande, o in ((v["a"], v["mot_a"]), (v["b"], v["mot_b"])):
            if o is None:
                continue
            p = (ande, v["c"]) if v["ax"] == "h" else (v["c"], ande)
            punkter.setdefault((round(p[0]), round(p[1])), set()).update({v["namn"], o["namn"]})
    ut = []
    for (x, y), namn in sorted(punkter.items()):
        vs = [VAGG[n] for n in sorted(namn, key=lambda s: int(s[1:]))]
        # T: någon av väggarna går igenom punkten (punkten ligger inne på väggen, inte i en ände)
        genom = [w for w in vs if (w["a"] + 1 < (x if w["ax"] == "h" else y) < w["b"] - 1)]
        # två kolinjära väggar som möts i punkten bildar tillsammans en genomgående vägg
        kol = {}
        for w in vs:
            kol.setdefault((w["ax"], w["c"]), []).append(w)
        genomgaende = [ws for ws in kol.values() if len(ws) == 2] or [[w] for w in genom]
        typ = "T" if genomgaende else "hörn"
        ut.append(dict(x=float(x), y=float(y), typ=typ, vaggar=[w["namn"] for w in vs],
                       genom=[w["namn"] for ws in genomgaende for w in ws]))
    return ut


ANSLUTNINGAR = anslutningar()

# ------------------------------------------------------------------ öppningar
# Öppningarna i betongkärnan, mellan två väggars fria ändar (K-05). Höjder från bottenplattans överkant: betongens
# underkant (bröstning) och överkant (mellanbjälklagets underkant). Färdig öppning: 100 mm cellplast i smygen och på
# bröstningen. Lägena kontrolleras mot modellen (kontroll_r045.py).
OPPNINGAR = [
    dict(namn="F1", vaggar=("V10", "V11"), z0=1400.0),
    dict(namn="F2", vaggar=("V11", "V12"), z0=1400.0),
    dict(namn="F3", vaggar=("V12", "V13"), z0=800.0),
    dict(namn="D1", vaggar=("V8", "V9"), z0=0.0),
    dict(namn="D2", vaggar=("V4", "V5"), z0=0.0),
    dict(namn="D3", vaggar=("V5", "V6"), z0=0.0),
]
for o in OPPNINGAR:
    v1, v2 = VAGG[o["vaggar"][0]], VAGG[o["vaggar"][1]]
    assert v1["ax"] == v2["ax"] and v1["c"] == v2["c"] and v1["mot_b"] is None and v2["mot_a"] is None
    o.update(ax=v1["ax"], c=v1["c"], x0=v1["b"], x1=v2["a"], z1=H_VAGG, typ=v1["typ"])
    o["bredd"] = o["x1"] - o["x0"]
    o["fardig"] = (o["x0"] + GLIPA_SMYG, o["x1"] - GLIPA_SMYG, o["z0"] + (GLIPA_SMYG if o["z0"] > 0 else 0.0))
assert set(I06.BROSTNING) == {o["z0"] / 1000 for o in OPPNINGAR if o["z0"] > 0}, "K-06: BROSTNING"
OPP = dict(OPP, namn={o["namn"]: o for o in OPPNINGAR})

# ------------------------------------------------------------------ rören (K-05)
PLAT = 80.0                      # VKR 80×80×4
ROR = []                         # (namn, [(x, y) för varje rör], lastytans mitt (x, y))
for p in R05["pelare"]:
    x0, y0, x1, y1 = p["yta"]
    n = int(p.get("antal", 1))
    xs = [x0 + PLAT / 2 + k * PLAT for k in range(n)] if (x1 - x0) > (y1 - y0) else [(x0 + x1) / 2] * n
    ys = [(y0 + y1) / 2] * n if (x1 - x0) > (y1 - y0) else [y0 + PLAT / 2 + k * PLAT for k in range(n)]
    ROR.append(dict(namn=p["namn"], ror=list(zip(xs, ys)), mitt=((x0 + x1) / 2, (y0 + y1) / 2), n=n,
                    yta=(x0, y0, x1, y1)))
assert [r["ror"][0] for r in ROR] == [tuple(map(float, xy)) for xy in G["pelare"]], "K-05: pelare och resultat"
ROR_D = {r["namn"]: r for r in ROR}
# rör och plåtar (K-05, K-06)
ROR_TEXT = "VKR 80×80×4 S235, kallformat (SS-EN 10219)"
TOPPLAT = (80.0, 80.0, 8.0, "S235")          # svetsad på röret, ingjuten kant i kant med plattans undersida
FOTPLAT = {1: (200.0, 200.0, 15.0), 2: (280.0, 200.0, 15.0)}   # S355, gjuts in i plintens överkant
SVETSBULT = (13.0, 75.0)        # Ø13, L = 75 mm (efter svetsning), fyra under varje fotplåt
BULT_LAGE = {1: ((-60.0, -60.0), (60.0, -60.0), (60.0, 60.0), (-60.0, 60.0)),
             2: ((-100.0, -60.0), (100.0, -60.0), (100.0, 60.0), (-100.0, 60.0))}
L_ROR = H_VAGG                   # 2 100: från fotplåten till mellanbjälklagets underkant

# ------------------------------------------------------------------ bottenplattan (K-06)
PL06 = R06["platta"]["L300"]
PLINT = {r["namn"]: float(b) for r, b in zip(ROR, PL06["plint"])}   # plintarnas sida, centrerad under stödet


def kantbalk():
    """Kantbalken: 450 mm längs bottenplattans hela betongkant, som ligger 100 mm innanför väggarnas ytterliv."""
    return BETONG.difference(BETONG.buffer(-B_BALK, join_style=2))


def l_element():
    """L-elementen: 600 mm från väggarnas ytterliv, med ryggen 100 och foten under kantbalken och 50 mm förbi den."""
    return KALLARE.difference(KALLARE.buffer(-B_L, join_style=2))


def balkar_inre():
    """Balkar 450 mm under innerväggarna (K-06): V15, V19 och V4–V6 i hela linjen mellan V19 och V15, hela även i
    hörnen (ändarna förlängda en halv balkbredd) och fram till kantbalken."""
    y4, x19, x15 = VAGG["V4"]["c"], VAGG["V19"]["c"], VAGG["V15"]["c"]
    lin = [_linje(VAGG[n], VAGG[n]["a"], VAGG[n]["b"]) for n in ("V15", "V19")] + [LineString([(x19, y4), (x15, y4)])]
    return unary_union([l.buffer(B_BALK / 2, cap_style="square") for l in lin]).intersection(BETONG)


def plintar():
    return {r["namn"]: box(r["mitt"][0] - PLINT[r["namn"]] / 2, r["mitt"][1] - PLINT[r["namn"]] / 2,
                           r["mitt"][0] + PLINT[r["namn"]] / 2, r["mitt"][1] + PLINT[r["namn"]] / 2) for r in ROR}


def ytor(g):
    """Polygonerna i en geometri (utan linjer och punkter från skärningar)."""
    if g.geom_type == "Polygon":
        return [g] if g.area > 1 else []
    return [p for gg in getattr(g, "geoms", []) for p in ytor(gg)]


def sv(x, n=0):
    return f"{x:,.{n}f}".replace(",", "\u00a0").replace(".", ",").replace("-", "−")


def svm(x):
    return sv(x, 0 if abs(x - round(x)) < 0.05 else 1)


if __name__ == "__main__":
    print("källaren", list(KALLARE.exterior.coords))
    print("yttre hörn", HORN_UT, "inåtgående", HORN_IN)
    for a in ANSLUTNINGAR:
        print(a)
    for o in OPPNINGAR:
        print(o["namn"], o["vaggar"], o["x0"], o["x1"], o["bredd"], o["z0"], o["fardig"])
    for v in VAGGAR:
        print(v["namn"], v["typ"], v["ax"], v["c"], v["a"], v["b"], "ute", v["ute"], "ytterliv", v["ytterliv"],
              "mot", v["mot_a"] and v["mot_a"]["namn"], v["mot_b"] and v["mot_b"]["namn"])
    for r in ROR:
        print(r["namn"], r["ror"], r["mitt"], PLINT[r["namn"]])
    print("kärna", KARNA.area / 1e6, "hel", HEL.area / 1e6, "kantbalk", kantbalk().area / 1e6,
          "inre balkar", balkar_inre().area / 1e6)
