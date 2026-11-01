"""Takets skikt ovanpå takbalkarna (F-01, U-03): profiler i husets (x, z) som extruderas längs y.

Skikten ligger parallellt med takplanet, med avståndet w vinkelrätt från takbalkarnas överkant. Takytan delas i
regioner (y-intervall) med samma kanter: nocken (lodrätt plan genom nocklinjen), dalen (lodrätt plan genom
dallinjen) eller takfoten (lodrätt vid takbalkarnas ände). Takfönstren skär ut skikten vinkelrätt mot takplanet.
"""
from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import Polygon, box

from .. import skelett as S
from .takbalk import _halvplan_vinkelratt, langs  # noqa: F401  (langs används av taket och isoleringen)

HARDBOARD = (0.0, 3.0)
STROLAKT = (3.0, 37.0)               # 34×45 på hårdboarden
RASPONT = (37.0, 57.0)
PAPP = (57.0, 59.0)
PLAT = (59.0, 59.6)
FALS = (59.6, 84.6)                  # stående fals 25 mm på plåten
STOPP_T = 22.0                       # isolerstoppet vid takfoten: bräda på hammarbandet i varje fack
RASPONT_UT = 20.0                    # råspont, papp och plåt utanför takbalkarnas ände vid takfoten


@dataclass(frozen=True)
class Kant:
    typ: str                         # "lodratt" (lodrätt plan vid x) eller "vinkelrat" (vinkelrätt mot takplanet)
    x: float                         # lodratt: planets x; vinkelrat: x i takbalkarnas plan där snittet går


def profil(t: S.Takfall, w0: float, w1: float, a: Kant, b: Kant) -> list[tuple[float, float]] | None:
    """Skiktets profil (x, z) mellan kanterna a och b, w0–w1 vinkelrätt över takbalkarnas överkant."""
    xa, xb = sorted((a.x, b.x))
    x0, x1 = xa - 600.0, xb + 600.0
    d0, d1 = w0 / S.COS, w1 / S.COS
    q = Polygon([(x0, t.z_overkant(x0) + d0), (x1, t.z_overkant(x1) + d0), (x1, t.z_overkant(x1) + d1),
                 (x0, t.z_overkant(x0) + d1)])
    for k, annan in ((a, b), (b, a)):
        storre = annan.x > k.x
        if k.typ == "lodratt":
            q = q.intersection(box(k.x, -1e5, 1e5, 1e5) if storre else box(-1e5, -1e5, k.x, 1e5))
        else:
            q = q.intersection(_halvplan_vinkelratt(t, k.x, storre))
    if q.is_empty or q.area < 1.0:
        return None
    if q.geom_type != "Polygon":
        q = max(q.geoms, key=lambda g: g.area)
    return [(float(x), float(z)) for x, z in list(q.exterior.coords)[:-1]]

