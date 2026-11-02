"""Takstol 1SV: gavelstol på väggen 1SV under nockbalk 5 (K-03: Stol 1SV).

Byggd med reglerna i byggdelar/takstol.py. Spikplåtarna vid fötterna som i Onshape-modellen.
"""
from modellering import Montage

from trebodar.byggdelar.takstol import takstol


def montage() -> Montage:
    t = takstol("1SV", "NB5")
    t.fotplat(265.0, -1).fotplat(265.0, 1)
    t.fotplat(3505.0, 1)
    t.fotplat(3505.0, -1)
    return t.montage()
