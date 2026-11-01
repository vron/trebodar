"""Yttervägg 1NO: vänstra huskroppens gavel mot NO.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["1NO"]): u från (-30; 3560) i växande x, w genom väggen inåt från stommens utsida, z uppåt från bjälklagets överkant.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg

DAL = S.BALKAR["DB2"].uk


def montage() -> Montage:
    v = regelvagg("1NO")
    v.syll(0, 3000)
    v.regel(0)
    v.hammarband(0, 4332)
    v.regel(45, b=95, w0=50, w1=95)
    v.regel(705)
    v.liggande(750, 1750, 1055)
    v.liggande(750, 1750, 2100)
    v.regel(1155, z1=1055)
    v.regel(1155, z0=2145)
    v.regel(1750)
    v.regel(2355)
    v.regel(2955)
    v.liggande(3000, 3600, 2100)
    v.regel(3277.5, z0=2145)
    v.syll(3600, 4595)
    v.regel(3600)
    v.regel(3855)
    v.liggande(3900, 4595, DAL - 45)
    v.liggande(4242, 4287, DAL, h=41.0769)
    v.regel(4265, z1=DAL - 45)
    v.liggande(4287, 4332, DAL, h=41.0769)
    v.regel(4455, z1=DAL - 45)
    v.regel(4550, z1=DAL - 45)
    return v.montage()
