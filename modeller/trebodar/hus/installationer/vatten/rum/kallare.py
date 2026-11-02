"""Källaren (användarens markeringar): tvättmaskinen och ett tvättho på västra ytterväggen V21, ett tvättho i
källarrummet på V15:s västsida och ett på V7:s norrsida i källarens vänstra del. Rören kommer från stråken i
mellanbjälklaget, ned ur bjälklagets underkant i väggens cellplast bakom gipsen, till väggdosorna.

Tvätthoet på V7 är flyttat till väggen från markeringen 0,8 m norr om den.
"""
from __future__ import annotations

from ...montering import kallarvagg
from ..katalog import ROR_I_ROR_16, TVATTHO, TVATTMASKIN, VAGGDOSA, VAGGDOSA_BLANDARE
from ..punkter import Rum, Tappstalle
from ..teknikrum import Y_S

RUM = Rum("KA", "Källare", plan=0)

TAPPSTALLEN = [
    Tappstalle("KA-TM1", TVATTMASKIN, VAGGDOSA, kallarvagg("V21", 8420.0, 1000.0, sida=1), ROR_I_ROR_16),
    Tappstalle("KA-TH1", TVATTHO, VAGGDOSA_BLANDARE, kallarvagg("V21", 7700.0, 600.0, sida=1), ROR_I_ROR_16),
    Tappstalle("KA-TH2", TVATTHO, VAGGDOSA_BLANDARE, kallarvagg("V15", 8730.0, 600.0, sida=-1), ROR_I_ROR_16),
    Tappstalle("KA-TH3", TVATTHO, VAGGDOSA_BLANDARE, kallarvagg("V7", 3590.0, 600.0, sida=1), ROR_I_ROR_16,
               via=(None, Y_S)),
]
