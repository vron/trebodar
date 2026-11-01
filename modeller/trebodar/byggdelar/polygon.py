"""Plana former (shapely) som recept: prismor med hål, och polygonerna i en shapely-geometri."""
from __future__ import annotations

from typing import Any, Iterator

from shapely.geometry import Polygon

from modellering import Form, Placering, Prisma, prisma

_YZX = Placering(((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)), (0.0, 0.0, 0.0))   # (y, z, x) → (x, y, z)


def polygoner(g: Any, minsta_area: float = 1.0) -> Iterator[Polygon]:
    """Polygonerna i en shapely-geometri (Polygon, MultiPolygon, GeometryCollection), utan de minsta."""
    for q in getattr(g, "geoms", [g]):
        if q.geom_type == "Polygon" and q.area >= minsta_area:
            yield q
        elif hasattr(q, "geoms"):
            yield from polygoner(q, minsta_area)


def kontur(q: Polygon) -> list[tuple[float, float]]:
    return [(float(x), float(y)) for x, y in list(q.exterior.coords)[:-1]]


def hal(q: Polygon) -> list[list[tuple[float, float]]]:
    return [[(float(x), float(y)) for x, y in list(r.coords)[:-1]] for r in q.interiors]


def prisma_ur(q: Polygon, z0: float, z1: float) -> Prisma:
    """Polygonen (med hål) i xy, extruderad från z0 till z1."""
    return prisma(kontur(q), z1 - z0, hal(q), z0)


def prisma_x(kontur_yz: list[tuple[float, float]], x0: float, x1: float) -> Form:
    """Profilen i (y, z), extruderad längs x från x0 till x1."""
    return prisma(kontur_yz, x1 - x0, z0=x0).placerad(_YZX)
