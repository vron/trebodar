"""Takstol 3NO: gavelstol på väggen 3NO under nockbalk 1, mot dalbalk 2 i början (K-03: Stol 3NO).

Byggd med reglerna i byggdelar/takstol.py.
"""
from modellering import Montage

from trebodar.byggdelar.takstol import takstol


def montage() -> Montage:
    return takstol("3NO", "NB1").montage()
