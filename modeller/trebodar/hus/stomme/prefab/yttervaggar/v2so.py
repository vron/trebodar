"""Yttervägg 2SO: mittre huskroppens långsida mot SO.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["2SO"]), byggt med reglerna i regelstomme.py: plattor,
ändreglar, öppningarna (karmreglar, överstycken, bröstningar, kortlingar) och fria reglar.
"""
from modellering import Montage

from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import AVVAXLING, Karm, vagg


def montage() -> Montage:
    v = regelvagg("2SO")
    vagg(v, "2SO", raster_origo=2355.0, karmar={"D1": Karm(dubbel=True, overstycke=AVVAXLING)})
    return v.montage()
