"""Grunden och källaren: bottenplattan, källarväggarna V1–V21, rören P1–P19, plattan på mark på plan 1 och
fasadstenen.

Bottenplattan (K-06, R-04): 100 mm betong på 200 mm cellplast i hela källaren med överkanten z −2 250 (balkar,
plintar och L-element förenklade bort). Plattan på mark på plan 1 (bakom V3 och V20): 400 mm cellplast under
mellanbjälklaget på dränerande fyllning upp till 1,7 m över bottenplattan. Fasadstenen (AR-01): beklädnadsgranit
50 mm, 15 mm utanför källarväggarnas cellplast.
"""
from __future__ import annotations

from shapely.geometry import Polygon, box

from modellering import Del, Montage, Placering, box as box3, prisma

from trebodar import skelett as S
from trebodar.material import BETONG, CELLPLAST, FYLLNING, GRANIT

from . import kallarvaggar, pelare

Z_BP = -2250.0                   # bottenplattans överkant
MARK_PLATTA = ((0.0, 9205.0), (4545.0, 9205.0), (4545.0, 11010.0), (4310.0, 11010.0), (4310.0, 15900.0),
               (0.0, 15900.0))   # plattan på mark på plan 1 (K-05)


def _prisma(namn: str, poly: Polygon, z0: float, z1: float, material, hal=()) -> Del:  # type: ignore[no-untyped-def]
    return Del(namn, prisma([tuple(p) for p in list(poly.exterior.coords)[:-1]], z1 - z0,
                            [list(h) for h in hal] + [[tuple(p) for p in list(r.coords)[:-1]] for r in poly.interiors],
                            z0), material)


def bottenplatta() -> Montage:
    m = Montage("Bottenplatta", beskrivning="100 mm betong på 200 mm cellplast (K-06, R-04), förenklad")
    kontur = kallarvaggar.ytterkontur()
    betong = Del("Bottenplatta betong 100", prisma([tuple(p) for p in list(kontur.exterior.coords)[:-1]], 100.0,
                                                   z0=Z_BP - 100.0), BETONG)
    # ursparingar för rörens fotplåtar (ingjutna i överkanten)
    urs = [box3(x0, x1, y0, y1, Z_BP - pelare.FOT_T, Z_BP + 1) for x0, x1, y0, y1 in pelare.fotplatar()]
    m.lagg(Del("Bottenplatta betong 100", betong.form - urs[0] if len(urs) == 1 else
               _diff(betong.form, urs), BETONG), Placering(), "BP-B")
    m.lagg(Del("Bottenplatta cellplast 200", prisma([tuple(p) for p in list(kontur.exterior.coords)[:-1]], 200.0,
                                                    z0=Z_BP - 300.0), CELLPLAST), Placering(), "BP-C")
    return m


def _diff(form, verktyg):  # type: ignore[no-untyped-def]
    from modellering.form import Diff
    return Diff(form, tuple(verktyg))


def platta_pa_mark() -> Montage:
    m = Montage("Plattan på mark", beskrivning="Under mellanbjälklaget på plan 1: 400 cellplast på fyllning")
    # fram till källarväggarnas cellplast (V3, V20): källarens kontur tas bort
    p = Polygon(MARK_PLATTA).difference(kallarvaggar.ytterkontur())
    for i, g in enumerate(getattr(p, "geoms", [p]), 1):
        m.lagg(_prisma("Cellplast 400 under plattan på mark", g, -S.H_BJALKLAG - 400.0, -S.H_BJALKLAG, CELLPLAST),
               Placering(), f"PM-C{i}")
        m.lagg(_prisma("Dränerande fyllning", g, Z_BP, -S.H_BJALKLAG - 400.0, FYLLNING), Placering(), f"PM-F{i}")
    return m


def fasadsten() -> Montage:
    """Beklädnadsgranit 50 mm, baksidan 15 mm utanför cellplasten (AR-01), som i Onshape-modellen flyttad 15 mm."""
    m = Montage("Fasadsten", beskrivning="Beklädnadsgranit Bohus Grå 50 mm, 15 mm utanför cellplasten (AR-01)")
    stor = Polygon([(9470, 905), (13905, 905), (13905, 12605), (9470, 12605), (9470, 12555), (13855, 12555),
                    (13855, 955), (9470, 955)])
    m.lagg(_prisma("Fasadsten stor", stor, -2150.0, -S.H_BJALKLAG, GRANIT), Placering(), "FS1")
    m.lagg(Del("Fasadsten liten", box3(-95, -45, 3560, 8060, -1540, -740), GRANIT), Placering(), "FS2")
    return m


def montage() -> Montage:
    m = Montage("Grund", beskrivning="Bottenplatta, källarväggar, rör, plattan på mark och fasadsten")
    m.lagg(bottenplatta())
    m.lagg(kallarvaggar.montage())
    m.lagg(pelare.montage())
    m.lagg(platta_pa_mark())
    m.lagg(fasadsten())
    return m
