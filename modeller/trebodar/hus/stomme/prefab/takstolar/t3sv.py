"""Takstol 3SV: gavelstol på väggen 3SV under nockbalk 1 (K-03: Stol 3SV).

Byggd med reglerna i byggdelar/takstol.py.
"""
from modellering import Montage

from trebodar.byggdelar.takstol import takstol


def montage() -> Montage:
    return takstol("3SV", "NB1").montage()
