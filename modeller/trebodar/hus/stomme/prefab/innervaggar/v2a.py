"""Bärande innervägg 2A: mittre huskroppen, y 2 200, med stolpen LN3_1.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["2A"]): stolpen LN3_1 i väggens början (fyra reglar från
bjälklaget till nockbalk 3:s underkant, K-03) och en syll 70 mitt i väggen efter den.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import R, stolpe

NOCK3 = S.BALKAR["NB3"].uk


def montage() -> Montage:
    v = regelvagg("2A", hojd=NOCK3)
    stolpe(v, "LN3_1", 0.0, 4, z0=0.0, z1=NOCK3)
    v.syll(4 * R, S.VAGGAR["2A"].langd, w0=12.5, w1=82.5)
    return v.montage()
