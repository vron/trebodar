"""Inredning som byggs in i huset men hålls isär från husets system, så att den är lätt att visa eller dölja för
sig: garderoben i sovrummet (garderob.py) och köket (kok.py: kylen, frysen, skåpen och skafferiet i kökets
inbyggnad, vars väggar hör till de invändiga, hus/invandigt/kokets_inbyggnad.py). Garderobens väggar byggs som de
lätta innerväggarna (45×70 C24, gips), men deras lägen står bland innerväggarnas (invandigt/lattvaggar.py), så att
installationerna kan monteras på dem.
"""
from __future__ import annotations

from modellering import Montage

from . import garderob, kok


def montage() -> Montage:
    m = Montage("Inredning", beskrivning="Inbyggd inredning: garderoben i sovrummet, kylen, frysen och skafferiet")
    m.lagg(garderob.montage())
    m.lagg(kok.montage())
    return m
