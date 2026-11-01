"""Yttervägg 2NV: mittre huskroppens långsida mot NV.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["2NV"]): u från (9340; 65) i växande y, w genom väggen inåt från stommens utsida, z uppåt från bjälklagets överkant.
"""
from modellering import Montage

from trebodar.byggdelar.regelvagg import regelvagg


def montage() -> Montage:
    v = regelvagg("2NV")
    v.syll(0, 905)
    v.regel(0)
    v.hammarband(0, 905)
    v.regel(415)
    v.regel(860)
    return v.montage()
