"""Bärande innervägg 1B: vänstra huskroppen, under nockbalk 5, y 7 115–9 325.

Regelverk 70 mm C24 i väggens system (skelett.VAGGAR["1B"]) upp till nockbalkens underkant: syll och hammarband
brutna där innerväggen 1C går in i 1B, dubbla reglar på båda sidor om den, reglar i ändarna och c/c 600 från dem.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import CC, R

NOCK = S.BALKAR["NB5"].uk


def montage() -> Montage:
    v = regelvagg("1B", hojd=NOCK)
    langd = S.VAGGAR["1B"].langd
    k0 = S.VAGGAR["1C"].origo[1] - S.VAGGAR["1B"].origo[1]        # 1C:s läge längs 1B
    k1 = k0 + S.VAGGAR["1C"].tjocklek
    for a, b in ((0.0, k0), (k1, langd)):
        v.syll(a, b)
        v.hammarband(a, b)
    for u in (0.0, CC, k0 - 2 * R, k0 - R, k1, k1 + R, langd - R - CC, langd - R):
        v.regel(u)
    return v.montage()
