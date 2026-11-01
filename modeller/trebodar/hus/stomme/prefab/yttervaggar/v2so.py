"""Yttervägg 2SO: mittre huskroppens långsida mot SO.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["2SO"]): u från (4470; 3560) i minskande y, w genom väggen inåt från stommens utsida, z uppåt från bjälklagets överkant.
"""
from modellering import Montage

from trebodar.byggdelar.regelvagg import regelvagg


def montage() -> Montage:
    v = regelvagg("2SO")
    v.syll(0, 490)
    v.regel(0)
    v.hammarband(0, 3495)
    v.regel(400)
    v.regel(445)
    v.liggande(490, 1590, 2100)
    v.liggande(490, 1590, 2400)
    v.syll(1590, 3495)
    v.regel(1590)
    v.regel(1635)
    v.regel(2355)
    v.regel(2955)
    v.regel(3450)
    return v.montage()
