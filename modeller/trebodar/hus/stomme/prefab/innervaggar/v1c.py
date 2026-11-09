"""Bärande innervägg 1C: vänstra huskroppen, y 8 220, från 1B under nockbalk 5.

Regelverk 70 mm C24 i väggens system (skelett.VAGGAR["1C"]), byggt med reglerna i regelstomme.py: syll, en regel vid
1B:s yta och ändregeln under nockbalk 5 (båda till balkens underkant; nockbalken bärs av stolparna LN5_1 och LN5_3 i
1B:s hörn), ett lutande hammarband under takfallet 1NV från ändregeln till väggens slut, reglar upp till sätena i
hammarbandet och en kortling. Hammarbandets ände är vinkelrät mot lutningen och går 11,25 in i ändregeln, som har ett
urtag för den.
"""
from shapely.geometry import box

from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar import polygon as P
from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import (KORTLING_Z, LODRAT, VINKELRAT, R, hammarbandsplan,
                                                    lutande_hammarband)

NOCK = S.BALKAR["NB5"].uk
INNE = 11.25                 # hammarbandets ände in i ändregeln


def montage() -> Montage:
    v = regelvagg("1C", hojd=NOCK)
    w = S.VAGGAR["1C"]
    v.syll(0.0, w.langd)
    u1 = S.BALKAR["NB5"].x - w.origo[0] + 2 * R                    # ändregelns sida mot väggens slut
    hb, toppar = lutande_hammarband(hammarbandsplan("1C", "1NV"), (u1 - INNE, VINKELRAT), (w.langd, LODRAT),
                                    (427.5, 1027.5, 1240.0))
    v.regel(S.VAGGAR["1B"].tjocklek, z1=NOCK)                      # vid 1B:s yta
    v.profil(P.hornen(box(u1 - R, R, u1, NOCK).difference(hb)))
    v.profil(P.hornen(hb), typ="L")
    v.liggande(u1, min(toppar), KORTLING_Z)
    for u, z in toppar.items():
        v.regel(u, z1=z)
    return v.montage()
