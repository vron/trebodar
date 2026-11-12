"""Bärande innervägg 1A: vänstra huskroppen, y 7 150, från långsidan 1SO till nockbalk 5.

Regelverk 70 mm C24 i väggens system (skelett.VAGGAR["1A"]), byggt med reglerna i regelstomme.py: syll, ett lutande
hammarband under takfallet 1SO, vinkelrätt kapat vid nockbalken, reglar upp till sätena i hammarbandet och
kortlingar mellan reglarna.

Ovanpå hammarbandet ligger en regel 45×95 (H02) längs hela lutningen, som går ut över springan till takbalken 1SO-T07
och ligger an mot dess sida. Den skruvas i hammarbandet och i takbalken, så att takfallets kraft i x (K-04, #110) går
från takbalken rakt in i väggen och inte tvärs genom långsidans hammarband 1SO-H03.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar import polygon as P
from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import (KORTLING_Z, LODRAT, VINKELRAT, R, hammarbandsplan,
                                                    lutande_hammarband)
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT

TAKBALK = "1SO"                  # takfallet vars takbalk ligger intill väggen
H2_B = 95.0                      # den övre regeln: bredd (w) och höjd (vinkelrätt mot lutningen R)
H2_SLUT = 100.0                  # slutar så långt före hammarbandets slut vid nockbalken (längs u)


def montage() -> Montage:
    v = regelvagg("1A")
    langd = S.VAGGAR["1A"].langd
    v.syll(0.0, langd)
    hb, toppar = lutande_hammarband(hammarbandsplan("1A", "1SO"), (0.0, LODRAT), (langd, VINKELRAT),
                                    (0.0, 622.5, 1222.5, 1950.0))
    v.profil(P.hornen(hb), typ="H")
    for u, z in toppar.items():
        v.regel(u, z1=z)
    reglar = sorted(toppar)
    for a, b in zip(reglar, reglar[1:]):
        v.liggande(a + R, b, KORTLING_Z)
    # den övre regeln: från väggens början till H2_SLUT före slutet, vinkelrätt kapad, fram till takbalkens sida
    w = S.VAGGAR["1A"]
    tb = max((y for y in FALT[TAKBALK].y if y + S.TAKBALK_B <= w.origo[1] + 1e-6), default=None)
    assert tb is not None and w.origo[1] - (tb + S.TAKBALK_B) < H2_B - w.tjocklek, "ingen takbalk intill 1A"
    w0 = tb + S.TAKBALK_B - w.origo[1]                    # takbalkens sida (negativt: på andra sidan väggens yta)
    ok = hammarbandsplan("1A", "1SO")
    k = (ok(1000.0) - ok(0.0)) / 1000.0
    c = 1.0 / (1.0 + k * k) ** 0.5
    u1 = langd - H2_SLUT
    h2 = [(0.0, ok(0.0)), (u1, ok(u1)), (u1 - R * k * c, ok(u1) + R * c), (0.0, ok(0.0) + R / c)]
    v.profil(h2, w0, w0 + H2_B, typ="H", namn="1A-H02")
    return v.montage()
