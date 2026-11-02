"""Köket (planritning 201 rev 02 och användarens markeringar): diskbänken på bänken längs 3NV mellan fönstret 3NV-F4
och köksfläkten. Rören kommer upp genom golvet i diskbänksskåpet (golvdosa, kallt öster om varmt) från stråket O i
mellanbjälklaget. Diskmaskinen ansluts i diskbänksskåpet.
"""
from __future__ import annotations

from ...montering import golv
from ..katalog import DISKBANK, GOLVDOSA, ROR_I_ROR_16
from ..punkter import Rum, Tappstalle

RUM = Rum("KO", "Kök", plan=1)

TAPPSTALLEN = [
    Tappstalle("KO-DB1", DISKBANK, GOLVDOSA, golv(13300.0, 8450.0), ROR_I_ROR_16, kallt=(1.0, 0.0, 0.0)),
]
