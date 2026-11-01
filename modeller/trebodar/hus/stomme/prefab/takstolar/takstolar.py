"""Takstolarna (K-03): gavelstolarna på gavelväggarna och mittstolen på innerväggen 2C. Namn efter väggen."""
from modellering import Montage

from trebodar import skelett as S

from . import t1no, t1sv, t2c, t2no, t2sv, t3no, t3sv

STOLAR = {"1NO": t1no, "1SV": t1sv, "2NO": t2no, "2C": t2c, "2SV": t2sv, "3NO": t3no, "3SV": t3sv}


def montage() -> Montage:
    m = Montage("Takstolar", beskrivning="Takstolar 45×220 C24 med spikplåtar och toppklossar (K-03)")
    for kod, modul in STOLAR.items():
        t = modul.montage()
        m.lagg(t, S.VAGGAR[kod].placering(), t.namn)
    return m
