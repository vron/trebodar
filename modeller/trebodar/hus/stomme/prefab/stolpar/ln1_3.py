"""Huvudstolpen LN1_3 under nockbalk 1, stöd D (K-01, K-03): fyra lager 45×120 C24 med stolpe, topregel och strävor
45° åt båda hållen (dubbeltriangel), spikplåtar 100×400 på de yttre sidorna.

Koordinater som i huset (K-05): lagren ligger i x 11 575–11 755, profilerna i (y, z). Stolpen står på syllen
LN1_3-S (y 6 542–6 612) och bjälklaget; topregeln bär balken.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import Plan
from trebodar.material import C24, SPIKPLAT

X0 = 11575.0                 # första lagrets sida
LAGER = 4
T = 45.0
YM = 6602.0                  # stolpens mitt (y)
ZT = S.BALKAR["NB1"].uk - 120.0          # topregelns underkant
ZS = ZT - 700.0                          # strävornas fäste i stolpen
SPIK_T = 2.0


def _spegla(p: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return [(2 * YM - y, z) for y, z in reversed(p)]


def montage() -> Montage:
    m = Plan("LN1_3", "Stolpe LN1_3", 180.0, beskrivning="Huvudstolpe 4 × 45×120 C24 med strävor (K-03)")
    stolpe = [(YM + 10, 0.0), (YM + 60, 0.0), (YM + 60, ZT), (YM - 60, ZT), (YM - 60, 45.0), (YM + 10, 45.0)]
    strava = [(YM + 60, ZS), (YM + 760, ZT), (YM + 590.294, ZT), (YM + 60, ZS + 169.706)]
    for i in range(LAGER):
        x0, x1 = X0 + i * T, X0 + (i + 1) * T
        m.tvarprofil(stolpe, x0, x1, typ="R")
        m.lada("L", x0, x1, YM - 760, YM + 760, ZT, ZT + 120, "w")          # topregel, fibrer längs y
        m.tvarprofil(strava, x0, x1, typ="D")
        m.tvarprofil(_spegla(strava), x0, x1, typ="D")
    # spikplåtar på de yttre sidorna: strävans fot och topp, stolpens topp
    # strävans fot: plåten 100×400 längs strävan, så långt upp att den inte går förbi stolpens mitt (strävor åt
    # båda hållen)
    fot = [(YM + 70.711, ZS + 35.952), (YM + 353.554, ZS + 318.794), (YM + 282.843, ZS + 389.505),
           (YM, ZS + 106.662)]
    topp = [(YM + 680.59, ZT + 87.252), (YM + 397.748, ZT - 195.59), (YM + 468.458, ZT - 266.301),
            (YM + 751.301, ZT + 16.542)]
    for x0, x1 in ((X0 - SPIK_T, X0), (X0 + LAGER * T, X0 + LAGER * T + SPIK_T)):
        for p in (fot, topp, _spegla(fot), _spegla(topp)):
            m.tvarprofil(p, x0, x1, typ="P", material=SPIKPLAT)
        m.lada("P", x0, x1, YM - 50, YM + 50, ZT - 290, ZT + 110, "z", SPIKPLAT)
    m.lada("S", X0 - 595, 13745, YM - 60, YM + 10, 0, 45, "u")             # syll under stolpen
    return m.montage()
