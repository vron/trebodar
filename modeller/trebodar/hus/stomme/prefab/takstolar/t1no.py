"""Takstol 1NO: gavelstol på väggen 1NO under nockbalk 5, mot dalbalk 4 i slutet (K-03: Stol 1NO).

Byggd med reglerna i byggdelar/takstol.py. Spikplåtarna vid fötterna som i Onshape-modellen.
"""
from modellering import Montage

from trebodar.byggdelar.takstol import takstol


def montage() -> Montage:
    t = takstol("1NO", "NB5")
    t.fotplat(265.0, 1).fotplat(265.0, -1).fotplat(3558.5, 1).fotplat(3558.5, -1)
    return t.montage()
