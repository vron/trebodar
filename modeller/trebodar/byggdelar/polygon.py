"""Plana former (shapely) som recept: prismor med hål, och polygonerna i en shapely-geometri."""
from __future__ import annotations

import math
from typing import Any, Iterator

from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

from modellering import Form, Placering, Prisma, polyeder, prisma

_YZX = Placering(((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)), (0.0, 0.0, 0.0))   # (y, z, x) → (x, y, z)
_XZY = Placering(((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)), (0.0, 0.0, 0.0))  # (x, z, −y) → (x, y, z)


def polygoner(g: Any, minsta_area: float = 1.0) -> Iterator[Polygon]:
    """Polygonerna i en shapely-geometri (Polygon, MultiPolygon, GeometryCollection), utan de minsta."""
    for q in getattr(g, "geoms", [g]):
        if q.geom_type == "Polygon" and q.area >= minsta_area:
            yield q
        elif hasattr(q, "geoms"):
            yield from polygoner(q, minsta_area)


def kontur(q: Polygon) -> list[tuple[float, float]]:
    return [(float(x), float(y)) for x, y in list(q.exterior.coords)[:-1]]


def hornen(q: Polygon) -> list[tuple[float, float]]:
    """Polygonens hörn moturs från det lägsta (x, y), utan hörn mitt på en rak kant: samma lista för samma form,
    var den än ligger (likadana delar blir samma del)."""
    p = list(orient(q).exterior.coords)[:-1]
    ut = []
    for i, (x, y) in enumerate(p):
        (xa, ya), (xb, yb) = p[i - 1], p[(i + 1) % len(p)]
        if abs((x - xa) * (yb - y) - (y - ya) * (xb - x)) > 1e-6 * max(1.0, abs(xb - xa) + abs(yb - ya)):
            ut.append((float(x), float(y)))
    i0 = min(range(len(ut)), key=lambda i: (round(ut[i][0], 6), round(ut[i][1], 6)))
    return ut[i0:] + ut[:i0]


def hal(q: Polygon) -> list[list[tuple[float, float]]]:
    return [[(float(x), float(y)) for x, y in list(r.coords)[:-1]] for r in q.interiors]


def prisma_ur(q: Polygon, z0: float, z1: float) -> Prisma:
    """Polygonen (med hål) i xy, extruderad från z0 till z1."""
    return prisma(kontur(q), z1 - z0, hal(q), z0)


def prisma_x(kontur_yz: list[tuple[float, float]], x0: float, x1: float) -> Form:
    """Profilen i (y, z), extruderad längs x från x0 till x1."""
    return prisma(kontur_yz, x1 - x0, z0=x0).placerad(_YZX)


def prisma_y(kontur_xz: list[tuple[float, float]], y0: float, y1: float) -> Form:
    """Profilen i (x, z), extruderad längs y från y0 till y1."""
    return prisma(kontur_xz, y1 - y0, z0=-y1).placerad(_XZY)


def stympad(nedre: Polygon, ovre: Polygon, z0: float, z1: float, flytt: float) -> Form:
    """Kroppen mellan polygonen nedre i z0 och ovre i z1 med plana sidor, t.ex. en fasad kant: ovre är nedre med
    hörnen flyttade högst flytt i planet (samma hörn i samma ordning, kanterna parallella). Utan hål."""
    a, b = hornen(nedre), hornen(ovre)
    j0 = min(range(len(b)), key=lambda j: math.dist(a[0], b[j]))
    b = b[j0:] + b[:j0]
    if len(a) != len(b) or any(math.dist(p, q) > flytt + 1e-6 for p, q in zip(a, b)):
        raise ValueError("stympad: polygonernas hörn motsvarar inte varandra")
    n = len(a)
    horn = [(x, y, z0) for x, y in a] + [(x, y, z1) for x, y in b]
    ytor = [list(range(n)), list(range(n, 2 * n))] + [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    return polyeder(horn, ytor)
