"""Köldbärarledningarnas geometri ur ledningar.py: skyddsrören Ø110 svepta längs vägen med böjar. Delarna kontrolleras
inte i modellens krockkontroll (kontrollregler.UTOM_KONTROLL); köldbäraren har en egen kontroll
(`./mod kollektor kontroll`, med krockarna mot huset och de andra installationerna).
"""
from __future__ import annotations

from modellering import Del, Montage, Placering, svep

from trebodar.material import SKYDDSROR

from .ledningar import D, ledningar

BOJRADIE = 2.0 * D


def montage() -> Montage:
    m = Montage("Köldbärare", beskrivning="Skyddsrör Ø110 för kollektorslangarna från energibrunnen till teknikrummet "
                                         "(hus/installationer/kollektor)")
    for k in ledningar().values():
        m.lagg(Del(f"Skyddsrör Ø{D:g} för kollektorslang", svep(k.vag, D / 2, BOJRADIE), SKYDDSROR), Placering(), k.id)
    return m
