"""Elcentralen och grupperna (ärendena #50 och #51): gruppcentralen i teknikrummet (..teknikrum.GRUPPCENTRAL, på V3
väster om vattenmätaren, med 800 mm fritt framför) och gruppförteckningen, som i ett nybyggt svenskt hus (SS 436 40 00):

- grupper per område och ändamål: belysningen och uttagen var för sig (utom i sovrummen och kontoren, en grupp per
  huskropp), och egna grupper för de fasta och tunga apparaterna (hällen, ugnen eller mikron,
  diskmaskinen, kylen, frysen och köksfläkten, tvättmaskinen, torktumlaren, värmepumpen) och för köksbänkens och öns
  uttag;
- varje grupp med personskyddsautomat (dvärgbrytare och jordfelsbrytare typ A, 30 mA), så att ett fel bara löser ut
  sin egen grupp; värmepumpen enligt tillverkaren (JORDFEL_VP); överspänningsskydd typ 2 i centralen;
- ledarna i rör (FK och PE), 1,5 mm² för 10 A och 2,5 mm² för 16 A, hällen och värmepumpen 400 V (fem ledare).

Varje grupp matar sina punkter (apparaterna och anslutningarna) i ordning: röret från centralen går till den första
(ingjutet i mellanbjälklaget, bjalklag/mellanbjalklag.py) och därifrån mellan punkterna i apparatdosorna, i väggarna,
innertaket eller bjälklaget. Lamporna matas genom brytarna och dimrarna som styr dem.
"""
from __future__ import annotations

from dataclasses import dataclass

JORDFEL = "personskyddsautomat typ A 30 mA"
JORDFEL_VP = "enligt värmepumpens tillverkare (typ B om den kräver det)"
OVERSPANNINGSSKYDD = "typ 2"
HUVUDBRYTARE = "3 × 63 A"
# brandlarmets matningsdosa D01 i källarens tak (brandlarm/larm.py), matad från grupp G02: mellan underkantsnätets järn
BRANDLARM_D01 = (6200.0, 5125.0)


@dataclass(frozen=True)
class Grupp:
    id: str
    namn: str
    sakring: int                    # [A]
    faser: int                      # 1 (230 V) eller 3 (400 V)
    area: float                     # ledarnas area [mm²]
    punkter: tuple[str, ...]        # i rörens ordning från centralen
    jordfel: str = JORDFEL

    @property
    def text(self) -> str:
        return f"{self.faser} × {self.sakring} A" if self.faser == 3 else f"{self.sakring} A"


GRUPPER = [
    Grupp("G01", "Belysning hall och vardagsrum", 10, 1, 1.5, ("HA-B1", "VR-B1", "VR-B2")),
    Grupp("G02", "Belysning allrum, gång och kök, brandlarmet", 10, 1, 1.5,
          ("AL-B1", "AL-B2", "BL-D01", "GA-B1", "KO-B1", "KO-B2")),
    Grupp("G03", "Sovrum och kontor i mittre huskroppen, belysning och uttag", 10, 1, 1.5, ("SV-B1", "SV-U1", "KT-B1")),
    Grupp("G04", "Gästrum, kontor och sovrum i högra huskroppen, belysning och uttag", 10, 1, 1.5,
          ("GR-B1", "KL-B1", "SL-B1", "GR-U1", "KL-U1", "SL-U1")),
    Grupp("G05", "Belysning och fläkten FF2, badrum", 10, 1, 1.5, ("BA-B1", "BA-D2")),
    Grupp("G06", "Uttag hall, vardagsrum och allrum", 10, 1, 1.5,
          ("HA-U1", "VR-U1", "VR-U2", "VR-U3", "AL-U1", "AL-U2")),
    Grupp("G07", "Uttag och handdukstork, badrum", 10, 1, 1.5, ("BA-U1", "BA-D1")),
    Grupp("G08", "Tvättmaskin, badrummets skåp", 10, 1, 1.5, ("BA-U2",)),
    Grupp("G09", "Torktumlare, badrummets skåp", 10, 1, 1.5, ("BA-U3",)),
    Grupp("G10", "Häll", 16, 3, 2.5, ("KO-D1",)),
    Grupp("G11", "Ugn eller mikro", 16, 1, 2.5, ("KO-U6",)),
    Grupp("G12", "Köksbänken", 16, 1, 2.5, ("KO-U8", "KO-U1", "KO-U2", "KO-U9", "KO-U10", "KO-U3")),
    Grupp("G13", "Köksön", 16, 1, 2.5, ("KO-U11", "KO-U12")),
    Grupp("G14", "Diskmaskin", 10, 1, 1.5, ("KO-U7",)),
    Grupp("G15", "Kyl, frys och köksfläkt", 10, 1, 1.5, ("KO-U4", "KO-U5", "KO-U13")),
    Grupp("G16", "Värmepump", 16, 3, 2.5, ("TK-D1",), JORDFEL_VP),
    Grupp("G17", "Belysning källaren, det stora rummet", 10, 1, 1.5, ("KA-D1", "KA-B5")),
    Grupp("G18", "Belysning källaren, de små rummen", 10, 1, 1.5, ("KA-B6", "KA-B7")),
    Grupp("G19", "Uttag teknikrummet", 10, 1, 1.5, ("TK-U1", "TK-U2", "TK-U3")),
    Grupp("G20", "Uttag tvättstugan", 10, 1, 1.5, ("KA-U1", "KA-U2")),
    Grupp("G21", "Tvättmaskin, tvättstugan", 10, 1, 1.5, ("KA-U3",)),
    Grupp("G22", "Torktumlare, tvättstugan", 10, 1, 1.5, ("KA-U4",)),
    Grupp("G23", "Uttag de små rummen söder om KL1", 10, 1, 1.5, ("KA-U5", "KA-U6", "KA-U7", "KA-U8")),
]
GRUPP = {g.id: g for g in GRUPPER}
