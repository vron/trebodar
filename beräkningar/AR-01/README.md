# AR-01 rev A – Fasadsten på källarväggarna, infästning

Egen arbetsritning för utförandet, ingår inte i handlingarna till tekniskt samråd (F-01 avsnitt 6). Ritning över hur beklädnadsgranit Bohus Grå från Stengrossen (600–1 200 × 400 × 30/50 mm, kluven framsida, 28 m² och 9 hörnstenar) fästs på källarväggarnas ytterväggar av Sundolitt Kub 350-150 (betongkärna 150, cellplast 100 + 100) ovan mark. Stenen limmas mot armeringsbruk med nät, som är pluggat genom nätet in i betongkärnan, och står på en rostfri stödvinkel under nedersta skiftet. Vinkeln bärs av gängstänger M16 genom cellplasten och är dimensionerad för att ensam bära stenen om fästet mot cellplasten går förlorat. Inga infästningar i de enskilda stenarna, som i de godkända systemen för natursten på cellplast. Stenens baksida hamnar 15 mm och den kluvna framsidan 45–65 mm utanför cellplasten. Stödvinkeln ligger 50 mm under färdig mark.

| Blad | Innehåll | Skala |
|---|---|---|
| AR-01.1 | Sektion A–A genom väggen, detalj B stödvinkeln på gängstång, detalj C armeringsbruk och isolerplugg genom nätet, anvisningar | 1:10, 1:2,5, 1:2 |
| AR-01.2 | Fasad E (exempel med 400 mm skift i slumpade längder och hörnstenar), positionsförteckning, dimensionering | 1:20 |

| Fil | Innehåll |
|---|---|
| `indata.toml` | Väggen, skikten, stenen, stödvinkel, gängstänger (fischer FIS V, ETA-02/0024), isolerplugg (EJOT STR U 2G, ETA-04/0023), vind och lastfaktorer |
| `berakning.py` | Laster, gängstänger med hävarm genom cellplasten (SS-EN 1992-4), stödvinkel och isolerplugg; skriver `resultat.json` |
| `ritningar.py` | Bladen AR-01.1 och AR-01.2 med den gemensamma mallen i [`../ritningsmall`](../ritningsmall/) |

Stenhöjden på en stödvinkel (högst 2,0 m) och stenens läge följer beklädnaden i modellen (`Beklädnad stor`, `Beklädnad liten`), kontrollerad med `verktyg/modellanalys`. Beräkningen läser inte modellen.

## Köra

```
pip install -r requirements.txt
python berakning.py      # resultat.json
python ritningar.py      # ritningar/AR-01 Fasadsten på källarväggarna.pdf
```

Ritningsserien blir en pdf i [`ritningar/`](../../ritningar/) med ett blad per sida. Bladen (`blad/`), `AR-01.x.json` och `resultat.json` skapas här och versionshanteras inte. Ändra bara i `indata.toml` för att räkna om.
