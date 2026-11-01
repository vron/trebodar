"""Nock- och dalbalkarna NB1, DB2, NB3, DB4 och NB5 (K-01): en egen beställning, skild från prefabstommen."""
from modellering import Montage

from trebodar import skelett as S

from . import kompositbalk


def montage() -> Montage:
    m = Montage("Nock- och dalbalkar", beskrivning="Limträ GL30c 190×180 med stålplåtar 190×10 S355 (K-01)")
    for kod in ("NB1", "DB2", "NB3", "DB4", "NB5"):
        m.lagg(kompositbalk.montage(kod), kompositbalk.placering(S.BALKAR[kod]))
    return m
