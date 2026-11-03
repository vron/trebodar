"""Inredning som byggs in i huset men hålls isär från husets system, så att den är lätt att visa eller dölja för
sig: garderoben i sovrummet (garderob.py). Väggarna byggs som de lätta innerväggarna (45×70 C24, gips), men deras
lägen står bland innerväggarnas (invandigt/lattvaggar.py), så att installationerna kan monteras på dem.
"""
from __future__ import annotations

from modellering import Montage

from . import garderob


def montage() -> Montage:
    m = Montage("Inredning", beskrivning="Inbyggd inredning: garderoben i sovrummet")
    m.lagg(garderob.montage())
    return m
