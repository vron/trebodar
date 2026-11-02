"""Takstol 2NO: gavelstol på väggen 2NO under nockbalk 3 (K-03: Stol 2NO).

Byggd med reglerna i byggdelar/takstol.py, med spikreglar på insidan.
"""
from modellering import Montage

from trebodar.byggdelar.takstol import takstol


def montage() -> Montage:
    return takstol("2NO", "NB3", spikreglar=True).montage()
