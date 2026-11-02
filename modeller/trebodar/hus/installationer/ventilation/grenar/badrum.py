"""Badrummet: badrumsfläkt i gaveln 1NO, högt på väggen mellan fönstret 1NO-F1 och väggen L9, med röret rakt genom
ytterväggen och galler på fasaden.

Fläkten sitter 2 300 mm över golvet (över fönstrens överkant 2 100), mitt i regelfacket öster om fönstret (reglarna
vid u 1 750–1 795 och 2 355–2 400). Fuktstyrd: grundflöde 10 l/s, forcerat 15 l/s.
"""
from __future__ import annotations

from ...montering import utsida, vagg
from ..delar import Avluft, Don, Gren, Kanal
from ..katalog import GALLER_100, VAGGFLAKT_100, VAGGHYLSA_100

U = 2075.0                                  # mitt i regelfacket öster om 1NO-F1
Z = 2300.0

GREN = Gren("FF2", "Badrumsfläkten", "Badrum", VAGGFLAKT_100.flode, (
    Don("FF2-D1", VAGGFLAKT_100, vagg("1NO", U, Z)),
    Kanal("FF2-K1", VAGGHYLSA_100),                              # genom ytterväggen
    Avluft("FF2-A1", GALLER_100, utsida("1NO", U, Z)),
), flode_normal=VAGGFLAKT_100.flode_normal)
