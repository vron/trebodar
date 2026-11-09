"""Yttervägg 1NV: vänstra huskroppens långsida mot NV.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["1NV"]), byggt med reglerna i regelstomme.py: plattor,
ändreglar, öppningarna (karmreglar, överstycken, bröstningar, kortlingar) och fria reglar.
"""
from modellering import Montage

from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import AVVAXLING, DUBBELT_HB, Karm, vagg


def montage() -> Montage:
    v = regelvagg("1NV")
    vagg(v, "1NV", raster_origo=1990.0, utan=(190.0, 4390.0),
         karmar={"F1": Karm(overstycke=AVVAXLING), "D1": Karm(overstycke=DUBBELT_HB, kortlingar=(155.0,))})
    return v.montage()
