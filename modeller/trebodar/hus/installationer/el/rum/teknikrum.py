"""Teknikrummet i källaren (#51): uttagen på V3 mellan centralen och vattenmätaren (gruppen G19, ur centralens
baksida i V3:s cellplast), gruppcentralen (..teknikrum.GRUPPCENTRAL, på V3 väster om vattenmätaren) som punkten
GC, där varje grupps rör börjar på centralens ovansida (bjalklag/mellanbjalklag.py), och värmepumpens fasta
anslutning (TK-D1) på V19 ovanför värmepumpen, med röret från centralens östra ände i källarväggarnas cellplast
bakom gipsen (fräst spår): i V3 och V19 under ventilationens kanal FF3-K2, som går framför V3.
"""
from __future__ import annotations

from ...montering import PLAN, Montering, Vek, kallarvagg
from ...teknikrum import DRIVDONSSKAP as LC, GC_MATT, GRUPPCENTRAL, Z_GC_TOPP
from ..katalog import ANSLUTNING_3FAS, CENTRAL, DRIVDONSSKAP, FXP16, FXP20, UTTAG_2
from ..punkter import Apparat, Dosa, Ror, Rum

RUM = Rum("TK", "Teknikrum", plan=0)
NAMN = RUM.namn

Y_VARMEPUMP = 7700.0            # värmepumpens anslutning på V19, ovanför den
Z_VARMEPUMP = 1950.0
_TOPP = GRUPPCENTRAL.anslutningar["topp"]
_VP = kallarvagg("V19", Y_VARMEPUMP, Z_VARMEPUMP, -1)
_V3_EPS = kallarvagg("V3", 0.0, 0.0, -1).punkt[1] + 63.0      # mitt i V3:s cellplast bakom gipsen
_V19_EPS = _VP.punkt[0] + 63.0

Z_UTTAG = 1100.0                             # uttagen i teknikrummet och tvättstugan, över golvet
X_UTTAG = (3200.0, 3450.0, 3700.0)          # teknikrummets uttag på V3, mellan centralen och vattenmätaren (x 3 850)
PUNKTER = [
    Dosa("GC", CENTRAL, Montering(_TOPP, (0.0, 0.0, 1.0), "central", GRUPPCENTRAL.id)),
    # drivdonsskåpet för källarens ljuslinjer på KL8 mitt emot centralen (rören i rum/kallare.py)
    Dosa("TK-LC", DRIVDONSSKAP, Montering(LC.anslutningar["topp"], (0.0, 0.0, 1.0), "central", LC.id)),
    Apparat("TK-D1", ANSLUTNING_3FAS, _VP),
    *[Apparat(f"TK-U{i + 1}", UTTAG_2, kallarvagg("V3", x, Z_UTTAG, -1)) for i, x in enumerate(X_UTTAG)],
]

_X_UT = _TOPP[0] + GC_MATT[0] / 2 - 20.0     # röret ur centralens ovansida i dess östra ände, mot väggen
_Z = Z_GC_TOPP + 20.0                        # i väggarna strax över centralens överkant, under kanalen FF3-K2
_Z_U = PLAN[0] + Z_UTTAG                     # uttagens höjd: rören i V3:s cellplast i den höjden
_BAK = GRUPPCENTRAL.lage.punkt[1]            # centralens baksida mot väggens gips


def bakifran(x: float, z: float) -> tuple[Vek, ...]:
    """Ett rör ur centralens baksida i x och z, in i V3:s cellplast bakom gipsen."""
    return (x, _BAK, z), (x, _V3_EPS, z)


ROR = [
    # teknikrummets uttag (G19): ur centralens baksida österut i V3:s cellplast i uttagens höjd
    Ror("G19-M", FXP16, "GC", "TK-U1", via=(*bakifran(_TOPP[0] + GC_MATT[0] / 2 - 20.0, _Z_U),
                                            (X_UTTAG[0], _V3_EPS, _Z_U))),
    *[Ror(f"G19-R{i + 1}", FXP16, f"TK-U{i + 1}", f"TK-U{i + 2}",
          via=((a, _V3_EPS, _Z_U), (b, _V3_EPS, _Z_U))) for i, (a, b) in enumerate(zip(X_UTTAG, X_UTTAG[1:]))],
    Ror("G16-R1", FXP20, "GC", "TK-D1",
        via=((_X_UT, _TOPP[1] + 40.0, Z_GC_TOPP), (_X_UT, _TOPP[1] + 40.0, _Z), (_X_UT, _V3_EPS, _Z),
             (_V19_EPS, _V3_EPS, _Z), (_V19_EPS, Y_VARMEPUMP, _Z), (_V19_EPS, Y_VARMEPUMP, _VP.punkt[2]))),
]
