"""Takbalkar 45×170 C24 (K-03) i ett takfall: profiler i husets (x, z) som extruderas 45 mm i y.

Regler:
- överkanten i takplanet (skelett.Takfall); underkanten 170 mm vinkelrätt under;
- vid takfoten slutar takbalken lodrätt 70 mm utanför fasaden, och underkanten kapas vågrätt i hammarbandets
  överkant (z 2 490) där den annars skulle gå under;
- vid en nock- eller dalbalk slutar takbalken lodrätt mot balkens sida och vilar med ett hak på upplagsregeln
  45×45: regeln sitter mot balkens sida med överkanten där takbalkens underkant skär regelns yttre sida, dock lägst
  45 mm över underplåten (K-03 figur 2);
- avväxlingar 45×170 vid takfönstren ligger vinkelrätt mot takplanet med överkanten i planet; kortlingar i öppningens
  mitt går från avväxlingarna till balken respektive takfoten och kapas vinkelrätt mot takplanet vid avväxlingen.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from shapely.geometry import Polygon, box

from .. import skelett as S

UPPLAG_B = 45.0              # upplagsregelns bredd (vågrätt) och höjd
PLAT = 10.0                  # balkens underplåt


@dataclass(frozen=True)
class Ande:
    """Takbalkens ände: vid takfoten (x = takfotens läge) eller mot en balk."""
    typ: str                 # "takfot", "balk" eller "vinkelrat" (kapad vinkelrätt mot takplanet vid x)
    x: float                 # takfot: ändens x; balk: balkens sida; vinkelrat: x i takplanet där snittet går
    balk: str | None = None


def regel_ok(t: S.Takfall, balk: str, sida_x: float, utat: int) -> float:
    """Upplagsregelns överkant vid balkens sida sida_x; utat = +1 om takbalken går mot växande x från balken."""
    b = S.BALKAR[balk]
    return max(b.uk + PLAT + UPPLAG_B, t.z_underkant(sida_x + utat * UPPLAG_B))


def _halvplan_vinkelratt(t: S.Takfall, x: float, behall_storre_x: bool) -> Polygon:
    """Halvplanet på ena sidan om linjen vinkelrätt mot takplanet genom planets punkt vid x."""
    z = t.z_overkant(x)
    # takplanets riktning uppåt längs planet och normalen
    ex, ez = t.riktning * S.COS, S.SIN
    nx, nz = -t.riktning * S.SIN, S.COS
    L = 1e5
    s = 1.0 if behall_storre_x else -1.0
    # riktning längs planet åt det håll som behålls (i x-led tecknet s)
    dx, dz = (ex, ez) if ex * s > 0 else (-ex, -ez)
    p0 = (x - nx * L, z - nz * L)
    p1 = (x + nx * L, z + nz * L)
    return Polygon([p0, p1, (p1[0] + dx * L, p1[1] + dz * L), (p0[0] + dx * L, p0[1] + dz * L)])


def profil(t: S.Takfall, a: Ande, b: Ande) -> list[tuple[float, float]]:
    """Takbalkens profil (x, z) mellan ändarna a och b (i valfri ordning)."""
    xa, xb = sorted((a.x, b.x))
    pad = 400.0
    x0, x1 = xa - pad, xb + pad
    remsa = Polygon([(x0, t.z_underkant(x0)), (x1, t.z_underkant(x1)), (x1, t.z_overkant(x1)),
                     (x0, t.z_overkant(x0))])
    q = remsa.intersection(box(xa if a.typ != "vinkelrat" and b.typ != "vinkelrat" else x0, -1e5,
                               xb if a.typ != "vinkelrat" and b.typ != "vinkelrat" else x1, 1e5))
    for e, annan in ((a, b), (b, a)):
        utat = 1 if annan.x > e.x else -1                     # riktning från änden in i takbalken
        if e.typ == "takfot":
            q = q.intersection(box(-1e5, S.H_VAGG, 1e5, 1e5))
            q = q.intersection(box(e.x, -1e5, 1e5, 1e5) if utat > 0 else box(-1e5, -1e5, e.x, 1e5))
        elif e.typ == "balk":
            assert e.balk
            q = q.intersection(box(e.x, -1e5, 1e5, 1e5) if utat > 0 else box(-1e5, -1e5, e.x, 1e5))
            zr = regel_ok(t, e.balk, e.x, utat)
            x2 = e.x + utat * UPPLAG_B
            q = q.difference(box(min(e.x, x2), -1e5, max(e.x, x2), zr))
        elif e.typ == "vinkelrat":
            q = q.intersection(_halvplan_vinkelratt(t, e.x, utat > 0))
        else:
            raise ValueError(e.typ)
    if q.geom_type != "Polygon":
        q = max(q.geoms, key=lambda g: g.area)
    return [(float(x), float(z)) for x, z in list(q.exterior.coords)[:-1]]


def avvaxling(t: S.Takfall, x_kant: float, nedanfor: bool) -> list[tuple[float, float]]:
    """Avväxlingens tvärsnitt (x, z): 45 längs takplanet och 170 vinkelrätt, med överkanten i planet, nedanför
    eller ovanför öppningens kant x_kant (kanten i takplanet)."""
    ds = 45.0
    # punkter i takplanet: kanten och 45 mm längs planet bort från öppningen
    steg_x = ds * S.COS
    uppat = t.riktning                                         # x-riktningen uppåt längs planet
    x_annan = x_kant - uppat * steg_x if nedanfor else x_kant + uppat * steg_x
    A = (x_kant, t.z_overkant(x_kant))
    B = (x_annan, t.z_overkant(x_annan))
    nx, nz = -t.riktning * S.SIN, S.COS
    C = (B[0] - nx * S.TAKBALK_H, B[1] - nz * S.TAKBALK_H)
    D = (A[0] - nx * S.TAKBALK_H, A[1] - nz * S.TAKBALK_H)
    return [(float(x), float(z)) for x, z in (A, B, C, D)]


def langs_planet(t: S.Takfall, x: float, ds: float) -> float:
    """x för punkten ds längre upp längs takplanet (negativt ds: nedåt) från punkten vid x."""
    return x + t.riktning * ds * S.COS


def vinkel() -> float:
    return math.radians(S.TAKVINKEL)
