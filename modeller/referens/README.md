# Referensmodellen

`trebodar-onshape.step` är Onshape-modellen som den kodgenererade modellen i [`modeller/trebodar`](../trebodar/)
byggdes efter. Den är fryst och ändras inte. Koordinater: Onshapes globala system; till K-05:s system är det en
förflyttning (x + 12 147,711, y + 1 292,101, z − 13 939,887 mm, se `trebodar/skelett.py`).

| Fil | Innehåll |
|---|---|
| `trebodar-onshape.step` | Onshape-modellen (STEP AP242) |
| `namntabell.csv` | Varje del i Onshape-modellen och motsvarande del i den kodgenererade modellen, med status (identisk, städad, ändrad, ersatt, borttagen) och andel gemensam volym. Skrivs av `verktyg/modellering/mod jamfor` |
| `delar/*.bbrep` | Delar som modellen ännu läser ur Onshape-modellen (marken: berget, uppfyllnaden och sovrumsavsatsen), i K-05:s koordinater |

Kontrollerna i `verktyg/modellanalys` (`kontroll_*.py`) läser fortfarande den här filen; de ska flyttas över till den
kodgenererade modellens namn.
