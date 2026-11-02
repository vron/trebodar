"""Bärande innervägg 1C: vänstra huskroppen, y 8 220, med stolpen LN5_1.

Regelverk 70 mm C24 i väggens system (skelett.VAGGAR["1C"]), byggt med reglerna i regelstomme.py: syll, stolpen
LN5_1 mitt under nockbalk 5 (fyra reglar till balkens underkant, K-03), ett lutande hammarband under takfallet 1NV
från stolpen till väggens slut, reglar upp till sätena i hammarbandet och en kortling. Hammarbandets ände är
vinkelrät mot lutningen och går 11,25 in i stolpens sista regel, som har ett urtag för den.
"""
from shapely.geometry import box

from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar import polygon as P
from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import (KORTLING_Z, LODRAT, VINKELRAT, R, hammarbandsplan,
                                                    lutande_hammarband, stolpe)

NOCK = S.BALKAR["NB5"].uk
INNE = 11.25                 # hammarbandets ände in i stolpen


def montage() -> Montage:
    v = regelvagg("1C", hojd=NOCK)
    w = S.VAGGAR["1C"]
    v.syll(0.0, w.langd)
    u0 = S.BALKAR["NB5"].x - w.origo[0] - 2 * R                    # stolpen LN5_1 mitt under nockbalken
    u1 = u0 + 4 * R
    hb, toppar = lutande_hammarband(hammarbandsplan("1C", "1NV"), (u1 - INNE, VINKELRAT), (w.langd, LODRAT),
                                    (427.5, 1027.5, 1240.0))
    stolpe(v, "LN5_1", u0, 3, z1=NOCK)
    v.profil(P.hornen(box(u1 - R, R, u1, NOCK).difference(hb)), namn="LN5_1-4")
    v.profil(P.hornen(hb), typ="L")
    v.liggande(u1, min(toppar), KORTLING_Z)
    for u, z in toppar.items():
        v.regel(u, z1=z)
    return v.montage()
