"""Kontroll av källarstommen och bottenplattan i R-04 och R-05 (beräkningar/R-05/kallare.py) mot Onshape-modellen.

    .venv/bin/python kontroll_r045.py

kallare.py bygger källarens geometri för R-04 och R-05 ur K-05:s geometri.json (väggarna och rören, kontrollerade
med kontroll_geometri05.py), K-06:s indata och egna uppgifter: öppningarnas bröstning. Den här kontrollen läser
modellen (modeller/trebodar.step) och jämför:

    - öppningarna i betongkärnan: läge längs väggen och bröstningens höjd (betongen);
    - bottenplattans kontur, som ska ligga i väggarnas ytterliv (L-elementens ytterkant; betongen 100 mm innanför);
    - väggarnas höjd (betongkärnan från bottenplattans överkant till mellanbjälklagets underkant);
    - rörens tvärsnitt, matkällarens golv och kärnorna i anslutningarna, där modellen avviker från handlingarna
      tills punkterna i modeller/modell-todo.md är gjorda.

Koordinater i mm som i K-05 (x, y från skärningen mellan mellanbjälklagets kanter, z från bjälklagets överkant).
Skriver ingenting.
"""
import os
import sys

import numpy as np
from shapely.geometry import Polygon
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
_pl = [d for d in m.delar if d.namn == "Mittenplatta"][0]
O = np.array([_pl.bbox[0], _pl.bbox[1], _pl.bbox[5]])
KARNA = m.valj("Bkärna")


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

# ---------------------------------------------------------------- bottenplattans kontur
plattor = m.valj("Bottenplatta*")
pl = Plan.tolka(f"z={O[2] + Z_GOLV - 250.0}").flytta(O[0], O[1])       # nära underkanten: båda plattorna
ytor = [sd.yta for sd in snitt(m, plattor, pl) if not sd.yta.is_empty]
modell_kontur = unary_union([p.buffer(0) for p in ytor])
diff = modell_kontur.symmetric_difference(K.KALLARE).area
rapport.append(f"  bottenplattan (L-elementens ytterkant): modellen {modell_kontur.area / 1e6:.3f} m², R-04 {K.KALLARE.area / 1e6:.3f} m², "
               f"skillnad {diff / 1e6:.4f} m²")
if diff > 1e4:
    fel.append(f"bottenplattans kontur: skillnad {diff / 1e6:.4f} m² mellan modellen och R-04")

# ---------------------------------------------------------------- väggarnas höjd
w = K.VAGG["V21"]
zs = lodratt(w["c"], (w["a"] + w["b"]) / 2, Z_GOLV - 400, 200.0, KARNA)
h = (max(b for a, b in zs) - min(a for a, b in zs)) if zs else 0.0
rapport.append(f"  V21:s kärna z {zs} → höjd {h:.1f} (R-05 {K.H_VAGG})")
if abs(h - K.H_VAGG) > TOL:
    fel.append(f"väggarnas höjd: R-05 {K.H_VAGG}, modellen {h:.1f}")

# ---------------------------------------------------------------- kända avvikelser (modell-todo)
kanda = []
ror = m.valj("K Pillar*")
storlek = sorted({round(d.bbox[3] - d.bbox[0]) for d in ror})
if storlek != [round(K.PLAT)]:
    kanda.append(f"rören i modellen är {storlek} mm breda, R-05 VKR {K.PLAT:.0f}×{K.PLAT:.0f}×4 (punkt 8)")
if len(ror) != sum(r["n"] for r in K.ROR):
    kanda.append(f"modellen har {len(ror)} rör, R-05 {sum(r['n'] for r in K.ROR)} (P7 två rör, punkt 8)")
zm = lodratt(7000.0, 9300.0, Z_GOLV - 400, Z_GOLV + 50, m.valj("Bottenplatta matkällare"))
if zm and abs(max(b for a, b in zm) - Z_GOLV) > TOL:
    kanda.append(f"matkällarens golv i modellen z {max(b for a, b in zm):.1f}, R-04 {Z_GOLV} (punkt 10)")
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
            kanda.append(f"{w['namn']} mot {o['namn']}: kärnorna går inte ihop i modellen (punkt 11)")

if __name__ == "__main__":
    print(f"modell: {m.fil.name} ({m.hash})")
    print("\n".join(rapport))
    if kanda:
        print("Kända avvikelser, i modeller/modell-todo.md:")
        print("\n".join("  " + k for k in kanda))
    if fel:
        print("R-04/R-05 avviker från modellen:")
        print("\n".join("  " + f for f in fel))
        sys.exit(1)
    print("R-04/R-05: allt stämmer med modellen (utom de kända avvikelserna).")
