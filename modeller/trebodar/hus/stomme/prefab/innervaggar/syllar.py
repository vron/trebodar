"""Syllar 45×70 för de lätta (icke bärande) innerväggarna, på bjälklaget. Koordinater som i huset (K-05)."""
from modellering import Montage

from trebodar.byggdelar.regelvagg import Plan

# (x0, x1, y0, y1), som i Onshape-modellen
SYLLAR = ((2525, 2595, 3655, 5265), (2595, 3275, 5195, 5265), (3275, 3345, 5195, 6175), (3275, 3345, 8035, 8185),
          (1540, 2060, 9255, 9325), (9440, 10055, 2760, 2830), (11980, 13745, 2760, 2830))


def montage() -> Montage:
    m = Plan("LS", "Syllar lätta väggar", 70.0, beskrivning="Syllar 45×70 C24 för lätta innerväggar")
    for x0, x1, y0, y1 in SYLLAR:
        m.lada("S", x0, x1, y0, y1, 0.0, 45.0, "u" if x1 - x0 > y1 - y0 else "w")
    return m.montage()
