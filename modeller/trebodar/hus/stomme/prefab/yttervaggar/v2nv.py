"""Yttervägg 2NV: mittre huskroppens långsida mot NV.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["2NV"]), byggt med reglerna i regelstomme.py: plattor,
ändreglar, öppningarna (karmreglar, överstycken, bröstningar, kortlingar) och fria reglar.
"""
from modellering import Montage

from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import vagg


def montage() -> Montage:
    v = regelvagg("2NV")
    vagg(v, "2NV", raster_origo=415.0)
    return v.montage()
