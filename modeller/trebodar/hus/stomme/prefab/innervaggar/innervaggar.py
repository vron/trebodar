"""Bärande innerväggar: kroppens nummer och en bokstav i växande y (1A–1D, 2A–2C)."""
from modellering import Montage

from trebodar import skelett as S

from . import syllar, v1a, v1b, v1c, v1d, v2a, v2b, v2c

VAGGAR = {"1A": v1a, "1B": v1b, "1C": v1c, "1D": v1d, "2A": v2a, "2B": v2b, "2C": v2c}


def montage() -> Montage:
    m = Montage("Innerväggar", beskrivning="Bärande innerväggar, regelverk C24")
    for kod, modul in VAGGAR.items():
        v = modul.montage()
        m.lagg(v, S.VAGGAR[kod].placering(), v.namn)
    m.lagg(syllar.montage())
    return m
