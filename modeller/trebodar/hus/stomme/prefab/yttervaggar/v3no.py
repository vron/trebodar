"""Yttervägg 3NO: högra huskroppens gavel mot NO. Hammarbandet och regelstyckena intill dalbalk 2:s ände går fram
till balkens sida (Onshape-modellen hade 8 mm spel, för HEA 200).

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["3NO"]): u från (9245; 970) i växande x, w genom väggen inåt från stommens utsida, z uppåt från bjälklagets överkant.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg

DAL = S.BALKAR["DB2"].uk


def montage() -> Montage:
    v = regelvagg("3NO")
    v.syll(0, 995)
    v.regel(0, z1=DAL - 45)
    v.liggande(0, 695, DAL - 45)
    v.regel(95, z1=DAL - 45, namn="LA3")
    v.liggande(255, 300, DAL, h=41.0769)
    v.hammarband(255, 4595)
    v.regel(285, z1=DAL - 45)
    v.liggande(300, 345, DAL, h=41.0769)
    v.regel(695)
    v.regel(950)
    v.liggande(995, 1595, 2100)
    v.regel(1272.5, z0=2145)
    v.syll(1595, 4595)
    v.regel(1595)
    v.regel(2195)
    v.regel(2800)
    v.liggande(2845, 3845, 1055)
    v.liggande(2845, 3845, 2100)
    v.regel(3395, z1=1055)
    v.regel(3395, z0=2145)
    v.regel(3845)
    v.regel(4455, b=95, w0=50, w1=95, namn="LA4-2")
    v.regel(4550, namn="LA4-1")
    return v.montage()
