"""Markens kroppar ur data (#92): berget och uppfyllnaden med de färdiga höjderna efter markarbetena, och
sovrumsavsatsen av granit, som de var ritade i Onshape-modellen som huset först byggdes efter (den togs bort ur repot
i #92 och finns kvar i git-historiken).

Data i marken.json, koordinater i mm (K-05):
- berget och uppfyllnaden: ovansidans ytor (`ytor`: månghörningar med höjden i varje hörn, [x, y, z]) och undersidans
  höjd (`botten`). Sidorna går lodrätt ned från ovansidans ytterkant till undersidan, och där två ytor möts på olika
  höjd blir det ett lodrätt steg. Uppfyllnadens böjda slänter i väster är uppdelade i trianglar (högst 5 mm från
  Onshape-modellens ytor). `undantag`: hörn vars sida lutar, med var sidan möter undersidan ([x, y, x', y']).
- sovrumsavsatsen: i avsatsens lutande plan (vriden `vinkel` kring x, ovansidan lutar 1:33 längs y), där den är
  prismor: blocket (`block`: kontur, botten och topp, 1 000 mm), urtaget för det rundade steget i blockets framkant
  (`urtag`: kontur och stegets höjd) och det nedre steget framför (`steg`, 500 mm).

Ändra en höjd: ändra z i hörnet i alla ytor som har det (hörnen delas exakt mellan ytorna). Kontrollera med
./mod kontroll och ./mod avtryck jamfor.
"""
from __future__ import annotations

import json
import math
from collections.abc import Sequence
from functools import cache
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import Polygon

from modellering import Form, Placering, polyeder

from trebodar.byggdelar.polygon import prisma_ur

DATA = Path(__file__).with_name("marken.json")
Vek = tuple[float, float, float]


def _plan(p: Sequence[float]) -> tuple[float, float]:
    return (round(p[0], 1), round(p[1], 1))


def _hela_kanter(ytor: list[list[Vek]]) -> list[list[Vek]]:
    """Ytorna med de andra ytornas hörn som ligger på deras kanter (i plan) insatta i kanterna, med höjden längs kanten,
    så att grannytor delar kanter exakt (inga T-korsningar)."""
    unika: dict[tuple[float, float], tuple[float, float]] = {}
    for yta in ytor:
        for p in yta:
            unika.setdefault(_plan(p), (p[0], p[1]))
    alla = np.array(list(unika.values()))
    ut = []
    for yta in ytor:
        ny: list[Vek] = []
        for a, b in zip(yta, yta[1:] + yta[:1]):
            ny.append(a)
            d = np.array(b[:2]) - np.array(a[:2])
            lg2 = float(d @ d)
            if lg2 < 1.0:
                continue
            t = ((alla - np.array(a[:2])) @ d) / lg2
            avst = np.abs((alla[:, 0] - a[0]) * d[1] - (alla[:, 1] - a[1]) * d[0]) / math.sqrt(lg2)
            lg = math.sqrt(lg2)
            pa = (t * lg > 0.1) & ((1 - t) * lg > 0.1) & (avst < 0.05)
            for k in np.argsort(t[pa]):
                tk = float(t[pa][k])
                x, y = alla[pa][k]
                ny.append((float(x), float(y), a[2] + tk * (b[2] - a[2])))
        ut.append(ny)
    return ut


def kropp(ytor: Sequence[Sequence[Sequence[float]]], botten: float,
          undantag: Sequence[Sequence[float]] = ()) -> Form:
    """Kroppen mellan ovansidans ytor och undersidan z = botten, med lodräta sidor längs ovansidans ytterkant (utom
    undantagens hörn, som möter undersidan i x', y') och lodräta steg där ytorna möts på olika höjd."""
    horn: list[Vek] = []
    index: dict[Vek, int] = {}

    def h(p: Sequence[float]) -> int:
        k = (round(float(p[0]), 2), round(float(p[1]), 2), round(float(p[2]), 2))
        if k not in index:
            index[k] = len(horn)
            horn.append(k)
        return index[k]

    flytt = {_plan(u[:2]): (float(u[2]), float(u[3])) for u in undantag}

    def ned(p: Vek) -> Vek:
        x, y = flytt.get(_plan(p), (p[0], p[1]))
        return (x, y, botten)

    ovan: list[list[Vek]] = []
    for pts in _hela_kanter([[(float(p[0]), float(p[1]), float(p[2])) for p in yta] for yta in ytor]):
        if Polygon([p[:2] for p in pts]).exterior.is_ccw is False:
            pts.reverse()
        if len(pts) > 3 and max(p[2] for p in pts) - min(p[2] for p in pts) > 0.01:
            # en lutande yta med fler än tre hörn i trianglar (plana även med avrundade höjder)
            z = {_plan(p): p[2] for p in pts}
            for t in shapely.constrained_delaunay_triangles(Polygon([p[:2] for p in pts])).geoms:
                tri = [(x, y, z[_plan((x, y))]) for x, y in list(t.exterior.coords)[:3]]
                ovan.append(tri if Polygon([q[:2] for q in tri]).exterior.is_ccw else tri[::-1])
        else:
            ovan.append(pts)
    kanter: dict[tuple[tuple[float, float], tuple[float, float]], list[tuple[Vek, Vek]]] = {}
    for pts in ovan:
        for a, b in zip(pts, pts[1:] + pts[:1]):
            kanter.setdefault((_plan(a), _plan(b)), []).append((a, b))
    ut = [[h(p) for p in pts] for pts in ovan]
    kant: list[tuple[Vek, Vek]] = []
    for (ka, kb), par in kanter.items():
        for a, b in par:
            mot = kanter.get((kb, ka), [])
            if not mot:                                        # ytterkanten: sidan ned till undersidan
                kant.append((a, b))
                ut.append([h(a), h(b), h(ned(b)), h(ned(a))])
            elif (ka, kb) < (kb, ka):                          # inre kant: steg om höjderna skiljer
                b2, a2 = mot[0]
                hor = [h(a), h(b), h(b2), h(a2)]
                unika = list(dict.fromkeys(hor))
                if len(unika) >= 3:
                    ut.append(unika)
    # undersidan: ytterkantens punkter nedflyttade, i kantens ordning
    nasta = {_plan(a): b for a, b in kant}
    start = kant[0][0]
    ring, p = [start], nasta[_plan(start)]
    while _plan(p) != _plan(start):
        ring.append(p)
        p = nasta[_plan(p)]
    if len(ring) != len(kant):
        raise ValueError(f"ovansidans ytterkant är inte en enda slinga ({len(ring)} av {len(kant)} kanter)")
    ut.append([h(ned(q)) for q in ring])
    # lodräta kanter som andra ytor delar på höjden (steg mot sidor): alla hörn i samma läge in i kanten
    hojder: dict[tuple[float, float], list[int]] = {}
    for i, p in enumerate(horn):
        hojder.setdefault(_plan(p), []).append(i)
    hela = []
    for yta in ut:
        ny: list[int] = []
        for i, j in zip(yta, yta[1:] + yta[:1]):
            ny.append(i)
            a, b = horn[i], horn[j]
            if _plan(a) == _plan(b):
                mellan = [k for k in hojder[_plan(a)] if min(a[2], b[2]) + 0.01 < horn[k][2] < max(a[2], b[2]) - 0.01]
                ny += sorted(mellan, key=lambda k: horn[k][2], reverse=b[2] < a[2])
        hela.append(ny)
    return polyeder(horn, hela)


@cache
def _data() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def berg() -> Form:
    d = _data()["berg"]
    return kropp(d["ytor"], d["botten"], d.get("undantag", ()))


def uppfyllnad() -> Form:
    d = _data()["uppfyllnad"]
    return kropp(d["ytor"], d["botten"], d.get("undantag", ()))


def sovrumsavsats() -> Form:
    """Avsatsens block med urtaget för det rundade steget i framkanten och det nedre steget framför, som prismor i
    avsatsens plan, vridna tillbaka kring x."""
    d = _data()["sovrumsavsats"]
    b, u, s_ = d["block"], d["urtag"], d["steg"]
    blocket = Polygon(b["kontur"])
    urtag = Polygon(u["kontur"])
    urtag = urtag.union(urtag.buffer(50.0, join_style=2).difference(blocket))      # ut genom framkanten
    f = prisma_ur(blocket, b["botten"], b["topp"]) - prisma_ur(urtag, u["botten"], b["topp"] + 10.0)
    steget = Polygon(s_["kontur"])
    steget = steget.union(steget.buffer(20.0, join_style=2).intersection(blocket))   # in i blocket: en kropp
    f = f | prisma_ur(steget, s_["botten"], s_["topp"])
    a = float(d["vinkel"])
    return f.placerad(Placering.axlar((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, -math.sin(a), math.cos(a))))
