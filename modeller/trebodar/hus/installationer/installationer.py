"""Installationer: avlopp och golvvärme i källaren, som i Onshape-modellen (referensdelar), elinstallationen (el/)
och ventilationen (ventilation/), se deras README. Lägena på husets ytor för el och ventilation i montering.py."""
from __future__ import annotations

from modellering import Del, Montage, Placering

from trebodar.byggdelar.referensdel import importerad
from trebodar.material import INSTALLATION

from .el import el
from .ventilation import ventilation


def montage() -> Montage:
    m = Montage("Installationer", beskrivning="VVS (ur Onshape-modellen), el och ventilation")
    vvs = Montage("VVS")
    vvs.lagg(Del("Avloppssystem", importerad("avloppssystem.bbrep"), INSTALLATION), Placering(), "Avlopp")
    vvs.lagg(Del("Golvvärme källare", importerad("varmeslingor-kallare.bbrep"), INSTALLATION), Placering(),
             "Golvvärme källare")
    m.lagg(vvs)
    m.lagg(el.montage())
    m.lagg(ventilation.montage())
    return m
