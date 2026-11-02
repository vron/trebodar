"""Takstol 1SV: gavelstol på väggen 1SV under nockbalk 5 (K-03: Stol 1SV).

Byggd med reglerna i byggdelar/takstol.py. Spikplåtarna vid fötterna som i Onshape-modellen, också plåten på
insidan vid slutet, som sitter 10 mm från underramen.
"""
from modellering import Montage

from trebodar.byggdelar.takstol import takstol


def montage() -> Montage:
    t = takstol("1SV", "NB5")
    t.fotplat(265.0, -1).fotplat(265.0, 1)
    t.spikplat(3505.0, 4105.0, 2490.0, 2590.0, 55.0, False)
    t.fotplat(3505.0, -1)
    return t.montage()
