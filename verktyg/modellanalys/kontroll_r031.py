"""
Kontroll av mellanbjälklagets geometri i K-05 och R-03 (bild/geometri.json) mot Onshape-modellen (exakt B-rep).

    ./.venv/bin/python kontroll_r031.py

Jämför plattans kontur, trapphålet, rören, Lecaväggarna och de fria kanterna i geometri.json – underlaget för
K-05, K-06 och ritningarna R-03 – med modellen, och R-03.1:s måttkedjor (lägen som i R-03/ritningar.py) med
modellens hörn. K-05-koordinater: origo i skärningen mellan plattkanterna x = 0 och y = 0.
geometri.json skapas ur modellen av beräkningar/K-05/bild/geometri.py; avvikelser här betyder att modellen har
ändrats utan att geometri.py har körts om.
Bild: ut/R-03.1_kontroll.png
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from geometri import Plan, linjeprob, snitt  # noqa: E402
from modell import Modell  # noqa: E402
from ritning import _patch  # noqa: E402

ROT = HERE.parent.parent
G = json.load(open(ROT / "beräkningar" / "K-05" / "bild" / "geometri.json", encoding="utf-8"))
m = Modell()
platta = m.valj("Mittenplatta")
betong = [d for d in platta if d.namn == "Mittenplatta"][0]
b = betong.bbox
O = np.array([b[0], b[1], b[5]])                     # skärningen mellan plattkanterna x = 0 och y = 0, överkant
plan = Plan.tolka(f"z={(b[2] + b[5]) / 2}").flytta(O[0], O[1])
sd = {s.del_.namn: s for s in snitt(m, platta, plan)}
yta = sd["Mittenplatta"].yta
ytter = np.array(yta.exterior.coords)[:-1]
hal = np.array(yta.interiors[0].coords)[:-1]
xs = sorted({round(v, 3) for v in ytter[:, 0]})
ys = sorted({round(v, 3) for v in ytter[:, 1]})
hx = sorted({round(v, 3) for v in hal[:, 0]})
hy = sorted({round(v, 3) for v in hal[:, 1]})
avvikelser = []


def rad(namn, ritn, modell, tol=0.05):
    d = np.max(np.abs(np.asarray(ritn, float) - np.asarray(modell, float)))
    ok = d <= tol
    if not ok:
        avvikelser.append(namn)
    txt = lambda v: " / ".join(f"{float(x):g}" for x in np.atleast_1d(v))
    print(f"  {namn:<22} {txt(ritn):<40} {txt(modell):<40} {'stämmer' if ok else f'AVVIKER {d:.1f} mm'}")


print(f"Modell {m.fil.name} ({m.hash}), origo globalt ({O[0]:.3f}; {O[1]:.3f})\n")
print(f"  {'storhet':<22} {'geometri.json / ritning':<40} {'modell':<40}")
K = np.array(G["kontur"], float)
dk = max(min(np.linalg.norm(ytter - p, axis=1)) for p in K)
if dk > 0.05 or len(K) != len(ytter):
    avvikelser.append("kontur")
print(f"  {'konturens hörn':<22} {f'{len(K)} hörn':<40} {f'{len(ytter)} hörn, största avstånd {dk:.3f} mm':<40} "
      f"{'stämmer' if 'kontur' not in avvikelser else 'AVVIKER'}")
H = np.array(G["hal"], float)
rad("trapphål x", [H[:, 0].min(), H[:, 0].max()], [hx[0], hx[-1]])
rad("trapphål y", [H[:, 1].min(), H[:, 1].max()], [hy[0], hy[-1]])

# rör
ror = [d for d in m.delar if d.namn.startswith("K Pillar")]
mitt = np.array([[(d.bbox[0] + d.bbox[3]) / 2 - O[0], (d.bbox[1] + d.bbox[4]) / 2 - O[1]] for d in ror])
for i, (x, y) in enumerate(G["pelare"], 1):
    j = int(np.argmin(np.hypot(mitt[:, 0] - x, mitt[:, 1] - y)))
    rad(f"rör P{i}", [x, y], [round(v, 3) for v in mitt[j]])

# Lecaväggarnas centrumlinjer (tvärs mitt på väggen, 1 m under bjälklaget)
LECA = m.valj("Bkärna,Isoskal")
for i, (ax_, c, a, b_, *_) in enumerate(G["vagg"], 1):
    s = (a + b_) / 2
    p1, p2 = ((s, c - 400, -1000), (s, c + 400, -1000)) if ax_ == "h" else ((c - 400, s, -1000), (c + 400, s, -1000))
    seg = linjeprob(m, LECA, np.array(p1) + O, np.array(p2) + O)
    lo, hi = c - 400 + min(t0 for t0, *_ in seg), c - 400 + max(t1 for _, t1, *_ in seg)
    rad(f"vägg V{i} centrum", round(c, 3), round((lo + hi) / 2, 3))

# R-03.1:s måttkedjor: lägen som i R-03/ritningar.py (lager_yttermatt); hålets kedjor ur geometri.json
XMAX, YMAX = K[:, 0].max(), K[:, 1].max()
kedjor = {
    "under": ([0, 4500, 9310, XMAX], [0, xs[2], xs[3], xs[-1]]),
    "över": ([0, 4310, 9500, XMAX], [0, xs[1], xs[4], xs[-1]]),
    "vänster": ([0, 3590, YMAX], [0, ys[2], ys[-1]]),
    "höger": ([0, 1000, 11010, 12510, YMAX], [0, ys[1], ys[3], ys[4], ys[-1]]),
    "hål vågrätt": ([0, H[:, 0].min(), H[:, 0].max(), XMAX], [0, hx[0], hx[-1], xs[-1]]),
    "hål lodrätt": ([1000, H[:, 1].min(), H[:, 1].max(), 12510], [ys[1], hy[0], hy[-1], ys[4]]),
}
print(f"\n  {'R-03.1 måttkedja':<22} {'ritningens mått':<40} {'modellens mått':<40}")
for k, (r_, mo) in kedjor.items():
    rad(k, [round(v, 1) for v in np.diff(r_)], [round(v, 1) for v in np.diff(mo)])

print("\nResultat:", "allt stämmer med modellen" if not avvikelser else f"{len(avvikelser)} avvikelser: {', '.join(avvikelser)}")

# figur: modellens snitt mot ritningens kontur, trapphål och rör
fig, ax = plt.subplots(figsize=(11, 12))
for n, s in sd.items():
    if not s.yta.is_empty:
        ax.add_patch(_patch(s.yta, facecolor=s.del_.farg, edgecolor="black", lw=0.6, zorder=2))
ax.add_patch(plt.Polygon(K, closed=True, fill=False, ec="red", lw=1.4, ls=(0, (5, 3)), zorder=4,
                         label="geometri.json (K-05, R-03): kontur och trapphål"))
ax.add_patch(plt.Polygon(H, closed=True, fill=False, ec="red", lw=1.4, ls=(0, (5, 3)), zorder=4))
P = np.array(G["pelare"])
ax.plot(mitt[:, 0], mitt[:, 1], "s", ms=6, mfc="none", mec="black", label="modellens rör", zorder=5)
ax.plot(P[:, 0], P[:, 1], "+", ms=9, color="red", label="geometri.json: rör", zorder=6)
ax.set_xlim(-1200, 15000); ax.set_ylim(-1200, 16800); ax.set_aspect("equal"); ax.grid(lw=0.3)
ax.set_title(f"Mellanbjälklag: modellens snitt (fyllt) mot ritningsunderlaget (rött)\n"
             f"K-05-koordinater, origo = ({O[0]:.3f}; {O[1]:.3f}) globalt – "
             + ("allt stämmer" if not avvikelser else f"{len(avvikelser)} avvikelser"), fontsize=10)
ax.legend(loc="upper right", fontsize=8)
fig.tight_layout()
(HERE / "ut").mkdir(exist_ok=True)
fig.savefig(HERE / "ut" / "R-03.1_kontroll.png", dpi=150)
print("ut/R-03.1_kontroll.png")
