"""Yttervägg 1NV: vänstra huskroppens långsida mot NV.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["1NV"]): u från (4340; 11040) i växande y, w genom väggen inåt från stommens utsida, z uppåt från bjälklagets överkant.
"""
from modellering import Montage

from trebodar.byggdelar.regelvagg import regelvagg


def montage() -> Montage:
    v = regelvagg("1NV")
    v.syll(0, 3035)
    v.regel(0)
    v.hammarband(0, 4795)
    v.regel(820)
    v.liggande(865, 1865, 1055)
    v.liggande(865, 1865, 2100)
    v.liggande(865, 1865, 2400)
    v.regel(1865)
    v.regel(1990)
    v.regel(2590)
    v.regel(2990)
    v.liggande(3035, 4035, 2100)
    v.regel(3190, z0=2145)
    v.syll(4035, 4795)
    v.regel(4035)
    v.regel(4750)
    return v.montage()
