"""Marken: berg, uppfyllnad och sovrumsavsatsen, som i Onshape-modellen (referensdelar), och fyllningen mot
källarväggarna där Onshape-modellen saknar mark (modell-todo 17, förenklat).

Under plattan på mark på plan 1 är berget bortsprängt ner till bottenplattans nivå (fyllning och cellplast, se
hus/grund).
"""
from __future__ import annotations

from shapely.geometry import Polygon

from modellering import Del, Montage, Placering, box, prisma

from trebodar.byggdelar.referensdel import importerad
from trebodar.hus.grund import kallarvaggar
from trebodar.hus.grund.grund import MARK_PLATTA
from trebodar.material import BERG, FYLLNING, MARK

Z_BP = -2250.0


def _husets_fotavtryck():  # type: ignore[no-untyped-def]
    """Källaren med fasadstenen och plattan på mark, som prisma från under bottenplattan till bjälklaget."""
    # stängning (+600, −530) så att öppningarna i fasaden räknas till huset
    p = kallarvaggar.ytterkontur().buffer(600.0, join_style=2).buffer(-530.0, join_style=2)
    p = p.union(Polygon(MARK_PLATTA).buffer(30.0, join_style=2))
    p = max(getattr(p, "geoms", [p]), key=lambda g: g.area)
    return prisma([tuple(q) for q in list(p.exterior.coords)[:-1]], 2900.0, z0=-2900.0)


def montage() -> Montage:
    m = Montage("Mark", beskrivning="Berg, uppfyllnad och sovrumsavsats (ur Onshape-modellen)")
    hus = _husets_fotavtryck()
    # berget utan bergschaktet under plattan på mark (x 0–4 545, y 9 205–15 900)
    berg = importerad("berg.bbrep") - box(-30, 4575, 9175, 15930, Z_BP, 0)
    avsats = importerad("sovrumsavsats.bbrep") - hus
    m.lagg(Del("Berg", berg, BERG), Placering(), "Berg")
    m.lagg(Del("Uppfyllnad", importerad("uppfyllnad.bbrep") - hus - importerad("sovrumsavsats.bbrep"), MARK),
           Placering(), "Uppfyllnad")
    m.lagg(Del("Sovrumsavsats", avsats, FYLLNING), Placering(), "Sovrumsavsats")
    return m
