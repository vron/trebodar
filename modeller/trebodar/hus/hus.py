"""Huset: system i byggordning. Varje grupp är ett eget montage i husets system (K-05:s koordinater)."""
from modellering import Montage

from .fasad import fasad
from .fonster_och_dorrar import fonster_och_dorrar
from .isolering import isolering
from .stomme import stomme
from .tak import tak


def montage() -> Montage:
    m = Montage("Hus")
    m.lagg(stomme.montage())
    m.lagg(tak.montage())
    m.lagg(fasad.montage())
    m.lagg(fonster_och_dorrar.montage())
    m.lagg(isolering.montage())
    return m
