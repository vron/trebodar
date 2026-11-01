"""Huset: system i byggordning. Varje grupp är ett eget montage i husets system (K-05:s koordinater)."""
from modellering import Montage

from .stomme import stomme


def montage() -> Montage:
    m = Montage("Hus")
    m.lagg(stomme.montage())
    return m
