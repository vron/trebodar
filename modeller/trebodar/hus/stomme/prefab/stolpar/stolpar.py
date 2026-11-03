"""Fristående stolpar under nock- och dalbalkarna (K-03). Stolpar som står i en vägg ingår i väggen.

LN1_1 (ny, nockbalk 1 stöd B), LN1_2 (nockbalk 1 stöd C, fristående), LN1_3 (huvudstolpen, ln1_3.py) och LD4_1
(stolpe B, GL30h 140×140, med södra sidan 12 mm norr om fickdörren ID6:s ficka i 2C), med stolparnas mitt som i
K-03 och K-05.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import Plan
from trebodar.material import GL30H

from . import ln1_3

LN1_1 = (S.BALKAR["NB1"].x, 2795.0)          # stolparnas mitt (x, y)
LN1_2 = (S.BALKAR["NB1"].x, 4686.0)
LD4_1 = (4475.0, 5843.0)                     # 12 mm norr om fickdörren ID6:s ficka (Onshape-modellens läge)
LD4_1_B = 140.0


def _flerlager(kod: str, mitt: tuple[float, float], z1: float, lager: int = 4,
               syll: tuple[float, float] | None = None) -> Montage:
    """Stolpe av `lager` reglar 45×95 sida vid sida i x, från bjälklaget till z1. Med syll 45×70 under stolpens mitt
    (x-ändarna): stolpen står över syllens kant med ett hak."""
    x0, (y0, y1) = mitt[0] - 45 * lager / 2, (mitt[1] - 47.5, mitt[1] + 47.5)
    sy0, sy1 = mitt[1] - 35.0, mitt[1] + 35.0
    m = Plan(kod, f"Stolpe {kod}", y1 - y0, beskrivning=f"{lager} × 45×95 C24")
    for i in range(lager):
        a, b = x0 + 45 * i, x0 + 45 * (i + 1)
        if syll:
            m.tvarprofil([(y0, 0.0), (sy0, 0.0), (sy0, 45.0), (sy1, 45.0), (sy1, 0.0), (y1, 0.0), (y1, z1),
                          (y0, z1)], a, b, typ="R")
        else:
            m.lada("R", a, b, y0, y1, 0.0, z1, "z")
    if syll:
        m.lada("S", syll[0], syll[1], sy0, sy1, 0.0, 45.0, "u")
    return m.montage()


def montage() -> Montage:
    m = Montage("Stolpar", beskrivning="Fristående stolpar under nock- och dalbalkarna (K-03)")
    nb1 = S.BALKAR["NB1"].uk
    m.lagg(_flerlager("LN1_1", LN1_1, nb1))
    m.lagg(_flerlager("LN1_2", LN1_2, nb1, syll=(ln1_3.SYLL_X0, S.TAKFALL["3NV"].x_insida)))
    m.lagg(ln1_3.montage())
    ld41 = Plan("LD4_1", "Stolpe LD4_1", LD4_1_B, beskrivning="Stolpe B, limträ GL30h 140×140 (K-03)")
    (x, y), r = LD4_1, LD4_1_B / 2
    ld41.lada("R", x - r, x + r, y - r, y + r, 0.0, S.BALKAR["DB4"].uk, "z", GL30H)
    m.lagg(ld41.montage())
    return m
