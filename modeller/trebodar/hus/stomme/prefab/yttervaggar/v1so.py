"""Yttervägg 1SO: vänstra huskroppens långsida mot SO.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["1SO"]), byggt med reglerna i regelstomme.py: plattor,
ändreglar, öppningarna (karmreglar, överstycken, bröstningar, kortlingar) och fria reglar.
"""
from modellering import Montage

from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import AVVAXLING, Karm, skarv, vagg


def montage() -> Montage:
    v = regelvagg("1SO")
    vagg(v, "1SO", skarvar=(skarv(473.0, 7), skarv(473.0, 13)), raster_origo=473.0,
         karmar={"D1": Karm(dubbel=True, overstycke=AVVAXLING, kortlingar=(793.0,))})
    return v.montage()
