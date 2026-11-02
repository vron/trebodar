"""Takstol 3NO: gavelstol på väggen 3NO under nockbalk 1, mot dalbalk 2 i början (K-03: Stol 3NO).

Byggd med reglerna i byggdelar/takstol.py. Spikplåtarna vid fötterna som i Onshape-modellen.
"""
from modellering import Montage

from trebodar.byggdelar.takstol import takstol


def montage() -> Montage:
    t = takstol("3NO", "NB1")
    t.fotplat(436.5, 1).fotplat(436.5, -1).fotplat(3730.0, 1).fotplat(3730.0, -1)
    return t.montage()
