"""
Kontroll av R-03.1 (mellanbjälklag, översikt och yttermått) mot Onshape-modellen (exakt B-rep).

    ./.venv/bin/python kontroll_r031.py

Jämför ritningens måttkedjor och K-05:s kontur/trapphål (bild/geometri.json) med modellens snitt mitt i
Mittenplatta, i K-05-koordinater (origo i skärningen mellan plattkanterna x = 0 och y = 0).
Måttkedjorna nedan är avskrivna från R-03.1 rev A – uppdatera dem om ritningen ändras.
Bild: ut/R-03.1_kontroll.png
"""
import json, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from modell import Modell
from geometri import Plan, snitt
from ritning import _patch

ROT = HERE.parent.parent
G = json.load(open(f"{ROT}/beräkningar/K-05/bild/geometri.json", encoding="utf-8"))
m = Modell()
platta = m.valj("Mittenplatta")
betong = [d for d in platta if d.namn == "Mittenplatta"][0]
b = betong.bbox
O = (b[0], b[1])                      # skärningen mellan plattkanterna x = 0 och y = 0
plan = Plan.tolka(f"z={(b[2] + b[5]) / 2}").flytta(*O)
sd = {s.del_.namn: s for s in snitt(m, platta, plan)}
yta = sd["Mittenplatta"].yta
ytter = np.array(yta.exterior.coords)[:-1]
hal = np.array(yta.interiors[0].coords)[:-1]
xs = sorted({round(v, 3) for v in ytter[:, 0]}); ys = sorted({round(v, 3) for v in ytter[:, 1]})
print("origo (globalt):", O, " tjocklek", b[5] - b[2])
print("modellens x-lägen:", xs); print("modellens y-lägen:", ys)
hx = sorted({round(v, 3) for v in hal[:, 0]}); hy = sorted({round(v, 3) for v in hal[:, 1]})
print("hål x:", hx, " y:", hy)

ritn = {  # måttkedjor enligt R-03.1 (text i pdf:en), lägen enligt ritningar.py
    "under":  ([0, 4500, 9310, 13810], [4500, 4810, 4500]),
    "över":   ([0, 4310, 9500, 13810], [4310, 5190, 4310]),
    "vänster": ([0, 3590, 15900], [3590, 12310]),
    "höger":  ([0, 1000, 11010, 12510, 15900], [1000, 10010, 1500, 3390]),
    "total x": ([0, 13810], [13810]), "total y": ([0, 15900], [15900]),
    "hål vågrätt": ([0, 7350, 9420, 13810], [7350, 2070, 4390]),
    "hål lodrätt": ([1000, 5050, 5878, 12510], [4050, 828, 6632]),
}
mod = {
    "under": [0, xs[2], xs[3], xs[-1]], "över": [0, xs[1], xs[4], xs[-1]],
    "vänster": [0, ys[2], ys[-1]], "höger": [0, ys[1], ys[3], ys[4], ys[-1]],
    "total x": [0, xs[-1]], "total y": [0, ys[-1]],
    "hål vågrätt": [0, hx[0], hx[1], xs[-1]], "hål lodrätt": [ys[1], hy[0], hy[1], ys[4]],
}
print(f"\n{'kedja':<13} {'ritning':<28} {'modell':<34} avvikelse")
for k, (lagen, matt) in ritn.items():
    mm_ = np.diff(mod[k])
    print(f"{k:<13} {' '.join(f'{v:>6}' for v in matt):<28} {' '.join(f'{v:>8.1f}' for v in mm_):<34} "
          f"{' '.join(f'{v:+.1f}' for v in mm_ - np.array(matt))}")
# hörn för hörn
K = np.array(G["kontur"], float)
avv = [min(np.linalg.norm(ytter - p, axis=1)) for p in K]
print(f"\nkonturens {len(K)} hörn: största avstånd till modellens hörn {max(avv):.4f} mm; modellen har {len(ytter)} hörn")
H = np.array(G["hal"], float)
print("trapphål ritning:", G["hal"], "\n           modell:", [tuple(np.round(p, 1)) for p in hal])

fig, ax = plt.subplots(figsize=(11, 12))
for n, s in sd.items():
    if not s.yta.is_empty:
        ax.add_patch(_patch(s.yta, facecolor=s.del_.farg, edgecolor="black", lw=0.6, zorder=2))
ax.add_patch(plt.Polygon(K, closed=True, fill=False, ec="red", lw=1.4, ls=(0, (5, 3)), zorder=4, label="R-03.1 kontur och trapphål (K-05 geometri.json)"))
ax.add_patch(plt.Polygon(H, closed=True, fill=False, ec="red", lw=1.4, ls=(0, (5, 3)), zorder=4))
for x in (0, 4500, 9310, 13810): ax.annotate(f"{x}", (x, -500), ha="center", fontsize=7, color="red")
ax.set_xlim(-1200, 15000); ax.set_ylim(-1200, 16800); ax.set_aspect("equal"); ax.grid(lw=0.3)
ax.set_title("Mellanbjälklag: modellens snitt z = mitt i plattan (fyllt) mot R-03.1 (rött streckat)\nK-05-koordinater, origo = (−12 147,711; −1 292,101) globalt", fontsize=10)
ax.legend(loc="upper right", fontsize=8)
# inzoomning hålet
ins = ax.inset_axes([0.36, 0.73, 0.30, 0.17])
ins.add_patch(_patch(sd["Mittenplatta"].yta, facecolor=betong.farg, edgecolor="black", lw=0.8))
ins.add_patch(plt.Polygon(H, closed=True, fill=False, ec="red", lw=1.4, ls=(0, (5, 3))))
ins.set_xlim(7250, 9520); ins.set_ylim(4980, 5960); ins.set_aspect("equal"); ins.grid(lw=0.3); ins.tick_params(labelsize=6)
ins.set_title("trapphålet: modell (svart) 2,0 mm åt −x och 9,5 mm åt +y mot ritningen", fontsize=7)
fig.tight_layout(); (HERE / "ut").mkdir(exist_ok=True)
fig.savefig(HERE / "ut" / "R-03.1_kontroll.png", dpi=150)
print("\nut/R-03.1_kontroll.png")
