"""Bärande innervägg 2A: mittre huskroppen, y 2 200, med stolpen LN3_1.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["2A"]): u från (6917; 2152.5) i växande x, w genom väggen från stommens ena sida, z uppåt från bjälklagets överkant.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg

NOCK3 = S.BALKAR["NB3"].uk


def montage() -> Montage:
    v = regelvagg("2A", hojd=NOCK3)
    v.regel(0, z0=0, z1=NOCK3, namn="LN3_1-1")
    v.regel(45, z0=0, z1=NOCK3, namn="LN3_1-2")
    v.regel(90, z0=0, z1=NOCK3, namn="LN3_1-3")
    v.regel(135, z0=0, z1=NOCK3, namn="LN3_1-4")
    v.syll(180, 2453, w0=12.5, w1=82.5)
    return v.montage()
