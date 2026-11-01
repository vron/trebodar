"""Grunden och källaren: bottenplattan, källarväggarna V1–V21, rören P1–P19, plattan på mark på plan 1 och
fasadstenen.

Bottenplattan (K-06, R-04): 100 mm betong på 200 mm cellplast i hela källaren med överkanten z −2 250 (balkar,
plintar och L-element förenklade bort). Plattan på mark på plan 1 (bakom V3 och V20): 400 mm cellplast under
mellanbjälklaget på dränerande fyllning upp till 1,7 m över bottenplattan. Fasadstenen (AR-01) i fasadsten.py.
"""
from __future__ import annotations

from shapely.geometry import Polygon

from modellering import Del, Montage, Placering, box, minus

from trebodar import skelett as S
from trebodar.byggdelar.polygon import polygoner, prisma_ur
from trebodar.material import BETONG, CELLPLAST, FYLLNING

from . import fasadsten, kallarvaggar, pelare

Z_BP = -2250.0                   # bottenplattans överkant
MARK_PLATTA = ((0.0, 9205.0), (4545.0, 9205.0), (4545.0, 11010.0), (4310.0, 11010.0), (4310.0, 15900.0),
               (0.0, 15900.0))   # plattan på mark på plan 1 (K-05)


def bottenplatta() -> Montage:
    m = Montage("Bottenplatta", beskrivning="100 mm betong på 200 mm cellplast (K-06, R-04), förenklad")
    kontur = kallarvaggar.ytterkontur()
    # ursparingar för rörens fotplåtar (ingjutna i överkanten)
    urs = [box(x0, x1, y0, y1, Z_BP - pelare.FOT_T, Z_BP + 1) for x0, x1, y0, y1 in pelare.fotplatar()]
    m.lagg(Del("Bottenplatta betong 100", minus(prisma_ur(kontur, Z_BP - 100.0, Z_BP), urs), BETONG), Placering(),
           "BP-B")
    m.lagg(Del("Bottenplatta cellplast 200", prisma_ur(kontur, Z_BP - 300.0, Z_BP - 100.0), CELLPLAST), Placering(),
           "BP-C")
    return m


def platta_pa_mark() -> Montage:
    m = Montage("Plattan på mark", beskrivning="Under mellanbjälklaget på plan 1: 400 cellplast på fyllning")
    # fram till källarväggarnas cellplast (V3, V20): källarens kontur tas bort
    p = Polygon(MARK_PLATTA).difference(kallarvaggar.ytterkontur())
    for i, g in enumerate(polygoner(p), 1):
        m.lagg(Del("Cellplast 400 under plattan på mark", prisma_ur(g, -S.H_BJALKLAG - 400.0, -S.H_BJALKLAG),
                   CELLPLAST), Placering(), f"PM-C{i}")
        m.lagg(Del("Dränerande fyllning", prisma_ur(g, Z_BP, -S.H_BJALKLAG - 400.0), FYLLNING), Placering(),
               f"PM-F{i}")
    return m


def montage() -> Montage:
    m = Montage("Grund", beskrivning="Bottenplatta, källarväggar, rör, plattan på mark och fasadsten")
    m.lagg(bottenplatta())
    m.lagg(kallarvaggar.montage())
    m.lagg(pelare.montage())
    m.lagg(platta_pa_mark())
    m.lagg(fasadsten.montage())
    return m
