"""Installationer: avloppet (stammen och grundledningarna som i Onshape-modellen, referensdel kapad under
mellanbjälklaget, och badrummets avlopp i avlopp/), elinstallationen (el/), ventilationen (ventilation/), tappvattnet
(vatten/), golvvärmen (golvvarme/), köldbärarledningarna (kollektor/), brandlarmet (brandlarm/), dräneringen och
dagvattnet (dranering/) och teknikrummets utrustning (teknikrum.py), se deras README. Lägena på husets ytor i
montering.py, genomföringarna i genomforingar.py och stråken i betongen i strak.py, gemensamma för installationerna."""
from __future__ import annotations

from modellering import Del, Kapad, Montage, Placering

from trebodar.byggdelar.referensdel import importerad
from trebodar.material import INSTALLATION

from . import teknikrum
from .avlopp import avlopp
from .avlopp.ledningar import Z_STAM
from .brandlarm import brandlarm
from .dranering import dranering
from .el import el
from .golvvarme import golvvarme
from .kollektor import kollektor
from .vatten import vatten
from .ventilation import ventilation


def montage() -> Montage:
    m = Montage("Installationer", beskrivning="Avlopp (stammen och grundledningarna ur Onshape-modellen och "
                                              "badrummets), el, ventilation, tappvatten, golvvärme, köldbärare, "
                                              "brandlarm, dränering och teknikrum")
    vvs = Montage("VVS")
    # stammen och grundledningarna ur Onshape-modellen, kapade under mellanbjälklaget: badrummets avlopp (avlopp/)
    # ansluter till stammens topp (ärende #49: hela avloppet som egen installation)
    stam = Kapad(importerad("avloppssystem.bbrep"), (0.0, 0.0, Z_STAM), (0.0, 0.0, 1.0))
    vvs.lagg(Del("Avloppssystem", stam, INSTALLATION), Placering(), "Avlopp")
    m.lagg(vvs)
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
