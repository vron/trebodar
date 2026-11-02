"""Yttervägg 3SV: högra huskroppens gavel mot SV.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["3SV"]), byggt med reglerna i regelstomme.py: plattor,
hörnstolpar, öppningarna (karmreglar, överstycken, bröstningar, kortlingar) och fria reglar.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import Karm, hornstolpe, vagg


def montage() -> Montage:
    v = regelvagg("3SV")
    hornen = hornstolpe(v, 0.0, 1, ("LA8-1", "LA8-2")) + hornstolpe(v, S.VAGGAR["3SV"].langd, -1, ("LA7-1", "LA7-2"))
    vagg(v, "3SV", ander=(False, False), staende=hornen, raster_origo=2365.0,
         karmar={"F1": Karm(kortlingar=(470.0,)), "F2": Karm(kortlingar=(790.0,))})
    return v.montage()
