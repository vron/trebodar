"""Bärande innervägg 1D: vänstra huskroppen, y 11 000, med stolpen LN5_2.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["1D"]): stolpen LN5_2 i väggens slut (fyra reglar från
bjälklaget till nockbalk 5:s underkant, K-03) och en syll 70 mitt i väggen fram till den.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import R, stolpe

NOCK = S.BALKAR["NB5"].uk


def montage() -> Montage:
    v = regelvagg("1D", hojd=NOCK)
    u = S.VAGGAR["1D"].langd - 4 * R
    v.syll(0.0, u, w0=12.5, w1=82.5)
    stolpe(v, "LN5_2", u, 4, z0=0.0, z1=NOCK)
    return v.montage()
