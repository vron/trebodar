"""Teknikrummet i källaren (#51): gruppcentralen (..teknikrum.GRUPPCENTRAL, på V3 väster om vattenmätaren) som punkten
GC, där varje grupps rör börjar på centralens ovansida (bjalklag/mellanbjalklag.py), och värmepumpens fasta
anslutning (TK-D1) på V19 ovanför värmepumpen, med röret från centralens östra ände i källarväggarnas cellplast
bakom gipsen (fräst spår): i V3 och V19 under ventilationens kanal FF3-K2, som går framför V3.
"""
from __future__ import annotations

from ...montering import Montering, kallarvagg
from ...teknikrum import GC_MATT, GRUPPCENTRAL, Z_GC_TOPP
from ..katalog import ANSLUTNING_3FAS, CENTRAL, FXP20
from ..punkter import Apparat, Dosa, Ror, Rum

RUM = Rum("TK", "Teknikrum", plan=0)
NAMN = RUM.namn

Y_VARMEPUMP = 7700.0            # värmepumpens anslutning på V19, ovanför den
Z_VARMEPUMP = 1950.0
_TOPP = GRUPPCENTRAL.anslutningar["topp"]
_VP = kallarvagg("V19", Y_VARMEPUMP, Z_VARMEPUMP, -1)
_V3_EPS = kallarvagg("V3", 0.0, 0.0, -1).punkt[1] + 63.0      # mitt i V3:s cellplast bakom gipsen
_V19_EPS = _VP.punkt[0] + 63.0

PUNKTER = [
    Dosa("GC", CENTRAL, Montering(_TOPP, (0.0, 0.0, 1.0), "central", GRUPPCENTRAL.id)),
    Apparat("TK-D1", ANSLUTNING_3FAS, _VP),
]

_X_UT = _TOPP[0] + GC_MATT[0] / 2 - 20.0     # röret ur centralens ovansida i dess östra ände, mot väggen
_Z = Z_GC_TOPP + 20.0                        # i väggarna strax över centralens överkant, under kanalen FF3-K2
ROR = [
    Ror("G16-R1", FXP20, "GC", "TK-D1",
        via=((_X_UT, _TOPP[1] + 40.0, Z_GC_TOPP), (_X_UT, _TOPP[1] + 40.0, _Z), (_X_UT, _V3_EPS, _Z),
             (_V19_EPS, _V3_EPS, _Z), (_V19_EPS, Y_VARMEPUMP, _Z), (_V19_EPS, Y_VARMEPUMP, _VP.punkt[2]))),
]
