"""Yttervägg 3SV: högra huskroppens gavel mot SV.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["3SV"]): u från (13840; 12540) i minskande x, w genom väggen inåt från stommens utsida, z uppåt från bjälklagets överkant.
"""
from modellering import Montage

from trebodar.byggdelar.regelvagg import regelvagg


def montage() -> Montage:
    v = regelvagg("3SV")
    v.syll(0, 2775)
    v.regel(0, namn="LA8-1")
    v.hammarband(0, 4370)
    v.regel(45, b=95, w0=50, w1=95, namn="LA8-2")
    v.regel(650)
    v.liggande(695, 1695, 1055)
    v.liggande(695, 1695, 2100)
    v.regel(1165, z1=1055)
    v.regel(1165, z0=2145)
    v.regel(1695)
    v.regel(2365)
    v.regel(2730)
    v.liggande(2775, 3675, 2100)
    v.regel(3565, z0=2145)
    v.syll(3675, 4370)
    v.regel(3675)
    v.regel(4230, b=95, w0=50, w1=95, namn="LA7-2")
    v.regel(4325, namn="LA7-1")
    return v.montage()
