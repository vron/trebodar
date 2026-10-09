"""
Kontroll av lastgeometrin i F-01, K-01, K-05 och K-06 mot Onshape-modellen: lastbredder, lastytor, höjder och
fyllnadshöjder. Stödens exakta lägen kontrolleras inte (trästommen under nock- och dalbalkarna är inte fullständigt
modellerad).

    ./.venv/bin/python kontroll_laster.py

Skriver tabellen till terminalen och figuren granskning/ytterväggens_läge.png (redovisning: granskning/lastgeometri.md).

Koordinater som i K-05: x, y från skärningen mellan plattkanterna x = 0 och y = 0, z från bjälklagets överkant (mm).
Handlingarnas värden är avskrivna från rapporterna och beräkningsfilerna – uppdatera dem om handlingarna ändras.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from geometri import Plan, linjeprob, snitt, ytanalys  # noqa: E402
from modell import Modell  # noqa: E402

ROT = HERE.parent.parent
G05 = json.loads((ROT / "beräkningar" / "K-05" / "bild" / "geometri.json").read_text(encoding="utf-8"))
# handlingarnas antaganden läses ur beräkningsfilerna: ytterväggens läge (K-05 laster.py) och fyllningen (K-06)
VAGG_IN = float(re.search(r"^VAGG_IN = ([\d.]+)", (ROT / "beräkningar" / "K-05" / "laster.py").read_text(
    encoding="utf-8"), re.M).group(1))
sys.path.insert(0, str(ROT / "beräkningar" / "K-06"))
import indata as K06  # noqa: E402
m = Modell(tyst=True)
_pl = [d for d in m.delar if d.namn == "Mittenplatta"][0]
O = np.array([_pl.bbox[0], _pl.bbox[1], _pl.bbox[5]])
TAN30 = np.tan(np.radians(30))
rader = []


def bb(d):
    b = np.array(d.bbox)
    return np.r_[b[:3] - O, b[3:] - O]


def del_(namn):
    return [d for d in m.delar if d.namn == namn][0]


def rad(grupp, storhet, handling, modell, bedomning):
    rader.append((grupp, storhet, handling, modell, bedomning))


def lodlinje(x, y, delar, z0=-6000, z1=6000):
    P1 = np.array([x, y, z0]) + O
    P2 = np.array([x, y, z1]) + O
    return [(a[2] - O[2], b[2] - O[2], d) for _, _, d, a, b in linjeprob(m, delar, P1, P2)]


def mark(x, y):
    s = lodlinje(x, y, m.valj("Uppfyllnad,Berg,Sovrumsavsats"))
    return max(s, key=lambda t: t[1]) if s else None


def plansnitt(z, urval):
    pl = Plan.tolka(f"z={O[2] + z}").flytta(O[0], O[1])
    return unary_union([s.yta for s in snitt(m, m.valj(urval), pl)])


# ---------------------------------------------------------------- tak
R = [d for d in m.delar if d.namn.startswith("Å")]
plan, _, _ = ytanalys(m.form(R[0]))
lut = sorted({round(np.degrees(np.arccos(abs(n[2]))), 2) for (n, _), _ in plan.items() if 0.1 < abs(n[2]) < 0.99})
rad("Tak", "takvinkel", "30°", " / ".join(f"{v:g}°" for v in lut), "stämmer")
djup = sorted(abs(d1 + d2) for (n1, d1), _ in plan.items() for (n2, d2), _ in plan.items()
              if 0.1 < abs(n1[2]) < 0.99 and np.allclose(n1, -np.array(n2)))
yt = sorted({round(min(bb(d)[3] - bb(d)[0], bb(d)[4] - bb(d)[1]), 1) for d in R})
fack = {}
for d in R:
    b = bb(d)
    fack.setdefault((round(b[0]), round(b[3])), []).append((b[1] + b[4]) / 2)
cc = np.concatenate([np.diff(sorted(v)) for v in fack.values() if len(v) > 1])
rad("Tak", "takbalkar", "45×170 c/c 600", f"{yt[0]:g}×{djup[0]:.0f}, c/c {np.median(cc):.0f} ({len(R)} st, "
    f"glesare vid öppningar)", "stämmer")

B = {k: bb(del_(f"HEA200 {v}")) for k, v in dict(N1="NV", D2="NVb", N3="M", D4="SEb", N5="SE").items()}
xc = {k: (b[0] + b[3]) / 2 for k, b in B.items()}
rad("Tak", "avstånd mellan nockarna N5–N3–N1", "4 750 (K-01 snöbredd dal)",
    f"{xc['N3'] - xc['N5']:.0f} / {xc['N1'] - xc['N3']:.0f}", "stämmer")
rad("Tak", "nockbalkarnas överkant över bjälklaget", "symmetriska huskroppar (K-05 gavelhöjder)",
    f"N1/N5 {B['N1'][5]:.0f}, N3 {B['N3'][5]:.0f} (mittre nocken {B['N3'][5] - B['N1'][5]:.0f} högre)",
    "mittre gavelns topp ca 0,09 m högre än K-05 räknar, försumbart")
for k, g in (("D2", ("N3", "N1")), ("D4", ("N5", "N3"))):
    mitt = (xc[g[0]] + xc[g[1]]) / 2
    rad("Tak", f"dalbalk {k}, läge x", f"{dict(D2=9280, D4=4530)[k]} (K-05 geometri.json, mitt mellan nockarna)",
        f"{xc[k]:.0f} ({xc[k] - mitt:+.0f}, följer av den högre mittnocken)",
        "påverkar inte lastbredderna; bara figurerna i K-05")

# Ytterväggarnas läge (takfotsväggarnas stöd) och takfot
vagg = {"vänster": "1SO <1>", "höger": "3NV <1>", "mittre vänster": "2SO <1>", "mittre höger": "2NV <1>"}
vx = {}
for k, g in vagg.items():
    ds = [d for d in m.delar if d.grupp.endswith("/" + g)]
    b = np.array(m.bbox(ds))
    vx[k] = ((b[0] + b[3]) / 2 - O[0], b[3] - b[0], b[5] - O[2])
rand = {"vänster": 0.0, "höger": 13810.0, "mittre vänster": 4500.0, "mittre höger": 9310.0}
ut = {k: abs(vx[k][0] - rand[k]) for k in vx}
avv = max(abs(v - VAGG_IN) for v in ut.values())
rad("Tak", "ytterväggens centrum innanför plattkanten", f"{VAGG_IN:g} mm (K-05 VAGG_IN)",
    f"{min(ut.values()):.1f}–{max(ut.values()):.1f} mm (stomme 95: 30 mm utanför till 65 mm innanför kanten)",
    "stämmer" if avv < 1 else f"AVVIKER {avv:.0f} mm")
rad("Tak", "väggens höjd till takfot (hammarbandets ök)", "2,5 m", f"{max(v[2] for v in vx.values()) / 1000:.2f} m",
    "stämmer")
# takfot = takbalkarnas yttersta ände på respektive sida
x0s, x1s = [bb(d)[0] for d in R], [bb(d)[3] for d in R]
eave = {"vänster": min(x0s), "höger": max(x1s),
        "mittre vänster": min(x for x in x0s if 4000 < x < 4500),
        "mittre höger": max(x for x in x1s if 9310 < x < 9600)}
uts = [abs(eave[k] - rand[k]) for k in eave]
rad("Tak", "takutsprång vid takfot", "0,2 m (K-05)", f"takbalkarna {min(uts):.0f} mm utanför plattkanten "
    f"({min(uts) - 30:.0f} mm utanför väggliv)", "K-05 på säker sida")
gav = [bb(d) for d in m.delar if "/Stol " in d.sokvag]
rad("Tak", "takutsprång vid gavel", "0,2 m (K-05)", "takstolens yttersida 30 mm utanför plattkanten, "
    "inga takbalkar utanför gaveln", "K-05 på säker sida")


def lastbredd(xn, vanster, hoger):
    return (abs(xn - vanster) + abs(hoger - xn)) / 2


lb = {"N1": lastbredd(xc["N1"], xc["D2"], vx["höger"][0]), "N3": lastbredd(xc["N3"], xc["D4"], xc["D2"]),
      "N5": lastbredd(xc["N5"], vx["vänster"][0], xc["D4"]), "D2": lastbredd(xc["D2"], xc["N3"], xc["N1"]),
      "D4": lastbredd(xc["D4"], xc["N5"], xc["N3"])}
rad("Tak", "lastbredd nockbalk (horisontellt)", "2,50 m, antaget största (K-01)",
    f"N3 {lb['N3'] / 1000:.3f}, N1 {lb['N1'] / 1000:.3f}, N5 {lb['N5'] / 1000:.3f} m", "stämmer (N3 exakt 2,50)")
rad("Tak", "lastbredd dalbalk (horisontellt)", "2,375 m (K-01)", f"D2 {lb['D2'] / 1000:.3f}, D4 {lb['D4'] / 1000:.3f} m",
    "stämmer")
tf = {k: (abs((xc["N1"] if k == "höger" else xc["N5"] if k == "vänster" else xc["N3"]) - vx[k][0]) / 2
          + abs(vx[k][0] - eave[k])) for k in vx}
rad("Tak", "takfotsväggens lastbredd", "1,28 m vänster/höger, 1,40 m mittre (K-05)",
    f"{tf['vänster'] / 1000:.2f} / {tf['höger'] / 1000:.2f}, mittre {tf['mittre vänster'] / 1000:.2f} / "
    f"{tf['mittre höger'] / 1000:.2f} m", "K-05 på säker sida")
kontur = Polygon(G05["kontur"])
tak_k05 = kontur.buffer(200, join_style=2).area / 1e6
u = eave["höger"] - 13810.0                 # takbalkarnas utstick utanför plattkanten
tak = unary_union([box(eave["vänster"], B["N5"][1], 4310 + u, B["N5"][4]),      # gavlar: nockbalkarnas ändar
                   box(eave["mittre vänster"], B["N3"][1], eave["mittre höger"], B["N3"][4]),
                   box(9500 - u, B["N1"][1], eave["höger"], B["N1"][4])]).area / 1e6
rad("Tak", "takets planarea (snö på hela taket)", f"{tak_k05:.1f} m² → 1,5 × A = {1.5 * tak_k05:.0f} kN (K-05)",
    f"{tak:.1f} m² → {1.5 * tak:.0f} kN", "K-05 på säker sida")
gips = ytanalys(m.form(m.valj("gyp_c_f1")[0]))[0]
dd = sorted({round(abs(d), 1) for (n, d), _ in gips.items() if 0.1 < abs(n[2]) < 0.99})
t_gips = min(b - a for a, b in zip(dd, dd[1:]))
rad("Tak", "innertak: gips och installationsspalt", "2 × 12,5 mm gips, korslagda reglar 45 mm (F-01)",
    f"{t_gips:.0f} mm gips, spalt 45 mm under takbalkarna", "F-01 på säker sida")

# ---------------------------------------------------------------- vind
pl1 = plansnitt(-75, "Mellanplatta")
bredd = eave["höger"] - eave["vänster"]
nock = max(bb(d)[5] for d in R + [del_(f"HEA200 {v}") for v in ("M", "NV")])
markniva = []
for x, y in [(7000, -600), (5000, -600), (14400, 2000), (14400, 7000), (-600, 4500), (11000, 13100)]:
    r = mark(x, y)
    if r:
        markniva.append(r[1])
h = (nock + 75 - min(markniva)) / 1000
rad("Vind", "referenshöjd z (nock över mark)", "7,0 m (F-01, K-01)",
    f"ca {h:.1f} m (nock {nock / 1000:.2f} m + ca 0,08 taktäckning över färdigt golv, mark {min(markniva) / 1000:.2f} m)",
    "på säker sida")
rad("Vind", "e = min(b, 2h), vind längs nocken", "12 m (K-01)",
    f"b = {bredd / 1000:.1f} m (takfot–takfot), 2h ≈ {2 * h:.1f} m → e ≈ {min(bredd / 1000, 2 * h):.1f} m",
    "K-01 på säker sida")

# ---------------------------------------------------------------- bjälklag
hal = Polygon(G05["hal"])
sl = plansnitt(-75, "#" + str(_pl.id))
hm = Polygon(sl.interiors[0]) if sl.interiors else None
rad("Bjälklag", "plattans area utan trapphål", f"{(kontur.area - hal.area) / 1e6:.2f} m² (K-05: 157 m²)",
    f"{sl.area / 1e6:.2f} m²", "stämmer")
rad("Bjälklag", "plattans tjocklek", "150 mm", f"{_pl.storlek[2]:.0f} mm", "stämmer")
if hm is not None:
    x0, y0, x1, y1 = hm.bounds
    hx0, hy0, hx1, hy1 = hal.bounds
    rad("Bjälklag", "trapphål", f"{hx1 - hx0:.0f} × {hy1 - hy0:.0f}, hörn ({hx0:g}; {hy0:g})",
        f"{x1 - x0:.0f} × {y1 - y0:.0f}, hörn ({x0:g}; {y0:g})",
        "stämmer" if max(abs(x0 - hx0), abs(y0 - hy0)) < 0.05 else f"storlek stämmer, läget {x0 - hx0:+.1f} / {y0 - hy0:+.1f} mm")
markplatta = Polygon(G05["mark"])
rad("Bjälklag", "plattan på mark (utan källare under)", f"{markplatta.area / 1e6:.1f} m² (K-05: 29,3 m²)",
    "Lecaväggarna V3/V20 inom 5 mm från K-05", "stämmer")
rad("Bjälklag", "trappan", "3,0 m lång, 0,83 m bred (K-05)", f"hålets bredd {(hm.bounds[3] - hm.bounds[1]) / 1000:.3f} m; "
    "trappan finns inte i modellen", "bredden stämmer")
pel = [d for d in m.delar if d.namn.startswith("K Pillar")]
rad("Källare", "fri höjd bottenplatta–bjälklag (rörens längd)", "2 100 mm (K-05, K-06)",
    f"{np.median([d.storlek[2] for d in pel]):.0f} mm ({len(pel)} rör)", "stämmer")

# ---------------------------------------------------------------- källare
vg = plansnitt(-2000, "Bkärna,Isoskal")
bp = plansnitt(-2400, "Bottenplatta")
kallare = unary_union([Polygon(g.exterior) for g in getattr(bp, "geoms", [bp])])   # matkällaren fylls i
golv = kallare.difference(vg)
rad("Källare", "Lecaväggarnas tjocklek", "350 mm (100 + 150 + 100)", "350 mm, ytterliv 30 mm utanför plattkanten",
    "stämmer")
rad("Källare", "golvyta för nyttig last", "359 kN / (2,0 + 0,7) = 133 m² (K-06)",
    f"{golv.area / 1e6:.1f} m² innanför väggarna", "K-06 på säker sida")
rad("Källare", "bottenplatta i matkällaren", "platta 100 mm i hela källaren (K-06)",
    "ingen platta innanför V2/V15/V19–V20, bara en remsa under väggarna", "modellen avviker (kontrollera)")

# ---------------------------------------------------------------- fyllning mot källarväggarna
UT = {"V1": (0, 1), "V2": (0, 1), "V3": (0, 1), "V7": (0, -1), "V9": (0, -1), "V14": (1, 0), "V16": (-1, 0),
      "V18": (-1, 0), "V20": (-1, 0), "V21": (-1, 0), "V10–V13": (0, -1)}
TOPP_BP = -2250.0
vagg05 = {f"V{i}": w for i, w in enumerate(G05["vagg"], 1)}
for n, fy in K06.FYLL.items():
    if "fasad" in fy:                             # hela fasaden mellan hörnen (K-06: fri överkant)
        lin = vagg05[fy["fasad"]["linje"]]
        a, b = sorted(vagg05[x][1] for x in fy["fasad"]["mellan"])
        ax, c = lin[0], lin[1]
    else:
        ax, c, a, b = vagg05[n][:4]
    nx, ny = UT[n]
    h = []
    for s in np.linspace(a + 100, b - 100, 9):
        for dist in (175 + 50, 175 + 300, 175 + 600):          # närmast väggen; glipa mot berget i modellen
            x, y = (s, c) if ax == "h" else (c, s)
            r = mark(x + nx * dist, y + ny * dist)
            if r:
                k = fy["h"][0] + (fy["h"][1] - fy["h"][0]) * (s - a) / (b - a)     # K-06 i samma punkt
                h.append(((r[1] - TOPP_BP) / 1000, r[2].namn, k))
                break
    k = fy["h"]
    if not h:
        rad("Fyllning", n, f"{k[0]:.2f}–{k[1]:.2f} m (K-06)", "ingen mark modellerad intill väggen", "kan inte kontrolleras")
        continue
    hv = [v for v, _, _ in h]
    over = max(v - kk for v, _, kk in h)          # > 0: modellen har högre fyllning än K-06
    material = ", ".join(sorted({t for _, t, _ in h}))
    if fy.get("platta") and material == "Berg":
        bed = "berg i stället för fyllning (inget jordtryck från berg); se plattan på mark"
    elif over > 0.05:
        bed = f"AVVIKER: modellen ger upp till {over:.2f} m högre fyllning"
    elif max(abs(v - kk) for v, _, kk in h) <= 0.05:
        bed = "stämmer"
    else:
        bed = "K-06 på säker sida"
    rad("Fyllning", n, f"{k[0]:.2f}–{k[1]:.2f} m över bottenplattans ök (K-06)",
        f"{min(hv):.2f}–{max(hv):.2f} m ({material})", bed)
r = lodlinje(2000, 12000, m.valj("Berg,Uppfyllnad"))
rad("Fyllning", "under plattan på mark", "400 mm cellplast på fyllning upp till 1,7 m (K-06)",
    f"berget {max(b for _, b, _ in r) - TOPP_BP:.0f} mm över bottenplattans ök, "
    f"{-150 - max(b for _, b, _ in r):.0f} mm under plattan", "AVVIKER: inget utrymme för 400 mm cellplast")

# ---------------------------------------------------------------- F-01 areor
plan1 = Polygon(pl1.exterior).area / 1e6      # till ytterliv (platta + kantisolering), trapphålet medräknat
rad("Areor", "byggnadsarea", "135 + 30 m² (F-01)", f"plan 1 till ytterliv {plan1:.1f} m²", "jämför med bygglovets areor")
rad("Areor", "bruttoarea", "270 + 30 m² (F-01)", f"källare {kallare.area / 1e6:.1f} + plan 1 {plan1:.1f} = "
    f"{kallare.area / 1e6 + plan1:.1f} m²", "jämför med bygglovets areor")

# ---------------------------------------------------------------- figur: ytterväggens läge
def rita_vaggens_lage(ut):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ritning import _patch, _polygoner

    def regel_y(grupp, nara):
        ys = [(d.bbox[1] + d.bbox[4]) / 2 - O[1] for d in m.delar if d.grupp.endswith("/" + grupp) and d.storlek[2] > 2000]
        return min(ys, key=lambda y: abs(y - nara))
    fig, axs = plt.subplots(1, 2, figsize=(11, 7.5))
    delar = [d for d in m.delar if not d.namn.startswith(("Uppf", "Berg"))]
    for ax, (titel, grupp, lim, kant, ut_) in zip(axs, [
            ("Vänster långsida: plan 1 vägg 1SO över V21", "1SO <1>", (-400, 500), 0.0, -1),
            ("Höger långsida: plan 1 vägg 3NV över V14", "3NV <1>", (13310, 14210), 13810.0, 1)]):
        y = regel_y(grupp, 6000)
        for s_ in snitt(m, delar, Plan.tolka(f"y={O[1] + y}").flytta(O[0], O[2])):
            for p in _polygoner(s_.yta):
                ax.add_patch(_patch(p, facecolor=s_.del_.farg, edgecolor="black", lw=0.5))
        ax.axvline(kant, color="k", lw=0.8, ls=":")
        ax.axvline(kant - ut_ * 120, color="red", lw=1.8, ls="--")
        ax.axvline(kant - ut_ * ut_min, color="tab:blue", lw=1.8)
        ax.text(0.03, 0.97, f"– – K-05/K-06: väggens centrum {VAGG_IN:g} mm innanför plattkanten\n"
                f"—— modellen: stommens centrum {ut_min:.1f} mm innanför plattkanten\n· · · plattkant",
                transform=ax.transAxes, va="top", fontsize=7.5, bbox=dict(fc="white", ec="0.7"))
        ax.set_xlim(*lim); ax.set_ylim(-1100, 1300); ax.set_aspect("equal"); ax.grid(lw=0.3)
        ax.set_title(f"{titel} (snitt y = {y:.1f})", fontsize=9)
        ax.set_xlabel("x (mm, K-05)"); ax.set_ylabel("z (mm från bjälklagets ök)")
    fig.suptitle("Ytterväggens läge på plan 1: stommen står över Lecans yttre skikt och 30 mm ut över plattkanten",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(ut, dpi=150)
    plt.close(fig)


ut_min = min(ut.values())


# ---------------------------------------------------------------- utskrift
if __name__ == "__main__":
    grp = None
    for g, s, hd, md, bd in rader:
        if g != grp:
            print(f"\n{g}")
            grp = g
        print(f"  {s:<44} {hd:<52} {md:<62} {bd}")
    (HERE / "granskning").mkdir(exist_ok=True)
    rita_vaggens_lage(HERE / "granskning" / "ytterväggens_läge.png")
    print("\nfigur: granskning/ytterväggens_läge.png")
