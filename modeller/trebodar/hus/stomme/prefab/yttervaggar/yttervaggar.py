"""Ytterväggarnas regelverk: en grupp per vägg, med väggarnas koder (kropp och väderstreck)."""
from modellering import Montage

from trebodar import skelett as S

from . import v1no, v1nv, v1so, v1sv, v2no, v2nv, v2so, v2sv, v3no, v3nv, v3so, v3sv

VAGGAR = {"1NO": v1no, "1SO": v1so, "1SV": v1sv, "1NV": v1nv, "2NO": v2no, "2SO": v2so, "2SV": v2sv, "2NV": v2nv,
          "3NO": v3no, "3SO": v3so, "3SV": v3sv, "3NV": v3nv}


def montage() -> Montage:
    m = Montage("Ytterväggar", beskrivning="Regelverk 45×95 C24 c/c 600")
    for kod, modul in VAGGAR.items():
        v = modul.montage()
        m.lagg(v, S.VAGGAR[kod].placering(), v.namn)
    return m
