"""Installationspassagerna (#114): där rören i mellanbjälklaget går under de bärande väggarna.

Stommens syllar bultas i plattan efter gjutningen (stomme/forankring.py), och rören i plattan (elens, tappvattnets,
avloppets och golvvärmens) håller minst 200 mm från varje bult: de går utanför spärrzonerna (forankring.sparrzon),
som med målet att vara så få och enkla som möjligt är rektanglar längs väggarna från den första till den sista
bulten. Där rören går under en bärande vägg går de samlade i en passage: en kort bit av väggen där inga bultar
borras, och där spärrzonen bryts. Bultarna placeras ur stommen och passagerna, och rören dras runt zonerna;
gjutningens kontroll prövar avståndet, och AR-03 visar passagerna och spärrzonerna.

En passage är ett intervall längs väggen (u i väggens system, skelett.VAGGAR) med det som går igenom den. Passagerna
hålls få: elen till plan 1 går inte genom de bärande väggarna utan upp i lätta väggar och i innertaket
(el/bjalklag/mellanbjalklag.UPP_I_TAKET), brandlarmets stigare står i lätta väggar eller i en passage, och nya rör
under en vägg dras genom en befintlig passage där det går.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import cache

from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from trebodar import skelett as S

TVARS = 400.0               # passagen når så långt utanför väggens stomme på båda sidor [mm] (förbi spärrzonen)


@dataclass(frozen=True)
class Passage:
    u0: float
    u1: float
    vad: str                 # vad som går igenom den


PASSAGER: dict[str, tuple[Passage, ...]] = {
    "1A": (Passage(938.0, 1088.0, "tappvattnets stråk S till badkaret och tvättstället"),
           Passage(1508.0, 1680.0, "tappvattnets stråk S2 till UF2 och källarens tvättho")),
    "1B": (Passage(1315.0, 1880.0, "tappvattnets stråk S2, S och V västerut och golvvärmens tillopp till hallen"),),
    "2B": (Passage(420.0, 935.0, "golvvärmens slinga i kontoret"),
           Passage(5170.0, 5925.0, "golvvärmens tillopp G och O österut")),
    "1NO": (Passage(1016.0, 1380.0, "tvättställets golvdosa och rör"),),
    "1SO": (Passage(7330.0, 8200.0, "källarens tvätthos och tvättmaskinens rör ned längs V21"),
            Passage(9460.0, 9670.0, "badkarets rör upp i väggen")),
}


def rektangel(kod: str, p: Passage) -> Polygon:
    """Passagen i plan: u0–u1 längs väggen och tvärs över den med TVARS på båda sidor."""
    v = S.VAGGAR[kod]
    o, u, w = v.origo, v.u, v.w
    hornen = [(o[0] + a * u[0] + b * w[0], o[1] + a * u[1] + b * w[1])
              for a, b in ((p.u0, -TVARS), (p.u1, -TVARS), (p.u1, v.tjocklek + TVARS), (p.u0, v.tjocklek + TVARS))]
    return Polygon(hornen)


@cache
def passagerna() -> BaseGeometry:
    """Alla passager i plan."""
    return unary_union([rektangel(kod, p) for kod, ps in PASSAGER.items() for p in ps] or [Polygon()])
