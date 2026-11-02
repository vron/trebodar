"""Yttervägg 3NV: högra huskroppens långsida mot NV.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["3NV"]), byggt med reglerna i regelstomme.py: plattor,
ändreglar, öppningarna (karmreglar, överstycken, bröstningar, kortlingar) och fria reglar.
"""
from modellering import Montage

from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import AVVAXLING, Karm, skarv, vagg


def montage() -> Montage:
    v = regelvagg("3NV")
    vagg(v, "3NV", skarvar=(skarv(472.5, 5), skarv(472.5, 13)), raster_origo=472.5, utan=(1672.5,),
         karmar={"F1": Karm(kortlingar=(512.5,)), "F2": Karm(kortlingar=(0.0,)), "F3": Karm(kortlingar=(712.5,)),
                 "F4": Karm(overstycke=AVVAXLING), "F5": Karm(overstycke=AVVAXLING, kortlingar=(502.5,))})
    return v.montage()
