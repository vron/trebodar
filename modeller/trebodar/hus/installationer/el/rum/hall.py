"""Hallen: två tubspotar som lyser upp mot väggen 1B och snedtaket, dimmern vid entrédörren och ett uttag på väggen
1D (belysningsplanen i ärende #8).

Tube Mini R nära takfoten vid 1SO, mitt emellan installationsskiktets läkt, vinklade upp mot 1B:s övre del (väggen
under nocken skymmer det motsatta takfallet). Dimmern sitter på 1SO:s insida bredvid entrédörren 1SO-D1; röret går
upp i väggen och längs raden i installationsskiktet. Uttaget på 1D (hallsidan) är ett av planens uttag ovanför
fönster, men här finns inget fönster: höjden är tills vidare densamma som ovanför fönstren.
"""
from __future__ import annotations

from ..katalog import DIMMER_1, FXP16, TUBE_MINI_R, UTTAG_1
from ..lakt import mellan_lakten
from ...montering import tak, vagg, vid_tak
from ..punkter import Apparat, Lampa, Ror, Rum, Tandgrupp, mot

RUM = Rum("HA", "Hall", plan=1)
NAMN = RUM.namn

X, Y = 305.0, (7875.0, 8920.0)               # önskat läge, flyttas till mitt mellan läkten
MAL_X = 2040.0                                # 1B:s yta mot hallen (ungefär)
U_B = 6235.0                                  # dimmern längs 1SO: söder om entrédörren (u 5 080–6 080)

TANDGRUPPER = [Tandgrupp("HA-T1", "Hall, tubspotar")]


def _tub(i: int, y: float) -> Lampa:
    m = tak(mellan_lakten("1SO", X, y), y)
    return Lampa(f"HA-L{i + 1:02d}", TUBE_MINI_R, m, "HA-T1",
                 riktning=mot(m, (MAL_X, y, tak(MAL_X, y).punkt[2] - 400.0)))


PUNKTER = [
    *[_tub(i, y) for i, y in enumerate(Y)],
    Apparat("HA-B1", DIMMER_1, vagg("1SO", U_B, 1050.0), styr=("HA-T1",)),
    Apparat("HA-U1", UTTAG_1, vagg("1D", 1015.0, 2200.0, sida=-1)),
]

ROR = [
    Ror("HA-R01", FXP16, "HA-B1", "HA-L02", via=vid_tak("1SO", U_B)),
    Ror("HA-R02", FXP16, "HA-L02", "HA-L01"),
]
