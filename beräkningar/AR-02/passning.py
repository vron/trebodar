"""
AR-02: passning av K-05:s koordinater till SWEREF 99 12 00 ur bygglovets situationsplan.

Situationsplanen (lokalt/bygglov/BeslutSituationsplan_1495503.pdf, versionshanteras inte) har ett koordinatrutnät
med kors var 25:e meter (N 6 520 125–6 520 200, E 102 325–102 400) och huset som en blå, skrafferad yta (ca 135 m²,
utan tillbyggnaden). Ur PDF:ens vektorer: korsen ger skalan och läget, skrafferingens linjer slutar i husets kontur.
Fasadens kontur i K-05:s koordinater (plattans kant + regel + beklädnad, utan plattan på mark) passas in med rotation
och förflyttning så att ytornas symmetriska skillnad blir minst, först med beklädnaden fri (som kontroll) och sedan
med beklädnaden enligt indata.toml.

Husets läge på AR-02 kommer i stället från utsättningsdatan (indata.toml, [koordinater] hornen); passningen här är
en kontroll av att den stämmer med situationsplanen.

    python passning.py        -> skriver passningen och hörnens avstånd till konturen
"""
import json
import math
import os
import tomllib

import numpy as np
import pymupdf
from scipy.optimize import minimize
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import polygonize, unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
ROT = os.path.dirname(os.path.dirname(HERE))
PDF = os.path.join(ROT, "lokalt", "bygglov", "BeslutSituationsplan_1495503.pdf")
IN = tomllib.loads(open(os.path.join(HERE, "indata.toml"), encoding="utf-8").read())
G = json.load(open(os.path.join(os.path.dirname(HERE), "K-05", "bild", "geometri.json"), encoding="utf-8"))
BLA = (0.22, 0.45)                         # husets färg i situationsplanen (r, g)


def rutnat(p):
    """Korsen (vågräta och lodräta linjer 6–40 pt som skär varandra mitt på): skala och nollpunkt. Sidan är
    roterad 90°: x mot söder (N minskar), y mot väster (E minskar)."""
    H, V = [], []
    for d in p.get_drawings():
        for it in d["items"]:
            if it[0] != "l":
                continue
            a, b = it[1], it[2]
            if 6 < abs(a - b) < 40:
                if abs(a.y - b.y) < 0.01:
                    H.append((min(a.x, b.x), max(a.x, b.x), a.y))
                elif abs(a.x - b.x) < 0.01:
                    V.append((min(a.y, b.y), max(a.y, b.y), a.x))
    kors = [(x, y) for x0, x1, y in H for y0, y1, x in V
            if x0 < x < x1 and y0 < y < y1 and abs((x0 + x1) / 2 - x) < 0.5 and abs((y0 + y1) / 2 - y) < 0.5]
    def medel(v):                                                 # korsens lägen, grupperade, medelvärde
        g = []
        for t in sorted(v):
            if g and t - g[-1][-1] < 1.0:
                g[-1].append(t)
            else:
                g.append([t])
        return [sum(x) / len(x) for x in g]
    xs, ys = medel([k[0] for k in kors]), medel([k[1] for k in kors])
    s = 75.0 / (xs[-1] - xs[0])                                   # 75 m mellan yttersta korsen
    assert abs(75.0 / (ys[-1] - ys[0]) - s) < 1e-4 * s
    return s, xs[0], ys[-1]                                       # (N 6 520 200, E 102 325) i (xs[0], ys[-1])


def husyta(p, s, x0, y0):
    seg = []
    for d in p.get_drawings():
        c = d.get("color")
        if c and abs(c[0] - BLA[0]) < 0.03 and abs(c[1] - BLA[1]) < 0.03 and abs((d.get("width") or 0) - 0.51) < 0.01:
            seg += [LineString([(it[1].x, it[1].y), (it[2].x, it[2].y)]) for it in d["items"] if it[0] == "l"]
    hatch = [l for l in seg if abs(l.coords[0][1] - l.coords[1][1]) < 0.01 and l.length > 2]
    ytor = [f for f in polygonize(unary_union([l for l in seg if l.length > 0.3]))
            if any(f.buffer(0.05).contains(l.interpolate(0.5, normalized=True)) for l in hatch)]
    u = unary_union(ytor).buffer(0.01).buffer(-0.01).simplify(0.05)
    return Polygon([(102325 + s * (y0 - y), 6520200 - s * (x - x0)) for x, y in u.exterior.coords])   # (E, N)


def modell(t):
    k, mark = Polygon(G["kontur"]), Polygon(G["mark"])
    return k.difference(mark.buffer(1, join_style=2)).buffer(IN["fasad"]["regel"] + t, join_style=2)


def trans(P, th, E0, N0):
    Q = affinity.rotate(affinity.scale(P, 1e-3, 1e-3, origin=(0, 0)), th, origin=(0, 0))
    return affinity.translate(Q, E0, N0)


def main():
    p = pymupdf.open(PDF)[0]
    s, x0, y0 = rutnat(p)
    hus = husyta(p, s, x0, y0)
    cb = np.array(hus.centroid.coords[0])
    # först med beklädnaden fri (som kontroll), sedan med beklädnaden enligt indata (det som används)
    f = lambda v: trans(modell(v[3]), *v[:3]).symmetric_difference(hus).area
    best = None
    for th0 in range(0, 360, 15):
        c = np.array(trans(modell(60), th0, 0, 0).centroid.coords[0])
        r = minimize(f, [th0, *(cb - c), 60], method="Nelder-Mead", options=dict(xatol=1e-4, fatol=1e-6, maxiter=4000))
        best = r if best is None or r.fun < best.fun else best
    best = minimize(f, best.x, method="Nelder-Mead", options=dict(xatol=1e-6, fatol=1e-8, maxiter=8000))
    print(f"skala {s:.6f} m/pt, husets yta {hus.area:.2f} m²")
    print(f"beklädnaden fri: theta {best.x[0]:.4f}, beklädnad {best.x[3]:.1f} mm, avvikelse {best.fun:.3f} m²")
    t = IN["fasad"]["beklad"]
    g = lambda v: trans(modell(t), *v).symmetric_difference(hus).area
    best = minimize(g, best.x[:3], method="Nelder-Mead", options=dict(xatol=1e-6, fatol=1e-8, maxiter=8000))
    th, E0, N0 = best.x
    Q = trans(modell(t), th, E0, N0)
    print(f"beklädnad {t} mm: theta = {th:.4f}, E0 = {E0:.3f}, N0 = {N0:.3f}, avvikelse {best.fun:.3f} m²")
    for e, n in list(hus.exterior.coords)[:-1]:
        print(f"  hörn N {n:.3f} E {e:.3f}: {Q.exterior.distance(Point(e, n)) * 1000:4.0f} mm från konturen")


if __name__ == "__main__":
    main()
