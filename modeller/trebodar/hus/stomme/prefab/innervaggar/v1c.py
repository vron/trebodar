"""Bärande innervägg 1C: vänstra huskroppen, y 8 220, med stolpen LN5_1.

Regelverk 70 mm C24 i väggens system (skelett.VAGGAR["1C"]): u från (2060; 8185) i växande x, w genom väggen från stommens ena sida, z uppåt från bjälklagets överkant.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg

NOCK = S.BALKAR["NB5"].uk


def montage() -> Montage:
    v = regelvagg("1C", hojd=NOCK)
    v.syll(0, 1285)
    v.profil([(5, 3593.2646), (16.25, 3599.7598), (5, 3619.2454), (5, NOCK), (50, NOCK), (50, 45), (5, 45)], namn="LN5_1-1")
    v.regel(50, z1=NOCK, namn="LN5_1-2")
    v.regel(95, z1=NOCK, namn="LN5_1-3")
    v.profil([(140, NOCK), (185, NOCK), (185, 3619.2454), (173.75, 3599.7598), (185, 3593.2646), (185, 45), (140, 45)], namn="LN5_1-4")
    v.profil([(1285, 2984.1601), (1285, 3010.1408), (196.25, 3638.7309), (173.75, 3599.7598), (450, 3440.2668), (472.5, 3440.2668), (472.5, 3427.2764), (1050, 3093.8566), (1072.5, 3093.8566), (1072.5, 3080.8662), (1240, 2984.1601)], typ="L")
    v.liggande(185, 427.5, 2199.5797)
    v.regel(427.5, z1=3440.2668)
    v.regel(1027.5, z1=3093.8566)
    v.regel(1240, z1=2984.1601)
    return v.montage()
