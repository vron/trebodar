"""Yttervägg 2NO: mittre huskroppens gavel mot NO.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["2NO"]), byggt med reglerna i regelstomme.py: plattor,
hörnstolpar, öppningarna (karmreglar, överstycken, bröstningar, kortlingar) och fria reglar.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import Karm, hornstolpe, vagg


def montage() -> Montage:
    v = regelvagg("2NO")
    hornen = hornstolpe(v, 0.0, 1, ("LA1-1", "LA1-2")) + hornstolpe(v, S.VAGGAR["2NO"].langd, -1, ("LA2-1", "LA2-2"))
    vagg(v, "2NO", ander=(False, False), staende=hornen, raster_origo=0.0, utan=(1800.0,),
         karmar={"F1": Karm(kortlingar=(555.0,)), "F2": Karm(kortlingar=(355.0,))})
    return v.montage()
