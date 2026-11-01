"""Bärande innervägg 1B: vänstra huskroppen, under nockbalk 5, y 7 115–9 325.

Regelverk 70 mm C24 i väggens system (skelett.VAGGAR["1B"]): u från (2130; 7115) i växande y, w genom väggen från stommens ena sida, z uppåt från bjälklagets överkant.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg

NOCK = S.BALKAR["NB5"].uk


def montage() -> Montage:
    v = regelvagg("1B", hojd=NOCK)
    v.syll(0, 1070)
    v.regel(0)
    v.hammarband(0, 1070)
    v.regel(600)
    v.regel(980)
    v.regel(1025)
    v.syll(1140, 2210)
    v.regel(1140)
    v.hammarband(1140, 2210)
    v.regel(1185)
    v.regel(1565)
    v.regel(2165)
    return v.montage()
