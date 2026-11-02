"""Huvudstolpen LN1_3 under nockbalk 1, stöd D (K-01, K-03): fyra lager 45×120 C24 med stolpe, topregel och strävor
45° åt båda hållen (dubbeltriangel), spikplåtar 100×400 på de yttre sidorna.

Koordinater som i huset (K-05): lagren ligger i x kring stolpens mitt, profilerna i (y, z). Stolpen står på syllen
LN1_3-S och bjälklaget; topregeln bär balken.
"""
import math

from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import Plan
from trebodar.material import SPIKPLAT

MITT = (11665.0, 6602.0)     # stolpens mitt (K-03)
LAGER = 4
T = 45.0
B = 120.0                    # stolpens, topregelns och strävornas bredd
X0 = MITT[0] - LAGER * T / 2             # första lagrets sida
YM = MITT[1]
ZT = S.BALKAR["NB1"].uk - B              # topregelns underkant
ZS = ZT - 700.0                          # strävornas fäste i stolpen (45°)
TOPPREGEL = 760.0                        # topregelns halva längd: strävans fäste i balken från stolpens mitt
SPIK_T = 2.0
PLAT = (400.0, 100.0)                    # spikplåtarna längs strävorna
FOT = (YM, ZS + 106.662)                 # plåtarnas hörn vid strävans fot (vid stolpens mitt) och topp (som i
TOPP = (YM + 751.301, ZT + 16.542)       # Onshape-modellen)
SYLL_X0 = 10980.0                        # syllarna under LN1_2 och LN1_3 går från den lätta väggen L2 till 3NV


def _spegla(p: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return [(2 * YM - y, z) for y, z in reversed(p)]


def _plat(horn: tuple[float, float], langs: int) -> list[tuple[float, float]]:
    """Spikplåten längs strävan från hörnet, uppåt (langs = 1) eller nedåt (−1), tvärs åt den andra sidan."""
    a, c = langs * PLAT[0] / math.sqrt(2), langs * PLAT[1] / math.sqrt(2)
    y, z = horn
    return [(y + c, z - c), (y + c + a, z - c + a), (y + a, z + a), (y, z)]


def montage() -> Montage:
    m = Plan("LN1_3", "Stolpe LN1_3", LAGER * T, beskrivning="Huvudstolpe 4 × 45×120 C24 med strävor (K-03)")
    syll = (YM - B / 2, YM + 10.0)                                  # syllen 70 under stolpens ena sida
    stolpe = [(syll[1], 0.0), (YM + B / 2, 0.0), (YM + B / 2, ZT), (YM - B / 2, ZT), (YM - B / 2, 45.0),
              (syll[1], 45.0)]
    d = 169.706                                                     # strävans höjd i lodled, B·√2
    strava = [(YM + B / 2, ZS), (YM + TOPPREGEL, ZT), (YM + TOPPREGEL - d, ZT), (YM + B / 2, ZS + d)]
    for i in range(LAGER):
        x0, x1 = X0 + i * T, X0 + (i + 1) * T
        m.tvarprofil(stolpe, x0, x1, typ="R")
        m.lada("L", x0, x1, YM - TOPPREGEL, YM + TOPPREGEL, ZT, ZT + B, "w")          # topregel, fibrer längs y
        m.tvarprofil(strava, x0, x1, typ="D")
        m.tvarprofil(_spegla(strava), x0, x1, typ="D")
    # spikplåtar på de yttre sidorna: strävans fot och topp, stolpens topp
    # strävans fot: plåten 100×400 längs strävan, så långt upp att den inte går förbi stolpens mitt (strävor åt
    # båda hållen)
    fot, topp = _plat(FOT, 1), _plat(TOPP, -1)
    for x0, x1 in ((X0 - SPIK_T, X0), (X0 + LAGER * T, X0 + LAGER * T + SPIK_T)):
        for p in (fot, topp, _spegla(fot), _spegla(topp)):
            m.tvarprofil(p, x0, x1, typ="P", material=SPIKPLAT)
        m.lada("P", x0, x1, YM - 50, YM + 50, ZT - 290, ZT + 110, "z", SPIKPLAT)
    m.lada("S", SYLL_X0, S.TAKFALL["3NV"].x_insida, *syll, 0, 45, "u")    # syll under stolpen, till 3NV
    return m.montage()
