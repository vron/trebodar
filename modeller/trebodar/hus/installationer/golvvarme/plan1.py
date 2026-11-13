"""Plan 1:s golvvärme, ingjuten i mellanbjälklaget ovanför tappvattnets rör: zonerna med en slinga var och
tilloppens stråk från fördelaren på V5:s norra sida i källaren (rören upp i bjälklaget framför väggen, mellan
underkantsnätets järn).

Källarväggarnas lodräta järn når upp i bjälklaget (R-05) och delar golvet: allrummet söder om V4–V6, hallen och
vardagsrummet söder om V3 och resten. Slingorna stannar i sin del, och stråken går över järnens rader i dörröppningarna
(D2 i V4–V5) eller mellan två järn (V3). Zonerna och stråken i fördelarens ordning från väster:

- AR: allrummet, genom D2 och längs dess norra kant.
- N: vardagsrummet och hallens södra del (med allrummets västra del), söderut genom V3.
- V: badrummet och hallens norra del, västerut från stråket i allrummets västra del.
- S: sovrummet, norrut genom 2C väster om kaminen och elens rör i bjälklaget (MB-R01).
- G: kontoret, sovrummet och kontoret vid gången och gästrummet: österut under 2B och norrut i gången.
- O: köket, österut längs kökets norra vägg.

Tilloppen värmer också golvet de går under (allrummets norra del, gången). Koordinater i mm (K-05).
"""
from __future__ import annotations

from trebodar.hus.rum import BADRUM

from ..montering import I_BETONGEN, kallarvagg
from ..strak import Strak, glipa
from .punkter import Zon

Z = I_BETONGEN["golvvarme"]
VAGG = kallarvagg("V5", 0.0, 0.0, -1).punkt[1]          # V5:s norra gips, fördelaren
X0 = 6475.0                                              # den första filen (väster), mellan underkantsnätets järn
Y_FD = {"fram": VAGG - 115.0, "retur": VAGG - 75.0}      # stammarna, under nätets maska närmast väggen
Z_FD = {"fram": -650.0, "retur": -550.0}

X_N = glipa("V3", Z, 3926.0)                             # stråket N genom V3:s järn
X_V, X_S, X_G = 3650.0, 5350.0, 9900.0                   # V och N i allrummets västra del, S genom 2C:s dörr och G i
#                                                          gången, utanför stommens spärrzoner (#114)
Y_O = 6900.0                                             # O österut norr om huvudstolpens syll
Y_HALL = 9120.0                                          # hallens zon HS uppåt: tilloppet till HS går genom 1B:s
#                                                          passage (installationer/passager.py)
Y_HN = 9560.0                                            # HN från norr om 1B:s ände (dess spärrzon, #114)
Y_KT = 1930.0                                            # KT (och tilloppen till slingans ändar) minst 200 mm
#                                                          från 2A:s bultar
# SO: sänkt väster om stolpen LD4_1, så att returen från slingans ände går minst 200 mm från stolpens bultar
SO_HORN = (4850.0, 5480.0)
Y_GR = 6460.0                                            # GR (och tilloppet längs översta raden) söder om
#                                                          huvudstolpens spärrzon

# i fördelarens ordning från väster; i ett stråk det som viker av först ytterst mot sin sida
ZONER = [
    Zon("AR", "Allrum", (4545.0, 7515.0, 9645.0, 10875.0), 300.0, "y", (4545.0, 7515.0), "AR"),
    Zon("VR", "Vardagsrum", (0.0, 11072.0, 4400.0, 16000.0), 300.0, "x", (4175.0, 11072.0), "N"),
    Zon("HN", "Hall och allrum, väster", (0.0, Y_HN, 4545.0, 11072.0), 300.0, "x", (4545.0, Y_HN), "N"),
    Zon("HS", "Hall", (0.0, 7210.0, 2035.0, Y_HALL), 300.0, "x", (2035.0, Y_HALL), "V"),
    Zon("BA", "Badrum", tuple(BADRUM.exterior.coords)[:-1], 200.0, "x", (3237.0, 7700.0), "V"),
    Zon("SO", "Sovrum", ((2620.0, 2272.0), (9345.0, 2272.0), (9345.0, 5850.0), (SO_HORN[0], 5850.0), SO_HORN,
                         (2620.0, SO_HORN[1])), 300.0, "x", (X_S, 5850.0), "S"),
    Zon("KT", "Kontor", (4635.0, 135.0, 9345.0, Y_KT), 300.0, "x", (9345.0, Y_KT), "G"),
    Zon("SL", "Sovrum, litet", (9465.0, 1135.0, 13675.0, 2735.0), 300.0, "x", (9465.0, 2735.0), "G"),
    Zon("KL", "Kontor, litet", (11075.0, 2855.0, 13675.0, 4626.0), 300.0, "x", (11075.0, 4626.0), "G"),
    Zon("GR", "Gästrum", (11075.0, 4746.0, 13675.0, Y_GR), 300.0, "x", (11075.0, Y_GR), "G"),
    Zon("KO2", "Kök, öster", (11650.0, 6637.0, 13675.0, 12375.0), 300.0, "y", (11650.0, 6637.0), "O"),
    Zon("KO1", "Kök, väster", (9645.0, 6637.0, 11650.0, 12375.0), 300.0, "y", (9645.0, 6637.0), "O"),
]


def strak(mitt: dict[str, float]) -> dict[str, Strak]:
    """Tilloppens stråk norrut från fördelaren, med deras första sträcka genom mitten av sina filer (mitt: x); de
    som viker av åt samma håll gör det i ordning, det första närmast väggen."""
    return {s.id: s for s in (
        Strak("AR", ((mitt["AR"], VAGG), (mitt["AR"], 7150.0), (5830.0, 7150.0), (5830.0, 7600.0), (4600.0, 7600.0))),
        Strak("N", ((mitt["N"], VAGG), (mitt["N"], 7000.0), (X_N, 7000.0), (X_N, 11700.0))),
        Strak("V", ((mitt["V"], VAGG), (mitt["V"], 6800.0), (X_V, 6800.0), (X_V, 9050.0))),
        Strak("S", ((mitt["S"], VAGG), (mitt["S"], 6650.0), (X_S, 6650.0), (X_S, 5720.0))),
        Strak("G", ((mitt["G"], VAGG), (mitt["G"], 6440.0), (X_G, 6440.0), (X_G, 1600.0))),
        Strak("O", ((mitt["O"], VAGG), (mitt["O"], Y_O), (13500.0, Y_O))),
    )}
