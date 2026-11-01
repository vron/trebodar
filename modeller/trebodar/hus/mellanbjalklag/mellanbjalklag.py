"""Mellanbjälklaget (K-05, R-06): betongplatta 150 mm med trapphålet, 30 mm cellplast runt kanten, ursparingar för
rörens topplåtar i underkanten."""
from __future__ import annotations

from shapely.geometry import Polygon

from modellering import Del, Montage, Placering, box, prisma
from modellering.form import Diff

from trebodar import skelett as S
from trebodar.hus.grund import pelare
from trebodar.material import BETONG, CELLPLAST


def montage() -> Montage:
    m = Montage("Mellanbjälklag", beskrivning="Betongplatta 150 mm (K-05), kantisolering 30 mm")
    z0 = -S.H_BJALKLAG
    platta = prisma(S.KONTUR, S.H_BJALKLAG, [S.TRAPPHAL], z0)
    urs = tuple(box(x0, x1, y0, y1, z0 - 1, z0 + pelare.TOPP_T) for x0, x1, y0, y1 in pelare.topplatar())
    m.lagg(Del("Mellanbjälklag betong 150", Diff(platta, urs), BETONG, dokument="K-05"), Placering(), "MB-B")
    yttre = Polygon(S.KONTUR).buffer(S.STOMME_UT, join_style=2)
    kant = yttre.difference(Polygon(S.KONTUR))
    m.lagg(Del("Kantisolering 30", prisma([tuple(p) for p in list(kant.exterior.coords)[:-1]], S.H_BJALKLAG,
                                          [[tuple(p) for p in list(r.coords)[:-1]] for r in kant.interiors], z0),
               CELLPLAST), Placering(), "MB-C")
    return m
