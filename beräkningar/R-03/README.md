# R-03 rev A – Konstruktionsritning mellanbjälklag

Ritningarna till mellanbjälklaget (F-01: R-03), i A3 med den gemensamma mallen i [`../ritningsmall`](../ritningsmall/). Underlag är K-05 (geometri och armering) och K-06 (förankring i U-blocket, stålstolparna i system A).

| Blad | Innehåll | Skala |
|---|---|---|
| R-03.1 | Översikt och yttermått, hela plattan inklusive plattan på mark, trapphålets läge | 1:100 |
| R-03.2 | Armering i underkant, rörens lägen och topplåtar, snittmarkeringar | 1:50 |
| R-03.3 | Armering i överkant, zonerna Ö1–Ö18, diagonaljärn, förankring i U-blocket, ingjutna plåtar | 1:50 |
| R-03.4 | Sektioner A–D, detaljer E–F, stålförteckning | 1:5, 1:10, 1:20 |

`ritningar.py` är uppdelad i underlag, placeringar (`PLAC`, verkliga koordinater i mm för etiketter, symboler och snitt), lager (en funktion per lager), blad och main. Allt ritas i K-05:s koordinater (mm, origo i skärningen mellan plattkanterna x = 0 och y = 0); mallen skalar till papperet.

## Köra

```
python beräkningar/K-05/berakning.py      # om K-05/resultat.json saknas
python beräkningar/R-03/ritningar.py      # ritningar/R-03 Mellanbjälklag.pdf (R-03.1 … R-03.4)
```

Ritningsserien blir en pdf, `R-03 Mellanbjälklag.pdf` i [`ritningar/`](../../ritningar/), med ett blad per sida. Varje blad har sin egen funktion i `ritningar.py` och kompileras för sig till `blad/` (och `R-03.x.json` här); båda versionshanteras inte. Ett lager kan döljas vid kompileringen, t.ex. `main(dolj=("vaggar",))`.
