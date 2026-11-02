"""Installationer: avlopp och golvvärme i källaren, som i Onshape-modellen (referensdelar), och elinstallationen
(el/, se dess README). Ventilationen läggs till här när den projekteras."""
from __future__ import annotations

from modellering import Del, Montage, Placering

from trebodar.byggdelar.referensdel import importerad
from trebodar.material import INSTALLATION

from .el import el


def montage() -> Montage:
    m = Montage("Installationer", beskrivning="VVS (ur Onshape-modellen) och el; ventilation senare")
    vvs = Montage("VVS")
    vvs.lagg(Del("Avloppssystem", importerad("avloppssystem.bbrep"), INSTALLATION), Placering(), "Avlopp")
    vvs.lagg(Del("Golvvärme källare", importerad("varmeslingor-kallare.bbrep"), INSTALLATION), Placering(),
             "Golvvärme källare")
    m.lagg(vvs)
    m.lagg(el.montage())
    return m
