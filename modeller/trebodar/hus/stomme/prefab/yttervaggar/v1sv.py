"""Yttervägg 1SV: vänstra huskroppens gavel mot SV.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["1SV"]): u från (4340; 15930) i minskande x, w genom väggen inåt från stommens utsida, z uppåt från bjälklagets överkant.
"""
from modellering import Montage

from trebodar.byggdelar.regelvagg import regelvagg


def montage() -> Montage:
    v = regelvagg("1SV")
    v.syll(0, 1135)
    v.regel(0, namn="LA10-1")
    v.hammarband(0, 4370)
    v.regel(45, b=95, w0=50, w1=95, namn="LA10-2")
    v.regel(600)
    v.regel(1045)
    v.regel(1090)
    v.liggande(1135, 3235, 2186)
    v.liggande(1135, 3235, 2231)
    v.syll(3235, 4370)
    v.regel(3235)
    v.regel(3280)
    v.regel(3725)
    v.regel(4230, b=95, w0=50, w1=95, namn="LA9-2")
    v.regel(4325, namn="LA9-1")
    return v.montage()
