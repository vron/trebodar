"""Kontroll av källarstommen och bottenplattan i R-04 och R-05 (beräkningar/R-05/kallare.py) mot modellen.

    .venv/bin/python kontroll_r045.py

kallare.py bygger källarens geometri för R-04 och R-05 ur K-05:s geometri.json (väggarna och rören, kontrollerade
med kontroll_geometri05.py), K-06:s indata och egna uppgifter: öppningarnas bröstning. Den här kontrollen läser
modellen (modeller/trebodar/ut/trebodar.step) och jämför:

    - öppningarna i betongkärnan: läge längs väggen och bröstningens höjd (betongen);
    - bottenplattans kontur, som ska ligga i väggarnas ytterliv (L-elementens ytterkant; betongen 100 mm innanför);
    - bottenplattans kantbalk, balkar under innerväggarna och plintar (R-04.1) och L-elementen i plan;
    - bottenplattans höjder (K-06:s utförande): plattan, cellplasten i fält med skiktgränsen (plastfolien) i balkarnas
      underkant, kantbalken på L-elementens fot och L-elementens rygg med fasen, som betongen fyller;
    - cellplastens zoner med den starkare kvaliteten (K-06): det undre skiktet under bottenplattan och plattan på marks
      fria hörn;
    - väggarnas höjd (betongkärnan från bottenplattans överkant till mellanbjälklagets underkant);
    - rörens tvärsnitt och antal, matkällarens golv och att kärnorna går ihop i hörn och anslutningar.

Koordinater i mm som i K-05 (x, y från skärningen mellan mellanbjälklagets kanter, z från bjälklagets överkant).
Skriver ingenting.
"""
import os
import sys

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
ROT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROT, "beräkningar", "R-05"))
from geometri import Plan, linjeprob, snitt  # noqa: E402
from modell import Modell  # noqa: E402
import kallare as K  # noqa: E402

TOL = 0.5
Z_GOLV = -K.H_VAGG - K.H_MB          # bottenplattans överkant i K-05:s z (−2 250)

m = Modell(tyst=True)
_pl = [d for d in m.delar if d.namn == "MB-B"][0]
O = np.array([_pl.bbox[0], _pl.bbox[1], _pl.bbox[5]])
KARNA = m.valj("V*-K,F*-B-K")                                  # källarväggarnas och bröstningarnas kärnor


def prob(p1, p2, z, delar):
    """Sträckor [(t0, t1)] längs linjen p1→p2 (2D, K-05) på nivån z, sammanslagna, t i mm från p1."""
    iv = sorted((t0, t1) for t0, t1, *_ in linjeprob(m, delar, np.r_[p1, z] + O, np.r_[p2, z] + O))
    ut = []
    for a, b in iv:
        if ut and a <= ut[-1][1] + 0.01:
            ut[-1][1] = max(ut[-1][1], b)
        else:
            ut.append([a, b])
    return ut


def lodratt(x, y, z0, z1, delar):
    """Sträckor i z längs en lodrät linje genom (x, y) mellan z0 och z1."""
    return [(z0 + a, z0 + b) for a, b in prob_z(x, y, z0, z1, delar)]


def prob_z(x, y, z0, z1, delar):
    P1 = np.r_[x, y, z0] + O
    P2 = np.r_[x, y, z1] + O
    iv = sorted((t0, t1) for t0, t1, *_ in linjeprob(m, delar, P1, P2))
    return iv


fel = []
rapport = []

# ---------------------------------------------------------------- öppningarna
for o in K.OPPNINGAR:
    c = o["c"]
    zc = Z_GOLV + K.H_VAGG - 50.0                         # strax under bjälklaget
    iv = prob((o["x0"] - 800, c), (o["x1"] + 800, c), zc, KARNA)
    iv = [(o["x0"] - 800 + a, o["x0"] - 800 + b) for a, b in iv]
    luckor = [(a[1], b[0]) for a, b in zip(iv, iv[1:]) if b[0] - a[1] > 1]
    lucka = min(luckor, key=lambda q: abs(q[0] - o["x0"]) + abs(q[1] - o["x1"])) if luckor else None
    zs = lodratt((o["x0"] + o["x1"]) / 2, c, Z_GOLV - 10, Z_GOLV + K.H_VAGG + 10, KARNA)
    z_brost = (max(b for a, b in zs) - Z_GOLV) if zs else 0.0
    rapport.append(f"  {o['namn']}: modellen x {lucka}, bröstning {z_brost:.1f}; R-05 x ({o['x0']}, {o['x1']}), "
                   f"bröstning {o['z0']}")
    if lucka is None or abs(lucka[0] - o["x0"]) > TOL or abs(lucka[1] - o["x1"]) > TOL:
        fel.append(f"{o['namn']}: öppningen i kärnan, R-05 {o['x0']}–{o['x1']}, modellen {lucka}")
    if abs(z_brost - o["z0"]) > TOL:
        fel.append(f"{o['namn']}: bröstningens höjd, R-05 {o['z0']}, modellen {z_brost:.1f}")

# ---------------------------------------------------------------- bottenplattan
def plansnitt(z, delar):
    """Delarnas snitt i planet z (K-05) som en yta i K-05:s x, y."""
    pl = Plan.tolka(f"z={O[2] + z}").flytta(O[0], O[1])
    ytor = [sd.yta for sd in snitt(m, delar, pl) if not sd.yta.is_empty]
    return unary_union([p.buffer(0) for p in ytor])


def jamfor_yta(namn, modell, r04):
    diff = modell.symmetric_difference(r04).area
    rapport.append(f"  {namn}: modellen {modell.area / 1e6:.3f} m², R-04 {r04.area / 1e6:.3f} m², "
                   f"skillnad {diff / 1e6:.4f} m²")
    if diff > 1e4:
        fel.append(f"{namn}: skillnad {diff / 1e6:.4f} m² mellan modellen och R-04")


platta = m.valj("/Bottenplatta/")
jamfor_yta("bottenplattan (L-elementens ytterkant)", plansnitt(Z_GOLV - K.UTF["h_balk"] + 50.0, platta), K.KALLARE)
jamfor_yta("bottenplattans betong", plansnitt(Z_GOLV - 50.0, m.valj("BP-B")), K.BETONG)
jamfor_yta("kantbalk, balkar och plintar (R-04.1)", plansnitt(Z_GOLV - 150.0, m.valj("BP-KB,BP-IB,BP-PL")),
           unary_union([K.kantbalk(), K.balkar_inre()] + list(K.plintar().values())).intersection(K.BETONG))
Z_FOT = Z_GOLV - K.UTF["h_balk"] - K.T_FOT / 2                  # mitt i L-elementens fot
jamfor_yta("L-elementens fot", plansnitt(Z_FOT, m.valj("BP-L")), K.l_element())


def lager(x, y, z0, z1, delar):
    """Delarna längs en lodrät linje genom (x, y): [(z0, z1, namn)] nerifrån."""
    return sorted((z0 + t0, z0 + t1, d.namn) for t0, t1, d, *_ in linjeprob(m, delar, np.r_[x, y, z0] + O,
                                                                          np.r_[x, y, z1] + O))


def jamfor_z(namn, modell, r04):
    rapport.append(f"  {namn}: modellen {modell}, R-04 {r04}")
    if len(modell) != len(r04) or any(abs(a - b) > TOL for p, q in zip(modell, r04) for a, b in zip(p, q)):
        fel.append(f"{namn}: modellen {modell}, R-04 {r04}")


# höjderna i K-06:s utförande: plattan HP på cellplast EPS (det undre skiktet TF, plastfolien i balkarnas underkant)
HP, HB, TF, EPS = K.H_PLATTA, K.UTF["h_balk"], K.T_FOT, K.UTF["t_eps"]
tjock = unary_union([K.kantbalk(), K.balkar_inre()] + list(K.plintar().values()))
fp = K.BETONG.difference(tjock.buffer(300.0)).representative_point()       # i fält, utanför balkar och plintar
lf = lager(fp.x, fp.y, Z_GOLV - 600, Z_GOLV + 1, m.valj("BP-B,BP-C*"))
jamfor_z("bottenplattan i fält: betong och cellplastens skikt (z)", [(round(a, 1), round(b, 1)) for a, b, _ in lf],
         [(Z_GOLV - HP - EPS, Z_GOLV - HB), (Z_GOLV - HB, Z_GOLV - HP), (Z_GOLV - HP, Z_GOLV)])
w = K.VAGG["V21"]
xk, yk = w["c"] + w["ute"] * (K.T_VAGG / 2 - K.L_BEN - K.B_BALK / 2), (w["a"] + w["b"]) / 2   # kantbalkens mitt
lk = lager(xk, yk, Z_GOLV - 600, Z_GOLV + 1, m.valj("BP-B,BP-KB,BP-L"))
jamfor_z("kantbalken vid V21 på L-elementens fot (z)", [(round(a, 1), round(b, 1)) for a, b, _ in lk],
         [(Z_GOLV - HB - TF, Z_GOLV - HB), (Z_GOLV - HB, Z_GOLV - HP), (Z_GOLV - HP, Z_GOLV)])
# ryggen i överkant: cellplast FAS från ytterkanten, sedan fasens betong (45°) och plattan
xu = w["c"] + w["ute"] * K.T_VAGG / 2                                                     # väggens ytterliv
z_t = Z_GOLV - 10.0
ut_in = [(round(abs(t0), 1), round(abs(t1), 1), d.namn[:5])
         for t0, t1, d, *_ in linjeprob(m, m.valj("BP-L,BP-FAS,BP-B"), np.r_[xu, yk, z_t] + O,
                                        np.r_[xu - w["ute"] * 200.0, yk, z_t] + O)]
jamfor_z("L-elementens rygg 10 mm under överkant: cellplast, fasens betong, plattan (mm från ytterlivet)",
         [(a, b) for a, b, _ in sorted(ut_in)], [(0.0, K.FAS + 10.0), (K.FAS + 10.0, K.L_BEN), (K.L_BEN, 200.0)])

# ---------------------------------------------------------------- cellplastens zoner med den starkare kvaliteten
def i_plan(namn):
    """Delarnas omskrivna rektanglar i plan (x0, y0, x1, y1), K-05:s koordinater."""
    return sorted((round(float(d.bbox[0] - O[0]), 1), round(float(d.bbox[1] - O[1]), 1),
                   round(float(d.bbox[3] - O[0]), 1), round(float(d.bbox[4] - O[1]), 1)) for d in m.valj(namn))


jamfor_z("det undre skiktets zon med den starkare cellplasten (BP-CS; K-06 EPS_ZON)", i_plan("BP-CS"),
         sorted(tuple(z) for z in K.EPS_ZON))
_pm, _, _rygg = K.platta_pa_mark(urtag=False)               # plattan på mark och L-elementens rygg under plattan
jamfor_z("plattan på marks zoner med den starkare cellplasten, innanför L-elementens rygg (PM-CS*; K-06 EPS_MARK_ZON)",
         i_plan("PM-CS*"), sorted(tuple(round(v, 1) for v in box(*z).intersection(_pm.difference(_rygg)).bounds)
                                  for z in K.EPS_MARK_ZON))

# ---------------------------------------------------------------- väggarnas höjd
w = K.VAGG["V21"]
zs = lodratt(w["c"], (w["a"] + w["b"]) / 2, Z_GOLV - 400, 200.0, KARNA)
h = (max(b for a, b in zs) - min(a for a, b in zs)) if zs else 0.0
rapport.append(f"  V21:s kärna z {zs} → höjd {h:.1f} (R-05 {K.H_VAGG})")
if abs(h - K.H_VAGG) > TOL:
    fel.append(f"väggarnas höjd: R-05 {K.H_VAGG}, modellen {h:.1f}")

# ---------------------------------------------------------------- rören, matkällarens golv, kärnornas anslutningar
ror = [d for d in m.delar if d.namn.startswith("P") and d.namn.endswith("-R")]
storlek = sorted({round(d.bbox[3] - d.bbox[0]) for d in ror})
rapport.append(f"  rören: {len(ror)} st, {storlek} mm breda (R-05 {sum(r['n'] for r in K.ROR)} st VKR {K.PLAT:.0f})")
if storlek != [round(K.PLAT)]:
    fel.append(f"rören i modellen är {storlek} mm breda, R-05 VKR {K.PLAT:.0f}×{K.PLAT:.0f}×4")
if len(ror) != sum(r["n"] for r in K.ROR):
    fel.append(f"modellen har {len(ror)} rör, R-05 {sum(r['n'] for r in K.ROR)} (P7 två rör)")
zm = lodratt(7000.0, 9300.0, Z_GOLV - 400, Z_GOLV + 50, m.valj("BP-B"))
if zm and abs(max(b for a, b in zm) - Z_GOLV) > TOL:
    fel.append(f"matkällarens golv i modellen z {max(b for a, b in zm):.1f}, R-04 {Z_GOLV}")
for w in K.VAGGAR:
    # kärnan ska gå hela vägen till den vinkelräta väggens centrumlinje i hörn och anslutningar
    for ande, o in ((w["a"], w["mot_a"]), (w["b"], w["mot_b"])):
        if o is None:
            continue
        mitt = (w["a"] + w["b"]) / 2
        p_in = (mitt, w["c"]) if w["ax"] == "h" else (w["c"], mitt)
        p_slut = (ande, w["c"]) if w["ax"] == "h" else (w["c"], ande)
        iv = prob(p_in, p_slut, Z_GOLV + 1000.0, KARNA)
        L = float(np.hypot(p_slut[0] - p_in[0], p_slut[1] - p_in[1]))
        if not iv or iv[0][0] > 1 or iv[0][1] < L - 1:
            fel.append(f"{w['namn']} mot {o['namn']}: kärnorna går inte ihop i modellen")

if __name__ == "__main__":
    print(f"modell: {m.fil.name} ({m.hash})")
    print("\n".join(rapport))
    if fel:
        print("R-04/R-05 avviker från modellen:")
        print("\n".join("  " + f for f in fel))
        sys.exit(1)
    print("R-04/R-05: allt stämmer med modellen.")
