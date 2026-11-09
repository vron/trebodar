"""Bärande innervägg 1B: vänstra huskroppen, under nockbalk 5, y 7 115–9 325.

Regelverk 70 mm C24 i väggens system (skelett.VAGGAR["1B"]) upp till nockbalkens underkant: stolparna LN5_1 och LN5_3
(två reglar var till balkens underkant, K-03) i väggens ändar, där de bildar hörn med 1A och den lätta väggen L20,
som stagar dem ut ur väggens plan; LN5_1 står på plattan och syllen börjar intill den. Hammarbandet mellan
stolparna, syll och hammarband brutna där innerväggen 1C går in i 1B, dubbla reglar på båda sidor om den och reglar
c/c 600 från väggens ändar.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import CC, R, stolpe

NOCK = S.BALKAR["NB5"].uk


def montage() -> Montage:
    v = regelvagg("1B", hojd=NOCK)
    langd = S.VAGGAR["1B"].langd
    k0 = S.VAGGAR["1C"].origo[1] - S.VAGGAR["1B"].origo[1]        # 1C:s läge längs 1B
    k1 = k0 + S.VAGGAR["1C"].tjocklek
    stolpe(v, "LN5_1", 0.0, 2, z0=0.0, z1=NOCK)                  # på plattan (K-03: syllen räcker inte)
    stolpe(v, "LN5_3", langd - 2 * R, 2, z1=NOCK)
    v.syll(2 * R, k0)
    v.syll(k1, langd)
    v.hammarband(2 * R, k0)
    v.hammarband(k1, langd - 2 * R)
    for u in (CC, k0 - 2 * R, k0 - R, k1, k1 + R, langd - R - CC):
        v.regel(u)
    return v.montage()
