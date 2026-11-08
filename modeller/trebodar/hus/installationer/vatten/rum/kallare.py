"""Källaren (användarens markeringar): tvättmaskinen och ett tvättho på västra ytterväggen V21, ett tvättho i
källarrummet på V15:s västsida och ett på V7:s södersida i källarens vänstra del. Rören kommer från stråken i
mellanbjälklaget, ned ur bjälklagets underkant i väggens cellplast bakom gipsen, till väggdosorna.

Källarrummets rör viker av söderut från stråket O var för sig (varmt först) till V15. Tvätthoet på V7 är flyttat till
väggen från markeringen 0,8 m söder om den.
"""
from __future__ import annotations

from ...montering import i_vaggen, kallarvagg
from ..katalog import ROR_I_ROR_16, TVATTHO, TVATTMASKIN, VAGGDOSA, VAGGDOSA_BLANDARE
from ..punkter import FIL, Rum, Tappstalle

RUM = Rum("KA", "Källare", plan=0)

_V15 = i_vaggen(kallarvagg("V15", 0.0, 0.0, -1), (0.0, 0.0, 0.0))[0]     # V15:s cellplast i källarrummet (x)

TAPPSTALLEN = [
    Tappstalle("KA-TM1", TVATTMASKIN, VAGGDOSA, kallarvagg("V21", 8420.0, 1000.0, sida=1), ROR_I_ROR_16),
    Tappstalle("KA-TH1", TVATTHO, VAGGDOSA_BLANDARE, kallarvagg("V21", 7700.0, 600.0, sida=1), ROR_I_ROR_16),
    Tappstalle("KA-TH2", TVATTHO, VAGGDOSA_BLANDARE, kallarvagg("V15", 8730.0, 600.0, sida=-1), ROR_I_ROR_16,
               via={"VV": (_V15 - 2 * FIL, None), "KV": (_V15 - FIL, None)}),
    Tappstalle("KA-TH3", TVATTHO, VAGGDOSA_BLANDARE, kallarvagg("V7", 3590.0, 600.0, sida=1), ROR_I_ROR_16),
]
