"""Huset: system i byggordning. Varje grupp är ett eget montage i husets system (K-05:s koordinater)."""
from modellering import Montage

from .fasad import fasad
from .grund import grund
from .installationer import installationer
from .invandigt import invandigt
from .mellanbjalklag import mellanbjalklag
from .fonster_och_dorrar import fonster_och_dorrar
from .isolering import isolering
from .kamin import kamin
from .stomme import stomme
from .tak import tak
from .trappa import trappa


def montage() -> Montage:
    from trebodar.byggdelar.genomforing import genomfor
    m = Montage("Hus")
    m.lagg(grund.montage())
    m.lagg(mellanbjalklag.montage())
    m.lagg(stomme.montage())
    m.lagg(tak.montage())
    m.lagg(fasad.montage())
    m.lagg(fonster_och_dorrar.montage())
    m.lagg(installationer.montage())
    m.lagg(isolering.montage())
    m.lagg(invandigt.montage())
    m.lagg(trappa.montage())
    m.lagg(kamin.montage())
    # skorstenens hål genom taket, isoleringen och innertaket
    hal, lada = kamin.genomforing()
    for i in m.barn:
        if i.namn in ("Tak", "Isolering", "Invändigt") and isinstance(i.barn, Montage):
            genomfor(i.barn, hal, lada, i.placering)
    return m
