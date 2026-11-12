"""Mellanbjälklaget (K-05, R-06): betongplatta 150 mm med trapphålet, 30 mm cellplast runt kanten, ursparingar för
rörens topplåtar i underkanten. Vid plattan på marks fria kanter är kantisoleringen L-elementens rygg (AR-02, R-06)."""
from __future__ import annotations

from shapely.geometry import Polygon

from modellering import Del, Montage, Placering, box, minus

from trebodar import skelett as S
from trebodar.byggdelar.polygon import prisma_ur
from trebodar.hus.grund import pelare
from trebodar.hus.grund.grund import kantrygg
from trebodar.material import BETONG, CELLPLAST


def montage() -> Montage:
    m = Montage("Mellanbjälklag", beskrivning="Betongplatta 150 mm (K-05), kantisolering 30 mm")
    z0 = -S.H_BJALKLAG
    platta = prisma_ur(Polygon(S.KONTUR, [S.TRAPPHAL]), z0, 0.0)
    urs = [box(x0, x1, y0, y1, z0 - 1, z0 + pelare.TOPP_T) for x0, x1, y0, y1 in pelare.topplatar()]
    m.lagg(Del("Mellanbjälklag betong 150", minus(platta, urs), BETONG, dokument="K-05"), Placering(), "MB-B")
    kant = Polygon(S.KONTUR).buffer(S.STOMME_UT, join_style=2).difference(Polygon(S.KONTUR)).difference(kantrygg())
    m.lagg(Del("Kantisolering 30", prisma_ur(kant, z0, 0.0), CELLPLAST), Placering(), "MB-C")
    return m
