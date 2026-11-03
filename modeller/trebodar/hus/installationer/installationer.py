"""Installationer: avloppet, som i Onshape-modellen (referensdel), elinstallationen (el/), ventilationen
(ventilation/), tappvattnet (vatten/), golvvärmen (golvvarme/), köldbärarledningarna (kollektor/), brandlarmet
(brandlarm/) och teknikrummets utrustning (teknikrum.py), se deras README. Lägena på husets ytor i montering.py,
genomföringarna i genomforingar.py och stråken i betongen i strak.py, gemensamma för installationerna."""
from __future__ import annotations

from modellering import Del, Montage, Placering

from trebodar.byggdelar.referensdel import importerad
from trebodar.material import INSTALLATION

from . import teknikrum
from .brandlarm import brandlarm
from .el import el
from .golvvarme import golvvarme
from .kollektor import kollektor
from .vatten import vatten
from .ventilation import ventilation


def montage() -> Montage:
    m = Montage("Installationer", beskrivning="Avlopp (ur Onshape-modellen), el, ventilation, tappvatten, golvvärme, "
                                              "köldbärare, brandlarm och teknikrum")
    vvs = Montage("VVS")
    vvs.lagg(Del("Avloppssystem", importerad("avloppssystem.bbrep"), INSTALLATION), Placering(), "Avlopp")
    m.lagg(vvs)
    m.lagg(el.montage())
    m.lagg(ventilation.montage())
    m.lagg(vatten.montage())
    m.lagg(golvvarme.montage())
    m.lagg(kollektor.montage())
    m.lagg(brandlarm.montage())
    m.lagg(teknikrum.montage())
    return m
