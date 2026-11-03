"""Huset: system i byggordning. Varje grupp är ett eget montage i husets system (K-05:s koordinater)."""
from modellering import Montage

from trebodar.byggdelar.genomforing import genomfor, genomfor_alla

from .armering import armering
from .fasad import fasad
from .fonster_och_dorrar import fonster_och_dorrar
from .grund import grund
from .inredning import inredning
from .installationer import installationer
from .installationer.el.installation import haltagningar
from .invandigt import invandigt
from .isolering import isolering
from .kamin import kamin
from .mellanbjalklag import mellanbjalklag
from .stomme import stomme
from .tak import tak
from .trappa import trappa


def montage() -> Montage:
    m = Montage("Hus")
    m.lagg(grund.montage())
    m.lagg(mellanbjalklag.montage())
    m.lagg(armering.montage())
    m.lagg(stomme.montage())
    m.lagg(tak.montage())
    m.lagg(fasad.montage())
    m.lagg(fonster_och_dorrar.montage())
    m.lagg(installationer.montage())
    m.lagg(isolering.montage())
    m.lagg(invandigt.montage())
    m.lagg(inredning.montage())
    m.lagg(trappa.montage())
    m.lagg(kamin.montage())
    # skorstenens och förbränningsluftens hål genom taket, isoleringen och innertaket
    for (hal, lada), montage in ((kamin.genomforing(), ("Tak", "Isolering", "Invändigt")),
                                 (kamin.luftkanalens_hal(), ("Tak", "Isolering", "Invändigt"))):
        for i in m.barn:
            if i.namn in montage and isinstance(i.barn, Montage):
                genomfor(i.barn, hal, lada, i.placering)
    # de infällda armaturernas håltagning i innertaket
    for i in m.barn:
        if i.namn == "Invändigt" and isinstance(i.barn, Montage):
            genomfor_alla(i.barn, haltagningar(), i.placering)
    return m
