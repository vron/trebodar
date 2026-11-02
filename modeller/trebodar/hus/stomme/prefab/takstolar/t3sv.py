"""Takstol 3SV: gavelstol på väggen 3SV under nockbalk 1 (K-03: Stol 3SV).

Byggd med reglerna i byggdelar/takstol.py. Spikplåtarna vid fötterna som i Onshape-modellen.
"""
from modellering import Montage

from trebodar.byggdelar.takstol import takstol


def montage() -> Montage:
    t = takstol("3SV", "NB1")
    t.fotplat(265.0, -1).fotplat(265.0, 1).fotplat(3505.0, 1).fotplat(3505.0, -1)
    return t.montage()
