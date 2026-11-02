"""Takstol 1NO: gavelstol på väggen 1NO under nockbalk 5, mot dalbalk 4 i slutet (K-03: Stol 1NO).

Byggd med reglerna i byggdelar/takstol.py.
"""
from modellering import Montage

from trebodar.byggdelar.takstol import takstol


def montage() -> Montage:
    return takstol("1NO", "NB5").montage()
