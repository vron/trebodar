"""Bärande innervägg 1A: vänstra huskroppen, y 7 150, från långsidan till nocken.

Regelverk 70 mm C24 i väggens system (skelett.VAGGAR["1A"]): u från (65; 7115) i växande x, w genom väggen från stommens ena sida, z uppåt från bjälklagets överkant.
"""
from modellering import Montage

from trebodar.byggdelar.regelvagg import regelvagg


def montage() -> Montage:
    v = regelvagg("1A", hojd=3628.8234)
    v.syll(0, 1995)
    v.regel(0, z1=2464.0192)
    v.profil([(45, 2464.0192), (622.5, 2797.439), (622.5, 2810.955), (645.9103, 2810.955), (1222.5, 3143.8492), (1222.5, 3157.3652), (1245.9103, 3157.3652), (1950, 3563.8715), (1950, 3576.8619), (1972.5, 3576.8619), (1995, 3589.8523), (1972.5, 3628.8234), (0, 2490), (0, 2464.0192)], typ="H")
    v.liggande(45, 622.5, 2199.5797)
    v.regel(622.5, z1=2810.955)
    v.liggande(667.5, 1222.5, 2199.5797)
    v.regel(1222.5, z1=3157.3652)
    v.liggande(1267.5, 1950, 2199.5797)
    v.regel(1950, z1=3576.8619)
    return v.montage()
