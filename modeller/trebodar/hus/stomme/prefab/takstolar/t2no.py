"""Takstol 2NO: gavelstol på väggen 2NO under nockbalk 3 (K-03: Stol 2NO).

Byggd med reglerna i byggdelar/takstol.py, med spikreglar på insidan (underkanten 0,5 mm över takbalkarnas)
och 2 mm hak för ståndarna i underramen. Spikplåtarna vid fötterna och i toppen som i Onshape-modellen.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.takstol import takstol


def montage() -> Montage:
    t = takstol("2NO", "NB3", hak=2.0, spikregel=0.9104 * S.TAN, topplat_spel=6.0)
    t.fotplat(235.0, -1).fotplat(235.0, 1).fotplat(4035.0, 1).fotplat(4035.0, -1)
    return t.montage()
