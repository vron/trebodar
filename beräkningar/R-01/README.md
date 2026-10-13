# R-01 rev A – Konstruktionsritning nock- och dalbalkar

Ritningarna till de fem nock- och dalbalkarna (F-01: R-01), i A3 med den gemensamma mallen i [`../ritningsmall`](../ritningsmall/). Ritningen är underlag för balktillverkaren: balkarnas längder, plåtar, distansreglar, skruvzoner, hålbilder, material och utförande, enligt K-01. Stöden ritas bara ut för orientering, utan mått och utan krafter. Balkarnas lägen i huset kommer ur K-03 (`geometri.json`) och husets kontur ur K-05.

| Blad | Innehåll | Skala |
|---|---|---|
| R-01.1 | Elevationer av de fem balkarna (plåtar, distansreglar, skruvzoner, snitt och stödens lägen), balkarnas lägen i huset | 1:50, 1:200 |
| R-01.2 | Sektion A–A med plåt och B–B utan plåt (gemensamma för alla balkar), detalj C plåtände inne på balken, detalj D tre rader vid balkänden, plåt- och balkförteckning | 1:2,5, 1:5 |

`ritningar.py` är uppdelad i underlag, placeringar (`PLAC`: balkarnas ordning, snittens lägen, planens läge), elevationer, plan, sektioner och detaljer, blad och main. Elevationerna ritas i balkens koordinater (x från balkens vänstra ände som i K-01, z = 0 i underkant), sektionerna i tvärsnittets (x från plåtens kant mot framsidan som i hålbilderna) och planen i K-05:s koordinater; mallen skalar till papperet.

## Köra

```
python beräkningar/K-01/berakning.py      # om K-01/resultat.json saknas
python beräkningar/R-01/ritningar.py      # ritningar/R-01 Nock- och dalbalkar.pdf (R-01.1, R-01.2)
```

Ritningsserien blir en pdf, `R-01 Nock- och dalbalkar.pdf` i [`ritningar/`](../../ritningar/), med ett blad per sida. Bladen kompileras var för sig till `blad/` (och `R-01.x.json` här); båda versionshanteras inte. Skriptet kontrollerar att hålbilderna stämmer med plåtlägena och skruvzonerna i K-01.
