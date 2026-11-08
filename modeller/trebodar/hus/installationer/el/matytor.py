"""Mätytor för ljusberäkningen (`./mod ljusplan`): vågräta ytor där belysningsstyrkan [lux] räknas fram i
renderingen, med de tända tändgrupperna och dagsljuset, och ritas som planer med belysningsstyrkan i färg,
isolinjer och medel-, minsta och största värde per rum och delområde.

Ytan mäter utan att störa: den syns bara för kameran (ovanifrån), och kastar varken skuggor eller reflekterar ljus.
Ett delområde kan mätas i en egen höjd (bänkskivorna och ön på planerna över plan 1), med en egen yta där.
"""
from __future__ import annotations

from dataclasses import dataclass

from trebodar.hus.badrum import FALLYTOR
from trebodar.hus.inredning import koksbank as KB
from trebodar.hus.inredning.koksskap import Z_TOPP
from trebodar.hus.invandigt.lattvaggar import K_YTA

Ruta = tuple[float, float, float, float]       # (x0, x1, y0, y1) [mm]


@dataclass(frozen=True)
class Zon:
    """Ett delområde med egen statistik, i mätytans höjd eller i en egen (hojd, över golvet [mm])."""
    namn: str
    omrade: Ruta
    hojd: float | None = None


@dataclass(frozen=True)
class Matyta:
    namn: str
    plan: int                    # 1 (plan 1) eller 0 (källaren)
    hojd: float                  # över golvet [mm]
    omrade: Ruta
    cell: float = 50.0           # rutnätets steg [mm]
    zoner: tuple[Zon, ...] = ()  # delområden med egen statistik (t.ex. en bänk)


PLAN1: Ruta = (-500.0, 14300.0, -300.0, 16300.0)
KALLARE: Ruta = (0.0, 14000.0, 0.0, 12800.0)
# köksbänkens skivor (inredning/koksbank.py): längs 3NV från kökets inbyggnad till 3SV, längs 3SV till den vita sidan
# och ön
BANK_NV: Ruta = (KB.X_FRONT - KB.UTSTICK, KB.X_VAGG, K_YTA, KB.Y_SYD)
BANK_SV: Ruta = (KB.FOGAR_KORT[-1] - KB.FOG / 2 - KB.SIDA_T, KB.X_FRONT - KB.UTSTICK, KB.Y_FRONT - KB.UTSTICK,
                 KB.Y_SYD)
ON: Ruta = (KB.ON_X - KB.ON_DJUP / 2, KB.X_ON_FRONT + KB.UTSTICK, KB.FOGAR_ON[0] - KB.FOG / 2 - KB.SIDA_T,
            KB.FOGAR_ON[-1] + KB.FOG / 2 + KB.SIDA_T)
KOK: Ruta = (ON[0] - 500.0, KB.X_VAGG, K_YTA, KB.Y_SYD)
BANK_Z = Z_TOPP + KB.BANK_T + 10.0                     # 10 mm över bänkskivorna, ovanför hällens glas
BANKAR = (Zon("Bänken längs 3NV", BANK_NV, BANK_Z), Zon("Bänken längs 3SV", BANK_SV, BANK_Z), Zon("Ön", ON, BANK_Z))
# tvättstugans bänk längs V21 (inte modellerad): tvätthoet KA-TH1 och tvättmaskinen och torktumlaren vid KA-TM1, 600
# djup från V21:s gips (x 333), mätt i arbetshöjden
TVATTBANKEN = Zon("Tvättbänken längs V21", (333.0, 933.0, 7400.0, 8950.0), 900.0)
# inredningen på mätytan (skåpen, sängen, bänkskivorna, kaminen) lämnas utanför statistiken: den snittas i de här
# höjderna över golvet [mm] som ligger på mätytan eller högst INREDNING_OVER över den (bänkskivorna i sin mitt)
INREDNING_SNITT = (2.0, 100.0, 200.0, 300.0, 450.0, 600.0, 750.0, Z_TOPP + KB.BANK_T / 2)
INREDNING_OVER = 900.0

# plan 1:s golv mäts strax över badrummets klinker, som ligger över bjälklaget (golvets fall, hus/badrum.py)
GOLV_Z = max(f.z(x, y) for f in FALLYTOR for x, y in f.yta.exterior.coords) + 5.0

MATYTOR = {
    # köket med bänkskivorna och ön i sin höjd: belysningsstyrkan där man arbetar
    "plan1-golv": Matyta("Plan 1, golvet", 1, GOLV_Z, PLAN1, zoner=BANKAR),
    "plan1-bord": Matyta("Plan 1, bordshöjd 0,75 m", 1, 750.0, PLAN1, zoner=BANKAR),
    "kok-bank": Matyta("Köket, bänkskivorna 0,91 m", 1, BANK_Z, KOK, cell=25.0, zoner=BANKAR),
    "kallare-golv": Matyta("Källaren, golvet", 0, 0.0, KALLARE, zoner=(TVATTBANKEN,)),
}
