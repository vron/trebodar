"""Installationer: avloppet (avlopp/), elinstallationen (el/), ventilationen (ventilation/), tappvattnet
(vatten/), golvvärmen (golvvarme/), köldbärarledningarna (kollektor/), brandlarmet (brandlarm/), dräneringen och
dagvattnet (dranering/) och teknikrummets utrustning (teknikrum.py), se deras README. Lägena på husets ytor i
montering.py, genomföringarna i genomforingar.py och stråken i betongen i strak.py, gemensamma för installationerna."""
from __future__ import annotations

from modellering import Montage

from . import teknikrum
from .avlopp import avlopp
from .brandlarm import brandlarm
from .dranering import dranering
from .el import el
from .golvvarme import golvvarme
from .kollektor import kollektor
from .vatten import vatten
from .ventilation import ventilation


def montage() -> Montage:
    m = Montage("Installationer", beskrivning="Avlopp, el, ventilation, tappvatten, golvvärme, köldbärare, "
                                              "brandlarm, dränering och teknikrum")
    m.lagg(avlopp.montage())
    m.lagg(el.montage())
    m.lagg(ventilation.montage())
    m.lagg(vatten.montage())
    m.lagg(golvvarme.montage())
    m.lagg(kollektor.montage())
    m.lagg(brandlarm.montage())
    m.lagg(dranering.montage())
    m.lagg(teknikrum.montage())
    return m
