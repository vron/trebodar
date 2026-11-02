"""Ljusplaner: belysningsstyrkan [lux] på en vågrät mätyta (renderad i Blender, blender/scen.matyta) som en
planritning med belysningsstyrkan i färg (fasta steg, så att planerna går att jämföra), isolinjer, armaturerna och
medel-, minsta och största värde och jämnhet (minsta / medel) per rum och delområde. Rummen är de slutna ytorna
mellan väggarna i modellens snitt (STEP-filen), utan en kantzon på 0,5 m längs väggarna (SS-EN 12464-1); en öppen
planlösning delas mellan rummens namn. A3, skala 1:75.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Circle, Rectangle
from matplotlib.patches import Polygon as PolygonPatch
from matplotlib.path import Path as Bana
from shapely import voronoi_polygons
from shapely.geometry import MultiPoint, Point, Polygon
from shapely.ops import unary_union

from .planritning import BLAD, UTOM, plan

SKALA = 75.0
NIVAER = [0, 10, 20, 50, 75, 100, 150, 200, 300, 500, 750, 1000, 2000, 5000]
ISOLINJER = [50, 100, 200, 300, 500]
GLIPA = 30.0                     # rummens slutning: glipor i snittet upp till 2 × GLIPA
KANTZON = 500.0                  # utan kantzonen längs väggarna i rummens statistik [mm]


def _fargskala() -> tuple[ListedColormap, BoundaryNorm]:
    farger = plt.get_cmap("inferno")(np.linspace(0.08, 0.98, len(NIVAER) - 1))
    return ListedColormap(farger), BoundaryNorm(NIVAER, len(NIVAER) - 1)


def rummen(delar: list[dict], rumsnamn: dict[str, tuple]) -> list[tuple[str, Polygon]]:
    """Rummen: de slutna ytorna mellan väggarna (hålen i unionen av snittets ytor, glipor upp till 60 mm slutna),
    med namnen ur RUMSNAMN som ligger i dem. En öppen planlösning (flera namn i samma yta) delas mellan namnen efter
    närmaste namn (Voronoi)."""
    ytor = [Polygon(y[0]).buffer(0) for d in delar if not d["sokvag"].startswith(UTOM) for y in d["ytor"]
            if len(y[0]) >= 3]
    u = unary_union([y.buffer(GLIPA, join_style=2) for y in ytor if y.area > 0])
    ut: list[tuple[str, Polygon]] = []
    for g in getattr(u, "geoms", [u]):
        for h in g.interiors:
            yta = Polygon(h).buffer(GLIPA, join_style=2)
            if yta.area < 0.5e6:
                continue
            namn = [(n, Point(lage[0], lage[1])) for n, lage in rumsnamn.values() if yta.contains(Point(lage[0], lage[1]))]
            if len(namn) == 1:
                ut.append((namn[0][0], yta))
            elif len(namn) > 1:
                celler = voronoi_polygons(MultiPoint([p for _, p in namn]), extend_to=yta.envelope.buffer(1000.0))
                for c in getattr(celler, "geoms", [celler]):
                    for n, p in namn:
                        if c.contains(p):
                            ut.append((n, c.intersection(yta)))
    return ut


def _statistik(lux: np.ndarray, x: np.ndarray, y: np.ndarray, yta: Polygon) -> dict[str, float] | None:
    """Medel, minsta och största värde och jämnhet i rutorna vars mitt ligger inom ytan."""
    bana = Bana(np.asarray(yta.exterior.coords))
    inne = bana.contains_points(np.column_stack([x.ravel(), y.ravel()])).reshape(lux.shape)
    for h in yta.interiors:
        inne &= ~Bana(np.asarray(h.coords)).contains_points(np.column_stack([x.ravel(), y.ravel()])).reshape(lux.shape)
    if inne.sum() < 4:
        return None
    v = lux[inne]
    medel = float(v.mean())
    return {"medel": medel, "minst": float(v.min()), "storst": float(v.max()),
            "jamnhet": float(v.min() / medel) if medel > 0 else 0.0, "rutor": int(inne.sum())}


def rita(lux: np.ndarray, yta: object, delar: list[dict], utdrag: dict, rumsnamn: dict[str, tuple],
         titel: str, undertitel: str, ut: Path) -> list[dict[str, object]]:
    """Ljusplanen för mätytan (lux: rutnätet, rad 0 vid y0) och statistiken per rum och delområde."""
    x0, x1, y0, y1 = yta.omrade                           # type: ignore[attr-defined]
    ny, nx = lux.shape
    cx = x0 + (np.arange(nx) + 0.5) * (x1 - x0) / nx
    cy = y0 + (np.arange(ny) + 0.5) * (y1 - y0) / ny
    X, Y = np.meshgrid(cx, cy)
    cmap, norm = _fargskala()
    fig = plt.figure(figsize=(BLAD[0] / 25.4, BLAD[1] / 25.4))
    omrade = (min(x0, -500.0), max(x1, 14300.0), min(y0, -300.0), max(y1, 16300.0)) if (x1 - x0) > 6000 else \
        (x0 - 1500.0, x1 + 1500.0, y0 - 500.0, y1 + 500.0)
    ax = plan(fig, (8.0, 14.0), omrade, [], "", SKALA)
    ax.imshow(lux, origin="lower", extent=(x0, x1, y0, y1), cmap=cmap, norm=norm, interpolation="nearest", zorder=1)
    cs = ax.contour(X, Y, lux, levels=ISOLINJER, colors="white", linewidths=0.5, alpha=0.8, zorder=2)
    ax.clabel(cs, fmt="%d", fontsize=4.5, colors="white")
    for d in delar:
        if d["sokvag"].startswith(UTOM):
            continue
        for y_ in d["ytor"]:
            xs, ys = zip(*y_[0])
            ax.fill(xs, ys, fc="#d4d4d4", ec="#303030", lw=0.15, zorder=3)
    # armaturerna på planet
    for k, p in utdrag["punkter"].items():
        if p["slag"] != "lampa" or not (x0 <= p["punkt"][0] <= x1 and y0 <= p["punkt"][1] <= y1):
            continue
        rum = utdrag["rum"].get(p.get("rum", ""), {})
        if rum and (rum["plan"] == 1) != (yta.plan == 1):     # type: ignore[attr-defined]
            continue
        ax.add_patch(Circle(tuple(p["punkt"][:2]), 90.0, fc="none", ec="#7dd3fc", lw=0.8, zorder=4))
        ax.text(p["punkt"][0] + 120, p["punkt"][1] + 120, k, fontsize=4.5, color="#7dd3fc", zorder=4)
    # statistik per rum (namnen ur RUMSNAMN) och per delområde
    stat: list[dict[str, object]] = []
    for namn, r in rummen(delar, rumsnamn):
        lage = next(lg for n, lg in rumsnamn.values() if n == namn)
        if not (x0 <= lage[0] <= x1 and y0 <= lage[1] <= y1):
            continue
        delar_r = [g for g in getattr(r, "geoms", [r]) if isinstance(g, Polygon) and g.area > 0.2e6]
        if not delar_r:
            continue
        # statistiken utan en kantzon längs väggarna (SS-EN 12464-1: 0,5 m), i små rum mindre
        storst = max(delar_r, key=lambda g: g.area)
        inre = storst.buffer(-KANTZON)
        if inre.is_empty or inre.area < 0.25 * storst.area:
            inre = storst.buffer(-KANTZON / 4)
        inre = max(getattr(inre, "geoms", [inre]), key=lambda g: g.area)
        s = _statistik(lux, X, Y, inre)
        if s is None:
            continue
        stat.append({"namn": namn, **s})
        ax.add_patch(PolygonPatch(np.asarray(inre.exterior.coords), closed=True, fc="none", ec="white", lw=0.4,
                                  ls=(0, (1, 2)), zorder=5))
        c = inre.representative_point()
        ax.text(c.x, c.y, f"{namn}\nmedel {s['medel']:.0f} lux\nmin {s['minst']:.0f} / max {s['storst']:.0f}",
                fontsize=5.5, ha="center", va="center", color="#111111", zorder=6,
                bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "none", "alpha": 0.8})
    for namn, (a, b, c_, d_) in yta.zoner:                # type: ignore[attr-defined]
        s = _statistik(lux, X, Y, Polygon([(a, c_), (b, c_), (b, d_), (a, d_)]))
        ax.add_patch(Rectangle((a, c_), b - a, d_ - c_, fc="none", ec="#22d3ee", lw=0.9, ls=(0, (3, 2)), zorder=5))
        if s:
            stat.append({"namn": namn, **s})
            ax.text(b + 80, (c_ + d_) / 2, f"{namn}\nmedel {s['medel']:.0f} lux\nmin {s['minst']:.0f}", fontsize=5.5,
                    va="center", color="#111111", zorder=6,
                    bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "none", "alpha": 0.8})
    fig.text(10 / BLAD[0], 287 / BLAD[1], titel, fontsize=15, weight="bold", va="top")
    fig.text(10 / BLAD[0], 278 / BLAD[1], undertitel, fontsize=8.5, va="top", color="#333333")
    fig.text(10 / BLAD[0], 6 / BLAD[1], f"Skala 1:{SKALA:g} (A3). Belysningsstyrkan på en vågrät yta "
             f"{yta.hojd / 1000:.2f} m över golvet, rutor {yta.cell:g} mm, ur renderingen (Cycles, armaturernas "  # type: ignore[attr-defined]
             "uppmätta ljusfördelning, dagsljus och reflexer). `./mod ljusplan`.", fontsize=7.5, color="#555555")
    cax = fig.add_axes((222 / BLAD[0], 150 / BLAD[1], 6 / BLAD[0], 110 / BLAD[1]))
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, ticks=NIVAER[:-1])
    cb.set_label("Belysningsstyrka [lux]", fontsize=8)
    cb.ax.tick_params(labelsize=7)
    fig.text(222 / BLAD[0], 140 / BLAD[1], "Rum och delområden", fontsize=9, weight="bold", va="top")
    for i, rad in enumerate(sorted(stat, key=lambda q: str(q["namn"]))):
        fig.text(222 / BLAD[0], (133 - 4.6 * i) / BLAD[1],
                 f"{rad['namn']}: medel {rad['medel']:.0f} lux, min {rad['minst']:.0f}, max {rad['storst']:.0f}, "
                 f"jämnhet {rad['jamnhet']:.2f}", fontsize=7, va="top")
    ut.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ut, dpi=200)
    plt.close(fig)
    return stat
