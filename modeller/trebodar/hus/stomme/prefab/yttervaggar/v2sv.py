"""Yttervägg 2SV: mittre huskroppens gavel mot SV.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["2SV"]): u från (9565; 11040) i minskande x, w genom väggen inåt från stommens utsida, z uppåt från bjälklagets överkant.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.material import S235

DAL = S.BALKAR["DB2"].uk


def montage() -> Montage:
    v = regelvagg("2SV", hojd=DAL)
    v.syll(0, 260)
    v.regel(0)
    v.profil([(0, DAL), (0, DAL - 45), (125, DAL - 45), (125, DAL - 27), (625, DAL - 27), (625, DAL - 45), (4695, DAL - 45), (4695, DAL - 27), (5195, DAL - 27), (5195, DAL - 45), (5320, DAL - 45), (5320, DAL)], typ="H")
    v.regel(125, z1=DAL - 43, namn="LD2_4-1")
    v.liggande(125, 625, DAL - 43, h=16, w0=0, w1=90, typ="P", material=S235)
    v.regel(170, z1=DAL - 43, namn="LD2_4-2")
    v.regel(215, z1=DAL - 43, namn="LD2_4-3")
    v.liggande(4695, 5195, DAL - 43, h=16, w0=0, w1=90, typ="P", material=S235)
    v.syll(5060, 5320)
    # stolpen LD4_2 under dalbalk 4:s ände: 4 reglar sida vid sida (K-03)
    v.regel(5060, z1=DAL - 43, namn="LD4_2-1")
    v.regel(5105, z1=DAL - 43, namn="LD4_2-2")
    v.regel(5150, z1=DAL - 43, namn="LD4_2-3")
    v.regel(5195, namn="LD4_2-4")
    v.regel(5240)
    return v.montage()
