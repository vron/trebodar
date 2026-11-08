"""Stommen: den bärande konstruktionen ovanför mellanbjälklaget, i två leveranser, och dess förankring i
bjälklaget (betongbultar genom syllarna, #88)."""
from modellering import Montage

from . import forankring
from .nock_och_dalbalkar import nock_och_dalbalkar
from .prefab import prefab


def montage() -> Montage:
    m = Montage("Stomme")
    m.lagg(prefab.montage())
    m.lagg(nock_och_dalbalkar.montage())
    m.lagg(forankring.montage())
    return m
