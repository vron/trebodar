"""Yttervägg 2NO: mittre huskroppens gavel mot NO.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["2NO"]): u från (4470; -30) i växande x, w genom väggen inåt från stommens utsida, z uppåt från bjälklagets överkant.
"""
from modellering import Montage

from trebodar.byggdelar.regelvagg import regelvagg


def montage() -> Montage:
    v = regelvagg("2NO")
    v.syll(0, 4870)
    v.regel(0, namn="LA1-1")
    v.hammarband(0, 4870)
    v.regel(45, b=95, w0=50, w1=95, namn="LA1-2")
    v.regel(600)
    v.liggande(645, 1645, 1055)
    v.liggande(645, 1645, 2100)
    v.regel(1200, z1=1055)
    v.regel(1200, z0=2145)
    v.regel(1645)
    v.regel(2000)
    v.liggande(2045, 3045, 1055)
    v.liggande(2045, 3045, 2100)
    v.regel(2400, z1=1055)
    v.regel(2400, z0=2145)
    v.regel(3045)
    v.regel(3600)
    v.regel(4200)
    v.regel(4730, b=95, w0=50, w1=95, namn="LA2-2")
    v.regel(4825, namn="LA2-1")
    return v.montage()
