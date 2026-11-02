"""Bärande innervägg 1A: vänstra huskroppen, y 7 150, från långsidan 1SO till nockbalk 5.

Regelverk 70 mm C24 i väggens system (skelett.VAGGAR["1A"]), byggt med reglerna i regelstomme.py: syll, ett lutande
hammarband under takfallet 1SO, vinkelrätt kapat vid nockbalken, reglar upp till sätena i hammarbandet och
kortlingar mellan reglarna. Sätena är 22,5 breda; vid väggens början hela regelns bredd och på de två mittre reglarna
23,4 (som i Onshape-modellen).
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar import polygon as P
from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import (KORTLING_Z, LODRAT, VINKELRAT, R, hammarbandsplan,
                                                    lutande_hammarband)


def montage() -> Montage:
    v = regelvagg("1A")
    langd = S.VAGGAR["1A"].langd
    v.syll(0.0, langd)
    hb, toppar = lutande_hammarband(hammarbandsplan("1A", "1SO"), (0.0, LODRAT), (langd, VINKELRAT),
                                    {0.0: R, 622.5: 23.4103, 1222.5: 23.4103, 1950.0: 22.5})
    v.profil(P.hornen(hb), typ="H")
    for u, z in toppar.items():
        v.regel(u, z1=z)
    reglar = sorted(toppar)
    for a, b in zip(reglar, reglar[1:]):
        v.liggande(a + R, b, KORTLING_Z)
    return v.montage()
