"""Källarens golvvärme, ingjuten i bottenplattan mellan armeringsnäten: zonerna med en slinga var och tilloppens
stråk från fördelaren på V5:s södra sida (rören ned i plattan framför väggen, mellan överkantsnätets järn).

Balkarna under V4–V6, V15 och V19 har sina överkantsjärn i rörens nivå (R-04), så stråken går inte över dem:
källarrummet norr om V4–V6 värms inte (som i Onshape-modellen). Zonerna och stråken i fördelarens ordning från väster:

- V: källarens västra del (teknikrummet, utom under värmepumpen och vid servisen) och mittdelens västra halva, västerut
  söder om V4 och norrut framför V19.
- ÖS: mittdelens östra halva (utom under trappan) och den östra delens södra del, österut och söderut öster om V17.
- ÖN: den östra delens mitt och norra del, österut och norrut öster om V15.

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

X_V, X_O = 4200.0, 9970.0                                # V framför V19, ÖS och ÖN öster om V15:s balk

ZONER = [
    Zon("KV", "Källare väster", (0.0, 3700.0, 4545.0, 8650.0), 300.0, "x", (4545.0, 8650.0), "V"),
    Zon("KM1", "Källare mitt, väster", (4545.0, 333.0, 7000.0, 7327.0), 300.0, "y", (4545.0, 7327.0), "V"),
    Zon("KM2", "Källare mitt, öster", (7000.0, 333.0, 9833.0, 7327.0), 300.0, "y", (7000.0, 7327.0), "ÖS"),
    Zon("KÖ1", "Källare öster, söder", (9833.0, 1333.0, 13477.0, 5000.0), 300.0, "x", (9833.0, 5000.0), "ÖS"),
    Zon("KÖ2", "Källare öster, mitt", (9833.0, 5000.0, 13477.0, 8600.0), 300.0, "x", (9833.0, 8600.0), "ÖN"),
    Zon("KÖ3", "Källare öster, norr", (9833.0, 8600.0, 13477.0, 12177.0), 300.0, "x", (9833.0, 8600.0), "ÖN"),
]


def strak(mitt: dict[str, float]) -> dict[str, Strak]:
    """Tilloppens stråk söderut från fördelaren (söder om stammarna), med deras första sträcka genom mitten av sina
    filer (mitt: x)."""
    return {s.id: s for s in (
        Strak("V", ((mitt["V"], VAGG), (mitt["V"], 7000.0), (X_V, 7000.0), (X_V, 8600.0))),
        Strak("ÖS", ((mitt["ÖS"], VAGG), (mitt["ÖS"], 6800.0), (X_O, 6800.0), (X_O, 1600.0))),
        Strak("ÖN", ((mitt["ÖN"], VAGG), (mitt["ÖN"], 7000.0), (X_O, 7000.0), (X_O, 9300.0))),
    )}
