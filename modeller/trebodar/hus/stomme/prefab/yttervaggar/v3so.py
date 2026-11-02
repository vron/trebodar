"""Yttervägg 3SO: högra huskroppens långsida mot SO. Hammarbandets överkant som de andra ytterväggarnas (z 2 490),
så att takbalkarna vilar på det (Onshape-modellen hade 2 488).

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["3SO"]), byggt med reglerna i regelstomme.py: plattor,
hörnstolpar, öppningarna (karmreglar, överstycken, bröstningar, kortlingar) och fria reglar.
"""
from modellering import Montage

from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import vagg


def montage() -> Montage:
    v = regelvagg("3SO")
    vagg(v, "3SO")
    return v.montage()
