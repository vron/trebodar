"""Köket (planritning 201 rev 02 och användarens markeringar): diskbänken på bänken längs 3NV mellan fönstret 3NV-F4
och köksfläkten. Rören kommer upp genom golvet i diskbänksskåpet (golvdosa) från stråket O i mellanbjälklaget, de
sista 0,3 m var för sig (kallt norr om varmt) förbi vinkeljärnen vid V14. Diskmaskinen ansluts i diskbänksskåpet.
"""
from __future__ import annotations

from ...montering import golv
from ..katalog import DISKBANK, GOLVDOSA, ROR_I_ROR_16
from ..punkter import Rum, Tappstalle
from ..teknikrum import X_O_SLUT

RUM = Rum("KO", "Kök", plan=1)

TAPPSTALLEN = [
    Tappstalle("KO-DB1", DISKBANK, GOLVDOSA, golv(13300.0, 8320.0), ROR_I_ROR_16, kallt=(0.0, 1.0, 0.0),
               via=(X_O_SLUT - 50.0, None)),
]
