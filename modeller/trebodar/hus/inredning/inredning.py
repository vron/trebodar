"""Inredning som byggs in i huset men hålls isär från husets system, så att den är lätt att visa eller dölja för
sig: garderoben i sovrummet (garderob.py), dubbelsängen där (sang.py), köket (kok.py: kylen, frysen, skåpen och
skafferiet i kökets inbyggnad, vars väggar hör till de invändiga, hus/invandigt/kokets_inbyggnad.py, och bänken och ön,
koksbank.py, med köksskåpen i koksskap.py) och badrummet (badrum.py: bänken, badkaret, WC:n, duschen, skåpet, spegeln
och handdukstorken på lägena i hus/badrum.py). Garderobens väggar byggs som de
lätta innerväggarna (45×70 C24, gips), men deras lägen står bland innerväggarnas (invandigt/lattvaggar.py), så att
installationerna kan monteras på dem.
"""
from __future__ import annotations

from modellering import Montage

from . import badrum, garderob, kok, sang


def montage() -> Montage:
    m = Montage("Inredning", beskrivning="Inbyggd inredning: garderoben och sängen i sovrummet, köket och badrummet")
    m.lagg(garderob.montage())
    m.lagg(sang.montage())
    m.lagg(kok.montage())
    m.lagg(badrum.montage())
    return m
