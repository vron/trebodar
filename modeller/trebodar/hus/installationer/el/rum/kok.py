"""Köket: tubspotar i snedtaket riktade mot bänken längs den nordvästra långsidan (prov).

Tre Tube Mini R i takfallet 3NV, mitt emellan läkten, riktade mot bänkens mitt (450 mm från väggen, 900 mm över
golvet) mellan och bredvid fönstren, och en dimmer på den lätta väggen L4 (köksidan) rakt under raden: röret går
upp i väggen och in i installationsskiktet mellan samma läkt som spotarna och längs raden.
"""
from __future__ import annotations

from trebodar import skelett as S
from trebodar.hus.invandigt.vaggar import vaggdef

from ..katalog import DIMMER_1, FXP16, TUBE_MINI_R
from ..lakt import mellan_lakten
from ...montering import tak, vagg, vid_tak
from ..punkter import Apparat, Lampa, Ror, Rum, Tandgrupp, mot

RUM = Rum("KO", "Kök", plan=1)
NAMN = RUM.namn

RAD_X = 12900.0                              # önskat läge i takfallet 3NV, flyttas till mitt mellan läkten
Y = (7700.0, 9600.0, 11500.0)                # bredvid och mellan fönstren 3NV-F4 och 3NV-F5
BANK_X = S.YTTERVAGGAR["3NV"].origo[0] - S.T_STOMME - 70.0 - 450.0     # bänkens mitt: 450 mm från väggens yta
BANK_Z = 900.0

_X = {y: mellan_lakten("3NV", RAD_X, y) for y in Y}
_U = _X[Y[0]] - vaggdef("L4").origo[0]      # dimmern på L4 rakt under raden

TANDGRUPPER = [Tandgrupp("KO-T1", "Kök, spotar mot bänken")]

PUNKTER = [
    *[Lampa(f"KO-L{i + 1:02d}", TUBE_MINI_R, tak(_X[y], y), "KO-T1", riktning=mot(tak(_X[y], y), (BANK_X, y, BANK_Z)))
      for i, y in enumerate(Y)],
    Apparat("KO-B1", DIMMER_1, vagg("L4", _U, 1150.0, sida=1), styr=("KO-T1",)),
]

ROR = [
    Ror("KO-R01", FXP16, "KO-B1", "KO-L01", via=vid_tak("L4", _U)),
    Ror("KO-R02", FXP16, "KO-L01", "KO-L02"),
    Ror("KO-R03", FXP16, "KO-L02", "KO-L03"),
]
