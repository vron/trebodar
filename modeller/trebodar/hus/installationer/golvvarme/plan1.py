"""Plan 1:s golvvärme, ingjuten i mellanbjälklaget ovanför tappvattnets rör: zonerna med en slinga var och
tilloppens stråk från fördelaren på V5:s södra sida i källaren (rören upp i bjälklaget framför väggen, mellan
underkantsnätets järn).

Källarväggarnas lodräta järn når upp i bjälklaget (R-05) och delar golvet: allrummet norr om V4–V6, hallen och
vardagsrummet norr om V3 och resten. Slingorna stannar i sin del, och stråken går över järnens rader i dörröppningarna
(D2 i V4–V5) eller mellan två järn (V3). Zonerna och stråken i fördelarens ordning från väster:

- AR: allrummet, genom D2 och längs dess södra kant.
- N: vardagsrummet och hallens norra del (med allrummets västra del), norrut genom V3.
- V: badrummet och hallens södra del, västerut från stråket i allrummets västra del.
- S: sovrummet, söderut genom 2C väster om kaminen och elens rör i bjälklaget (MB-R01).
- G: kontoret, sovrummet och kontoret vid gången och gästrummet: österut under 2B och söderut i gången.
- O: köket, österut längs kökets södra vägg.

Tilloppen värmer också golvet de går under (allrummets södra del, gången). Koordinater i mm (K-05).
"""
from __future__ import annotations

from trebodar.hus.rum import BADRUM

from ..montering import I_BETONGEN, kallarvagg
from ..strak import Strak, glipa
from .punkter import Zon

Z = I_BETONGEN["golvvarme"]
VAGG = kallarvagg("V5", 0.0, 0.0, -1).punkt[1]          # V5:s södra gips, fördelaren
X0 = 6475.0                                              # den första filen (väster), mellan underkantsnätets järn
Y_FD = {"fram": VAGG - 115.0, "retur": VAGG - 75.0}      # stammarna, under nätets maska närmast väggen
Z_FD = {"fram": -650.0, "retur": -550.0}

X_N = glipa("V3", Z, 3926.0)                             # stråket N genom V3:s järn
X_V, X_S, X_G = 3500.0, 5550.0, 9690.0                   # V och N i allrummets västra del, S väster om elens rör,
#                                                          G i gången

# i fördelarens ordning från väster; i ett stråk det som viker av först ytterst mot sin sida
ZONER = [
    Zon("AR", "Allrum", (4545.0, 7515.0, 9645.0, 10875.0), 300.0, "y", (4545.0, 7515.0), "AR"),
    Zon("VR", "Vardagsrum", (0.0, 11072.0, 4400.0, 16000.0), 300.0, "x", (4175.0, 11072.0), "N"),
    Zon("HN", "Hall och allrum, väster", (0.0, 9170.0, 4545.0, 11072.0), 300.0, "x", (4545.0, 9170.0), "N"),
    Zon("HS", "Hall", (0.0, 7210.0, 2035.0, 9170.0), 300.0, "x", (2035.0, 9170.0), "V"),
    Zon("BA", "Badrum", tuple(BADRUM.exterior.coords)[:-1], 200.0, "x", (3237.0, 8147.0), "V"),
    Zon("SO", "Sovrum", (2620.0, 2272.0, 9345.0, 5850.0), 300.0, "x", (X_S, 5850.0), "S"),
    Zon("KT", "Kontor", (4635.0, 135.0, 9345.0, 2128.0), 300.0, "x", (9345.0, 2128.0), "G"),
    Zon("SL", "Sovrum, litet", (9465.0, 1135.0, 13675.0, 2735.0), 300.0, "x", (9465.0, 2735.0), "G"),
    Zon("KL", "Kontor, litet", (11075.0, 2855.0, 13675.0, 4626.0), 300.0, "x", (11075.0, 4626.0), "G"),
    Zon("GR", "Gästrum", (11075.0, 4746.0, 13675.0, 6517.0), 300.0, "x", (11075.0, 6517.0), "G"),
    Zon("KO2", "Kök, öster", (11650.0, 6637.0, 13675.0, 12375.0), 300.0, "y", (11650.0, 6637.0), "O"),
    Zon("KO1", "Kök, väster", (9645.0, 6637.0, 11650.0, 12375.0), 300.0, "y", (9645.0, 6637.0), "O"),
]


def strak(mitt: dict[str, float]) -> dict[str, Strak]:
    """Tilloppens stråk söderut från fördelaren, med deras första sträcka genom mitten av sina filer (mitt: x); de
    som viker av åt samma håll gör det i ordning, det första närmast väggen."""
    return {s.id: s for s in (
        Strak("AR", ((mitt["AR"], VAGG), (mitt["AR"], 7150.0), (5830.0, 7150.0), (5830.0, 7600.0), (4600.0, 7600.0))),
        Strak("N", ((mitt["N"], VAGG), (mitt["N"], 7000.0), (X_N, 7000.0), (X_N, 11700.0))),
        Strak("V", ((mitt["V"], VAGG), (mitt["V"], 6800.0), (X_V, 6800.0), (X_V, 9050.0))),
        Strak("S", ((mitt["S"], VAGG), (mitt["S"], 6650.0), (X_S, 6650.0), (X_S, 5300.0))),
        Strak("G", ((mitt["G"], VAGG), (mitt["G"], 6440.0), (X_G, 6440.0), (X_G, 1600.0))),
        Strak("O", ((mitt["O"], VAGG), (mitt["O"], 6740.0), (13500.0, 6740.0))),
    )}
