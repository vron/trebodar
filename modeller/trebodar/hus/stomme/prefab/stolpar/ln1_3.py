"""Huvudstolpen LN1_3 under nockbalk 1, stöd D (K-01, K-03): fyra prefabricerade lager C24, var och ett med stolpe och
topregel 45×120 och strävor 45×145 i 45° åt båda hållen (dubbeltriangel), med inpressade spikplåtar 1,0 mm (K-03,
MiTek M20H eller likvärdig) på båda sidor av varje lager: vid strävans fot FOTPLAT från stolpens mitt in på strävan
(lodrät, så att plåtarna för de två strävorna möts i stolpens mitt), i strävans topp TOPPLAT längs strävans mittlinje
och mitt på stolpens topp STOLPPLAT över fogen mot topregeln. Lägena och storlekarna är K-03:s. Plåtarna mellan lagren
(1 mm) är inte ritade; de på de yttre sidorna är det.

Koordinater som i huset (K-05): lagren ligger i x kring stolpens mitt, profilerna i (y, z). Stolpen står direkt på
bjälklaget (ändträ mot betongen; tryck vinkelrätt fibrerna i en syll klarade inte lasten, K-04) och syllen under den
lätta väggen är delad i två bitar som slutar mot stolpens sidor; topregeln bär balken. Stolpen förankras i bjälklaget
för lyftet (K-03) med ett vinkelbeslag på var syllbit, skruvat i stolpens ände och i syllen, och en betongbult genom
beslaget och syllen ned i plattan (förankringen, BULTAR), borrad efter gjutningen. Beslaget är bredare än syllen och
går BESLAG_OVER in i den lätta väggens OSB på båda sidor, som tas ur där.
"""
import math

from modellering import Del, Montage, Placering

from trebodar import skelett as S
from trebodar.byggdelar.beslag import ABR_BREDD, BULT_U, BULT_V, vinkelbeslag
from trebodar.byggdelar.regelvagg import Plan
from trebodar.material import SPIKPLAT, VINKELBESLAG

MITT = (11665.0, 6602.0)     # stolpens mitt (K-03)
LAGER = 4
T = 45.0
B = 120.0                    # stolpens och topregelns bredd
BS = 145.0                   # strävornas bredd (K-03: så att spikplåtarna vid foten får plats)
X0 = MITT[0] - LAGER * T / 2             # första lagrets sida
YM = MITT[1]
ZT = S.BALKAR["NB1"].uk - B              # topregelns underkant
ZS = ZT - 700.0                          # strävornas fäste i stolpen (45°)
TOPPREGEL = 760.0                        # topregelns halva längd: strävans fäste i balken från stolpens mitt
SPIK_T = 1.0
FOTPLAT = (102.0, 152.0, 125.0)          # vid strävans fot: bredd (y, från stolpens mitt), höjd och mitten över ZS (K-03)
TOPPLAT = (102.0, 102.0, -50.0)          # i strävans topp: längd och bredd längs strävan, förskjutning (K-03)
STOLPPLAT = (76.0, 102.0)                # mitt på stolpens topp: bredd och höjd, mitt på fogen mot topregeln (K-03)
SYLL_X0 = 10980.0                        # syllarna under LN1_2 och LN1_3 går från den lätta väggen L2 till 3NV
SYLL = (YM - B / 2, YM + 10.0)           # syllen 70 (y), i liv med stolpens ena sida
SYLL_H = 45.0
# vinkelbeslagen vid foten (K-03: Simpson Strong-Tie ABR10525, byggdelar/beslag.py) mitt på syllen, så att beslaget
# går lika långt in i OSB:n på var sida
BESLAG_OVER = (ABR_BREDD - (SYLL[1] - SYLL[0])) / 2
X1 = X0 + LAGER * T                      # sista lagrets sida
# betongbultarna genom beslagen och syllen (förankringen ritar dem och prövar avståndet till rören), (x, y)
BULTAR = ((X0 - BULT_U, (SYLL[0] + SYLL[1]) / 2 - BULT_V), (X1 + BULT_U, (SYLL[0] + SYLL[1]) / 2 - BULT_V))


def _spegla(p: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return [(2 * YM - y, z) for y, z in reversed(p)]


R2 = math.sqrt(0.5)                      # cos 45°
MITTLINJE = (YM + B / 2, ZS + BS * R2)   # strävans mittlinje vid stolpens sida, uppåt i 45°


def _plat(t0: float, L: float, b: float) -> list[tuple[float, float]]:
    """Spikplåten mitt på strävans mittlinje, från t0 längs den (från stolpens sida), L lång och b bred."""
    (my, mz), h = MITTLINJE, b / 2
    return [(my + (t - s * h) * R2, mz + (t + s * h) * R2)
            for t, s in ((t0, -1), (t0 + L, -1), (t0 + L, 1), (t0, 1))]


def beslag(sida: int) -> tuple[Del, Placering]:
    """Vinkelbeslaget vid stolpens ände x0 (sida −1) eller x1 (+1): en skänkel mot änden och en på syllen."""
    xs = X0 if sida < 0 else X1
    plac = Placering.axlar((xs, (SYLL[0] + SYLL[1]) / 2, SYLL_H), (sida, 0.0, 0.0), "z")
    return Del("Vinkelbeslag ABR10525", vinkelbeslag(), VINKELBESLAG, produkt="VINKELBESLAG-LN1_3"), plac


def montage() -> Montage:
    m = Plan("LN1_3", "Stolpe LN1_3", LAGER * T, beskrivning="Huvudstolpe 4 × 45×120 C24 med strävor (K-03)")
    syll = SYLL
    stolpe = [(YM - B / 2, 0.0), (YM + B / 2, 0.0), (YM + B / 2, ZT), (YM - B / 2, ZT)]   # direkt på bjälklaget
    d = BS * math.sqrt(2)                                           # strävans höjd i lodled
    strava = [(YM + B / 2, ZS), (YM + TOPPREGEL, ZT), (YM + TOPPREGEL - d, ZT), (YM + B / 2, ZS + d)]
    for i in range(LAGER):
        x0, x1 = X0 + i * T, X0 + (i + 1) * T
        m.tvarprofil(stolpe, x0, x1, typ="R")
        m.lada("L", x0, x1, YM - TOPPREGEL, YM + TOPPREGEL, ZT, ZT + B, "w")          # topregel, fibrer längs y
        m.tvarprofil(strava, x0, x1, typ="D")
        m.tvarprofil(_spegla(strava), x0, x1, typ="D")
    # spikplåtar på de yttre sidorna (K-03): vid strävans fot från stolpens mitt in på strävan, i strävans topp längs
    # strävans mittlinje, mitt på stolpens topp över fogen mot topregeln
    fw, fh, fz = FOTPLAT
    fot = [(YM, ZS + fz - fh / 2), (YM + fw, ZS + fz - fh / 2), (YM + fw, ZS + fz + fh / 2), (YM, ZS + fz + fh / 2)]
    tL, tb, td = TOPPLAT
    topp = _plat((TOPPREGEL - B / 2) / R2 - tb / 2 - tL + td, tL, tb)
    sw, sh = STOLPPLAT
    for x0, x1 in ((X0 - SPIK_T, X0), (X0 + LAGER * T, X0 + LAGER * T + SPIK_T)):
        for p in (fot, topp, _spegla(fot), _spegla(topp)):
            m.tvarprofil(p, x0, x1, typ="P", material=SPIKPLAT)
        m.lada("P", x0, x1, YM - sw / 2, YM + sw / 2, ZT - sh / 2, ZT + sh / 2, "z", SPIKPLAT)
    # syllen till 3NV, delad vid stolpen: en bit på var sida som slutar mot stolpens sidor
    m.lada("S", SYLL_X0, X0, *syll, 0, SYLL_H, "u")
    m.lada("S", X1, S.TAKFALL["3NV"].x_insida, *syll, 0, SYLL_H, "u")
    # vinkelbeslagen mot lyftet vid foten
    for sida in (-1, 1):
        m.del_i("B", *beslag(sida), (X0 if sida < 0 else X1, SYLL_H))
    return m.montage()
