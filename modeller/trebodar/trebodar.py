"""Fritidshus Trebodar, Resö, Tanum: huset med mark. Modellens rot.

Koordinater som i K-05 (mm): x och y från skärningen mellan mellanbjälklagets kanter, z från bjälklagets överkant.
"""
from modellering import Montage

from .hus import hus


def montage() -> Montage:
    m = Montage("Trebodar", beskrivning="Fritidshus Trebodar, Resö, Tanum")
    m.lagg(hus.montage())
    return m
