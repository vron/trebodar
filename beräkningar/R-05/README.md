# R-05 rev A – Konstruktionsritning källarstomme

Ritningarna till källarens väggar av Sundolitt Kub 350-150 och rören under mellanbjälklaget (F-01: R-05), i A3 med den gemensamma mallen i [`../ritningsmall`](../ritningsmall/). Underlag är K-06 (väggarna: armering, hörn och anslutningar, öppningar, gjutning och återfyllning) och K-05 (väggarnas och rörens lägen, rören VKR 80×80×4 med topplåt).

| Blad | Innehåll | Skala |
|---|---|---|
| R-05.1 | Plan med väggarnas ytterliv, öppningarna i betongen, rörens lägen med måttkedjor och tabell, öppningstabell | 1:50 |
| R-05.2 | Väggarnas armering i plan: vågräta järn, lodräta järn, vinkeljärn i hörn och anslutningar, järn vid öppningarna | 1:50 |
| R-05.3 | Elevationer av fasaden med F1–F3, V8/V9 med D1, V4–V6 med D2 och D3, V3 och V2 (typisk yttervägg) | 1:50 |
| R-05.4 | Sektion A–A (yttervägg mot jord), B–B (innervägg), detalj C (hörn), D (anslutning), E (öppningens smyg och bröstning) | 1:10, 1:20 |
| R-05.5 | Rör med topplåt och fotplåt, fotplåtarna i plan, stålförteckning för väggarna och rörens stål | 1:5, 1:10 |

`kallare.py` är källarens geometri för både R-04 och R-05: väggarna ur K-05:s `geometri.json` (centrumlinjer, betongkärnans ändar vid öppningarna), hörn och anslutningar, öppningarna med bröstningens höjd, rören (P7 två rör), bottenplattans kontur, balkar och plintar (K-06). Bröstningens höjd är R-05:s egen uppgift. Inget läses ur modellen; `verktyg/modellanalys/kontroll_r045.py` jämför `kallare.py` med modellen. `ritningar.py` är uppdelad i underlag, placeringar (`PLAN`, `PLAC`, `ELEV`), lager, blad och main.

Positionsnummer: R-06 1–14, R-05 21–28, R-04 31–41. Stålförteckningarna räknas ur samma funktioner som ritar järnen.

## Köra

```
python beräkningar/K-05/berakning.py      # om K-05/resultat.json saknas
python beräkningar/K-06/berakning.py      # om K-06/resultat.json saknas
python beräkningar/R-05/ritningar.py      # ritningar/R-05 Källarstomme.pdf (R-05.1 … R-05.5)
```

Bladen kompileras var för sig till `blad/` (och `R-05.x.json` här); båda versionshanteras inte.
