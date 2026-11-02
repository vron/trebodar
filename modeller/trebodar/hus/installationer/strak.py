"""Stråk för installationernas rör i betongen (vatten, golvvärme): gemensamma vägar med en fil per rör, och rörets
väg från sin utgång längs filen till sitt mål.

Ett stråk är en polylinje i plan från fördelaren. Filen genom en punkt (rörets utgång) är stråket förskjutet i sidled
så att dess första sträcka går genom punkten; rören följer sina filer utan att korsa varandra, så länge de viker av åt
det håll där deras fil ligger ytterst. Koordinater i mm (K-05).
"""
from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

from shapely.geometry import LineString, Point
from shapely.ops import substring

from trebodar.hus.armering.armering import jarnen_i_nivan

from .genomforingar import kallarvaggarna
from .montering import Vek


@dataclass(frozen=True)
class Strak:
    """En gemensam väg (punkter i plan, från fördelaren), med en fil per rör."""
    id: str
    punkter: tuple[tuple[float, float], ...]

    def fil(self, p: tuple[float, ...]) -> LineString:
        """Filen genom punkten p: stråket förskjutet i sidled (åt vänster positivt) så att dess första sträcka går
        genom p."""
        linje = LineString(self.punkter)
        d = self.sida(p)
        return linje.offset_curve(d, join_style="mitre") if abs(d) > 1e-6 else linje

    def sida(self, p: tuple[float, ...]) -> float:
        """Punktens avstånd åt vänster från stråkets första sträcka."""
        (x0, y0), (x1, y1) = self.punkter[0], self.punkter[1]
        return ((p[1] - y0) * (x1 - x0) - (p[0] - x0) * (y1 - y0)) / math.hypot(x1 - x0, y1 - y0)


def langs(linje: LineString, p: tuple[float, float], ben: int | None = None) -> float:
    """Punktens läge längs linjen: avståndet till den närmaste punkten på linjen eller på dess ben `ben`."""
    if ben is None:
        return float(linje.project(Point(p)))
    h = list(linje.coords)
    fore = sum(math.dist(h[i], h[i + 1]) for i in range(ben))
    return fore + float(LineString(h[ben:ben + 2]).project(Point(p)))


def vag(ut: Vek, z: float, strak: Strak, genom: tuple[tuple[float, float], ...], slut: tuple[Vek, ...] = (),
        ben: int | None = None) -> tuple[Vek, ...]:
    """Rörets väg från utgången ut: rakt upp eller ned till nivån z, längs filen genom utgången till punkten närmast
    den första punkten i genom (på stråkets ben `ben`, om det anges), därifrån genom punkterna i plan och vidare genom
    slut (t.ex. upp eller ned i en vägg)."""
    fil = strak.fil(ut)
    a = fil.project(Point(ut[0], ut[1]))
    del_ = substring(fil, a, max(a, langs(fil, genom[0], ben)))
    pa_filen = list(del_.coords) if del_.geom_type == "LineString" else [(del_.x, del_.y)]
    punkter: list[Vek] = []
    for x, y in [(ut[0], ut[1]), *pa_filen, *genom]:
        if not punkter or math.hypot(x - punkter[-1][0], y - punkter[-1][1]) > 0.5:
            punkter.append((float(x), float(y), z))
    return (*punkter, *slut)


def filer(rader: list[tuple[str, str, int | None, dict[str, tuple[float, float]]]],
          strak: Callable[[dict[str, float]], dict[str, Strak]], borjan: tuple[float, float],
          riktning: tuple[float, float], fil: float) -> tuple[dict[tuple[str, str], int], dict[str, float]]:
    """Rörens filer längs fördelaren (filen 0 i borjan, c/c fil längs riktning) och stråkens mitt.

    rader: (id, stråk, ben där rören viker av (None: närmast), målet per rör, t.ex. {"KV": (x, y), "VV": (x, y)}) i
    ordning längs riktning. Ett ids rör ligger bredvid varandra, det som viker av först ytterst mot målets sida av
    stråket. stråk(mitt) ger stråken med deras första sträcka genom mitten av sina filer (mitt: läget längs riktning);
    sidan beror på var stråket går och mitten på filerna, så de räknas om tills de stämmer."""
    mitt = {s: borjan[0] * riktning[0] + borjan[1] * riktning[1] for _, s, _, _ in rader}
    ut: dict[tuple[str, str], int] = {}
    for _ in range(4):
        s_av = strak(mitt)
        ut = {}
        for i, s_id, ben, mal in rader:
            s = s_av[s_id]
            linje = LineString(s.punkter)
            forst = min(mal, key=lambda m: langs(linje, mal[m], ben))
            p = mal[forst]
            t = langs(linje, p, ben)
            fot, q = linje.interpolate(t), linje.interpolate(t + 1.0)
            vanster = (q.x - fot.x) * (p[1] - fot.y) - (q.y - fot.y) * (p[0] - fot.x) > 0.0
            vanster_uppat = s.sida((borjan[0] + riktning[0], borjan[1] + riktning[1])) > s.sida(borjan)
            for m in sorted(mal, key=lambda m: (m == forst) == (vanster == vanster_uppat)):
                ut[(i, m)] = len(ut)
        ny = {}
        for s_id in mitt:
            f = [n for (i, _), n in ut.items() if next(r[1] for r in rader if r[0] == i) == s_id]
            ny[s_id] = borjan[0] * riktning[0] + borjan[1] * riktning[1] + (min(f) + max(f)) / 2 * fil
        if ny == mitt:
            break
        mitt = ny
    return ut, mitt


def glipa(vagg: str, z: float, nara: float) -> float:
    """Mitten av glipan mellan källarväggens järn som går genom nivån z (i betongen ovanför eller under väggen) närmast
    läget nara längs väggen (x för en vägg i x-led, y för en i y-led): där ett stråk går över väggen."""
    karna = kallarvaggarna()[vagg][1].buffer(50.0)
    x0, y0, x1, y1 = karna.bounds
    i = 0 if x1 - x0 > y1 - y0 else 1
    t = sorted({g.coords[0][i] for g, _ in jarnen_i_nivan(z - 1.0, z + 1.0)
                if g.geom_type == "Point" and karna.contains(g)})
    return min(((a + b) / 2 for a, b in zip(t, t[1:])), key=lambda m: abs(m - nara))
