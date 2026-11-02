"""Takstol 1SV: gavelstol på väggen 1SV under nockbalk 5 (K-03: Stol 1SV).

Byggd med reglerna i byggdelar/takstol.py.
"""
from modellering import Montage

from trebodar.byggdelar.takstol import takstol


def montage() -> Montage:
    return takstol("1SV", "NB5").montage()
