"""Stråk för installationernas rör i betongen (vatten, golvvärme): gemensamma vägar med en fil per rör, och rörets
väg från sin utgång längs filen till sitt mål.

Ett stråk är en polylinje i plan från fördelaren. Filen genom en punkt (rörets utgång) är stråket förskjutet i sidled
så att dess första sträcka går genom punkten; rören följer sina filer utan att korsa varandra, så länge de viker av åt
det håll där deras fil ligger ytterst. Koordinater i mm (K-05).
"""
from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import cache

from shapely.geometry import LineString, Point
from shapely.geometry.base import BaseGeometry
from shapely.ops import substring
from shapely.strtree import STRtree

from trebodar.hus.armering.armering import jarnen_i_nivan

from .genomforingar import kallarvaggarna
from .montering import Vek


@dataclass(frozen=True)
class Strak:
    """En gemensam väg (punkter i plan, från fördelaren), med en fil per rör. skala: filernas avstånd per sträcka
    (benen i ordning) i förhållande till den första, för ett stråk som smalnar av där rören kan ligga tätare (#114)."""
    id: str
    punkter: tuple[tuple[float, float], ...]
    skala: tuple[float, ...] = ()

    def fil(self, p: tuple[float, ...]) -> LineString:
        """Filen genom punkten p: stråket förskjutet i sidled (åt vänster positivt) så att dess första sträcka går
        genom p, på varje sträcka med dess skala."""
        linje = LineString(self.punkter)
        d = self.sida(p)
        if abs(d) < 1e-6:
            return linje
        if not self.skala:
            return linje.offset_curve(d, join_style="mitre")
        sk = list(self.skala) + [self.skala[-1]] * (len(self.punkter) - 1 - len(self.skala))
        bitar = []                                       # varje sträcka förskjuten: punkt och riktning
        for (a, b), k in zip(zip(self.punkter, self.punkter[1:]), sk):
            ux, uy = b[0] - a[0], b[1] - a[1]
            n = math.hypot(ux, uy)
            ux, uy = ux / n, uy / n
            off = d * k
            bitar.append(((a[0] - uy * off, a[1] + ux * off), (b[0] - uy * off, b[1] + ux * off), (ux, uy)))
        pts = [bitar[0][0]]
        for (a0, a1, ua), (b0, _, ub) in zip(bitar, bitar[1:]):
            kors = ua[0] * ub[1] - ua[1] * ub[0]
            if abs(kors) < 1e-9:                         # i linje: rakt över
                pts += [a1, b0]
            else:                                        # där de förskjutna sträckorna möts
                t = ((b0[0] - a0[0]) * ub[1] - (b0[1] - a0[1]) * ub[0]) / kors
                pts.append((a0[0] + ua[0] * t, a0[1] + ua[1] * t))
        pts.append(bitar[-1][1])
        return LineString(pts)

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


def rundad(punkter: Sequence[Vek], radie: float, minst: float = 0.0, hinder: BaseGeometry | None = None,
           hoppa: Sequence[tuple[float, float]] = (), nara: float = 150.0, steg: float = math.radians(15.0)
           ) -> tuple[tuple[Vek, ...], list[tuple[float, float]]]:
    """Polylinjen med hörnen i plan (där båda sträckorna ligger i samma nivå) rundade med radien (#87): en båge med
    punkter var steg radianer, tangent mot båda sträckorna; där sträckorna är för korta för radien den största som
    ryms (högst halva den kortare sträckan), men aldrig under minst. Hörnen där bågen skulle gå in i hindren (i plan)
    och hörnen närmare än nara från punkterna i hoppa lämnas räta; de förra returneras med vägen (så att ett rör
    bredvid kan lämna samma hörn rätt). Parallella filer med samma radie korsar inte varandra i hörnen."""
    if len(punkter) < 3:
        return tuple(punkter), []
    pts: list[Vek] = [(float(q[0]), float(q[1]), float(q[2])) for q in punkter]
    ut: list[Vek] = [pts[0]]
    hoppade: list[tuple[float, float]] = []
    kvar = [math.dist(a, b) for a, b in zip(pts, pts[1:])]         # det som är kvar av varje sträcka
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        if abs(a[2] - b[2]) > 0.5 or abs(b[2] - c[2]) > 0.5:
            ut.append(b)
            continue
        u = (b[0] - a[0], b[1] - a[1])
        w = (c[0] - b[0], c[1] - b[1])
        lu, lw = math.hypot(*u), math.hypot(*w)
        if lu < 1e-6 or lw < 1e-6:
            ut.append(b)
            continue
        u, w = (u[0] / lu, u[1] / lu), (w[0] / lw, w[1] / lw)
        vinkel = math.atan2(u[0] * w[1] - u[1] * w[0], u[0] * w[0] + u[1] * w[1])
        if abs(vinkel) < math.radians(1.0):
            ut.append(b)
            continue
        tg = math.tan(abs(vinkel) / 2)
        t_max = min(radie * tg, kvar[i - 1] * (1.0 if i == 1 else 0.5), kvar[i] * (1.0 if i == len(pts) - 2 else 0.5))
        r = t_max / tg
        if r < minst or any(math.dist(b[:2], q) < nara for q in hoppa):
            ut.append(b)
            continue
        p0 = (b[0] - u[0] * t_max, b[1] - u[1] * t_max)
        n = (-u[1], u[0]) if vinkel > 0 else (u[1], -u[0])              # mot bågens mitt
        m = (p0[0] + n[0] * r, p0[1] + n[1] * r)
        a0 = math.atan2(p0[1] - m[1], p0[0] - m[0])
        k = max(2, int(math.ceil(abs(vinkel) / steg)))
        bage = [(m[0] + r * math.cos(a0 + vinkel * j / k), m[1] + r * math.sin(a0 + vinkel * j / k), b[2])
                for j in range(k + 1)]
        if hinder is not None and LineString([q[:2] for q in bage]).intersects(hinder):
            hoppade.append((b[0], b[1]))
            ut.append(b)
            continue
        kvar[i] -= t_max
        ut.extend(bage)
    ut.append(pts[-1])
    return tuple(ut), hoppade


def filer(rader: list[tuple[str, str, int | None, dict[str, tuple[float, float]]]],
          strak: Callable[[dict[str, float]], dict[str, Strak]], borjan: tuple[float, float],
          riktning: tuple[float, float], fil: float) -> tuple[dict[tuple[str, str], int], dict[str, float]]:
    """Rörens filer längs fördelaren (filen 0 i borjan, c/c fil längs riktning) och stråkens mitt.

    rader: (id, stråk, ben där rören viker av (None: närmast), målet per rör, t.ex. {"KV": (x, y), "VV": (x, y)}) i
    ordning längs riktning. Ett ids rör ligger bredvid varandra, det som viker av först ytterst mot målets sida av
    idets filer. stråk(mitt) ger stråken med deras första sträcka genom mitten av sina filer (mitt: läget längs riktning);
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
            n0 = len(ut)                                    # sidan räknas från idets första fil, inte stråkets mitt
            egen = s.fil((borjan[0] + riktning[0] * n0 * fil, borjan[1] + riktning[1] * n0 * fil))
            t = langs(egen, p, ben)
            fot, q = egen.interpolate(t), egen.interpolate(t + 1.0)
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


def fri(g: BaseGeometry, r: float, z0: float, z1: float, spel: float = 5.0) -> bool:
    """Ett rör (radien r) lodrätt i punkten g eller vågrätt längs linjen g går fritt (spel) från järnen som går genom
    höjderna z0–z1."""
    trad, jarn = _jarnen(min(z0, z1), max(z0, z1))
    return all(g.distance(jarn[int(i)][0]) >= r + jarn[int(i)][1] / 2 + spel
               for i in trad.query(g.buffer(r + spel + 10.0)))


@cache
def _jarnen(z0: float, z1: float) -> tuple[STRtree, tuple[tuple[Point | LineString, float], ...]]:
    j = jarnen_i_nivan(z0, z1)
    return STRtree([g for g, _ in j]), j


def mellan_jarnen(punkter: Sequence[tuple[float, float]], z0: float, z1: float, r: float,
                  langs: tuple[float, float] | None = None, tvars: float = 0.0, undvik: BaseGeometry | None = None,
                  spel: float = 5.0, langst: float = 150.0, steg: float = 5.0) -> tuple[float, float]:
    """Den kortaste förskjutningen (dx, dy) av lodräta rör (radien r, punkterna i plan, från z0 till z1) som gör att
    alla går fria (spel) från järnen som går genom höjderna, t.ex. armeringsnäten där rören går upp ur betongen: längs
    riktningen langs (t.ex. längs en vägg, och högst tvars tvärs den) eller åt alla håll, med punkternas mitt utanför
    undvik (t.ex. väggarna runt en golvdosa); (0, 0) om de redan går fria."""
    trad, jarn = _jarnen(min(z0, z1), max(z0, z1))
    mx, my = sum(x for x, _ in punkter) / len(punkter), sum(y for _, y in punkter) / len(punkter)

    def fri(dx: float, dy: float) -> bool:
        if undvik is not None and undvik.contains(Point(mx + dx, my + dy)):
            return False
        for x, y in punkter:
            q = Point(x + dx, y + dy)
            for i in trad.query(q.buffer(r + spel + 10.0)):
                g, d = jarn[int(i)]
                if q.distance(g) < r + d / 2 + spel:
                    return False
        return True

    n = int(langst / steg)
    if langs is None:
        steg_ = [(i * steg, j * steg) for i in range(-n, n + 1) for j in range(-n, n + 1)]
    else:
        m = int(tvars / steg)
        steg_ = [(langs[0] * i * steg - langs[1] * j * steg, langs[1] * i * steg + langs[0] * j * steg)
                 for i in range(-n, n + 1) for j in range(-m, m + 1)]
    for dx, dy in sorted(steg_, key=lambda d: math.hypot(*d)):
        if fri(dx, dy):
            return dx, dy
    raise ValueError(f"inget läge mellan järnen inom {langst:g} mm från {punkter[0]}")
