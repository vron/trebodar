"""Källarens golvvärme, ingjuten i bottenplattan mellan armeringsnäten: en slinga per rum (det stora rummet delat) och
tilloppens stråk från fördelaren på V5:s södra sida i trapphallen (rören ned i plattan framför väggen, mellan
överkantsnätets järn). Trapphallen värms av tilloppen.

Rummen avgränsas av källarens innerväggar KL1–KL10 (invandigt/kallarens_innervaggar.py), och stråken går genom deras
dörröppningar: KD2 till hallen (och därifrån genom öppningen väster om KL8 till teknikrummet och genom KD1 till rummet
söder om hallen), KD4 till rummet söder om trapphallen (och genom KD3 till rummet öster om KL2) och KD5 till det stora
rummet i den högra huskroppen. Balkarna under V4–V6, V15 och V19 har sina överkantsjärn i rörens nivå (R-04), så
stråken går inte över dem: källarrummet norr om V4–V6 värms inte (som i Onshape-modellen).

Zonerna och stråken i fördelarens ordning från väster:

- VN: teknikrummet, västerut genom KD2, längs hallens norra vägg och norrut genom öppningen väster om KL8.
- VS: hallen och rummet söder om den (väster om KL2), västerut genom KD2, längs hallens södra vägg och söderut genom
  KD1.
- S: rummet söder om trapphallen och rummet öster om KL2, söderut genom KD4, västerut längs KL4 genom KD3 och norrut
  längs KL3.
- ÖS och ÖN: det stora rummet (söder, mitt och norr), österut genom KD5 och söderut och norrut öster om V15:s balk.

Koordinater i mm (K-05).
"""
from __future__ import annotations

from ..montering import I_BETONGEN, kallarvagg
from ..strak import Strak
from .punkter import Zon

Z = I_BETONGEN["golvvarme_bottenplattan"]
VAGG = kallarvagg("V5", 0.0, 0.0, -1).punkt[1]
X0 = 6600.0                                              # mellan överkantsnätets järn
Y_FD = {"fram": VAGG - 167.5, "retur": VAGG - 127.5}     # stammarna, över nätets maska framför väggen (rören böjs
#                                                          söderut i den)
Z_FD = {"fram": -1900.0, "retur": -2000.0}

X_O = 9970.0                                             # ÖS och ÖN öster om V15:s balk
X_KD1, X_KD4 = 1180.0, 6320.0                            # dörröppningarna KD1 och KD4

ZONER = [
    Zon("KT", "Teknikrum", ((0.0, 7675.0), (3600.0, 7675.0), (3600.0, 7266.0), (4545.0, 7266.0), (4545.0, 9200.0),
                            (0.0, 9200.0)), 300.0, "x", (0.0, 7675.0), "VN"),
    Zon("KH", "Hall", (0.0, 5820.0, 4200.0, 7675.0), 300.0, "y", (4200.0, 5820.0), "VS"),
    Zon("KSV", "Rum söder om hallen", (0.0, 3700.0, 2800.0, 5820.0), 300.0, "x", (X_KD1, 5820.0), "VS"),
    Zon("KSM", "Rum öster om KL2", (2800.0, 3700.0, 4531.0, 5820.0), 300.0, "x", (4531.0, 5820.0), "S"),
    Zon("KS", "Rum söder om trapphallen", (4531.0, 300.0, 9070.0, 4990.0), 300.0, "y", (4531.0, 4990.0), "S"),
    Zon("KÖ1", "Stora rummet, söder", (9070.0, 1333.0, 13477.0, 5000.0), 300.0, "x", (9833.0, 5000.0), "ÖS"),
    Zon("KÖ2", "Stora rummet, mitt", (9070.0, 5000.0, 13477.0, 8600.0), 300.0, "x", (9833.0, 8600.0), "ÖN"),
    Zon("KÖ3", "Stora rummet, norr", (9070.0, 8600.0, 13477.0, 12177.0), 300.0, "x", (9833.0, 8600.0), "ÖN"),
]


def strak(mitt: dict[str, float]) -> dict[str, Strak]:
    """Tilloppens stråk söderut från fördelaren (söder om stammarna), med deras första sträcka genom mitten av sina
    filer (mitt: x)."""
    return {s.id: s for s in (
        Strak("VN", ((mitt["VN"], VAGG), (mitt["VN"], 6775.0), (4300.0, 6775.0), (4300.0, 7050.0), (3450.0, 7050.0),
                     (3450.0, 7450.0), (700.0, 7450.0), (700.0, 7950.0))),
        Strak("VS", ((mitt["VS"], VAGG), (mitt["VS"], 6600.0), (4400.0, 6600.0), (4400.0, 6000.0), (X_KD1, 6000.0),
                     (X_KD1, 5400.0))),
        Strak("S", ((mitt["S"], VAGG), (mitt["S"], 5500.0), (X_KD4, 5500.0), (X_KD4, 4700.0), (4300.0, 4700.0),
                    (4300.0, 5650.0))),
        Strak("ÖS", ((mitt["ÖS"], VAGG), (mitt["ÖS"], 6700.0), (X_O, 6700.0), (X_O, 1600.0))),
        Strak("ÖN", ((mitt["ÖN"], VAGG), (mitt["ÖN"], 6950.0), (X_O, 6950.0), (X_O, 9300.0))),
    )}
