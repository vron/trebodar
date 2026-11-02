"""Takstol 2C: mittstol på innerväggen 2C under nockbalk 3, mellan dalbalk 4 och dalbalk 2 (K-03: Stol L2M).

Byggd med reglerna i byggdelar/takstol.py, på väggens överkant i dalbalkarnas underkant, i väggens sida
w 50–95, med underramen 45×145, utan ståndare och med toppklossen på den nordöstra sidan.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.takstol import takstol


def montage() -> Montage:
    return takstol("2C", "NB3", utsida=False, klossar=(-1,), sate=S.BALKAR["DB2"].uk, w0=50.0, underram=145.0,
                   standare=()).montage()
