# R-05 rev A – Konstruktionsritning bottenplatta

Ritningarna till bottenplattan i källaren (F-01: R-05), utförande L300 enligt K-06: 100 mm betong C25/30 på 200 mm cellplast S100, kantbalkar i L-element (ytterkanten i väggarnas ytterliv, betongen 100 mm innanför) och balkar under innerväggarna 450 × 200, plintar under rören; S300 under alla balkar och plintar. A3 med den gemensamma mallen i [`../ritningsmall`](../ritningsmall/).

| Blad | Innehåll | Skala |
|---|---|---|
| R-05.1 | Plan: kontur i väggarnas ytterliv, kantbalkar, balkar, plintar med storlek, S300-zonerna, plinttabell | 1:50 |
| R-05.2 | Armering: nät Ø6 s150 i båda lagren, balkarnas järn och byglar, plintarnas järn, diagonaljärn, startjärn till väggarna | 1:50 |
| R-05.3 | Sektion A–A (kantbalk i L-element), B–B (balk under innervägg), C–C (plint med fotplåt), detalj D (S300 vid hörn), stålförteckning och cellplast | 1:10, 1:20, 1:50 |

Geometrin kommer ur [`../R-04/kallare.py`](../R-04/kallare.py) (samma som R-04) och plintarnas storlek ur K-06:s `resultat.json`. `ritningar.py` använder också R-04:s måttkedjor och snitt genom bottenplattan.

## Köra

```
python beräkningar/K-06/berakning.py      # om K-06/resultat.json saknas
python beräkningar/R-05/ritningar.py      # ritningar/R-05 Bottenplatta.pdf (R-05.1 … R-05.3)
```

Bladen kompileras var för sig till `blad/` (och `R-05.x.json` här); båda versionshanteras inte.
