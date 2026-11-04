"""Innertakets läkt (installationsskiktet, c/c 400 längs takfallet) och gips ur innertakets geometri: armaturernas hål
och drivdon ska ligga mellan läkten (med armaturens avstånd till brännbart material) och hålen i gipsen, inte i
takfönstrens öppningar eller utanför innertakets kanter.
"""
from __future__ import annotations

import math
from functools import cache

from trebodar import skelett as S
from trebodar.hus.invandigt import innertak

Ruta = tuple[float, float, float, float]       # (x0, x1, y0, y1) i planet


@cache
def lakt(kod: str) -> tuple[Ruta, ...]:
    """Läkten under takfallet som lådor i planet, de som går längs y (inte gavlarnas läkt längs takfallet), ur
    innertakets profiler (innertak.skikten: profilen i (x, z), längs y från y0 till y1)."""
    ut = []
    for q, y0, y1, _ in innertak.skikten(kod)["lakt"]:
        x0, x1 = min(x for x, _ in q), max(x for x, _ in q)
        if y1 - y0 > x1 - x0:
            ut.append((x0, x1, y0, y1))
    return tuple(ut)


@cache
def gips(kod: str) -> tuple[Ruta, ...]:
    """Den yttre gipsskivan (takytan) under takfallet som lådor i planet, ur innertakets profiler."""
    return tuple((min(x for x, _ in q), max(x for x, _ in q), y0, y1)
                 for q, y0, y1, typ in innertak.skikten(kod)["gips"] if typ == "GY")


def i_gipsen(kod: str, x: float, y: float, r: float) -> bool:
    """Om ett hål med radien r (mitt x, y på takytan) ligger helt i innertakets gips under takfallet: mitten och
    punkterna r åt sidorna längs takfallet och längs y."""
    return all(any(g[0] <= px <= g[1] and g[2] <= py <= g[3] for g in gips(kod))
               for px, py in ((x, y), (x - i_planet(r), y), (x + i_planet(r), y), (x, y - r), (x, y + r)))


def mellan_lakten(kod: str, x: float, y: float) -> float:
    """x mitt emellan de två läkt som omger punkten (x, y) under takfallet (närmast x om punkten ligger på en läkt)."""
    kanter = sorted(r[:2] for r in lakt(kod) if r[2] <= y <= r[3])
    mellan = [(a[1] + b[0]) / 2 for a, b in zip(kanter, kanter[1:])]
    return min(mellan, key=lambda m: abs(m - x)) if mellan else x


def krockar(kod: str, x: float, y: float, halvbredd_x: float, halvbredd_y: float) -> list[Ruta]:
    """Läkt som en rektangel i planet (mitt x, y; halva bredden längs x och y) skär."""
    return [r for r in lakt(kod) if r[0] < x + halvbredd_x and x - halvbredd_x < r[1] and
            r[2] < y + halvbredd_y and y - halvbredd_y < r[3]]


def i_planet(r: float) -> float:
    """En längd r längs takfallet i planet (x)."""
    return r * math.cos(math.radians(S.TAKVINKEL))
