# R-06 rev A – Konstruktionsritning mellanbjälklag

Ritningarna till mellanbjälklaget (F-01: R-06), i A3 med den gemensamma mallen i [`../ritningsmall`](../ritningsmall/). Underlag är K-05 (geometri och armering) och K-06 (källarväggarna av Sundolitt Kub 350-150 och vinkeljärnen från väggarna till bjälklaget).

| Blad | Innehåll | Skala |
|---|---|---|
| R-06.1 | Översikt och yttermått, hela plattan inklusive plattan på mark, trapphålets läge | 1:100 |
| R-06.2 | Armering i underkant, rörens lägen och topplåtar, snittmarkeringar | 1:50 |
| R-06.3 | Armering i överkant, zonerna Ö1–Ö16, diagonaljärn, vinkeljärn från ytterväggarna | 1:50 |
| R-06.4 | Sektioner A–D, detalj E (armeringens lägen), stålförteckning | 1:5, 1:10, 1:20 |

`ritningar.py` är uppdelad i underlag, placeringar (`PLAC`, verkliga koordinater i mm för etiketter, symboler och snitt), lager (en funktion per lager), blad och main. Allt ritas i K-05:s koordinater (mm, origo i skärningen mellan plattkanterna x = 0 och y = 0); mallen skalar till papperet.

## Köra

```
python beräkningar/K-05/berakning.py      # om K-05/resultat.json saknas
python beräkningar/R-06/ritningar.py      # ritningar/R-06 Mellanbjälklag.pdf (R-06.1 … R-06.4)
```

Ritningsserien blir en pdf, `R-06 Mellanbjälklag.pdf` i [`ritningar/`](../../ritningar/), med ett blad per sida. Varje blad har sin egen funktion i `ritningar.py` och kompileras för sig till `blad/` (och `R-06.x.json` här); båda versionshanteras inte. Ett lager kan döljas vid kompileringen, t.ex. `main(dolj=("vaggar",))`.
