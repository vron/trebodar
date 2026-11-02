"""Takstol 2SV: gavelstol på väggen 2SV under nockbalk 3, mellan dalbalk 2 och dalbalk 4 (K-03: Stol 2SV).

Byggd med reglerna i byggdelar/takstol.py, på väggens överkant i dalbalkarnas underkant, med underramen 45×220.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.takstol import takstol


def montage() -> Montage:
    return takstol("2SV", "NB3", sate=S.BALKAR["DB2"].uk, underram=220.0).montage()
