"""Bärande innervägg 1D: vänstra huskroppen, y 11 000, med stolpen LN5_2.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["1D"]): u från (65; 10952.5) i växande x, w genom väggen från stommens ena sida, z uppåt från bjälklagets överkant.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg

NOCK = S.BALKAR["NB5"].uk


def montage() -> Montage:
    v = regelvagg("1D", hojd=NOCK)
    v.syll(0, 1898, w0=12.5, w1=82.5)
    v.regel(1898, z0=0, z1=NOCK)
    v.regel(1943, z0=0, z1=NOCK)
    v.regel(1988, z0=0, z1=NOCK)
    v.regel(2033, z0=0, z1=NOCK)
    return v.montage()
