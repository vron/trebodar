"""Mätytor för ljusberäkningen (`./mod ljusplan`): vågräta ytor där belysningsstyrkan [lux] räknas fram i
renderingen, med de tända tändgrupperna och dagsljuset, och ritas som planer med belysningsstyrkan i färg,
isolinjer och medel-, minsta och största värde per rum och delområde.

Ytan mäter utan att störa: den syns bara för kameran (ovanifrån), och kastar varken skuggor eller reflekterar ljus.
"""
from __future__ import annotations

from dataclasses import dataclass

from trebodar import skelett as S
from trebodar.hus.invandigt.lattvaggar import K_YTA

Ruta = tuple[float, float, float, float]       # (x0, x1, y0, y1) [mm]


@dataclass(frozen=True)
class Matyta:
    namn: str
    plan: int                    # 1 (plan 1) eller 0 (källaren)
    hojd: float                  # över golvet [mm]
    omrade: Ruta
    cell: float = 50.0           # rutnätets steg [mm]
    zoner: tuple[tuple[str, Ruta], ...] = ()     # delområden med egen statistik (t.ex. en bänk)


PLAN1: Ruta = (-500.0, 14300.0, -300.0, 16300.0)
KALLARE: Ruta = (0.0, 14000.0, 0.0, 12800.0)
_NV = S.YTTERVAGGAR["3NV"].origo[0] - S.T_STOMME - 70.0                    # köksväggens yta (insida)
BANK: Ruta = (_NV - 600.0, _NV, K_YTA, 12400.0)        # bänken längs köksväggen, 600 djup, från kökets inbyggnad

MATYTOR = {
    "plan1-golv": Matyta("Plan 1, golvet", 1, 0.0, PLAN1),
    "plan1-bord": Matyta("Plan 1, bordshöjd 0,75 m", 1, 750.0, PLAN1, zoner=(("Köksbänken (0,75 m)", BANK),)),
    "kok-bank": Matyta("Köket, bänkhöjd 0,9 m", 1, 900.0, (BANK[0] - 1000.0, BANK[1], BANK[2], BANK[3]), cell=25.0,
                       zoner=(("Bänken", BANK),)),
    "kallare-golv": Matyta("Källaren, golvet", 0, 0.0, KALLARE),
}
