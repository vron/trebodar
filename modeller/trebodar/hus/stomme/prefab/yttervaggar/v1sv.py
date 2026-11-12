"""Yttervägg 1SV: vänstra huskroppens gavel mot SV.

Regelverk 145 mm C24 (45×145, utan installationsskikt) i väggens system (skelett.VAGGAR["1SV"]), byggt med
reglerna i regelstomme.py: plattor, hörnstolpar, öppningarna (karmreglar, överstycken, bröstningar, kortlingar) och
fria reglar.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import DUBBELT, Karm, hornstolpe, vagg


def montage() -> Montage:
    v = regelvagg("1SV")
    hornen = hornstolpe(v, 0.0, 1, ("LA10-1", "LA10-2")) + hornstolpe(v, S.VAGGAR["1SV"].langd, -1, ("LA9-1", "LA9-2"))
    vagg(v, "1SV", ander=(False, False), staende=hornen, reglar=(600.0, 3725.0),
         karmar={"F1": Karm(dubbel=True, overstycke=DUBBELT)})
    return v.montage()
