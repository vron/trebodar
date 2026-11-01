"""Yttervägg 3SO: högra huskroppens långsida mot SO.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["3SO"]): u från (9470; 12445) i minskande y, w genom väggen inåt från stommens utsida, z uppåt från bjälklagets överkant.
"""
from modellering import Montage

from trebodar.byggdelar.regelvagg import regelvagg


def montage() -> Montage:
    v = regelvagg("3SO", hojd=2488)
    v.syll(0, 172.5)
    v.regel(0)
    v.hammarband(0, 1405)
    v.regel(127.5)
    v.liggande(172.5, 1072.5, 2100)
    v.syll(1072.5, 1405)
    v.regel(1072.5)
    v.regel(1360)
    return v.montage()
