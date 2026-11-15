"""Källaren (användarens markeringar): tvättmaskinen och ett tvättho på västra ytterväggen V21, ett tvättho i
källarrummet på V15:s västsida och ett på V7:s södersida i källarens vänstra del. Rören kommer från stråken i
mellanbjälklaget, ned ur bjälklagets underkant i väggens cellplast bakom gipsen, till väggdosorna.

Källarrummets tvättho (KA-TH2) har bara kallvatten (#139): röret kommer under bottenplattan direkt från vattenmätaren
under köket och upp i V15:s cellplast (teknikrum.DIREKT). Tvätthoet på V7 är flyttat till väggen från markeringen
0,8 m söder om den.
"""
from __future__ import annotations

from ...montering import kallarvagg
from ..katalog import PEM_20, ROR_I_ROR_16, TVATTHO, TVATTHO_KALLT, TVATTMASKIN, VAGGDOSA, VAGGDOSA_BLANDARE
from ..punkter import Rum, Tappstalle

RUM = Rum("KA", "Källare", plan=0)

TAPPSTALLEN = [
    Tappstalle("KA-TM1", TVATTMASKIN, VAGGDOSA, kallarvagg("V21", 8420.0, 1000.0, sida=1), ROR_I_ROR_16),
    Tappstalle("KA-TH1", TVATTHO, VAGGDOSA_BLANDARE, kallarvagg("V21", 7700.0, 600.0, sida=1), ROR_I_ROR_16),
    Tappstalle("KA-TH2", TVATTHO_KALLT, VAGGDOSA, kallarvagg("V15", 8730.0, 600.0, sida=-1), PEM_20),
    Tappstalle("KA-TH3", TVATTHO, VAGGDOSA_BLANDARE, kallarvagg("V7", 3590.0, 600.0, sida=1), ROR_I_ROR_16),
]
