"""Takstol 2C: mittstol på innerväggen 2C under nockbalk 3, mellan dalbalk 4 och dalbalk 2 (K-03: Stol L2M).

Byggd med reglerna i byggdelar/takstol.py, på väggens överkant i dalbalkarnas underkant, i väggens sida w 50–95,
med underramen 45×145 och toppklossen på den nordöstra sidan. Stolen saknar ståndare: diagonalerna har säten och
underramen 2 mm hak där de stod i Onshape-modellen (mittståndaren 3 mm från nockens mitt). Spikplåtarna vid
fötterna som i Onshape-modellen.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.takstol import takstol


def montage() -> Montage:
    t = takstol("2C", "NB3", utsida=False, klossar=(-1,), sate=S.BALKAR["DB2"].uk, w0=50.0, underram=145.0,
                hak=2.0, standare=(1262.5, 1862.5, 2462.5, 2993.0, 3662.5), standardelar=False)
    t.fotplat(214.484, 1).fotplat(214.484, -1).fotplat(4161.516, -1).fotplat(4161.516, 1)
    return t.montage()
