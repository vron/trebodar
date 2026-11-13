"""Yttervägg 2SO: mittre huskroppens långsida mot SO.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["2SO"]), byggt med reglerna i regelstomme.py: plattor,
ändreglar, öppningarna (karmreglar, överstycken, bröstningar, kortlingar) och fria reglar. Regeln under takbalken
vid skjutdörren D1 (u 1 700) står tätt intill karmreglarna (REGEL_VID_D1), så att karmens regelgrupp har en fri sida
längs väggen för vinkelbeslaget (forankring.py, #111); takbalken står till mer än halva bredden på den.
"""
from modellering import Montage

from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import DUBBELT_HB, Karm, vagg

REGEL_VID_D1 = 1680.0       # u: tätt intill D1:s yttre karmregel (u 1 635–1 680), under takbalken u 1 700–1 745


def montage() -> Montage:
    v = regelvagg("2SO")
    vagg(v, "2SO", raster_origo=2355.0, reglar=(REGEL_VID_D1,),
         karmar={"D1": Karm(dubbel=True, overstycke=DUBBELT_HB)})
    return v.montage()
