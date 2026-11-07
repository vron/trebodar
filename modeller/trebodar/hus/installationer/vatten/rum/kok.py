"""Köket (planritning 201 rev 02 och användarens markeringar): diskbänken på bänken längs 3NV mellan fönstret 3NV-F4
och köksfläkten, och diskmaskinen i öns skåp O1 (#50). Rören kommer från underfördelaren UF1 på V14 under köket
(underfordelare.py) i ett eget stråk i mellanbjälklaget, upp genom golvet: i diskbänksskåpet (golvdosa, kallt öster
om varmt) och under diskmaskinens bakkant (hus/inredning/koksbank.py).
"""
from __future__ import annotations

from trebodar.hus.inredning.koksbank import diskmaskinens_anslutningar

from ...montering import golv
from ..katalog import DISKBANK, DISKMASKIN, GOLVDOSA, ROR_I_ROR_16
from ..punkter import Rum, Tappstalle

RUM = Rum("KO", "Kök", plan=1)

TAPPSTALLEN = [
    Tappstalle("KO-DB1", DISKBANK, GOLVDOSA, golv(13300.0, 8450.0), ROR_I_ROR_16, kallt=(1.0, 0.0, 0.0)),
    Tappstalle("KO-DM1", DISKMASKIN, GOLVDOSA, golv(*diskmaskinens_anslutningar()[0]), ROR_I_ROR_16),
]
