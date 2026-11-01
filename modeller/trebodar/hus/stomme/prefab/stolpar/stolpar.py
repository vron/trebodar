"""Fristående stolpar under nock- och dalbalkarna (K-03). Stolpar som står i en vägg ingår i väggen.

LN1_1 (ny, nockbalk 1 stöd B), LN1_2 (nockbalk 1 stöd C, fristående), LN1_3 (huvudstolpen) och LD4_1 (stolpe B,
GL30h 140×140). Koordinater som i huset (K-05).
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import Plan
from trebodar.material import GL30H

from . import ln1_3


def _flerlager(kod: str, x0: float, y0: float, y1: float, z1: float, lager: int = 4,
               syll: tuple[float, float, tuple[float, float]] | None = None) -> Montage:
    """Stolpe av `lager` reglar 45×95 sida vid sida i x, från bjälklaget till z1. Med syll (y0, y1, x-ände):
    stolpen står över syllens kant med ett hak."""
    m = Plan(kod, f"Stolpe {kod}", y1 - y0, beskrivning=f"{lager} × 45×95 C24")
    for i in range(lager):
        a, b = x0 + 45 * i, x0 + 45 * (i + 1)
        if syll:
            sy0, sy1, _ = syll
            m.tvarprofil([(y0, 0.0), (sy0, 0.0), (sy0, 45.0), (sy1, 45.0), (sy1, 0.0), (y1, 0.0), (y1, z1),
                          (y0, z1)], a, b, typ="R")
        else:
            m.lada("R", a, b, y0, y1, 0.0, z1, "z")
    if syll:
        sy0, sy1, xs = syll
        m.lada("S", xs[0], xs[1], sy0, sy1, 0.0, 45.0, "u")
    return m.montage()


def montage() -> Montage:
    m = Montage("Stolpar", beskrivning="Fristående stolpar under nock- och dalbalkarna (K-03)")
    nb1 = S.BALKAR["NB1"].uk
    m.lagg(_flerlager("LN1_1", 11565.0, 2747.5, 2842.5, nb1))
    m.lagg(_flerlager("LN1_2", 11565.0, 4638.5, 4733.5, nb1,
                      syll=(4651.0, 4721.0, (10980.0, S.TAKFALL["3NV"].x_insida))))       # syllen till 3NV
    m.lagg(ln1_3.montage())
    ld41 = Plan("LD4_1", "Stolpe LD4_1", 140.0, beskrivning="Stolpe B, limträ GL30h 140×140 (K-03)")
    ld41.lada("R", 4475 - 70, 4475 + 70, 5855 - 70, 5855 + 70, 0.0, S.BALKAR["DB4"].uk, "z", GL30H)
    m.lagg(ld41.montage())
    return m
