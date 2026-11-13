# R-04 rev A – Konstruktionsritning bottenplatta

Ritningarna till bottenplattan i källaren (F-01: R-04), utförande L400 enligt K-06: 100 mm betong C30/37 på 300 mm cellplast (det undre skiktet S300 i hela ytan, det övre S100; 100 + 200 med plastfolien mellan), kantbalkar i L-element 400 (ytterkanten i väggarnas ytterliv, betongen 100 mm innanför, ryggen avfasad till 50 mm i överkant) och balkar under innerväggarna 450 × 300, plintar under rören; S300 under alla balkar och plintar. A3 med den gemensamma mallen i [`../ritningsmall`](../ritningsmall/).

| Blad | Innehåll | Skala |
|---|---|---|
| R-04.1 | Plan: kontur i väggarnas ytterliv, kantbalkar, balkar, plintar med storlek, plinttabell | 1:50 |
| R-04.2 | Armering: nät Ø6 s150 i båda lagren, balkarnas järn och byglar, plintarnas järn, diagonaljärn, startjärn till väggarna | 1:50 |
| R-04.3 | Sektion A–A (kantbalk i L-element), B–B (balk under innervägg), C–C (plint med fotplåt), detalj D (yttre hörn), stålförteckning och cellplast | 1:10, 1:20, 1:50 |

Geometrin kommer ur [`../R-05/kallare.py`](../R-05/kallare.py) (samma som R-05) och plintarnas storlek ur K-06:s `resultat.json`. `ritningar.py` använder också R-05:s måttkedjor och snitt genom bottenplattan.

## Köra

```
python beräkningar/K-06/berakning.py      # om K-06/resultat.json saknas
python beräkningar/R-04/ritningar.py      # ritningar/R-04 Bottenplatta.pdf (R-04.1 … R-04.3)
```

Bladen kompileras var för sig till `blad/` (och `R-04.x.json` här); båda versionshanteras inte.
