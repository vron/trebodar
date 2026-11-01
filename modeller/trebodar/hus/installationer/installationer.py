"""Installationer: avlopp och golvvärme i källaren, som i Onshape-modellen (referensdelar). El och ventilation
läggs till här när de projekteras."""
from __future__ import annotations

from modellering import Del, Montage, Placering

from trebodar.byggdelar.referensdel import importerad
from trebodar.material import INSTALLATION


def montage() -> Montage:
    m = Montage("Installationer", beskrivning="VVS (ur Onshape-modellen); el och ventilation senare")
    vvs = Montage("VVS")
    vvs.lagg(Del("Avloppssystem", importerad("avloppssystem.bbrep"), INSTALLATION), Placering(), "Avlopp")
    vvs.lagg(Del("Golvvärme källare", importerad("varmeslingor-kallare.bbrep"), INSTALLATION), Placering(),
             "Golvvärme källare")
    m.lagg(vvs)
    return m
