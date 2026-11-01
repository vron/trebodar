"""Stommen: den bärande konstruktionen ovanför mellanbjälklaget, i två leveranser."""
from modellering import Montage

from .nock_och_dalbalkar import nock_och_dalbalkar
from .prefab import prefab


def montage() -> Montage:
    m = Montage("Stomme")
    m.lagg(prefab.montage())
    m.lagg(nock_och_dalbalkar.montage())
    return m
