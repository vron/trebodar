"""Yttervägg 1SO: vänstra huskroppens långsida mot SO.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["1SO"]): u från (-30; 15835) i minskande y, w genom väggen inåt från stommens utsida, z uppåt från bjälklagets överkant.
"""
from modellering import Montage

from trebodar.byggdelar.regelvagg import regelvagg


def montage() -> Montage:
    v = regelvagg("1SO")
    v.syll(0, 4695.5)
    v.regel(0)
    v.hammarband(0, 4695.5)
    v.regel(473)
    v.regel(1073)
    v.liggande(1118, 1718, 1355)
    v.liggande(1118, 1718, 2000)
    v.regel(1718)
    v.regel(2273)
    v.liggande(2318, 2918, 1355)
    v.liggande(2318, 2918, 2000)
    v.regel(2918)
    v.regel(3473)
    v.regel(4073)
    v.regel(4673)
    v.syll(4695.5, 5080)
    v.hammarband(4695.5, 8295.5)
    v.regel(4990)
    v.regel(5035)
    v.liggande(5080, 6080, 2100)
    v.liggande(5080, 6080, 2400)
    v.regel(5873, z0=2145, z1=2400)
    v.syll(6080, 8295.5)
    v.regel(6080)
    v.regel(6125)
    v.regel(6473)
    v.regel(7073)
    v.regel(7673)
    v.regel(8273)
    v.syll(8295.5, 12180)
    v.hammarband(8295.5, 12180)
    v.regel(8873)
    v.regel(9473)
    v.regel(10073)
    v.regel(10673)
    v.liggande(10718, 11318, 1355)
    v.liggande(10718, 11318, 2000)
    v.regel(11318)
    v.regel(11873)
    v.regel(12135)
    return v.montage()
