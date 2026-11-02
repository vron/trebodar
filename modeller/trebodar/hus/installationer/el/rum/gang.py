"""Gången i högra huskroppen: tre tubspotar som lyser upp mot väggen L2 och snedtaket, och dimmern på L2 vid köket
(belysningsplanen i ärende #8).

Tube Mini R mitt i gången, mitt emellan installationsskiktets läkt, vinklade upp mot L2:s övre del (rummen bakom L2
skymmer det motsatta takfallet), så att väggen och taket lyser upp. Dimmern sitter på L2 (gångsidan) vid köket; röret
går upp i väggen och längs raden i installationsskiktet.
"""
from __future__ import annotations

from ..katalog import DIMMER_1, FXP16, TUBE_MINI_R
from ..lakt import mellan_lakten
from ...montering import tak, vagg, vid_tak
from ..punkter import Apparat, Lampa, Ror, Rum, Tandgrupp, mot

RUM = Rum("GA", "Gång", plan=1)
NAMN = RUM.namn

X, Y = 10210.0, (3425.0, 4365.0, 5605.0)     # önskat läge, flyttas till mitt mellan läkten
MAL_X = 10950.0                               # L2:s yta mot gången (ungefär)
U_B = 3570.0                                  # dimmern längs L2, vid köket

TANDGRUPPER = [Tandgrupp("GA-T1", "Gång, tubspotar")]


def _tub(i: int, y: float) -> Lampa:
    m = tak(mellan_lakten("3SO", X, y), y)
    return Lampa(f"GA-L{i + 1:02d}", TUBE_MINI_R, m, "GA-T1",
                 riktning=mot(m, (MAL_X, y, tak(MAL_X, y).punkt[2] - 300.0)))


PUNKTER = [
    *[_tub(i, y) for i, y in enumerate(Y)],
    Apparat("GA-B1", DIMMER_1, vagg("L2", U_B, 1050.0, sida=1), styr=("GA-T1",)),
]

ROR = [
    Ror("GA-R01", FXP16, "GA-B1", "GA-L03", via=vid_tak("L2", U_B, sida=1)),
    Ror("GA-R02", FXP16, "GA-L03", "GA-L02"),
    Ror("GA-R03", FXP16, "GA-L02", "GA-L01"),
]
