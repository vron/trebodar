"""Installationer: avlopp och golvvärme i källaren, som i Onshape-modellen (referensdelar), elinstallationen (el/),
ventilationen (ventilation/), tappvattnet (vatten/) och teknikrummets utrustning (teknikrum.py), se deras README.
Lägena på husets ytor i montering.py och genomföringarna i genomforingar.py, gemensamma för installationerna."""
from __future__ import annotations

from modellering import Del, Montage, Placering

from trebodar.byggdelar.referensdel import importerad
from trebodar.material import INSTALLATION

from . import teknikrum
from .el import el
from .vatten import vatten
from .ventilation import ventilation


def montage() -> Montage:
    m = Montage("Installationer", beskrivning="VVS (ur Onshape-modellen), el, ventilation, tappvatten och teknikrum")
    vvs = Montage("VVS")
    vvs.lagg(Del("Avloppssystem", importerad("avloppssystem.bbrep"), INSTALLATION), Placering(), "Avlopp")
    vvs.lagg(Del("Golvvärme källare", importerad("varmeslingor-kallare.bbrep"), INSTALLATION), Placering(),
             "Golvvärme källare")
    m.lagg(vvs)
    m.lagg(el.montage())
    m.lagg(ventilation.montage())
    m.lagg(vatten.montage())
    m.lagg(teknikrum.montage())
    return m
