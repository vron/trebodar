"""Bärande innervägg 2C: mittre huskroppen, y 5 950, med takstolen 2C.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["2C"]): u från (4417; 5900) i växande x, w genom väggen från stommens ena sida, z uppåt från bjälklagets överkant.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg

DAL = S.BALKAR["DB2"].uk


def montage() -> Montage:
    v = regelvagg("2C", hojd=DAL)
    # dörröppningen börjar vid stolpen LD4_1 (140×140, stolpar.py), som står i väggens början
    v.liggande(128, 1200, 2200)
    v.liggande(128, 1200, 2245)
    v.hammarband(128, 4953)
    v.syll(1200, 1983)
    v.regel(1200)
    v.regel(1938)
    v.liggande(1983, 2993, 2045)
    v.regel(2462.5, z0=2090)
    v.syll(2993, 4953)
    v.regel(2993)
    v.regel(3662.5)
    v.regel(4262.5)
    v.regel(4795)
    v.regel(4840)
    v.regel(4908)
    return v.montage()
