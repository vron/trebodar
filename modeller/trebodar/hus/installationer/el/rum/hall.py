"""Hallen: två tubspotar som lyser upp mot garderobens front framför väggen 1B och snedtaket, dimmern vid
entrédörren och ett uttag på väggen 1D (belysningsplanen i ärende #8).

Tube Mini R en bit upp på takfallet 1SO (två läktfack högre än vid takfoten), mitt emellan installationsskiktets läkt,
vinklade upp mot den övre delen av garderobens front framför 1B (väggen under nocken skymmer det motsatta takfallet).
Dimmern sitter på 1SO:s insida bredvid entrédörren 1SO-D1; röret går upp i väggen och längs raden i
installationsskiktet. Uttaget på 1D (hallsidan) är ett av planens uttag ovanför fönster, men här finns inget fönster:
höjden är tills vidare densamma som ovanför fönstren.
"""
from __future__ import annotations

from ..katalog import DIMMER_1, FXP16, TUBE_MINI_R, UTTAG_1
from ..lakt import mellan_lakten
from ...montering import tak, vagg, vid_tak
from ..punkter import Apparat, Lampa, Ror, Rum, Tandgrupp, mot

RUM = Rum("HA", "Hall", plan=1)
NAMN = RUM.namn

X, Y = 1000.0, (7875.0, 8920.0)              # önskat läge, flyttas till mitt mellan läkten
MAL_X = 1535.0                                # garderobens front framför 1B, mot hallen (ungefär, #96)
U_B = 6185.0                                  # dimmern längs 1SO: söder om entrédörren (u 5 030–6 030)

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
